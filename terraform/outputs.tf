output "external_ip" {
  description = "Ephemeral public IPv4 of the VM. Egress only -- nothing inbound reaches it."
  value       = google_compute_instance.misho.network_interface[0].access_config[0].nat_ip
}

output "ssh_command" {
  description = "Shell into the VM. Goes through the IAP tunnel, so no public SSH port is needed."
  value       = "gcloud compute ssh ${google_compute_instance.misho.name} --project ${var.project_id} --zone ${var.zone} --tunnel-through-iap"
}

output "logs_command" {
  description = "Tail the container logs from Cloud Logging."
  value       = "gcloud logging read 'resource.type=gce_instance' --project ${var.project_id} --limit 50 --freshness 1h"
}

# --- Values to copy into the GitHub repository ------------------------------
# Settings -> Secrets and variables -> Actions -> Variables.
# These are identifiers, not secrets: WIF grants nothing without a signed
# OIDC token whose `repository` claim matches var.github_repository.

output "github_actions_variables" {
  description = "Repository *variables* the deploy workflow reads."
  value = {
    GCP_PROJECT_ID   = var.project_id
    GCP_ZONE         = var.zone
    GCP_INSTANCE     = google_compute_instance.misho.name
    GCP_WIF_PROVIDER = google_iam_workload_identity_pool_provider.github.name
    GCP_DEPLOY_SA    = google_service_account.deployer.email
  }
}
