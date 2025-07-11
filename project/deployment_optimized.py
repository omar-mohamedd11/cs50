#!/usr/bin/env python3
"""
Production deployment configuration and utilities for Budget Tracker
"""

import os
import gzip
import shutil
from pathlib import Path

def setup_production_environment():
    """Set up production environment variables"""
    production_vars = {
        'FLASK_ENV': 'production',
        'CACHE_TYPE': 'simple',
        'SECRET_KEY': os.urandom(24).hex(),  # Generate random secret key
        'DATABASE_URL': 'sqlite:///budget_tracker_prod.db',
        'HOST': '0.0.0.0',
        'PORT': '8000'
    }
    
    # Write to .env file
    with open('.env.production', 'w') as f:
        for key, value in production_vars.items():
            f.write(f'{key}={value}\n')
    
    print("Production environment file created: .env.production")

def compress_static_files():
    """Compress static files for better performance"""
    static_dir = Path('static')
    
    for file_path in static_dir.rglob('*'):
        if file_path.is_file() and file_path.suffix in ['.js', '.css']:
            # Create gzipped version
            with open(file_path, 'rb') as f_in:
                with gzip.open(f'{file_path}.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            print(f"Compressed: {file_path}")

def create_gunicorn_config():
    """Create Gunicorn configuration for production"""
    config = """
# Gunicorn configuration file
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', 8000)}"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'budget_tracker'

# Server mechanics
preload_app = True
daemon = False
pidfile = '/tmp/gunicorn_budget_tracker.pid'
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment if using HTTPS)
# keyfile = 'path/to/keyfile'
# certfile = 'path/to/certfile'
"""
    
    with open('gunicorn.conf.py', 'w') as f:
        f.write(config)
    
    print("Gunicorn configuration created: gunicorn.conf.py")

def create_nginx_config():
    """Create Nginx configuration for reverse proxy"""
    config = """
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
    
    # Static files with caching
    location /static/ {
        alias /path/to/your/app/static/;  # Replace with actual path
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # Try to serve pre-compressed files
        location ~* \.(js|css)$ {
            gzip_static on;
        }
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
"""
    
    with open('nginx_budget_tracker.conf', 'w') as f:
        f.write(config)
    
    print("Nginx configuration created: nginx_budget_tracker.conf")

def create_systemd_service():
    """Create systemd service file for deployment"""
    service = """
[Unit]
Description=Budget Tracker Web Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
RuntimeDirectory=budget_tracker
WorkingDirectory=/path/to/your/app  # Replace with actual path
Environment=PATH=/path/to/your/venv/bin  # Replace with actual venv path
EnvironmentFile=/path/to/your/app/.env.production  # Replace with actual path
ExecStart=/path/to/your/venv/bin/gunicorn --config gunicorn.conf.py app_optimized:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    
    with open('budget_tracker.service', 'w') as f:
        f.write(service)
    
    print("Systemd service file created: budget_tracker.service")

def create_dockerfile():
    """Create Dockerfile for containerized deployment"""
    dockerfile = """
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app_optimized:app"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile)
    
    print("Dockerfile created: Dockerfile")

def create_docker_compose():
    """Create docker-compose.yml for easy deployment"""
    compose = """
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=sqlite:///budget_tracker.db
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx_budget_tracker.conf:/etc/nginx/conf.d/default.conf
      - ./static:/var/www/static:ro
    depends_on:
      - web
    restart: unless-stopped

volumes:
  data:
  logs:
"""
    
    with open('docker-compose.yml', 'w') as f:
        f.write(compose)
    
    print("Docker Compose file created: docker-compose.yml")

def main():
    """Run all optimization setup tasks"""
    print("Setting up production optimizations...")
    
    setup_production_environment()
    compress_static_files()
    create_gunicorn_config()
    create_nginx_config()
    create_systemd_service()
    create_dockerfile()
    create_docker_compose()
    
    print("\n✅ Production optimization setup complete!")
    print("\nNext steps:")
    print("1. Review and customize the generated configuration files")
    print("2. Update paths in nginx and systemd configurations")
    print("3. Install dependencies: pip install -r requirements.txt")
    print("4. Run with: gunicorn --config gunicorn.conf.py app_optimized:app")
    print("5. Or use Docker: docker-compose up -d")

if __name__ == '__main__':
    main()