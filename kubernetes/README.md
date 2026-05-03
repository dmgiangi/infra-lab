# Kubernetes

This directory contains Kubernetes resources intended to be reconciled by Flux.

## Layout

| Path | Purpose |
| --- | --- |
| `clusters/home/` | Entry point reconciled by Flux for the home cluster |
| `infrastructure/` | Cluster-wide platform resources |
| `apps/` | Application resources |

Flux is configured to reconcile:

```text
./kubernetes/clusters/home
```

## Bootstrap

Flux is bootstrapped by Ansible:

```bash
cd ansible
GITHUB_TOKEN=REPLACE_WITH_TOKEN ansible-playbook playbooks/60-bootstrap-flux.yaml
```

The bootstrap uses GitHub deploy key authentication. The GitHub token is used only by the Flux CLI during bootstrap to update the repository and configure the deploy key. The cluster stores the generated SSH private key in the `flux-system` namespace.

## Apply Model

After Flux is bootstrapped, permanent Kubernetes changes should be made through Git commits under this directory instead of direct `kubectl apply`.

## Storage

The home cluster uses `local-path-provisioner` with this StorageClass:

```text
local-path
```

The provisioner stores dynamically created volumes on:

```text
k8s-worker-01:/var/lib/k8s-storage
```

The control-plane node is explicitly configured with no provisioning paths, so PVC-backed workloads should run on worker nodes.
