# Proxmox Image

This directory contains configuration for preparing a Proxmox VE ISO with automated installation.

## Files

| File | Purpose |
| --- | --- |
| `answer.toml` | Proxmox automated installer answers |
| `prepare_proxmox_usb.py` | Downloads the ISO, customizes it with `answer.toml`, and optionally writes it to USB |

## Prerequisites

The system used to prepare the USB drive needs:

- Python 3.10+;
- `proxmox-auto-install-assistant`;
- `xorriso`;
- `openssl`;
- root permissions only for the final USB write.

On Debian/Ubuntu:

```bash
sudo apt install proxmox-auto-install-assistant xorriso openssl
```

## Usage

Start the interactive wizard:

```bash
python3 prepare_proxmox_usb.py
```

The wizard asks for:

- Proxmox ISO URL;
- checksum SHA256;
- file `answer.toml`;
- build directory;
- root password to inject as `root-password-hashed`;
- whether to write the ISO to a USB drive.

Download and prepare the customized ISO in non-interactive mode:

```bash
python3 prepare_proxmox_usb.py \
  --iso-url https://enterprise.proxmox.com/iso/REPLACE_WITH_PROXMOX_ISO.iso \
  --answer-file answer.toml \
  --prompt-root-password \
  --non-interactive
```

Also write the customized ISO to a USB drive in non-interactive mode:

```bash
sudo python3 prepare_proxmox_usb.py \
  --iso-url https://enterprise.proxmox.com/iso/REPLACE_WITH_PROXMOX_ISO.iso \
  --answer-file answer.toml \
  --prompt-root-password \
  --usb-device /dev/sdX \
  --yes \
  --non-interactive
```

Warning: `--usb-device` must point to the whole device, for example `/dev/sdX`, not to a partition such as `/dev/sdX1`. Writing erases the USB drive contents.

Take the current ISO URL from the official Proxmox VE download page. When available, also pass `--sha256` with the published checksum.

For non-interactive automation, pass the password through an environment variable:

```bash
export PROXMOX_ROOT_PASSWORD='replace-with-a-strong-password'
python3 prepare_proxmox_usb.py \
  --iso-url https://enterprise.proxmox.com/iso/REPLACE_WITH_PROXMOX_ISO.iso \
  --answer-file answer.toml \
  --root-password-env PROXMOX_ROOT_PASSWORD \
  --non-interactive
```

The script does not modify `answer.toml`: it generates `build/answer.generated.toml` with `root-password-hashed` and uses that file to prepare the ISO.

## Customization

Before use, edit `answer.toml`:

- `fqdn`;
- `root-ssh-keys`;
- network configuration;
- target disk filter or list.

To manually validate the final configuration, generate the ISO with the script and then validate the generated file:

```bash
proxmox-auto-install-assistant validate-answer build/answer.generated.toml
```
