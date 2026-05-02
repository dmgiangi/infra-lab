# Images

This directory contains tooling for preparing installation images used by the local infrastructure.

## Structure

| Area | Purpose | README |
| --- | --- | --- |
| `proxmox/` | Proxmox VE ISO preparation with automated install and USB writing | [proxmox/README.md](proxmox/README.md) |

## Operational Notes

ISO images and generated files are not versioned. Each subdirectory should document:

- local prerequisites;
- configuration files;
- command used to generate the image;
- any destructive steps, such as writing to a USB drive.
