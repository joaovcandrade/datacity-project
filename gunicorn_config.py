import multiprocessing
# Server socket
bind = "0.0.0.0:8000"
backlog = 2048
# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
user = "datacity"
group = "datacity"
# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50
# Logging
errorlog = "/var/www/datacity/logs/gunicorn_error.log"
accesslog = "/var/www/datacity/logs/gunicorn_access.log"
loglevel = "info"
# Process naming
proc_name = "datacity_gunicorn"
# Server mechanics
daemon = False
pidfile = "/var/www/datacity/datacity_project/gunicorn.pid"
tmp_upload_dir = None
