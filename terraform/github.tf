# Lets GitHub Actions deploy without any long-lived credential.
#
# GitHub mints a short-lived OIDC token for a workflow run; GCP's STS exchanges
# it for an access token on the deployer service account, but only for tokens
# whose `repository` claim matches var.github_repository. Nothing secret is
# stored on either side.

resource "google_project_service" "deploy" {
  for_each = toset([
    "iap.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "oslogin.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# NOTE: `terraform destroy` only *soft*-deletes a pool. It sits in state
# DELETED for 30 days with its ID still reserved, so the next apply fails with
# "Error 409: Requested entity already exists". Recover with:
#
#   gcloud iam workload-identity-pools undelete github --location=global
#   terraform import google_iam_workload_identity_pool.github \
#     projects/<project>/locations/global/workloadIdentityPools/github
#
# (and the same undelete/import pair for the provider below, if it comes back
# DELETED rather than absent). The ID is kept stable on purpose: it appears in
# GCP_WIF_PROVIDER in the GitHub repository variables, and a generated suffix
# would silently invalidate that on every recreate.
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github"
  display_name              = "GitHub Actions"
  description               = "Federated identities for GitHub Actions workflows."

  depends_on = [google_project_service.deploy]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "GitHub Actions OIDC"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }

  # Without this condition, a workflow in *any* GitHub repository on the
  # internet could exchange its token for one of ours.
  attribute_condition = "assertion.repository == \"${var.github_repository}\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "deployer" {
  account_id   = "misho-deployer"
  display_name = "Misho GitHub Actions deployer"
}

# Only workflow runs in our repository may impersonate the deployer.
resource "google_service_account_iam_member" "deployer_wif" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repository}"
}

resource "google_project_iam_member" "deployer" {
  for_each = toset([
    # Reach port 22 through the IAP tunnel rather than over the public internet.
    "roles/iap.tunnelResourceAccessor",
    # `gcloud compute ssh` has to look the instance up before connecting.
    "roles/compute.viewer",
    # OS Login, with sudo. Sudo is required, not a convenience: an OS Login
    # service account logs in as sa_<numeric-uid>, which is not the `misho`
    # user, is not in the `docker` group, and cannot write to /opt/misho.
    "roles/compute.osAdminLogin",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.deployer.email}"
}
