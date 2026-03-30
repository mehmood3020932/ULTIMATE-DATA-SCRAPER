output "namespace" {
  description = "Deployed namespace"
  value       = kubernetes_namespace.ai_scraping.metadata[0].name
}

output "services" {
  description = "Deployed services"
  value = [
    "api-service",
    "agent-service",
    "worker-service",
    "realtime-service",
    "billing-service",
    "notification-service",
    "analytics-service",
  ]
}