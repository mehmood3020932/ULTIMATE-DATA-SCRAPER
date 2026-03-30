# shared/kafka/topics.py
# Kafka topic definitions

class KafkaTopics:
    # Job lifecycle
    JOBS = "scraping.jobs"
    JOB_COMMANDS = "scraping.commands"
    JOB_UPDATES = "scraping.updates"
    JOB_EVENTS = "scraping.events"
    
    # Agent communication
    AGENT_TASKS = "agent.tasks"
    AGENT_RESULTS = "agent.results"
    
    # Notifications
    NOTIFICATIONS = "notifications"
    EMAIL_QUEUE = "email.queue"
    
    # Analytics
    ANALYTICS_EVENTS = "analytics.events"
    
    # Billing
    BILLING_EVENTS = "billing.events"