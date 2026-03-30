variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "cluster_name" {
  description = "Kubernetes cluster name"
  type        = string
  default     = "ai-scraping-cluster"
}

variable "domain" {
  description = "Application domain"
  type        = string
  default     = "api.aiscraping.com"
}

variable "replica_count" {
  description = "Number of replicas per service"
  type        = map(number)
  default = {
    api          = 3
    agent        = 5
    worker       = 10
    realtime     = 3
    billing      = 2
    notification = 2
    analytics    = 2
  }
}