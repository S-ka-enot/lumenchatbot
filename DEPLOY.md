# Deploy to Coolify with GitHub

This guide explains how to deploy the LumenPay Bot project to a server using Coolify, which pulls directly from GitHub.

## Prerequisites

- **Server with Coolify installed** (see [Coolify docs](https://coolify.io) for installation)
- **GitHub repository** where this project is hosted
- **GitHub Personal Access Token** (for Coolify to access the repo)
- **Domain name** (optional but recommended for production)

## Step 1: Prepare GitHub Repository

1. **Push the code to GitHub:**
   ```bash
   git init
   git remote add origin https://github.com/your-username/lumenchatbot.git
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git push -u origin main
   ```

2. **Generate GitHub Personal Access Token:**
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: `repo`, `read:packages`
   - Save the token (you'll need it in Coolify)

## Step 2: Set Up Coolify

### 2.1 Create a New Project in Coolify

1. Log in to your Coolify instance (`https://your-coolify-domain`)
2. Click **New Project** → Give it a name (e.g., "LumenPay")
3. Click **New Resource** → **Docker Container** or **Docker Compose** (depending on your Coolify plan)

### 2.2 Connect GitHub Repository

1. In Coolify project settings, add your GitHub integration:
   - **Git Provider:** GitHub
   - **Personal Access Token:** Paste the token from Step 1
   - **Repository:** `your-username/lumenchatbot`
   - **Branch:** `main`

### 2.3 Create Services

You'll create three services: **backend**, **bot**, and **frontend**. You can do this either as:
- **Three separate services** (recommended for independent scaling)
- **One Docker Compose** service (simpler setup, less flexible)

#### Option A: Three Separate Services (Recommended)

**Service 1: Backend**

1. Click **New Service** → **Docker** → Configure:
   - **Service Name:** `lumenpay-backend`
   - **Build Context:** `./` (repository root)
   - **Dockerfile Path:** `backend/Dockerfile`
   - **Port:** `8001` (exposed as `8001:8000`)
   - **Restart Policy:** Always
   - **Health Check:** HTTP GET `http://localhost:8000/api/v1/health`

2. **Environment Variables:**
   - Click **Add Environment Variable** and add (from `.env.example`):
     ```
     ENVIRONMENT=production
     LOG_LEVEL=INFO
     TIMEZONE=Europe/Moscow
     
     # Generate these securely:
     SECRET_KEY=<generate-random-key>
     ADMIN_SEED_PASSWORD=<secure-password>
     BOT_TOKEN_ENCRYPTION_KEY=<generate-random-key>
     
     # Set to your domain:
     BACKEND_CORS_ORIGINS=["https://yourdomain.com"]
     
     # Database (default SQLite in container)
     DATABASE_URL=sqlite+aiosqlite:///./data/lumenpay.db
     SYNC_DATABASE_URL=sqlite:///./data/lumenpay.db
     
     # Redis
     REDIS_URL=redis://lumenpay-redis:6379/0
     
     # Telegram Bot
     TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
     
     # YooKassa (payment processor)
     YOOKASSA_SHOP_ID=<your-shop-id>
     YOOKASSA_API_KEY=<your-api-key>
     
     # Other services
     BACKEND_BASE_URL=http://localhost:8000
     BACKEND_API_PREFIX=/api/v1
     ```

3. Click **Deploy**

**Service 2: Telegram Bot**

1. Click **New Service** → **Docker** → Configure:
   - **Service Name:** `lumenpay-bot`
   - **Build Context:** `./` (repository root)
   - **Dockerfile Path:** `bot/Dockerfile`
   - **Restart Policy:** Always

2. **Environment Variables:**
   ```
   ENVIRONMENT=production
   BACKEND_BASE_URL=http://lumenpay-backend:8000
   BACKEND_API_PREFIX=/api/v1
   TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
   BOT_TOKEN_ENCRYPTION_KEY=<same-as-backend>
   ```

3. Click **Deploy**

**Service 3: Frontend**

1. Click **New Service** → **Docker** → Configure:
   - **Service Name:** `lumenpay-frontend`
   - **Build Context:** `frontend` (important!)
   - **Dockerfile Path:** `Dockerfile` (relative to build context)
   - **Port:** `3000` (exposed as `3000:80`)
   - **Restart Policy:** Always
   - **Health Check:** HTTP GET `http://localhost/healthz`

2. **No environment variables needed** (frontend config is baked into the build)

3. Click **Deploy**

**Service 4: Redis (Cache)**

1. Click **New Service** → **Docker** → Configure:
   - **Service Name:** `lumenpay-redis`
   - **Image:** `redis:7-alpine`
   - **Port:** `6380` (exposed as `6380:6379`)
   - **Restart Policy:** Always
   - **Volumes:** Create persistent volume `/data`

2. Click **Deploy**

#### Option B: Docker Compose (Single Service)

If you prefer a single Compose-based deployment:

1. Click **New Service** → **Docker Compose**
2. Paste the content of `docker-compose.yml`
3. Update environment variables in Coolify's UI (or in the compose file itself)
4. Click **Deploy**

## Step 3: Configure Reverse Proxy / SSL

Coolify typically exposes services via an internal network. To access them from the internet:

### Option 1: Coolify's Built-in Proxy

1. In Coolify, go to your **Frontend service** → **Settings**
2. Under **Expose via proxy**, enable and set:
   - **Domain:** `yourdomain.com` (for frontend)
   - **Path:** `/` 
   - **Port:** `80`
   - **SSL:** Auto (Let's Encrypt)

3. For backend API, add another proxy route:
   - **Domain:** `yourdomain.com`
   - **Path:** `/api`
   - **Port:** `8000`
   - **SSL:** Auto

### Option 2: External Reverse Proxy (Nginx/Traefik)

If you're using an external proxy on the same server:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Frontend
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Step 4: Generate Secure Secrets

Before deployment, generate secure values:

```bash
# Generate random SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate random BOT_TOKEN_ENCRYPTION_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate admin password (or use a secure passphrase)
python3 -c "import secrets; print(secrets.token_urlsafe(16))"
```

Add these to Coolify's environment variables for the backend service.

## Step 5: Database Setup & Migrations

The backend runs migrations automatically on startup (see `backend/docker-entrypoint.sh`).

**First time setup:**

1. Backend container will create SQLite database in `./data/lumenpay.db`
2. Migrations run automatically
3. Default admin account created with `ADMIN_SEED_USERNAME` and `ADMIN_SEED_PASSWORD`

**To check logs:**

In Coolify, go to your **backend service** → **Logs** and verify:
- Migrations applied successfully
- "Created default admin account" message

## Step 6: Verify Deployment

### Check Backend Health

```bash
curl https://yourdomain.com/api/v1/health
# Expected response: {"status":"ok"}
```

### Check Frontend

Open `https://yourdomain.com` in your browser. You should see the React app.

### Monitor Logs

In Coolify UI:
1. Go to each service
2. Click **Logs** tab
3. Check for errors or warnings

## Troubleshooting

### Backend won't start
- Check `TELEGRAM_BOT_TOKEN` is set correctly
- Check `SECRET_KEY` is set
- Review logs for database connection errors

### Frontend not loading
- Check frontend service logs
- Verify `BACKEND_CORS_ORIGINS` matches your domain in backend
- Clear browser cache

### Migrations failed
- SSH into the container: `docker exec -it lumenpay-backend sh`
- Run migrations manually: `alembic -c backend/alembic.ini upgrade head`

### Redis connection error
- Ensure Redis service is running and port `6379` is accessible between containers
- Check Redis service logs

## Local Development

For local development, run:

```bash
# Backend
poetry install
poetry run uvicorn backend.app.main:app --reload

# Frontend (in separate terminal)
cd frontend
npm ci
npm run dev

# Or use Docker Compose
docker compose up --build
```

## Scaling & Performance

- **Backend:** Can be replicated for load balancing
- **Bot:** Only one instance recommended (Telegram polling)
- **Frontend:** Stateless, can replicate behind load balancer
- **Redis:** Consider external Redis instance for multi-node setups

## Backups

By default, SQLite database is in the container's ephemeral storage.

**For persistent data:**

In Coolify, add a volume to the backend service:
- **Mount Path:** `/app/data`
- **Volume Name:** `lumenpay-data` (creates persistent volume)

This ensures data survives container restarts.

## Security Notes

- ✅ Never commit `.env` files with real secrets
- ✅ Use Coolify's environment variable UI for production secrets
- ✅ Enable SSL/HTTPS (Coolify can auto-provision Let's Encrypt)
- ✅ Set strong `SECRET_KEY` and `ADMIN_SEED_PASSWORD`
- ✅ Restrict Telegram bot token to specific IP ranges if possible
- ✅ Regularly update base images (Python 3.10, Node 20, Nginx, Redis)

## Next Steps

1. Configure custom domain and SSL
2. Set up automated backups
3. Configure monitoring & alerting
4. Set up CI/CD with GitHub Actions (see `.github/workflows/ci.yml`)
5. Configure log aggregation if needed
