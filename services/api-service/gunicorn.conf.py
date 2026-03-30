# services/api-service/gunicorn.conf.py
# Gunicorn Configuration for Production

import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "ai-scraping-api"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"

# SSL (handled by reverse proxy)
forwarded_allow_ips = "*"
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

# Preload app for memory efficiency
preload_app = True

# Worker lifecycle
max_requests = 10000
max_requests_jitter = 1000
graceful_timeout = 30


def on_starting(server):
    """Called just before the master process is initialized."""
    pass


def on_reload(server):
    """Called when receiving SIGHUP."""
    pass


def when_ready(server):
    """Called just after the server is started."""
    pass


def worker_int(worker):
    """Called when a worker receives SIGINT or SIGQUIT."""
    pass


def on_exit(server):
    """Called just before exiting Gunicorn."""
    pass