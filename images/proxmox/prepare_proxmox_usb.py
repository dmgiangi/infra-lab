#!/usr/bin/env python3
"""Prepare a Proxmox VE automated installer ISO and optionally write it to USB."""

from __future__ import annotations

import argparse
import getpass
import hashlib
import os
import secrets
import shutil
import subprocess
import string
import urllib.request
from pathlib import Path


DEFAULT_BUILD_DIR = Path(__file__).resolve().parent / "build"
DEFAULT_ANSWER_FILE = Path(__file__).resolve().parent / "answer.toml"
DEFAULT_ISO_URL = "https://enterprise.proxmox.com/iso/proxmox-ve_9.1-1.iso"
DEFAULT_ISO_SHA256 = "6d8f5afc78c0c66812d7272cde7c8b98be7eb54401ceb045400db05eb5ae6d22"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download a Proxmox ISO, inject answer.toml, and optionally write it to a USB device."
    )
    parser.add_argument(
        "--iso-url",
        default=None,
        help="HTTP(S) URL of the Proxmox VE installer ISO to download.",
    )
    parser.add_argument(
        "--answer-file",
        type=Path,
        default=DEFAULT_ANSWER_FILE,
        help="Path to the Proxmox auto-installer answer.toml file.",
    )
    parser.add_argument(
        "--build-dir",
        type=Path,
        default=DEFAULT_BUILD_DIR,
        help="Directory used for downloaded and generated ISO files.",
    )
    parser.add_argument(
        "--sha256",
        default=None,
        help="Optional expected SHA256 checksum for the downloaded ISO.",
    )
    password_group = parser.add_mutually_exclusive_group()
    password_group.add_argument(
        "--prompt-root-password",
        action="store_true",
        help="Prompt for the Proxmox root password and inject it as root-password-hashed.",
    )
    password_group.add_argument(
        "--root-password-env",
        metavar="ENV_VAR",
        help="Read the Proxmox root password from an environment variable and inject it as root-password-hashed.",
    )
    parser.add_argument(
        "--usb-device",
        help="Optional whole USB block device to overwrite, for example /dev/sdX.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm destructive USB write without an interactive prompt.",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Do not run the wizard; require all needed values from command-line options.",
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
    value = prompt_text(label, str(default), required=required)
    return Path(value).expanduser()


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


def print_block_devices() -> None:
    if not command_exists("lsblk"):
        return

    result = subprocess.run(
        ["lsblk", "-o", "NAME,TYPE,SIZE,MODEL,SERIAL,TRAN,MOUNTPOINTS"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        print("\nDetected block devices:")
        print(result.stdout.rstrip())
        print()


def run_wizard(args: argparse.Namespace) -> argparse.Namespace:
    if args.non_interactive:
        if not args.iso_url:
            raise SystemExit("--iso-url is required when --non-interactive is used.")
        return args

    print("Proxmox USB preparation wizard")
    print("Press Enter to accept the value shown in brackets.\n")

    args.iso_url = prompt_text("Proxmox ISO URL", args.iso_url or DEFAULT_ISO_URL, required=True)
    sha_default = args.sha256
    if sha_default is None and args.iso_url == DEFAULT_ISO_URL:
        sha_default = DEFAULT_ISO_SHA256
    args.sha256 = prompt_text("ISO SHA256 checksum", sha_default)
    if not args.sha256:
        args.sha256 = None

    args.answer_file = prompt_path("Answer file", args.answer_file, required=True)
    args.build_dir = prompt_path("Build directory", args.build_dir, required=True)

    if not args.prompt_root_password and not args.root_password_env:
        if prompt_yes_no("Prompt for Proxmox root password now", default=True):
            args.prompt_root_password = True
        else:
            env_var = prompt_text("Root password environment variable name", "")
            if env_var:
                args.root_password_env = env_var

    if not args.usb_device and prompt_yes_no("Write the prepared ISO to a USB device", default=False):
        print_block_devices()
        args.usb_device = prompt_text("Whole USB device path", "/dev/sdX", required=True)
        args.yes = prompt_yes_no("Skip the final device-name confirmation", default=False)

    return args


def command_exists(command: str) -> bool:
    return shutil.which(Path(command)) is not None


def require_command(command: str) -> None:
    if not command_exists(command):
        raise SystemExit(f"Missing required command: {command}")


def filename_from_url(url: str) -> str:
    name = url.rstrip("/").rsplit("/", maxsplit=1)[-1]
    if not name or not name.endswith(".iso"):
        raise SystemExit("The --iso-url value must end with an ISO filename.")
    return name


def download_iso(url: str, destination: Path) -> None:
    if destination.exists():
        print(f"Using existing ISO: {destination}")
        return

    print(f"Downloading {url}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)
    print(f"Downloaded ISO: {destination}")


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_checksum(path: Path, expected: str | None) -> None:
    if expected is None:
        return

    actual = sha256sum(path)
    if actual.lower() != expected.lower():
        raise SystemExit(
            f"SHA256 mismatch for {path}: expected {expected.lower()}, got {actual.lower()}"
        )
    print("SHA256 checksum verified.")


def validate_answer(answer_file: Path) -> None:
    subprocess.run(
        ["proxmox-auto-install-assistant", "validate-answer", str(answer_file)],
        check=True,
    )


def read_root_password(args: argparse.Namespace) -> str | None:
    if args.prompt_root_password:
        password = getpass.getpass("Proxmox root password: ")
        repeated = getpass.getpass("Repeat Proxmox root password: ")
        if password != repeated:
            raise SystemExit("Root passwords do not match.")
        if not password:
            raise SystemExit("Root password cannot be empty.")
        return password

    if args.root_password_env:
        password = os.environ.get(args.root_password_env)
        if not password:
            raise SystemExit(f"Environment variable {args.root_password_env} is not set or is empty.")
        return password

    return None


def hash_root_password(password: str) -> str:
    require_command("openssl")
    salt_alphabet = string.ascii_letters + string.digits + "./"
    salt = "".join(secrets.choice(salt_alphabet) for _ in range(16))
    result = subprocess.run(
        ["openssl", "passwd", "-6", "-salt", salt, "-stdin"],
        input=password + "\n",
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def has_password_key(lines: list[str]) -> bool:
    return any(
        line.lstrip().startswith("root-password =")
        or line.lstrip().startswith("root-password-hashed =")
        for line in lines
    )


def render_answer_with_password_hash(answer_file: Path, output_file: Path, password_hash: str) -> Path:
    lines = answer_file.read_text(encoding="utf-8").splitlines(keepends=True)
    rendered: list[str] = []
    in_global = False
    inserted = False

    for line in lines:
        stripped = line.strip()
        if stripped == "[global]":
            in_global = True
            rendered.append(line)
            continue

        if in_global and stripped.startswith("[") and stripped.endswith("]"):
            if not inserted:
                rendered.append(f'root-password-hashed = "{password_hash}"\n')
                inserted = True
            in_global = False

        if in_global and (
            line.lstrip().startswith("root-password =")
            or line.lstrip().startswith("root-password-hashed =")
        ):
            if not inserted:
                rendered.append(f'root-password-hashed = "{password_hash}"\n')
                inserted = True
            continue

        rendered.append(line)

    if in_global and not inserted:
        rendered.append(f'root-password-hashed = "{password_hash}"\n')
        inserted = True

    if not inserted:
        raise SystemExit("Could not inject root-password-hashed: missing [global] section.")

    output_file.write_text("".join(rendered), encoding="utf-8")
    output_file.chmod(0o600)
    return output_file


def resolve_answer_file(args: argparse.Namespace, build_dir: Path) -> Path:
    answer_file = args.answer_file.resolve()
    if not answer_file.exists():
        raise SystemExit(f"Answer file not found: {answer_file}")

    password = read_root_password(args)
    if password is None:
        if not has_password_key(answer_file.read_text(encoding="utf-8").splitlines()):
            raise SystemExit(
                "The answer file has no root password. Use --prompt-root-password "
                "or --root-password-env to inject root-password-hashed at runtime."
            )
        return answer_file

    generated_answer = build_dir / "answer.generated.toml"
    password_hash = hash_root_password(password)
    return render_answer_with_password_hash(answer_file, generated_answer, password_hash)


def prepare_iso(source_iso: Path, answer_file: Path, output_iso: Path) -> None:
    if output_iso.exists():
        print(f"Using existing prepared ISO: {output_iso}")
        return

    print(f"Preparing automated installer ISO: {output_iso}")
    subprocess.run(
        [
            "proxmox-auto-install-assistant",
            "prepare-iso",
            str(source_iso),
            "--fetch-from",
            "iso",
            "--answer-file",
            str(answer_file),
            "--output",
            str(output_iso),
        ],
        check=True,
    )


def assert_usb_device(device: str) -> None:
    device_path = Path(device)
    if not device.startswith("/dev/"):
        raise SystemExit("--usb-device must be an absolute /dev path.")
    if not device_path.exists():
        raise SystemExit(f"USB device does not exist: {device}")
    if command_exists("lsblk"):
        result = subprocess.run(
            ["lsblk", "--noheadings", "--nodeps", "--output", "TYPE", device],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or result.stdout.strip() != "disk":
            raise SystemExit("Pass the whole USB device, for example /dev/sdX, not a partition.")
    if not os.access(device_path, os.W_OK):
        raise SystemExit("USB device is not writable. Re-run with sudo if the device is correct.")


def confirm_usb_write(device: str, yes: bool) -> None:
    if yes:
        return

    print(f"About to overwrite all data on {device}.")
    typed = input(f'Type "{device}" to continue: ')
    if typed != device:
        raise SystemExit("USB write aborted.")


def write_usb(iso_path: Path, device: str, yes: bool) -> None:
    assert_usb_device(device)
    confirm_usb_write(device, yes)

    print(f"Writing {iso_path} to {device}")
    subprocess.run(
        ["dd", f"if={iso_path}", f"of={device}", "bs=4M", "status=progress", "oflag=sync"],
        check=True,
    )
    subprocess.run(["sync"], check=True)
    print("USB write completed.")


def main() -> int:
    args = run_wizard(parse_args())

    require_command("proxmox-auto-install-assistant")
    require_command("xorriso")
    if args.usb_device:
        require_command("dd")

    build_dir = args.build_dir.resolve()
    build_dir.mkdir(parents=True, exist_ok=True)
    answer_file = resolve_answer_file(args, build_dir)

    source_iso = build_dir / filename_from_url(args.iso_url)
    prepared_iso = build_dir / source_iso.name.replace(".iso", "-autoinstall.iso")

    download_iso(args.iso_url, source_iso)
    verify_checksum(source_iso, args.sha256)
    validate_answer(answer_file)
    prepare_iso(source_iso, answer_file, prepared_iso)

    if args.usb_device:
        write_usb(prepared_iso, args.usb_device, args.yes)
    else:
        print(f"Prepared ISO available at: {prepared_iso}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
