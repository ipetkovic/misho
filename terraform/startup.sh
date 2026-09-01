#!/bin/bash
# Runs on every boot. Must stay idempotent.
set -euo pipefail

DEPLOY_USER="${deploy_user}"
APP_DIR="/opt/misho"
DATA_MOUNT="$APP_DIR/db"
DATA_DEVICE="/dev/disk/by-id/google-misho-data"

log() { echo "[misho-startup] $*"; }

# --- swap ---------------------------------------------------------------
# e2-micro has 1 GB of RAM. The app sits well under that, but a burst during
# image pull or an OpenAI response can push it over.
if [ ! -f /swapfile ]; then
  log "creating swapfile"
  fallocate -l 1G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
swapon --show | grep -q /swapfile || swapon /swapfile

# --- data disk ----------------------------------------------------------
log "preparing data disk"
mkdir -p "$DATA_MOUNT"

for _ in $(seq 1 30); do
  [ -b "$DATA_DEVICE" ] && break
  sleep 1
done

if ! blkid "$DATA_DEVICE" >/dev/null 2>&1; then
  log "formatting $DATA_DEVICE (first boot)"
  mkfs.ext4 -m 0 -F -E lazy_itable_init=0,lazy_journal_init=0,discard "$DATA_DEVICE"
fi

DATA_UUID=$(blkid -s UUID -o value "$DATA_DEVICE")
if ! grep -q "$DATA_UUID" /etc/fstab; then
  echo "UUID=$DATA_UUID $DATA_MOUNT ext4 discard,defaults,nofail 0 2" >> /etc/fstab
fi
mountpoint -q "$DATA_MOUNT" || mount "$DATA_MOUNT"

# --- docker -------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  log "installing docker"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq ca-certificates curl gnupg
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin
fi
systemctl enable --now docker

# --- app dir ------------------------------------------------------------
# deploy.py scps docker-compose.yml and .env here, then runs `docker compose
# up -d` from this directory, so the compose file's relative ./db volume
# resolves onto the mounted data disk.
id -u "$DEPLOY_USER" >/dev/null 2>&1 || useradd -m -s /bin/bash "$DEPLOY_USER"
usermod -aG docker "$DEPLOY_USER"
chown "$DEPLOY_USER":"$DEPLOY_USER" "$APP_DIR" "$DATA_MOUNT"

log "ready"
