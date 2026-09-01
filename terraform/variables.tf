variable "project_id" {
  description = "Existing GCP project ID with billing enabled."
  type        = string
}

variable "region" {
  description = "Region. Only these three qualify for the free-tier e2-micro."
  type        = string
  default     = "us-central1"

  validation {
    condition     = contains(["us-west1", "us-central1", "us-east1"], var.region)
    error_message = "Free-tier e2-micro is only free in us-west1, us-central1 or us-east1."
  }
}

variable "zone" {
  description = "Zone within var.region."
  type        = string
  default     = "us-central1-a"
}

variable "ssh_user" {
  description = "Linux user created on the VM and used by deploy.py."
  type        = string
  default     = "misho"
}

variable "ssh_public_key_path" {
  description = "Public key installed for ssh_user."
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "ssh_source_ranges" {
  description = "CIDRs allowed to reach port 22. Narrow this to your own IP."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# Free tier covers 30 GB-months of *standard* PD in total, so
# boot_disk_gb + data_disk_gb must stay at or below 30.
variable "boot_disk_gb" {
  description = "Boot disk size (pd-standard)."
  type        = number
  default     = 20
}

variable "data_disk_gb" {
  description = "Data disk holding the SQLite database (pd-standard)."
  type        = number
  default     = 10
}
