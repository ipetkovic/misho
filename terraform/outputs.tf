output "external_ip" {
  description = "Ephemeral public IPv4 of the VM."
  value       = google_compute_instance.misho.network_interface[0].access_config[0].nat_ip
}

output "ssh_command" {
  value = "ssh ${var.ssh_user}@${google_compute_instance.misho.network_interface[0].access_config[0].nat_ip}"
}

output "deploy_command" {
  value = "./deploy.py ~/.ssh/id_ed25519 --host ${google_compute_instance.misho.network_interface[0].access_config[0].nat_ip} --username ${var.ssh_user}"
}
