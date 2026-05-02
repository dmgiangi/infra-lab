#!/usr/bin/env python3
"""Configure managed /etc/hosts and SSH config entries for the local lab."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pwd
import re
import shutil
from pathlib import Path
from typing import Any


MARKER_NAME = "k8s-tests"
HOSTS_BEGIN = f"# BEGIN {MARKER_NAME} managed hosts"
HOSTS_END = f"# END {MARKER_NAME} managed hosts"
SSH_BEGIN = f"# BEGIN {MARKER_NAME} managed ssh"
SSH_END = f"# END {MARKER_NAME} managed ssh"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add managed entries to /etc/hosts and the current user's SSH config."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parent / "hosts.yaml",
        help="Path to a YAML or JSON host configuration file.",
    )
    parser.add_argument(
        "--hosts-file",
        type=Path,
        default=Path("/etc/hosts"),
        help="Hosts file to update.",
    )
    parser.add_argument(
        "--ssh-config",
        type=Path,
        help="SSH config path. Defaults to the invoking user's ~/.ssh/config.",
    )
    parser.add_argument(
        "--skip-hosts",
        action="store_true",
        help="Do not update the hosts file.",
    )
    parser.add_argument(
        "--skip-ssh",
        action="store_true",
        help="Do not update SSH config.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without writing files.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Do not ask for confirmation before writing /etc/hosts.",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip the wizard and use command-line options directly.",
    )
    return parser.parse_args()


def prompt_text(label: str, default: str | None = None, required: bool = False) -> str:
    while True:
        suffix = f" [{default}]" if default else ""
        value = input(f"{label}{suffix}: ").strip()
        if value:
            return value
        if default is not None:
            return default
        if not required:
            return ""
        print("A value is required.")


def prompt_path(label: str, default: Path, required: bool = False) -> Path:
    return Path(prompt_text(label, str(default), required=required)).expanduser()


def prompt_yes_no(label: str, default: bool = False) -> bool:
    default_text = "Y/n" if default else "y/N"
    while True:
        value = input(f"{label} [{default_text}]: ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Answer yes or no.")


def run_wizard(args: argparse.Namespace) -> argparse.Namespace:
    if args.non_interactive:
        return args

    print("Hosts and SSH configuration wizard")
    print("Press Enter to accept the value shown in brackets.\n")

    args.config = prompt_path("Host config file", args.config, required=True)

    args.skip_hosts = not prompt_yes_no("Update hosts file", default=not args.skip_hosts)
    if not args.skip_hosts:
        args.hosts_file = prompt_path("Hosts file", args.hosts_file, required=True)

    args.skip_ssh = not prompt_yes_no("Update SSH config", default=not args.skip_ssh)
    if not args.skip_ssh:
        args.ssh_config = prompt_path(
            "SSH config file",
            args.ssh_config or default_ssh_config_path(),
            required=True,
        )

    args.dry_run = prompt_yes_no("Dry run only", default=args.dry_run)
    if not args.dry_run and not args.skip_hosts and args.hosts_file == Path("/etc/hosts"):
        args.yes = prompt_yes_no("Skip final /etc/hosts confirmation", default=args.yes)

    return args


def invoking_home() -> Path:
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        return Path(pwd.getpwnam(sudo_user).pw_dir)
    return Path.home()


def default_ssh_config_path() -> Path:
    return invoking_home() / ".ssh" / "config"


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None", "~"}:
        return None
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_simple_yaml(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {"defaults": {}, "hosts": []}
    section: str | None = None
    current_host: dict[str, Any] | None = None
    current_list_key: str | None = None

    for raw_line in text.splitlines():
        line_without_comment = raw_line.split("#", maxsplit=1)[0].rstrip()
        if not line_without_comment.strip():
            continue

        indent = len(line_without_comment) - len(line_without_comment.lstrip(" "))
        line = line_without_comment.strip()

        if indent == 0 and line.endswith(":"):
            section = line[:-1]
            current_host = None
            current_list_key = None
            continue

        if section == "defaults" and indent == 2 and ":" in line:
            key, value = line.split(":", maxsplit=1)
            result["defaults"][key.strip()] = parse_scalar(value)
            continue

        if section == "hosts" and indent == 2 and line.startswith("- "):
            current_host = {}
            result["hosts"].append(current_host)
            current_list_key = None
            item = line[2:].strip()
            if item and ":" in item:
                key, value = item.split(":", maxsplit=1)
                current_host[key.strip()] = parse_scalar(value)
            continue

        if section == "hosts" and current_host is not None and indent == 4 and ":" in line:
            key, value = line.split(":", maxsplit=1)
            key = key.strip()
            if value.strip():
                current_host[key] = parse_scalar(value)
                current_list_key = None
            else:
                current_host[key] = []
                current_list_key = key
            continue

        if (
            section == "hosts"
            and current_host is not None
            and current_list_key is not None
            and indent == 6
            and line.startswith("- ")
        ):
            current_host[current_list_key].append(parse_scalar(line[2:]))
            continue

        raise SystemExit(f"Unsupported YAML syntax near line: {raw_line}")

    return result


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Config file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        data = json.loads(text)
    else:
        data = parse_simple_yaml(text)

    defaults = data.get("defaults", {})
    hosts = data.get("hosts", [])
    if not isinstance(defaults, dict):
        raise SystemExit("Config key 'defaults' must be a map.")
    if not isinstance(hosts, list) or not hosts:
        raise SystemExit("Config key 'hosts' must be a non-empty list.")

    for host in hosts:
        if not isinstance(host, dict):
            raise SystemExit("Every host entry must be a map.")
        if not host.get("name") or not host.get("ip"):
            raise SystemExit("Every host entry requires 'name' and 'ip'.")
        host.setdefault("aliases", [])
        if not isinstance(host["aliases"], list):
            raise SystemExit(f"Host {host['name']} aliases must be a list.")

    return {"defaults": defaults, "hosts": hosts}


def build_hosts_block(hosts: list[dict[str, Any]]) -> str:
    lines = [HOSTS_BEGIN]
    for host in hosts:
        names = [str(host["name"]), *[str(alias) for alias in host.get("aliases", [])]]
        lines.append(f"{host['ip']}\t{' '.join(names)}")
    lines.append(HOSTS_END)
    return "\n".join(lines) + "\n"


def build_ssh_block(defaults: dict[str, Any], hosts: list[dict[str, Any]]) -> str:
    default_user = defaults.get("user")
    default_identity_file = defaults.get("identity_file")

    lines = [SSH_BEGIN]
    for index, host in enumerate(hosts):
        if index:
            lines.append("")
        lines.append(f"Host {host['name']}")
        lines.append(f"  HostName {host['ip']}")
        user = host.get("user", default_user)
        if user:
            lines.append(f"  User {user}")
        identity_file = host.get("identity_file", default_identity_file)
        if identity_file:
            lines.append(f"  IdentityFile {identity_file}")
        lines.append("  IdentitiesOnly yes")
    lines.append(SSH_END)
    return "\n".join(lines) + "\n"


def replace_managed_block(content: str, begin: str, end: str, block: str) -> str:
    pattern = re.compile(rf"{re.escape(begin)}.*?{re.escape(end)}\n?", re.DOTALL)
    content = content.rstrip() + "\n" if content.strip() else ""
    if pattern.search(content):
        return pattern.sub(block, content)
    return content + ("\n" if content else "") + block


def timestamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%d%H%M%S")


def backup_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    backup_path = path.with_name(f"{path.name}.bak.{timestamp()}")
    shutil.copy2(path, backup_path)
    return backup_path


def ensure_ssh_permissions(path: Path) -> None:
    parent_existed = path.parent.exists()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not parent_existed or path.parent.name == ".ssh":
        path.parent.chmod(0o700)
    if path.exists():
        path.chmod(0o600)


def write_managed_file(path: Path, begin: str, end: str, block: str, dry_run: bool) -> None:
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    updated = replace_managed_block(original, begin, end, block)

    if updated == original:
        print(f"No changes needed: {path}")
        return

    if dry_run:
        print(f"Would update: {path}")
        print(block.rstrip())
        return

    backup = backup_file(path)
    if backup:
        print(f"Backup created: {backup}")
    path.write_text(updated, encoding="utf-8")
    print(f"Updated: {path}")


def confirm_hosts_write(path: Path, yes: bool, dry_run: bool) -> None:
    if yes or dry_run or path != Path("/etc/hosts"):
        return
    print("/etc/hosts requires elevated permissions and affects local name resolution.")
    typed = input('Type "yes" to update /etc/hosts: ').strip()
    if typed != "yes":
        raise SystemExit("Hosts file update aborted.")


def main() -> int:
    args = run_wizard(parse_args())
    if args.skip_hosts and args.skip_ssh:
        raise SystemExit("Nothing to do: both --skip-hosts and --skip-ssh were provided.")

    config = load_config(args.config.expanduser().resolve())
    defaults = config["defaults"]
    hosts = config["hosts"]
    ssh_config = args.ssh_config.expanduser() if args.ssh_config else default_ssh_config_path()

    if not args.skip_hosts:
        confirm_hosts_write(args.hosts_file, args.yes, args.dry_run)
        hosts_block = build_hosts_block(hosts)
        write_managed_file(args.hosts_file, HOSTS_BEGIN, HOSTS_END, hosts_block, args.dry_run)

    if not args.skip_ssh:
        if not args.dry_run:
            ensure_ssh_permissions(ssh_config)
        ssh_block = build_ssh_block(defaults, hosts)
        write_managed_file(ssh_config, SSH_BEGIN, SSH_END, ssh_block, args.dry_run)
        if not args.dry_run:
            ssh_config.chmod(0o600)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
