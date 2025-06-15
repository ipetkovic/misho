import argparse
import subprocess
import os

PROJECTS_TO_PUBLISH = ('misho-api', 'misho-cli', 'misho-client')

SCRIPT_DIR = os.path.dirname(__file__)


def build_project(project_dir: str):
    print(f"📦 Building {project_dir} ...")
    try:
        subprocess.run(["uv", "build"], cwd=SCRIPT_DIR +
                       '/' + project_dir, check=True)
        print(f"✅ Built {project_dir}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build {project_dir}: {e}")


def publish():
    print("🚀 Publishing ...")
    try:
        subprocess.run(["uv", "publish"], cwd=SCRIPT_DIR, check=True)
        print("✅ All projects published successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to publish projects: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Build all subprojects with uv.")
    parser.parse_args()

    for project in PROJECTS_TO_PUBLISH:
        build_project(project)

    publish()


if __name__ == "__main__":
    main()
