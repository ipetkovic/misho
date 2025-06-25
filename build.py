#!/usr/bin/env python

import argparse
import os
import subprocess
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def build_docker_image(app, tag, platform, push):
    cmd = [
        "docker", "buildx", "build",
        "--platform", platform,
        "-t", tag,
        '--file', os.path.join(_SCRIPT_DIR, app, 'Dockerfile'),
        '.'
    ]

    if push:
        cmd.append("--push")

    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, cwd=_SCRIPT_DIR)
        print("✅ Docker build completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker build failed: {e}")
        sys.exit(1)


_TAGS = {
    "misho-server": "mojo28/misho",
    "misho-bot": "mojo28/misho-bot"
}


def main():
    parser = argparse.ArgumentParser(
        description="Build (and optionally push) a Docker image.")
    parser.add_argument("app",
                        help="Application name (misho, misho-bot)")
    parser.add_argument("--tag", "-t", default="mojo28/misho:latest",
                        help="Docker image tag")
    parser.add_argument("--platform", "-p", default="linux/amd64",
                        help="Target platform (default: linux/amd64)")
    parser.add_argument("--push", action="store_true",
                        help="Push image to Docker registry")

    args = parser.parse_args()
    tag = _TAGS[args.app] + ':' + 'latest'
    build_docker_image(args.app, tag, args.platform, args.push)


if __name__ == "__main__":
    main()
