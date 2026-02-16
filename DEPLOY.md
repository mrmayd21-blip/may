# Deployment Guide

This guide covers deploying the Daily Messaging Balance Sheet app to various platforms.

## Prerequisites

- The app files: `app.py`, `requirements.txt`, `templates/`, `static/`
- A git repository (optional but recommended)
- Environment variables set for production

## Local Production Setup

1. Install dependencies in a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export FLASK_ENV=production
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export ADMIN_PASS="your-secure-password"
# Optional: SMTP settings
# export SMTP_HOST=smtp.example.com
# export SMTP_PORT=587
# export SMTP_USER=your-email@example.com
# export SMTP_PASS=your-smtp-password
# export SMTP_FROM=noreply@example.com
```

3. Run with a production WSGI server (e.g., Gunicorn):
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Docker Deployment

### Build a Docker Image

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py templates/ static/ ./

ENV FLASK_ENV=production
ENV SECRET_KEY=${SECRET_KEY}

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build the image:
```bash
docker build -t messaging-app:latest .
```

Run a container:
```bash
docker run -d \
  -p 5000:8000 \
  -e SECRET_KEY="your-secret-key" \
  -e ADMIN_PASS="your-password" \
  -v /path/to/data:/app/data \
  --name messaging-app \
  messaging-app:latest
```

(Replace `/path/to/data` with a host directory for persistent storage.)

## Cloud Platforms

### Railway.app

1. Connect your GitHub repo to Railway.
2. Add environment variables in Railway dashboard:
   - `SECRET_KEY`
   - `ADMIN_PASS`
   - `SMTP_*` (if using email)

3. Railway auto-detects `requirements.txt` and runs `gunicorn` by default.

**Cost**: Free tier available; pay-as-you-go after.

### Render

1. Create a new **Web Service** and connect your GitHub repo.
2. Set **Build Command**: `pip install -r requirements.txt`
3. Set **Start Command**: `gunicorn -w 4 -b 0.0.0.0:10000 app:app`
4. Add environment variables in the dashboard.

**Cost**: Free tier (limited); paid plans from $7/month.

### Heroku

1. Install the Heroku CLI and login:
```bash
heroku login
heroku create your-app-name
```

2. Create a `Procfile`:
```
web: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

3. Set environment variables:
```bash
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set ADMIN_PASS="your-password"
```

4. Deploy:
```bash
git push heroku main
```

**Cost**: Paid only (no free tier as of 2024).

### AWS Elastic Beanstalk

1. Install the EB CLI:
```bash
pip install awsebcli
```

2. Initialize and create an environment:
```bash
eb init -p python-3.11 messaging-app
eb create messaging-env
```

3. Deploy:
```bash
eb deploy
```

4. Set environment variables:
```bash
eb setenv SECRET_KEY="your-secret-key" ADMIN_PASS="your-password"
```

**Cost**: Free tier eligible; typically $5–15/month for small apps.

### Google Cloud Run

1. Create a `Dockerfile` (see Docker section above).
2. Build and push to Google Container Registry:
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/messaging-app
```

3. Deploy:
```bash
gcloud run deploy messaging-app \
  --image gcr.io/PROJECT_ID/messaging-app \
  --platform managed \
  --region us-central1 \
  --set-env-vars SECRET_KEY="your-key",ADMIN_PASS="your-pass"
```

**Cost**: Generous free tier (~2M requests/month); $0.40 per 1M additional requests.

## Persistence & Database

The app uses SQLite (`data.db`). For production:

- **Docker**: Mount a volume to `/app` to persist the database file.
- **Cloud platforms**: Use managed PostgreSQL or MySQL if you need multi-instance scaling.

To use PostgreSQL, update `app.py`:
```python
import psycopg2
# Replace sqlite3 connection with psycopg2 or use SQLAlchemy
```

## SSL/HTTPS

- **Railway, Render, Heroku, Cloud Run**: Automatically provide HTTPS via a CDN.
- **Elastic Beanstalk**: Enable HTTPS in the environment settings.
- **Self-hosted**: Use Nginx + Let's Encrypt or Caddy in front of Gunicorn.

## Monitoring & Logs

- **Railway**: View logs in the dashboard.
- **Render**: Real-time logs in the dashboard.
- **Heroku**: `heroku logs --tail`
- **Cloud Run**: Use Google Cloud Logging.
- **Elastic Beanstalk**: Use CloudWatch.

## Security Checklist

- [ ] Set a strong `SECRET_KEY` (use `secrets.token_urlsafe(32)`)
- [ ] Set a strong `ADMIN_PASS`
- [ ] Enable HTTPS/TLS
- [ ] Use environment variables (never hardcode secrets)
- [ ] Regularly update dependencies: `pip list --outdated`
- [ ] Add rate limiting for auth endpoints (consider Flask-Limiter)
- [ ] Back up the database regularly

## Quick Start: Docker + Compose

Create a `docker-compose.yml`:
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      FLASK_ENV: production
      SECRET_KEY: your-secret-key
      ADMIN_PASS: your-password
    volumes:
      - ./data:/app/data
```

Run:
```bash
docker-compose up -d
```

Access at `http://localhost:5000`.
