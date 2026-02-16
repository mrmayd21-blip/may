# Deployment Quick Start

## TL;DR - Deploy Locally with Docker

```bash
# 1. Copy example env file
cp .env.example .env

# 2. Update .env with your settings (especially SECRET_KEY and ADMIN_PASS)
nano .env

# 3. Run the deployment script
./deploy.sh

# 4. Access the app
open http://localhost:5000
```

Or manually with Docker Compose:
```bash
docker-compose up -d
```

---

## Platform-Specific Quick Commands

### Railway.app (Recommended for Beginners)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link repo
railway login
railway init

# Deploy
railway up
```

### Render
```bash
# Connect GitHub repo at https://dashboard.render.com
# Add environment variables in dashboard
# Auto-deploys on git push
```

### Heroku
```bash
# Install CLI: brew install heroku
heroku login
heroku create your-app-name
heroku config:set SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
heroku config:set ADMIN_PASS="your-password"
git push heroku main
```

### AWS Elastic Beanstalk
```bash
pip install awsebcli
eb init -p python-3.11 messaging-app
eb create messaging-env
eb deploy
```

### Google Cloud Run
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/messaging-app
gcloud run deploy messaging-app \
  --image gcr.io/PROJECT_ID/messaging-app \
  --platform managed \
  --set-env-vars SECRET_KEY="your-key",ADMIN_PASS="your-pass"
```

---

## Docker Commands

Build image:
```bash
docker build -t messaging-app .
```

Run container:
```bash
docker run -d \
  -p 5000:5000 \
  -e SECRET_KEY="your-secret" \
  -e ADMIN_PASS="your-pass" \
  -v $(pwd)/data:/app/data \
  messaging-app
```

With Docker Compose:
```bash
docker-compose up -d       # Start
docker-compose logs -f     # View logs
docker-compose down        # Stop
docker-compose restart     # Restart
```

---

## Environment Variables

Essential:
- `SECRET_KEY`: Generated with `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- `ADMIN_PASS`: Your admin password
- `FLASK_ENV`: Set to `production` for production deployments

Optional (for email):
- `SMTP_HOST`: e.g., smtp.gmail.com
- `SMTP_PORT`: e.g., 587
- `SMTP_USER`: Your email address
- `SMTP_PASS`: Your app password (not your main password!)
- `SMTP_FROM`: Email to send from

---

## Production Checklist

- [ ] Set strong `SECRET_KEY` (32+ char random string)
- [ ] Set strong `ADMIN_PASS` (12+ chars, mix of letters, numbers, symbols)
- [ ] Enable HTTPS (cloud platforms do this automatically)
- [ ] Configure SMTP if you want password reset emails
- [ ] Back up the database regularly
- [ ] Monitor logs and set up alerting
- [ ] Use a reverse proxy (Nginx) for increased security
- [ ] Enable rate limiting on login endpoints

---

## Troubleshooting

**Port already in use?**
```bash
docker ps
docker stop CONTAINER_ID
```

**Database issues?**
```bash
# Backup and reset database
cp data/data.db data/data.db.bak
rm data/data.db
# App will recreate it on restart
docker-compose restart app
```

**Can't log in?**
- Check ADMIN_PASS in .env matches what you set
- Restart the container: `docker-compose restart app`

**SMTP not sending emails?**
- Verify env vars are set: `docker-compose config`
- Check logs: `docker-compose logs app | grep -i smtp`
- Test SMTP credentials separately

---

## Support & Docs

- Full guide: See `DEPLOY.md`
- Repository: https://github.com/mrmayd21-blip/may
- Issues: Create a GitHub issue
