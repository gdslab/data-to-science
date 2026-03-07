import getpass
import os
import subprocess
import sys

COMPOSE_FILE = "docker-compose.quickstart.yml"


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
        sys.exit(1)


def _prompt_value(label, current_value):
    if current_value:
        return current_value
    value = input(f"{label}: ").strip()
    if not value:
        print(f"Error: {label} cannot be empty.")
        sys.exit(1)
    return value


def _prompt_password(current_value):
    if current_value:
        return current_value
    password = getpass.getpass("Password: ")
    if not password:
        print("Error: Password cannot be empty.")
        sys.exit(1)
    confirm = getpass.getpass("Password (confirm): ")
    if password != confirm:
        print("Error: Passwords do not match.")
        sys.exit(1)
    return password


def run(args):
    _check_docker()
    repo_root = _get_repo_root()
    compose_file = os.path.join(repo_root, COMPOSE_FILE)

    if not os.path.exists(compose_file):
        print(f"Error: {COMPOSE_FILE} not found in {repo_root}")
        sys.exit(1)

    email = _prompt_value("Email", args.email)
    first_name = _prompt_value("First name", args.first_name)
    last_name = _prompt_value("Last name", args.last_name)
    password = _prompt_password(args.password)

    print("Creating superuser account (this may take a moment)...", flush=True)

    cmd = [
        "docker", "compose", "-f", compose_file,
        "exec",
    ]

    if not sys.stdin.isatty():
        cmd.append("-T")

    cmd.extend([
        "backend", "python", "app/scripts/create_superuser.py",
        "--email", email,
        "--first-name", first_name,
        "--last-name", last_name,
        "--password", password,
    ])

    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    if result.returncode == 0:
        print(result.stdout.strip())
    else:
        print(result.stdout.strip())
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
    sys.exit(result.returncode)


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "createsuperuser", help="Create a superuser account"
    )
    parser.add_argument("--email", default=None, help="User email address")
    parser.add_argument("--first-name", default=None, help="First name")
    parser.add_argument("--last-name", default=None, help="Last name")
    parser.add_argument("--password", default=None, help="Password")
    parser.set_defaults(func=run)
