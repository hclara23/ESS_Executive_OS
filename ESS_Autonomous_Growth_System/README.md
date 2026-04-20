# ESS - Autonomous Growth System

A locally hosted bilingual SEO automation platform that continuously discovers search demand, generates revenue-focused content, expands service visibility, optimizes conversion, publishes safely to WordPress, tracks every change, and attributes traffic to leads and revenue.

---

## Deployment Guide (Ubuntu Server)

### Prerequisites

- Ubuntu server (24.04 LTS recommended) with Docker installed
- WordPress site with admin access
- OpenAI API key or Anthropic API key
- Access to WordPress `wp-config.php` file

### Step 1: Server Setup (run on Ubuntu server)

```bash
# Fix any broken apt repos (Cloudflare repo is a common culprit)
sudo rm -f /etc/apt/sources.list.d/cloudflare-main.list /etc/apt/sources.list.d/cloudflare.list

# Install Docker
sudo apt update
sudo apt install -y docker-ce
sudo usermod -aG docker $USER

# Create app directory
sudo mkdir -p /opt/ess-ags
sudo chown $USER:$USER /opt/ess-ags

# Verify
docker --version
docker compose version
```

### Step 2: Transfer Files (from Windows PowerShell)

```powershell
scp -r C:\dev\ESS_Autonomous_Growth_System\api morningstar@192.168.1.25:/opt/ess-ags/
scp -r C:\dev\ESS_Autonomous_Growth_System\db morningstar@192.168.1.25:/opt/ess-ags/
scp -r C:\dev\ESS_Autonomous_Growth_System\worker morningstar@192.168.1.25:/opt/ess-ags/
scp -r C:\dev\ESS_Autonomous_Growth_System\n8n morningstar@192.168.1.25:/opt/ess-ags/
scp -r C:\dev\ESS_Autonomous_Growth_System\nginx morningstar@192.168.1.25:/opt/ess-ags/
scp C:\dev\ESS_Autonomous_Growth_System\docker-compose.yml morningstar@192.168.1.25:/opt/ess-ags/
scp C:\dev\ESS_Autonomous_Growth_System\.env.example morningstar@192.168.1.25:/opt/ess-ags/
scp C:\dev\ESS_Autonomous_Growth_System\.gitignore morningstar@192.168.1.25:/opt/ess-ags/
```

Verify on server:
```bash
ls /opt/ess-ags/
# Should show: api  db  docker-compose.yml  n8n  nginx  worker  .env.example  .gitignore
```

### Step 3: Configure Environment (on Ubuntu server)

```bash
cd /opt/ess-ags
nano .env
```

Create this file with your real values:

```env
DB_PASSWORD=ess_secure_password_change_me

WP_URL=https://your-wordpress-site.com
WP_USERNAME=admin
WP_PASSWORD=your_wp_application_password
WP_JWT_SECRET=your_secret_key_here

OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=
LLM_PROVIDER=openai

GA4_PROPERTY_ID=
GA4_CREDENTIALS=
```

**Required fields:**

| Variable | Where to get it |
|---|---|
| `WP_URL` | Your WordPress site URL (e.g., `https://electricsupplysource.com`) |
| `WP_USERNAME` | WordPress admin username |
| `WP_PASSWORD` | WP Admin → Users → Profile → Application Passwords → Generate |
| `WP_JWT_SECRET` | Any random string — must match what you put in `wp-config.php` |
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/settings/keys (optional if using OpenAI) |
| `LLM_PROVIDER` | `openai` or `anthropic` |

Save: `Ctrl+O` → `Enter` → `Ctrl+X`

### Step 4: Install JWT Plugin on WordPress

1. **Upload the plugin** — copy the `wp-api-jwt-auth-develop` folder to `/wp-content/plugins/` on your WordPress server
2. **Activate** — WP Admin → Plugins → "JWT Authentication for WP REST API" → Activate
3. **Edit `wp-config.php`** — add these lines above `/* That's all, stop editing! */`:
   ```php
   define('JWT_AUTH_SECRET_KEY', 'your_secret_key_here');  // Must match WP_JWT_SECRET in .env
   define('JWT_AUTH_CORS_ENABLE', true);
   ```
4. **Edit `.htaccess`** (if on Apache) — add at the top:
   ```apache
   RewriteEngine on
   RewriteCond %{HTTP:Authorization} ^(.*)
   RewriteRule ^(.*) - [E=HTTP_AUTHORIZATION:%1]
   ```
5. **Flush permalinks** — WP Admin → Settings → Permalinks → Save Changes

### Step 5: Launch the System (on Ubuntu server)

```bash
cd /opt/ess-ags
docker compose up -d --build
```

