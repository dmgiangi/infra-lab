# Output with the list of created VM names.
output "vm_names" {
  # Description shown by Terraform when inspecting outputs.
  description = "Created VM names."
  # Extracts the keys from the Proxmox VM map.
  value = keys(proxmox_virtual_environment_vm.vm)
}

# Output with the Proxmox VM IDs.
output "vm_ids" {
  # Description shown by Terraform when inspecting outputs.
  description = "Created Proxmox VM IDs."
  # Builds a map of VM name -> Proxmox VM ID.
  value = {
    for name, vm in proxmox_virtual_environment_vm.vm : name => vm.vm_id
  }
}

# Output with the IPv4 addresses detected by qemu-guest-agent for each VM.
output "vm_ips" {
  # IPs are available only when qemu_guest_agent_enabled is true and the agent runs in the guest.
  description = "Detected VM IPv4 addresses from qemu-guest-agent."
  # Builds a map of VM name -> list of IP addresses.
  value = {
    # try avoids errors if a VM does not have detected addresses yet.
    for name, vm in proxmox_virtual_environment_vm.vm : name => try(flatten(vm.ipv4_addresses), [])
  }
}
