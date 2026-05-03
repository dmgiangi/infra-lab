# Proxmox API endpoint used by the provider.
variable "proxmox_endpoint" {
  # Text shown by Terraform in documentation and variable messages.
  description = "Proxmox VE API endpoint."
  # This variable accepts a single string.
  type = string
}

# API token used to authenticate Terraform against Proxmox.
variable "proxmox_api_token" {
  # Prefer a Proxmox API token over username/password for repeatable automation.
  description = "Proxmox API token in the form user@realm!tokenid=token-secret."
  type        = string
  # Keep credentials outside version control, for example in terraform.tfvars or env vars.
  sensitive = true
}

# Whether to skip TLS certificate verification for the Proxmox API.
variable "proxmox_insecure" {
  # Useful for the default self-signed certificate installed by Proxmox.
  description = "Skip TLS verification for the Proxmox API endpoint."
  type        = bool
}

# SSH username used by the provider when uploading files to the Proxmox node.
variable "proxmox_ssh_username" {
  # This is normally root on Proxmox because snippet uploads write into Proxmox storage paths.
  description = "SSH username used by the provider for Proxmox node file uploads."
  type        = string
}

# Whether the provider should authenticate to Proxmox SSH through ssh-agent.
variable "proxmox_ssh_agent" {
  # Keep this true when the private key is loaded with ssh-add.
  description = "Use ssh-agent for provider SSH authentication to the Proxmox node."
  type        = bool
}

# Proxmox node where the VMs are created.
variable "proxmox_node_name" {
  # This must match the node name shown in the Proxmox UI, not necessarily the FQDN.
  description = "Proxmox node name where VMs will be created."
  type        = string
}

# Datastore used to store downloaded/imported images.
variable "image_datastore_id" {
  # The cloud image is stored as import content on this datastore.
  description = "Proxmox datastore used for imported cloud images."
  type        = string
}

# Datastore used for VM disks.
variable "vm_datastore_id" {
  # Common defaults are local-lvm, local, zfs pools, or other configured datastores.
  description = "Proxmox datastore used for VM disks."
  type        = string
}

# Datastore used for Proxmox cloud-init snippets.
variable "snippets_datastore_id" {
  # The datastore must support the "Snippets" content type in Proxmox.
  description = "Proxmox datastore used for cloud-init snippet files."
  type        = string
}

# Proxmox Linux bridge attached to the VM network devices.
variable "network_bridge" {
  # vmbr0 is the default bridge created by many Proxmox installations.
  description = "Proxmox network bridge attached to the VMs."
  type        = string
}

# URL of the cloud image used as the base for VM disks.
variable "base_image_url" {
  # Terraform asks Proxmox to download and import this image.
  description = "Cloud image imported into Proxmox and used to create VM disks."
  # The image URL is a string.
  type = string
}

# File name assigned to the imported cloud image in Proxmox.
variable "base_image_file_name" {
  # Proxmox import content expects a qcow2-style filename for this image.
  description = "File name used by Proxmox for the imported cloud image."
  type        = string
}

# Name of the Linux user created by cloud-init on each VM.
variable "ssh_username" {
  # This user is configured with passwordless sudo.
  description = "Default user created through cloud-init."
  # The username is a string.
  type = string
}

# SSH public keys allowed to access the user created by cloud-init.
variable "ssh_authorized_keys" {
  # Add one or more public keys here, never private keys.
  description = "SSH public keys allowed for the default user."
  # List of strings, one per public key.
  type = list(string)
}

# Whether Proxmox should enable qemu-guest-agent integration for the VMs.
variable "qemu_guest_agent_enabled" {
  # IP outputs depend on a working qemu-guest-agent inside each VM.
  description = "Enable qemu-guest-agent integration in Proxmox for the VMs."
  type        = bool
}

# Map of virtual machines to create.
variable "vms" {
  # Each map entry represents a VM, indexed by hostname.
  description = "Virtual machines to create."
  # Required schema for each VM: logical role, CPU, RAM, OS disk, and optional data disk size.
  type = map(object({
    # Logical node role, useful for documentation and future outputs/inventory.
    role = string
    # Optional explicit Proxmox VM ID. Null lets Proxmox allocate one.
    vm_id = optional(number)
    # Static MAC address assigned to the VM network interface for DHCP reservations.
    mac_address = string
    # Number of vCPUs assigned to the VM.
    vcpu = number
    # Amount of RAM in megabytes.
    memory_mb = number
    # Main disk size in gigabytes.
    disk_gb = number
    # Optional data disk size in gigabytes. Null or omitted means no data disk.
    data_disk_gb = optional(number)
  }))
}
