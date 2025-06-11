#!/usr/bin/env python

import argparse
import os
import subprocess
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def build_docker_image(tag, platform, push):
    cmd = [
        "docker", "buildx", "build",
        "--platform", platform,
        "-t", tag,
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


def main():
    parser = argparse.ArgumentParser(
        description="Build (and optionally push) a Docker image.")
    parser.add_argument("--tag", "-t", default="mojo28/misho:latest",
                        help="Docker image tag")
    parser.add_argument("--platform", "-p", default="linux/amd64",
                        help="Target platform (default: linux/amd64)")
    parser.add_argument("--push", action="store_true",
                        help="Push image to Docker registry")

    args = parser.parse_args()
    build_docker_image(args.tag, args.platform, args.push)


if __name__ == "__main__":
    main()
