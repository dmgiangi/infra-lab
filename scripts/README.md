# Scripts

Local helper scripts for configuring the workstation used to manage the lab.

## Hosts And SSH

`configure_hosts_ssh.py` adds managed entries to `/etc/hosts` and `~/.ssh/config` so servers and VMs can be reached through stable names.

Recommended flow:

```bash
python3 configure_hosts_ssh.py
sudo python3 configure_hosts_ssh.py
```

The script always starts a wizard and proposes `hosts.yaml` as the default configuration.

The script:

- updates only marker-delimited blocks;
- creates a backup before changing files;
- uses the real invoking user even when executed with `sudo`;
- does not modify anything with `--dry-run`.

## Configuration

`hosts.yaml` contains the real lab configuration:

- `defaults.user`: default SSH user for the VMs;
- `defaults.identity_file`: SSH private key used for the hosts;
- `hosts[].name`: name used in `/etc/hosts` and `~/.ssh/config`;
- `hosts[].ip`: IP associated with the name;
- `hosts[].aliases`: additional aliases written to `/etc/hosts`;
- `hosts[].user`: SSH user override for a specific host.

Configured IPs must be stable addresses. If VMs are created with DHCP, update `hosts.yaml` after reading the real IPs from Terraform outputs or the DHCP server. Alternatively, reserve those IPs on the router/DHCP server or configure static IPs upstream.

## Non-Interactive Mode

For automation, skip the wizard with `--non-interactive`:

```bash
python3 configure_hosts_ssh.py --config hosts.yaml --dry-run --non-interactive
sudo python3 configure_hosts_ssh.py --config hosts.yaml --yes --non-interactive
```

## Partial Updates

To update only `~/.ssh/config`:

```bash
python3 configure_hosts_ssh.py --config hosts.yaml --skip-hosts --non-interactive
```

To update only `/etc/hosts`:

```bash
sudo python3 configure_hosts_ssh.py --config hosts.yaml --skip-ssh --yes --non-interactive
```
