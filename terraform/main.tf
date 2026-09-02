terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

resource "google_project_service" "compute" {
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

# --- Network -----------------------------------------------------------------
# The app makes only outbound connections (Telegram long polling, OpenAI,
# sportbooking.info). Nothing listens, so SSH is the only ingress -- and it
# arrives through the IAP tunnel rather than from the open internet. The
# /healthz port is deliberately not exposed: the Docker healthcheck and the
# rollout script both probe it from inside the container.

resource "google_compute_network" "misho" {
  name                    = "misho-net"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.compute]
}

resource "google_compute_subnetwork" "misho" {
  name          = "misho-subnet"
  ip_cidr_range = "10.10.0.0/24"
  region        = var.region
  network       = google_compute_network.misho.id
}

# IAP terminates the tunnel and forwards from this fixed Google-owned range.
# This is the only path in by default.
resource "google_compute_firewall" "ssh_iap" {
  name          = "misho-allow-ssh-iap"
  network       = google_compute_network.misho.name
  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["misho-ssh"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

# Direct SSH from the internet, off unless ssh_source_ranges is non-empty.
# Kept only as a break-glass route for the case where IAP or OS Login is
# misconfigured and the tunnel will not open.
resource "google_compute_firewall" "ssh_direct" {
  count = length(var.ssh_source_ranges) > 0 ? 1 : 0

  name          = "misho-allow-ssh"
  network       = google_compute_network.misho.name
  source_ranges = var.ssh_source_ranges
  target_tags   = ["misho-ssh"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

# --- Service account ---------------------------------------------------------

resource "google_service_account" "misho" {
  account_id   = "misho-vm"
  display_name = "Misho VM"
}

resource "google_project_iam_member" "logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.misho.email}"
}

# --- Disks -------------------------------------------------------------------
# Managed as its own resource so that replacing the instance (machine type
# change, image bump, startup-script edit) never touches the database.

resource "google_compute_disk" "data" {
  name = "misho-data"
  type = "pd-standard"
  size = var.data_disk_gb
  zone = var.zone

  depends_on = [google_project_service.compute]
}

data "google_compute_image" "debian" {
  family  = "debian-12"
  project = "debian-cloud"

  depends_on = [google_project_service.compute]
}

# --- Instance ----------------------------------------------------------------

resource "google_compute_instance" "misho" {
  name         = "misho"
  machine_type = "e2-micro"
  zone         = var.zone
  tags         = ["misho-ssh"]

  boot_disk {
    initialize_params {
      image = data.google_compute_image.debian.self_link
      size  = var.boot_disk_gb
      type  = "pd-standard"
    }
  }

  attached_disk {
    source      = google_compute_disk.data.id
    device_name = "misho-data"
    mode        = "READ_WRITE"
  }

  network_interface {
    subnetwork = google_compute_subnetwork.misho.id

    # Ephemeral external IPv4. Billed at ~$0.005/hr; the free tier does not
    # cover it. Required for egress -- the alternative, Cloud NAT, is ~$32/mo.
    access_config {}
  }

  metadata = {
    # Required for service-account SSH, which is how GitHub Actions gets in.
    enable-oslogin = "TRUE"

    # Inert while OS Login is enabled -- it takes precedence over per-instance
    # keys. Retained as the break-glass route: set enable-oslogin to "FALSE"
    # and this key works again over google_compute_firewall.ssh_direct.
    ssh-keys = "${var.ssh_user}:${trimspace(file(pathexpand(var.ssh_public_key_path)))}"
  }

  metadata_startup_script = templatefile("${path.module}/startup.sh", {
    deploy_user = var.ssh_user
  })

  service_account {
    email  = google_service_account.misho.email
    scopes = ["https://www.googleapis.com/auth/logging.write"]
  }

  allow_stopping_for_update = true
}
