# Global Terraform configuration block.
terraform {
  # Minimum Terraform binary version required to run this project.
  required_version = ">= 1.6.0"

  # External providers required to create and manage resources.
  required_providers {
    # Proxmox provider: lets Terraform talk to the Proxmox VE API.
    proxmox = {
      # Official provider namespace in the Terraform registry.
      source = "bpg/proxmox"
      # Version constraint: use releases compatible with the 0.100.x series.
      version = "~> 0.100"
    }
  }
}

# Configuration for the Proxmox provider used by all resources.
provider "proxmox" {
  # Proxmox API endpoint, usually https://HOST:8006/.
  endpoint = var.proxmox_endpoint
  # API token used by Terraform. Can also be provided through environment variables.
  api_token = var.proxmox_api_token
  # Allow self-signed certificates in local lab environments.
  insecure = var.proxmox_insecure

  # SSH is used by the provider when it uploads files such as cloud-init snippets.
  ssh {
    # ~/.ssh/config is not read by the provider, so the login user must be explicit.
    username = var.proxmox_ssh_username
    # Use keys already loaded in ssh-agent, for example with ssh-add.
    agent = var.proxmox_ssh_agent
  }
}
