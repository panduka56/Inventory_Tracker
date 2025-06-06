# Deployment Options for LCY London Inventory Tracker

## Option 1: Streamlit Cloud (Recommended - FREE)

1. **Go to**: https://streamlit.io/cloud
2. **Sign in** with your GitHub account
3. **Click** "New app"
4. **Select** your repository: `panduka56/Inventory_Tracker`
5. **Set** Main file path: `app.py`
6. **Click** "Deploy"

Your app will be live at: `https://[your-app-name].streamlit.app`

## Option 2: Heroku (Free tier available)

1. **Create** `Procfile`:
```
web: sh setup.sh && streamlit run app.py
```

2. **Create** `setup.sh`:
```bash
mkdir -p ~/.streamlit/

echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
```

3. **Deploy**:
```bash
heroku create your-app-name
git add .
git commit -m "Add Heroku deployment files"
git push heroku main
```

## Option 3: Railway.app (Simple & Fast)

1. **Go to**: https://railway.app
2. **Connect** your GitHub repo
3. **Add** environment variable: `PORT=8501`
4. **Deploy** automatically

## Option 4: Render.com (Free tier)

1. **Create** `render.yaml`:
```yaml
services:
  - type: web
    name: lcy-inventory
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "streamlit run app.py --server.port $PORT"
```

2. **Connect** GitHub repo at https://render.com

## Option 5: Google Cloud Run

1. **Create** `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8080
CMD streamlit run app.py --server.port=8080 --server.address=0.0.0.0
```

2. **Deploy**:
```bash
gcloud run deploy --source .
```

## Why Not Vercel?

Vercel is optimized for serverless functions and static sites. Streamlit apps need:
- Persistent WebSocket connections
- Stateful server sessions
- Continuous Python runtime

These requirements don't match Vercel's serverless architecture.

## Quick Start

For the fastest deployment, use **Streamlit Cloud**:
1. It's free
2. No configuration needed
3. Automatic updates when you push to GitHub
4. Built specifically for Streamlit apps