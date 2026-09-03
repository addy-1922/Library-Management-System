# Deploying to Render (git-based)

This project is configured for **Render Blueprint** deployment. It uses:
- **PostgreSQL** in production (auto-provided by Render), SQLite locally.
- **WhiteNoise** to serve static files in production.
- **Gunicorn** as the WSGI server.
- `render.yaml` to provision the web service + database in one click.

---

## One-time setup

### 1. Create a GitHub repository

```bash
# push it to GitHub
git add .
git commit -m "Ready for Render deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/library-management-system.git
git push -u origin main
```

### 2. Create a Render Blueprint

1. Go to https://render.com and sign in (free tier is fine).
2. Click **New → Blueprint**.
3. Connect your GitHub repo containing this project.
4. Render reads `render.yaml` and creates:
   - a **PostgreSQL** database (`library-db`)
   - a **Web Service** (`library-management-system`)
5. Click **Apply**. Render will build and deploy automatically.

Your app will be available at `https://library-management-system.onrender.com`.

> The first deploy runs `build.sh` (installs deps, runs `collectstatic`, runs `migrate`). This is done for you.

---

## Settings you may want to change

- **App URL / custom domain** — if you use a custom domain, update `DJANGO_ALLOWED_HOSTS`
  and `DJANGO_CSRF_TRUSTED_ORIGINS` in `render.yaml` to include it.
- **Email (SMTP)** — set `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, etc. under
  `Environment → Environment variables` in the Render dashboard if you want real
  password-reset / notification emails.

---

## Deploying updates

After every push to `main`, Render auto-deploys:

```bash
git add .
git commit -m "your change"
git push
```

You can also trigger a manual redeploy from the Render dashboard (Deploy → Clear build cache & deploy).

---

## Creating an admin account (important)

The build does **not** create a superuser automatically (do not commit credentials).
On first deploy, run this in the Render dashboard (Web Service → **Shell**):

```bash
python manage.py createsuperuser
```

Then log in at `/admin/` and use **Settings → General → Run a Seed** or run
`python manage.py seed_library --force` to add demo data (24 books, test users).

> Authentication requires admin signup. To let any visitor register themselves,
> registration is already enabled at `/accounts/register/`.

---

## Local development (unchanged)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py generate_covers   # fetch real book covers
python manage.py seed_library --force
python manage.py runserver
```

No `DATABASE_URL` set → uses local SQLite (`db.sqlite3`).

If you want to use Postgres locally, set `DATABASE_URL=postgres://user:pass@localhost:5432/library`.

---

## Useful Render Environment Variables

| Variable                  | Purpose                                        |
|---------------------------|------------------------------------------------|
| `DJANGO_SECRET_KEY`       | auto-generated; override for security          |
| `DJANGO_DEBUG`            | `False` in production                          |
| `DJANGO_ALLOWED_HOSTS`    | comma-separated hosts                          |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | trusted HTTPS origins for POST/CSRF        |
| `DATABASE_URL`            | set automatically by Render Blueprint          |