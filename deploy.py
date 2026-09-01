#!/usr/bin/env python

import argparse
import paramiko
from scp import SCPClient
import os
import sys


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Provisioned by terraform/startup.sh: owned by the deploy user, with the
# persistent data disk mounted at ./db so the compose file's relative volume
# lands on it.
REMOTE_APP_DIR = "/opt/misho"

# Merged over docker-compose.yml on the server only; see the file's header.
COMPOSE_OVERLAY = "docker-compose.gcp.yml"


def create_ssh_client(host, port, username, key_file=None, password=None):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=username, key_filename=key_file)
    return ssh


def deploy(host, username, docker_compose_path, key_file, tag):
    print("🔗 Establishing SSH connection...")
    print(f"Host: {host}, User: {username}, Key: {key_file}")
    ssh = create_ssh_client(host, 22, username, key_file)

    print(f"📦 Copying docker-compose.yml to {REMOTE_APP_DIR}...")
    transport = ssh.get_transport()
    assert transport is not None, "SSH transport is not available"

    env_path = os.path.join(_SCRIPT_DIR, '.env')

    with SCPClient(transport) as scp:
        scp.put(docker_compose_path,
                remote_path=f"{REMOTE_APP_DIR}/docker-compose.yml")

        # server-only overlay: routes container stdout to Cloud Logging
        scp.put(os.path.join(_SCRIPT_DIR, COMPOSE_OVERLAY),
                remote_path=f"{REMOTE_APP_DIR}/{COMPOSE_OVERLAY}")

        # compose reads .env for both container env and ${MISHO_ENVIRONMENT}
        # substitution, so it has to exist on the host.
        if os.path.isfile(env_path):
            print("🔑 Copying .env...")
            scp.put(env_path, remote_path=f"{REMOTE_APP_DIR}/.env")
        else:
            print("⚠️ No local .env found — the container will start without "
                  "TELEGRAM_BOT_TOKEN / OPENAI_API_KEY.")

    commands = [
        f"docker pull {tag}",
        f"cd {REMOTE_APP_DIR} && docker compose -f docker-compose.yml "
        f"-f {COMPOSE_OVERLAY} up -d",
    ]

    failed = False
    for cmd in commands:
        print(f"🚀 Executing: {cmd}")
        _, stdout, stderr = ssh.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        out = stdout.read().decode()
        err = stderr.read().decode()

        if out:
            print(out)
        if exit_status != 0:
            failed = True
            print(f"❌ Command failed (exit {exit_status}): {err}")
        elif err:
            # docker writes normal progress output to stderr
            print(err)

    ssh.close()

    if failed:
        print("❌ Deployment failed.")
        sys.exit(1)

    print("✅ Deployment complete.")


def main():
    parser = argparse.ArgumentParser(description="Deploy Misho app via SSH.")
    parser.add_argument("ssh_key", help="Path to private key file")
    parser.add_argument("--host", default=os.getenv("MISHO_HOST"),
                        help="Remote host (defaults to $MISHO_HOST)")
    parser.add_argument("--username", default="misho", help="SSH username")
    parser.add_argument("--tag", default="latest")
    parser.add_argument("--compose", default=f"{_SCRIPT_DIR}/docker-compose.yml",
                        help=f"Path to docker-compose.yml (default: {_SCRIPT_DIR}/docker-compose.yml)")
    args = parser.parse_args()

    if not args.host:
        print("❌ No host given. Pass --host or set MISHO_HOST "
              "(terraform output external_ip).")
        sys.exit(1)

    tag = 'mojo28/misho:' + args.tag

    if not os.path.isfile(args.compose):
        print(f"❌ File not found: {args.compose}")
        sys.exit(1)

    deploy(
        host=args.host,
        username=args.username,
        docker_compose_path=args.compose,
        key_file=args.ssh_key,
        tag=tag
    )


if __name__ == "__main__":
    main()
