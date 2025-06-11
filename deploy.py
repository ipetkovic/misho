#!/usr/bin/env python

import argparse
import paramiko
from scp import SCPClient
import os


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def create_ssh_client(host, port, username, key_file=None, password=None):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=username, key_filename=key_file)
    return ssh


def deploy(host, username, docker_compose_path, key_file, tag):
    print("🔗 Establishing SSH connection...")
    print(f"Host: {host}, User: {username}, Key: {key_file}")
    ssh = create_ssh_client(host, 22, username, key_file)

    print(ssh)

    print("📦 Copying docker-compose.yml...")
    with SCPClient(ssh.get_transport()) as scp:
        scp.put(f'{_SCRIPT_DIR}/docker-compose.yml',
                remote_path=f"./docker-compose.yml")

    commands = [
        f"docker pull {tag}",
        "docker-compose up -d misho"
    ]

    for cmd in commands:
        print(f"🚀 Executing: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        err = stderr.read().decode()
        if err:
            print(f"⚠️ Error: {err}")

    ssh.close()
    print("✅ Deployment complete.")


def main():
    parser = argparse.ArgumentParser(description="Deploy Misho app via SSH.")
    parser.add_argument("ssh_key", help="Path to private key file")
    parser.add_argument(
        "--host", default='ec2-52-57-94-53.eu-central-1.compute.amazonaws.com', help="Remote host")
    parser.add_argument("--username", default='ec2-user', help="SSH username")
    parser.add_argument("--tag", default="mojo28/misho:latest")
    parser.add_argument("--compose", default=f"{_SCRIPT_DIR}/docker-compose.yml",
                        help=f"Path to docker-compose.yml (default: {_SCRIPT_DIR}/docker-compose.yml)")

    args = parser.parse_args()

    if not os.path.isfile(args.compose):
        print(f"❌ File not found: {args.compose}")
        return

    deploy(
        host=args.host,
        username=args.username,
        docker_compose_path=args.compose,
        key_file=args.ssh_key,
        tag=args.tag
    )


if __name__ == "__main__":
    main()
