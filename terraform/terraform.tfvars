# Proxmox API endpoint.
proxmox_endpoint = "https://pve-01.lan:8006/"
# Set true for Proxmox self-signed certificates in a local lab.
proxmox_insecure = true
# SSH is required for provider-managed file uploads, including cloud-init snippets.
proxmox_ssh_username = "root"
proxmox_ssh_agent    = true

# Proxmox node and resources.
proxmox_node_name     = "pve-01"
image_datastore_id    = "local"
vm_datastore_id       = "local-lvm"
snippets_datastore_id = "local"
network_bridge        = "vmbr0"

# Ubuntu cloud image imported into Proxmox.
base_image_url       = "https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img"
base_image_file_name = "ubuntu-noble-server-cloudimg-amd64.qcow2"

# User created by cloud-init on each VM.
ssh_username = "dmgiangi"
# List of SSH public keys authorized for the user.
ssh_authorized_keys = [
  "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPMaHDb1rtvuXbbGI5YosJr4nGi+EAM2GWIPpf/GXiff dem.gianluigi@gmail.com",
]

# Keep qemu-guest-agent disabled until it is installed inside the guest OS.
qemu_guest_agent_enabled = true

# Definition of the VMs to create.
vms = {
  k8s-control-01 = {
    role         = "control-plane"
    vm_id        = 110
    mac_address  = "BC:24:11:00:01:10"
    vcpu         = 3
    memory_mb    = 2048
    disk_gb      = 15
    data_disk_gb = null
  }
  k8s-worker-01 = {
    role         = "worker"
    vm_id        = 120
    mac_address  = "BC:24:11:00:01:20"
    vcpu         = 3
    memory_mb    = 4096
    disk_gb      = 15
    data_disk_gb = 80
  }
}