This takes 2-5 minutes. Then verify:

```bash
docker compose ps
```

All containers should show `running` status.

### Step 6: Verify Everything Works

```bash
# Test API health
curl http://localhost:8000/health

# Test WordPress connection
curl http://localhost:8000/api/wordpress/test

# Open API docs in browser
# http://YOUR_SERVER_IP:8000/docs
```

Expected health response:
```json
{"status": "ok", "llm_provider": "openai"}
```

### Useful Commands

```bash
# View logs
docker compose logs -f api        # API service
docker compose logs -f worker     # Background worker
docker compose logs -f n8n        # Orchestrator
docker compose logs -f postgres   # Database

# Restart a service
docker compose restart api

# Stop everything
docker compose down

# Rebuild after code changes
docker compose up -d --build

# Access database
docker compose exec postgres psql -U ess_user -d ess_ags

# Access n8n UI
# http://YOUR_SERVER_IP:5678
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    nginx (port 80)                   │
├──────────────┬──────────────────┬───────────────────┤
│   API        │   n8n            │   Worker          │
│   FastAPI    │   Orchestrator   │   Scheduler       │
│   :8000      │   :5678          │   APScheduler     │
├──────────────┴──────────────────┴───────────────────┤
│              PostgreSQL :5432  │  Redis :6379       │
└────────────────────────────────┴────────────────────┘
```

## Modules

| Module | Status | Description |
|---|---|---|
| **Market Intelligence** | ✅ Built | Keyword discovery, competitor analysis, trend detection |
| **Opportunity Scoring** | ✅ Built | 7-component scoring model (threshold: 75/60/<60) |
| **Content Generation** | ✅ Built | 7 content types: blogs, landing pages, service expansions, FAQs, local pages, comparisons, buyer guides |
| **Validation Engine** | ✅ Built | Duplicate detection, tone check, SEO completeness, risk routing (auto_publish/review/manual) |
| **Internal Link Engine** | ✅ Built | Strategic linking, orphan page fixes, authority distribution |
| **Translation Engine** | ✅ Built | EN→ES with glossary, translation memory, paired pages |
| **WordPress Publisher** | ✅ Built | Draft → schedule → publish via JWT-authenticated REST API |
| **Change Tracking** | ✅ Built | Before/after snapshots, diffs, rollback capability |
| **Reporting Engine** | ✅ Built | Daily work logs, weekly SEO growth, monthly revenue reports |
| **n8n Orchestrator** | ✅ Built | Visual workflow automation |
| **Worker Scheduler** | ✅ Built | APScheduler: keyword discovery (6h), content generation (12h), reports (daily 8am) |

## API Endpoints

### Market Intelligence
- `GET /api/intelligence/discover` - Discover keyword opportunities
- `POST /api/intelligence/score` - Score a keyword opportunity
- `POST /api/intelligence/expand-keywords` - Expand seed keywords
- `POST /api/intelligence/analyze-competitors` - Analyze competitor gaps
- `GET /api/intelligence/cluster-balance` - Check cluster content balance

### Opportunities
- `POST /api/opportunities/` - Create and score new opportunity
- `GET /api/opportunities/` - List opportunities
- `GET /api/opportunities/{id}` - Get single opportunity
- `POST /api/opportunities/bulk-discover` - Bulk discover and score

### Content
- `POST /api/content/generate` - Generate content (blog, landing page, etc.)
- `POST /api/content/validate` - Validate content quality
- `POST /api/content/translate` - Translate to Spanish
- `POST /api/content/suggest-links` - Suggest internal links

### WordPress
- `POST /api/wordpress/publish` - Publish content to WordPress
- `POST /api/wordpress/publish-page` - Publish as WordPress page
- `GET /api/wordpress/test` - Test WordPress connection
- `GET /api/wordpress/posts` - List WordPress posts
- `GET /api/wordpress/categories` - List categories
- `POST /api/wordpress/update/{id}` - Update a post

### Tracking
- `POST /api/tracking/snapshot` - Create content snapshot
- `POST /api/tracking/diff` - Compute diff between versions
- `POST /api/tracking/rollback` - Rollback to previous snapshot
- `GET /api/tracking/history/{id}` - View change history

### Reports
- `GET /api/reports/daily` - Daily work log
- `GET /api/reports/weekly` - Weekly SEO growth
- `GET /api/reports/monthly` - Monthly revenue report
- `GET /api/reports/bilingual` - Bilingual page status
- `POST /api/reports/generate` - Generate custom report

### Tasks
- `POST /api/tasks/` - Create a new task
- `GET /api/tasks/` - List all tasks
- `GET /api/tasks/{id}` - Get task details
- `PUT /api/tasks/{id}/status` - Update task status

