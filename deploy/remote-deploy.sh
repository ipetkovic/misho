#!/usr/bin/env bash
#
# Rolls out a new image on the VM and verifies it came up healthy, restoring
# the previously deployed tag if it did not.
#
# This is not a rolling update: the bot consumes Telegram updates by long
# polling, so two live containers would fight over getUpdates (409) and run two
# reservation schedulers racing for the same court. The swap is therefore
# stop-then-start, and the cost of that is a few seconds of downtime.
#
# Invoked by .github/workflows/deploy.yml as:
#   sudo bash /tmp/misho-deploy/remote-deploy.sh <image-tag>
# with the compose files and .env staged alongside it in /tmp/misho-deploy.
set -euo pipefail

APP_DIR=/opt/misho
STAGE_DIR=/tmp/misho-deploy
IMAGE=ghcr.io/ipetkovic/misho
CONTAINER=misho
# Must exceed the Dockerfile's --start-period of 120s, or a slow-but-fine boot
# (migrations plus 100 days of time slots on a shared core) reads as a failure.
HEALTH_TIMEOUT=180
KEEP_IMAGES=3

NEW_TAG="${1:?usage: remote-deploy.sh <image-tag>}"

compose() {
    docker compose -f docker-compose.yml -f docker-compose.gcp.yml "$@"
}

log() { printf '==> %s\n' "$*"; }

current_tag() {
    # The deployed tag is recorded in .env, which is also where compose reads
    # it from for interpolation.
    sed -n 's/^MISHO_IMAGE_TAG=//p' "$APP_DIR/.env" 2>/dev/null | tail -1
}

set_tag() {
    local tag="$1" env_file="$APP_DIR/.env"
    if grep -q '^MISHO_IMAGE_TAG=' "$env_file"; then
        sed -i "s|^MISHO_IMAGE_TAG=.*|MISHO_IMAGE_TAG=$tag|" "$env_file"
    else
        printf 'MISHO_IMAGE_TAG=%s\n' "$tag" >> "$env_file"
    fi
}

wait_for_health() {
    local deadline=$((SECONDS + HEALTH_TIMEOUT)) status
    while ((SECONDS < deadline)); do
        status=$(docker inspect \
            -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' \
            "$CONTAINER" 2>/dev/null || echo missing)
        case "$status" in
            healthy)
                log "healthy after $((SECONDS))s"
                return 0
                ;;
            unhealthy)
                log "container reported unhealthy"
                return 1
                ;;
            none)
                log "container has no healthcheck -- image is too old to verify"
                return 1
                ;;
        esac
        sleep 3
    done
    log "timed out waiting for healthy after ${HEALTH_TIMEOUT}s (last status: ${status:-unknown})"
    return 1
}

diagnostics() {
    log "last 60 log lines from $CONTAINER:"
    docker logs --tail 60 "$CONTAINER" 2>&1 || true
    log "health probe output:"
    docker inspect -f '{{json .State.Health}}' "$CONTAINER" 2>/dev/null || true
}

prune_old_images() {
    # Keep the most recent few so a rollback needs no network. `docker images`
    # lists newest first.
    local stale
    stale=$(docker images --format '{{.ID}} {{.Repository}}:{{.Tag}}' \
        --filter "reference=$IMAGE" | awk -v keep="$KEEP_IMAGES" 'NR > keep {print $1}')
    if [[ -n "$stale" ]]; then
        log "pruning $(wc -l <<< "$stale") old image(s)"
        # Never fatal: an image still referenced by a stopped container is not
        # a reason to fail a deploy that already succeeded.
        xargs -r docker rmi <<< "$stale" || true
    fi
}

cd "$APP_DIR"

PREV_TAG=$(current_tag)
log "currently deployed: ${PREV_TAG:-<none>}; rolling out: $NEW_TAG"

log "installing staged compose files and environment"
install -m 0644 "$STAGE_DIR/docker-compose.yml" "$APP_DIR/docker-compose.yml"
install -m 0644 "$STAGE_DIR/docker-compose.gcp.yml" "$APP_DIR/docker-compose.gcp.yml"
# 0600: this file holds the bot and OpenAI tokens.
install -m 0600 "$STAGE_DIR/.env" "$APP_DIR/.env"
# The staged .env carries no tag, so restore the running one first. Until the
# pull below succeeds, the file must keep describing what is actually up.
set_tag "${PREV_TAG:-latest}"

log "pulling $IMAGE:$NEW_TAG"
if ! docker pull "$IMAGE:$NEW_TAG"; then
    log "FAILED to pull $IMAGE:$NEW_TAG -- nothing was changed, the running container is untouched."
    log "If this is the first deploy, check the ghcr.io package is set to public;"
    log "new packages default to private even from a public repository."
    exit 1
fi

# Committed only now that the image is definitely on disk.
set_tag "$NEW_TAG"

log "starting"
compose up -d

if wait_for_health; then
    log "deploy of $NEW_TAG succeeded"
    prune_old_images
    rm -rf "$STAGE_DIR"
    exit 0
fi

diagnostics

if [[ -z "$PREV_TAG" ]]; then
    log "FAILED and there is no previous tag recorded -- leaving as is for inspection"
    exit 1
fi

if ! docker image inspect "$IMAGE:$PREV_TAG" >/dev/null 2>&1; then
    log "FAILED and the previous image $IMAGE:$PREV_TAG is no longer on disk -- cannot roll back"
    exit 1
fi

log "rolling back to $PREV_TAG"
set_tag "$PREV_TAG"
compose up -d

if wait_for_health; then
    log "rolled back to $PREV_TAG; $NEW_TAG was not deployed"
else
    log "ROLLBACK ALSO FAILED -- the bot is down and needs manual attention"
fi
exit 1
