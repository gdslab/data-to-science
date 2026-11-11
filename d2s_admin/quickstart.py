import os
import shutil
import subprocess
import sys
import re
import secrets
from pathlib import Path

COMPOSE_FILE = "docker-compose.quickstart.yml"

ENV_FILE_PAIRS = [
    ("backend.example.env", "backend.env"),
    ("db.example.env", "db.env"),
    ("frontend.example.env", "frontend.env"),
]


def _get_repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _check_docker():
    try:
        subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            check=True,
        )
    except FileNotFoundError:
        print("Error: docker is not installed or not in PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("Error: 'docker compose' is not available.")
        print(
            "Please install Docker Compose v2: https://docs.docker.com/compose/install/"
        )
        sys.exit(1)


def _fill_secrets(target_path):
    """Replace placeholder secrets in a freshly created env file with random values."""
    text = Path(target_path).read_text()

    # backend.env: real random app secret
    text = re.sub(
        r"(?m)^SECRET_KEY=.*$",
        f"SECRET_KEY={secrets.token_urlsafe(48)}",
        text,
    )

    # db.env: one password, used in both POSTGRES_PASSWORD and DATABASE_URL
    if re.search(r"(?m)^POSTGRES_PASSWORD=", text):
        pw = secrets.token_urlsafe(24)
        text = re.sub(r"(?m)^POSTGRES_PASSWORD=.*$", f"POSTGRES_PASSWORD={pw}", text)
        text = re.sub(r"(DATABASE_URL=postgres://d2s:)[^@]*(@)", rf"\g<1>{pw}\g<2>", text)

    Path(target_path).write_text(text)


def init(args):
    repo_root = _get_repo_root()

    for src_name, dst_name in ENV_FILE_PAIRS:
        src = os.path.join(repo_root, src_name)
        dst = os.path.join(repo_root, dst_name)
        if os.path.exists(dst):
            print(f"  Skipped: {dst_name} already exists")
        elif not os.path.exists(src):
            print(f"  Warning: {src_name} not found, skipping")
        else:
            shutil.copy2(src, dst)
            _fill_secrets(dst)
            print(f"  Created: {dst_name}")

    tusd_dir = os.path.join(repo_root, "tusd-data")
    if os.path.isdir(tusd_dir):
        print("  Skipped: tusd-data/ already exists")
    else:
        os.makedirs(tusd_dir, exist_ok=True)
        print("  Created: tusd-data/")

    print("\nQuickstart environment initialized.")
    print("You can now run: python3 -m d2s_admin quickstart up")


def up(args):
    _check_docker()
    repo_root = _get_repo_root()
    compose_file = os.path.join(repo_root, COMPOSE_FILE)

    if not os.path.exists(compose_file):
        print(f"Error: {COMPOSE_FILE} not found in {repo_root}")
        sys.exit(1)

    result = subprocess.run(
        ["docker", "compose", "-f", compose_file, "up", "-d", "--wait"],
        cwd=repo_root,
    )
    sys.exit(result.returncode)


def down(args):
    _check_docker()
    repo_root = _get_repo_root()
    compose_file = os.path.join(repo_root, COMPOSE_FILE)

    if not os.path.exists(compose_file):
        print(f"Error: {COMPOSE_FILE} not found in {repo_root}")
        sys.exit(1)

    result = subprocess.run(
        ["docker", "compose", "-f", compose_file, "down"],
        cwd=repo_root,
    )
    sys.exit(result.returncode)


def add_parser(subparsers):
    qs_parser = subparsers.add_parser("quickstart", help="Manage quickstart deployment")
    qs_sub = qs_parser.add_subparsers(dest="quickstart_command")

    init_parser = qs_sub.add_parser(
        "init", help="Copy example env files and create tusd-data directory"
    )
    init_parser.set_defaults(func=init)

    up_parser = qs_sub.add_parser("up", help="Start the quickstart containers")
    up_parser.set_defaults(func=up)

    down_parser = qs_sub.add_parser("down", help="Stop the quickstart containers")
    down_parser.set_defaults(func=down)

    qs_parser.set_defaults(func=lambda args: qs_parser.print_help())