## Database Schema (15 Tables)

| Table | Purpose |
|---|---|
| `content_groups` | Clusters of related content |
| `content_versions` | Every version of every page (EN+ES) |
| `translations` | Paired EN/ES page mappings |
| `keywords` | Tracked keywords with volume/difficulty |
| `keyword_clusters` | Topic clusters (VFD, PLC, SCADA, etc.) |
| `opportunities` | Scored keyword opportunities |
| `briefs` | Content briefs from opportunities |
| `tasks` | Automation queue items |
| `automation_runs` | Batch execution records |
| `internal_links` | Suggested and applied internal links |
| `snapshots` | Before/after page state captures |
| `diffs` | Computed differences between snapshots |
| `reports` | Generated report data |
| `leads` | Captured leads with source attribution |
| `revenue` | Revenue attribution pipeline |
| `ranking_data` | Keyword position tracking |

## Deployment Phases

| Phase | Scope | Status |
|---|---|---|
| **Phase 1** | Core infrastructure, API, DB, WordPress publishing | ✅ Done |
| **Phase 2** | Market intelligence, blog generation | ✅ Built, needs live data |
| **Phase 3** | Landing pages, service expansions | ✅ Built, needs live data |
| **Phase 4** | Spanish translation | ✅ Built, needs live data |
| **Phase 5** | Conversion optimization | ⏳ Stubbed |
| **Phase 6** | Reporting and attribution | ⏳ Stubbed (reporting built, attribution needs CRM integration) |

## LLM Providers

The system supports both **OpenAI** (GPT-4o) and **Anthropic** (Claude 3.5 Sonnet). Switch via `LLM_PROVIDER` in `.env`. Both keys can be set simultaneously for easy switching.

| Provider | Model | Use Case |
|---|---|---|
| `openai` | GPT-4o | Default — fast, good for content generation |
| `anthropic` | Claude 3.5 Sonnet | Alternative — excellent for analysis and validation |

---

## TODO — What's Left to Implement

### High Priority (Phase 1-2)

- [ ] **Connect real WordPress site** — fill in `.env` with actual WP URL, credentials, and JWT secret
- [ ] **Install JWT plugin** on WordPress and configure `wp-config.php`
- [ ] **Run initial database migration** — `docker compose exec postgres psql -U ess_user -d ess_ags < /docker-entrypoint-initdb.d/001_initial_schema.sql` (auto-runs on first boot)
- [ ] **Test WordPress connection** — `curl http://localhost:8000/api/wordpress/test`
- [ ] **Test content generation** — `POST /api/content/generate` with a real keyword
- [ ] **Configure n8n credentials** — set up API endpoints in n8n workflows
- [ ] **Import existing WordPress content** — seed the DB with current pages for internal linking

### Medium Priority (Phase 3-4)

- [ ] **Google Analytics 4 integration** — configure `GA4_PROPERTY_ID` and service account credentials for real traffic data
- [ ] **Google Search Console API** — connect for real keyword ranking and impression data
- [ ] **Competitor URL list** — create a config file with competitor URLs for the competitor analysis engine
- [ ] **Content glossary** — expand the translation glossary with ESS-specific terminology
- [ ] **Conversion optimization engine** — implement CTA block injection, quote boxes, lead magnets
- [ ] **Local SEO engine** — automated location-based page generation (El Paso, Texas, Southwest)
- [ ] **Refresh engine** — detect and update old/underperforming content

### Low Priority (Phase 5-6)

- [ ] **Revenue attribution** — integrate with CRM (HubSpot, Salesforce, or custom) to track page → lead → revenue
- [ ] **Lead capture forms** — API endpoints for form submissions with source attribution
- [ ] **Dashboard UI** — build a simple web dashboard for monitoring (or use n8n + Grafana)
- [ ] **Email notifications** — send weekly/monthly reports via email
- [ ] **Rollback automation** — auto-rollback if traffic drops after publishing
- [ ] **A/B testing** — test different CTA variations
- [ ] **Vector DB** — add semantic search for better internal linking and content gap analysis
- [ ] **Rate limiting** — protect API endpoints
- [ ] **CI/CD pipeline** — automated testing and deployment
- [ ] **Backup strategy** — automated Postgres backups

### Infrastructure

- [ ] **SSL/HTTPS** — add Let's Encrypt or reverse proxy with TLS
- [ ] **Domain name** — point a subdomain (e.g., `ags.electricsupplysource.com`) to the server
- [ ] **Resource monitoring** — set up alerts for disk space, memory, container health
- [ ] **Log rotation** — configure Docker log limits
- [ ] **Automated updates** — set up unattended-upgrades on Ubuntu
