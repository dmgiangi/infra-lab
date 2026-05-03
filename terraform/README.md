# Terraform

This directory contains Terraform configuration for creating Kubernetes VMs on a Proxmox VE host.

## Assumptions

- Host already installed with Proxmox VE.
- Provider Terraform: `bpg/proxmox`.
- Reachable Proxmox API endpoint, usually `https://HOST:8006/`.
- Dedicated Proxmox API token for Terraform.
- SSH access from this workstation to the Proxmox node. This is required for provider-managed file uploads such as cloud-init snippets.
- Existing Proxmox node, for example `pve-01`.
- Datastore for images, for example `local`.
- Datastore for VM disks, for example `local-lvm`.
- Datastore for cloud-init snippets, for example `local`, with the `Snippets` content type enabled.
- Existing network bridge, for example `vmbr0`.
- Base image: Ubuntu cloud image imported by Proxmox.

## Files

| File | Purpose |
| --- | --- |
| `versions.tf` | Required Terraform and provider versions |
| `variables.tf` | Configurable variables |
| `main.tf` | Proxmox resources for cloud image import and VM creation |
| `cloud-init/user-data.yaml.tftpl` | Custom cloud-init user-data installed on first boot |
| `outputs.tf` | Useful outputs after `terraform apply` |
| `terraform.tfvars` | Local lab configuration values |

## Usage

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

`terraform.tfvars` contains the local lab defaults. Keep secrets out of it and pass credentials through environment variables.

The custom cloud-init user-data installs and starts `qemu-guest-agent` on first boot. `qemu_guest_agent_enabled` is still disabled for initial VM creation so Terraform does not wait for guest-agent data before cloud-init finishes. After the VMs complete first boot, it can be enabled and applied again.

Terraform can also attach an optional secondary data disk to each VM through `data_disk_gb`. The disk is created but not formatted or mounted by Terraform. Future Ansible playbooks will prepare it for Kubernetes persistent storage, for example at `/var/lib/k8s-storage`.

## Proxmox Credentials

Prefer a dedicated Proxmox API token:

```bash
pveum user add terraform@pve
pveum user token add terraform@pve provider --privsep=0
```

Pass the token through a Terraform environment variable:

```bash
export TF_VAR_proxmox_api_token='root@pam!TERRAFORM_API_TOKEN=REPLACE_WITH_TOKEN_SECRET'
```

The API token is not enough for `proxmox_virtual_environment_file`. The provider uploads snippet files over SSH and does not read `~/.ssh/config`, so `terraform.tfvars` also sets:

```hcl
proxmox_ssh_username = "root"
proxmox_ssh_agent    = true
```

Before running `terraform apply`, make sure the key accepted by the Proxmox node is loaded in the local SSH agent:

```bash
ssh-add -L
ssh-add ~/.ssh/github_id
ssh root@pve-01.lan
```

## Default VMs

The configuration creates the Kubernetes nodes defined in `terraform.tfvars`:

| Name | Role | MAC address | CPU | RAM | OS disk | Data disk |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `k8s-control-01` | control-plane | `BC:24:11:00:01:10` | 3 | 2048 MB | 30 GB | none |
| `k8s-worker-01` | worker | `BC:24:11:00:01:20` | 3 | 4096 MB | 30 GB | 80 GB |

Sizes, data disks, and MAC addresses can be changed through the `vms` variable. Use the MAC addresses for DHCP reservations on the router/DHCP server so each VM keeps a stable IP while still using DHCP.
