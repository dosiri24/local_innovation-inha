# Gunicorn 설정 파일
bind = "0.0.0.0:8080"
workers = 2
worker_class = "sync"
timeout = 60
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
