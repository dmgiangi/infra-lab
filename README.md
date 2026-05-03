# k8s-tests

Repository for preparing a local Kubernetes environment made of virtual machines, Ansible provisioning, and Kubernetes manifests.

## Structure

| Area | Purpose | README |
| --- | --- | --- |
| `images/` | Installation image preparation for the local server | [images/README.md](images/README.md) |
| `terraform/` | VM creation on the local server | [terraform/README.md](terraform/README.md) |
| `scripts/` | Local helper scripts for workstation configuration | [scripts/README.md](scripts/README.md) |
| `ansible/` | Node provisioning and system component installation | To be added |
| `kubernetes/` | Kubernetes application resources and manifests | To be added |

## Expected Flow

1. Prepare any required server installation images.
2. Create the VMs with Terraform.
3. Configure the operating system, packages, and cluster with Ansible.
4. Apply the Kubernetes resources.

Leaf README files document prerequisites, variables, and commands for each area.
