# Deploy to Railway in 5 Minutes

## Step 1: Push Code to GitHub

If not already done:
```bash
git init
git add .
git commit -m "Initial commit: messaging balance sheet app"
git remote add origin https://github.com/YOUR_USERNAME/may.git
git branch -M main
git push -u origin main
```

## Step 2: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Click **"Login with GitHub"** and authorize
3. You're in!

## Step 3: Create a New Project

1. Click **"Create a new project"** (or **+ New Project**)
2. Select **"Deploy from GitHub repo"**
3. Search for `may` and click to connect
4. Railway will auto-detect the project type (Python)

## Step 4: Configure Environment Variables

Railway will show a dashboard. Click the project, then **"Variables"** tab:

Add these variables:
```
SECRET_KEY = (click generate button or paste a long random string)
ADMIN_PASS = your-secure-admin-password
FLASK_ENV = production
```

Optional (for email reset tokens):
```
SMTP_HOST = smtp.gmail.com
SMTP_PORT = 587
SMTP_USER = your-email@gmail.com
SMTP_PASS = your-app-password
SMTP_FROM = noreply@yourapp.com
```

## Step 5: Deploy

1. Click the **"Deploy"** button
2. Wait ~2-3 minutes for build to complete
3. You'll see a live URL like `https://may-production.up.railway.app`

## Step 6: Access Your App

Click the URL in the Railway dashboard. You're live!

Login with:
- Username: `admin`
- Password: (whatever you set as `ADMIN_PASS`)

---

## Auto-Deploy (Optional but Recommended)

Railway auto-deploys when you push to GitHub:
```bash
# Make changes, commit, and push
git add .
git commit -m "Update feature"
git push origin main

# Railway automatically deploys within seconds
# Check status in the Railway dashboard
```

---

## View Logs

In Railway dashboard:
1. Click your project
2. Click **"Logs"** tab
3. See real-time server output

Or use Railway CLI:
```bash
npm install -g @railway/cli
railway login
railway logs
```

---

## Troubleshooting

**Build failed?**
- Check logs in Railway dashboard → Logs tab
- Ensure `requirements.txt` exists and is correct
- Verify environment variables are set

**App crashes after deploy?**
- Check `ADMIN_PASS` and `SECRET_KEY` are set
- Look at logs: Railway → Logs tab
- Common issue: SQLite file path — Railway handles this automatically

**Can't log in?**
- Ensure `ADMIN_PASS` is set in Railway Variables
- Restart deployment: Railway → Redeploy

**Database missing?**
- Railway automatically creates `/app/data/data.db` on first run
- Data persists between deployments

---

## Update After Deployment

Every time you update the app:
```bash
git add .
git commit -m "Your changes"
git push origin main
```

Railway auto-deploys. Check the dashboard for status.

---

## Troubleshooting Database Issues

If the database gets corrupted:
1. Enable SSH in Railway (optional)
2. Or: Create a PostgreSQL addon instead:
   - In Railway dashboard, click **"Add service"**
   - Select **"PostgreSQL"**
   - Railway will set `DATABASE_URL` automatically
   - (Would require updating `app.py` to use PostgreSQL)

For now, SQLite is fine — it works perfectly for small teams.

---

## Next Steps

- Set up SMTP for password reset emails (see SMTP config above)
- Add a custom domain (Railway → Domain settings)
- Add collaborators (Railway → Settings → Members)
- Monitor usage (Railway → Usage tab)

**Your app is now live! 🚀**
