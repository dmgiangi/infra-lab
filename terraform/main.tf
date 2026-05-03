# Cloud image imported by Proxmox and used as the source for VM disks.
resource "proxmox_download_file" "ubuntu_cloud_image" {
  # Import content can be used by VM disk import_from.
  content_type = "import"
  # Datastore where Proxmox stores the imported cloud image.
  datastore_id = var.image_datastore_id
  # Proxmox node that downloads the image.
  node_name = var.proxmox_node_name
  # Public Ubuntu cloud image URL.
  url = var.base_image_url
  # File name used inside the Proxmox datastore.
  file_name = var.base_image_file_name
  # Allow replacing an existing image left behind after state removal or manual upload.
  overwrite_unmanaged = true
}

# Cloud-init user-data snippet applied to every VM.
resource "proxmox_virtual_environment_file" "cloud_init_user_data" {
  # Snippets are used by Proxmox as custom cloud-init user-data files.
  content_type = "snippets"
  # Datastore where the snippet is stored.
  datastore_id = var.snippets_datastore_id
  # Proxmox node that owns the snippet file.
  node_name = var.proxmox_node_name

  # Raw cloud-init content rendered from a local template.
  source_raw {
    data = templatefile("${path.module}/cloud-init/user-data.yaml.tftpl", {
      ssh_username        = var.ssh_username
      ssh_authorized_keys = var.ssh_authorized_keys
    })
    file_name = "k8s-user-data.yaml"
  }
}

# Definition of the Proxmox virtual machines.
resource "proxmox_virtual_environment_vm" "vm" {
  # Creates one VM for each item in the var.vms map.
  for_each = var.vms

  # Name of the Proxmox VM, equal to the map key.
  name = each.key
  # Proxmox node where the VM is created.
  node_name = var.proxmox_node_name
  # Optional explicit VM ID; null lets Proxmox allocate it.
  vm_id = each.value.vm_id
  # Human-readable context visible in the Proxmox UI.
  description = "Kubernetes ${each.value.role} node managed by Terraform."
  # Start VM after creation.
  started = true
  # Shut down or stop the VM before destroying it if the guest agent cannot respond.
  stop_on_destroy = true

  # qemu-guest-agent integration. The guest OS still needs the agent installed and running.
  agent {
    # Enabled by default so Terraform can read guest IP addresses once the agent works.
    enabled = var.qemu_guest_agent_enabled
  }

  # CPU sizing for the VM.
  cpu {
    # Number of CPU cores assigned to this VM.
    cores = each.value.vcpu
  }

  # Memory sizing for the VM.
  memory {
    # Dedicated RAM in megabytes.
    dedicated = each.value.memory_mb
  }

  # Main VM disk imported from the cloud image.
  disk {
    # Datastore where this VM disk is created.
    datastore_id = var.vm_datastore_id
    # Imported cloud image used as the initial disk content.
    import_from = proxmox_download_file.ubuntu_cloud_image.id
    # VirtIO disk interface for Linux guests.
    interface = "virtio0"
    # Enable a dedicated IO thread for better disk performance.
    iothread = true
    # Allow discard/TRIM support from the guest.
    discard = "on"
    # Disk size in gigabytes.
    size = each.value.disk_gb
  }

  # VM network interface attached to the Proxmox bridge.
  network_device {
    # Proxmox bridge, typically vmbr0.
    bridge = var.network_bridge
    # Stable MAC address used by DHCP reservations.
    mac_address = each.value.mac_address
    # VirtIO network model for Linux guests.
    model = "virtio"
  }

  # Native Proxmox cloud-init configuration.
  initialization {
    # Custom cloud-init user-data installs packages needed before Ansible runs.
    user_data_file_id = proxmox_virtual_environment_file.cloud_init_user_data.id

    # Use DHCP by default; static IPs can be added later per VM if needed.
    ip_config {
      ipv4 {
        # DHCP address assignment.
        address = "dhcp"
      }
    }
  }
}
