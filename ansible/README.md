# Ansible

This directory contains Ansible automation for preparing the Ubuntu VMs before Kubernetes is initialized.

## Scope

Ansible is responsible for guest operating system configuration:

- verify SSH and sudo access;
- install base packages;
- disable swap;
- load Kubernetes kernel modules;
- configure required sysctl values;
- prepare the worker data disk for future Kubernetes persistent volumes.
- install `containerd`;
- configure `containerd` for systemd cgroups;
- install and hold `kubelet`, `kubeadm`, and `kubectl`.
- initialize the Kubernetes control plane with `kubeadm`;
- fetch a local kubeconfig for `kubectl`;
- install Flannel CNI;
- join worker nodes idempotently.

Terraform creates VMs and disks. Ansible formats and mounts the data disk. Kubernetes manifests will later create StorageClasses, applications, and MinIO resources inside the cluster.

Initial VM access, hostnames, and `qemu-guest-agent` are handled by Terraform Cloud-Init, not by Ansible.

## Files

| File | Purpose |
| --- | --- |
| `ansible.cfg` | Local Ansible defaults for this directory |
| `inventory/hosts.yaml` | Inventory for the current Proxmox VMs |
| `inventory/group_vars/all.yaml` | Shared variables for all nodes |
| `requirements.yaml` | External Ansible collections used by the playbooks |
| `playbooks/00-check-connectivity.yaml` | SSH and sudo connectivity check |
| `playbooks/10-prepare-nodes.yaml` | Base OS preparation for Kubernetes |
| `playbooks/20-prepare-storage.yaml` | Worker data disk formatting and mount |
| `playbooks/30-install-kubernetes-tools.yaml` | Container runtime and Kubernetes package installation |
| `playbooks/40-init-control-plane.yaml` | `kubeadm init`, kubeconfig fetch, and join command generation |
| `playbooks/45-install-flannel.yaml` | Flannel CNI installation |
| `playbooks/50-join-workers.yaml` | Worker node join |
| `playbooks/60-bootstrap-flux.yaml` | Flux bootstrap from GitHub |
| `playbooks/site.yaml` | Runs the current preparation flow |

## Prerequisites

- VMs created by Terraform.
- SSH access to each node as `dmgiangi`.
- Passwordless sudo for `dmgiangi`.
- The SSH private key referenced by the inventory exists locally.
- Worker data disk created by Terraform when `storage_data_disk_enabled` is `true`.

Install required collections:

```bash
cd ansible
ansible-galaxy collection install -r requirements.yaml
```

## Usage

Check connectivity:

```bash
cd ansible
ansible-playbook playbooks/00-check-connectivity.yaml
```

Prepare nodes and worker storage:

```bash
ansible-playbook playbooks/site.yaml
```

Use the fetched kubeconfig from the workstation:

```bash
export KUBECONFIG=/persistent/k8s-tests/ansible/artifacts/admin.conf
kubectl get nodes
kubectl get pods -A
```

## Storage

`k8s-worker-01` is configured to prepare:

```text
/dev/vdb -> /var/lib/k8s-storage
```

The playbook only creates a filesystem when the disk has no existing filesystem. It does not wipe an already formatted disk.

This mount point is intended for a future local Kubernetes provisioner such as `local-path-provisioner`.

## Kubernetes Packages

The playbooks install Kubernetes packages from the official `pkgs.k8s.io` repository for the minor version configured in `inventory/group_vars/all.yaml`:

```yaml
kubernetes_minor_version: "1.35"
```

The installed packages are put on hold:

```text
kubelet
kubeadm
kubectl
```

This keeps node upgrades explicit and avoids accidental version drift during normal system package upgrades.

`containerd` is installed from the Ubuntu package repositories and configured with `SystemdCgroup = true`, which matches kubelet on systemd-based Ubuntu nodes.

## Cluster Bootstrap

The control plane is initialized only when `/etc/kubernetes/admin.conf` does not exist.

The playbook stores generated cluster access files in `ansible/artifacts/`:

| File | Purpose |
| --- | --- |
| `admin.conf` | Local kubeconfig for `kubectl` |
| `kubeadm-join-command.sh` | Current worker join command |

The artifacts directory is ignored by Git because these files grant cluster access.

Flannel is installed as the initial CNI. The configured pod CIDR is:

```yaml
kubernetes_pod_cidr: 10.244.0.0/16
```

## Flux

Flux is bootstrapped from GitHub with:

```bash
GITHUB_TOKEN=REPLACE_WITH_TOKEN ansible-playbook playbooks/60-bootstrap-flux.yaml
```

The playbook uses:

```yaml
flux_github_owner: dmgiangi
flux_github_repository: infra-lab
flux_github_branch: master
flux_github_path: ./kubernetes/clusters/home
```

The GitHub token is required only on the workstation running the bootstrap. The default bootstrap mode uses a GitHub deploy key: Flux stores the generated private key in the cluster as the `flux-system` secret in the `flux-system` namespace, and GitHub stores the matching public key as a repository deploy key.
