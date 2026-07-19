# VNC BCA College Website - Content Management System

A Flask website for the Department of Computer Applications (BCA),
Vijayanagara College, rebuilt as a full Content Management System.
Every piece of visible content - home page copy, faculty, events,
notices, About College, contact details, gallery photos, and site-wide
settings - is stored in the database and editable from a
password-protected admin dashboard. **No template or Python file needs
to be touched for routine content updates.**

The public site's look and feel (CSS, layout, animations) is
unchanged from the original design; only the source of the content
changed, from hardcoded HTML to the database.

---

## What's new in this version

- **Full CRUD admin dashboard** for 8 content modules (see below), each
  with add / edit / delete, server-side validation, CSRF protection,
  and delete-confirmation dialogs.
- **SQLAlchemy models** replace the old hand-rolled SQLite queries -
  a normalized schema with a dedicated table per content type.
- **Image & PDF uploads** go through `Flask-WTF` file validators (type
  checked) and are stored under `static/uploads/<module>/` with
  randomized filenames; old files are cleaned up automatically when
  replaced or deleted.
- **Admin users live in the database** (hashed passwords), not in an
  environment variable - change your password from the dashboard after
  first login.
- **Flash messages** confirm every create/update/delete action.
- A **seed script** migrates your original hardcoded content (faculty
  roster, notices, feature cards, photo folders) into the new schema
  automatically the first time the app starts, so the site looks the
  same on day one.
- A **legacy data importer** (`flask migrate-legacy`) pulls any
  notices/messages that were already stored in the old
  `instance/database.db` into the new database.

---

## Admin Dashboard Modules

| Module | What you can manage |
|---|---|
| **Home Page** | Hero title/subtitle, CTA button(s), banner image, welcome message, statistics/counters, featured sections |
| **Faculty** | Photo, name, department, designation, qualification, email, phone, display order, "show on home page" |
| **Events** | Title, description, date, venue, cover image, per-event photo gallery, upcoming/completed status |
| **Notices** | Title, description, PDF attachment, publish/expiry date, pin to top |
| **About College** | Vision, mission, principal's message + photo, about text, images |
| **Contact** | Address, phone numbers, email, Google Maps link, social media links |
| **Gallery** | Create albums/categories, upload images, edit captions, delete images |
| **Website Settings** | College name, logo, favicon, footer text, copyright text |

Contact messages submitted through the public contact form can be
viewed/deleted under **Messages**, and your own admin password can be
changed under **Change Password**.

### Developer credit button & developer role

There are now two kinds of accounts:

- **Admin** - full access to all 8 content modules above.
- **Developer** - everything an admin can do, *plus* exclusive control
  over whether the "Developed by ..." credit button shows on the public
  site at all. A regular admin can edit the developer's name and link
  under Website Settings, but only the developer account can hide the
  button (under the developer-only **Developer Tools** page, which only
  appears in the sidebar for that account).

On the public site, the credit button appears in the footer as
"Developed by &lt;name&gt;" and links to whatever URL is set in
Website Settings (falls back to the built-in `/developer` profile page
if no link is set). Every page with a footer also has a small,
unlabeled admin-login link (just a faint dot) so the login page isn't
advertised in the main navigation.

To create the developer account:

```bash
flask --app run create-admin
# Username: whatever you like
# Role: developer
# Password: choose a strong password
```

or seed it automatically on first boot by setting `DEVELOPER_USERNAME`
and `DEVELOPER_PASSWORD_HASH` in your environment before starting the
app (same pattern as the admin bootstrap variables - see `.env.example`).

---

## Project Structure

```
project/
├── app/
│   ├── __init__.py        # App factory: config, DB, CSRF, CLI, error pages
│   ├── models.py          # SQLAlchemy models (one per content module)
│   ├── forms.py           # Flask-WTF forms (validation + file uploads)
│   ├── utils.py           # login_required decorator, upload helpers
│   ├── seed.py             # First-run seeding of initial CMS content
│   ├── migrate_legacy.py   # One-off importer for the old SQLite schema
│   └── routes/
│       ├── __init__.py
│       ├── public.py       # Public pages - fully DB-driven
│       └── admin.py        # Authenticated CRUD routes for every module
├── static/
│   ├── css/                # style.css (site) + admin.css (dashboard)
│   ├── images/              # Original bundled theme images (unchanged)
│   └── uploads/              # NEW uploads land here, per module subfolder
├── templates/
│   ├── *.html               # Public pages (index, staff, about, events, ...)
│   ├── admin/                # Admin dashboard templates (one per module)
│   └── errors/                # 400 / 403 / 404 / 500 pages
├── instance/
│   ├── app.db                # New CMS database (created automatically)
│   └── database.db            # Old pre-CMS database (kept for migration)
├── config.py
├── run.py
├── requirements.txt
├── Procfile
├── runtime.txt
├── .env.example
└── .gitignore
```

---

## Zero-Setup Admin Login

**No environment variables, password hashes, or CLI commands are required
to log in for the first time.** The very first time the app starts:

1. It checks whether any admin account exists.
2. If not, it automatically creates one:
   - **Username:** `admin`
   - **Password:** `Admin@123`
3. The password is hashed with Werkzeug's `generate_password_hash()` before
   being stored - it is never kept in plain text.
4. This only ever happens once. If an admin account already exists, it is
   never recreated or overwritten.

**Log in at `/login` with the credentials above, then immediately go to
"Change Password" in the sidebar and set your own password.**

If you'd rather set a specific username/password hash yourself instead of
using the auto-created default, you still can via `ADMIN_USERNAME` /
`ADMIN_PASSWORD_HASH` in `.env` - but this is entirely optional now.

---

## New in this version

Beyond the original 8-module CMS, the following upgrades have been added:

- **Notice auto-expiry** - notices past their expiry date are hidden from
  the public notice board automatically (with a "Show expired notices
  too" link to reveal them).
- **Inline PDF preview** - notice attachments expand in-page via a
  collapsible `<iframe>` instead of only opening in a new tab.
- **One-click database backup** - a "Download Backup" button on the admin
  dashboard downloads the current SQLite file directly (Postgres/MySQL
  deployments should use their provider's own backup tools instead).
- **SEO settings** - meta description, meta keywords, and a social-share
  (Open Graph) image are now editable from Website Settings and rendered
  in the homepage's `<head>`.
- **Light/Dark mode** - a toggle in the homepage nav bar switches themes
  and remembers the choice (via `localStorage`) on return visits.
- **Global search** - a search box in the homepage nav bar searches
  faculty, events, notices, and gallery albums at once (`/search?q=...`).
- **CSV import/export for Faculty and Notices** - opens fine in Excel;
  export existing rows or bulk-import new ones from the Faculty/Notices
  admin pages. Photos/PDFs aren't part of the CSV - add those by editing
  each imported entry afterwards.
- **Opportunistic image compression** - if `Pillow` is installed
  (it's in `requirements.txt`), uploaded images are automatically
  downsized (max 1600px) and re-compressed to save space. If Pillow isn't
  available for any reason, uploads still work - they're just stored at
  original size.
- **Basic PWA support** - `static/manifest.json` + `static/sw.js` let the
  site be "installed" from a mobile browser and cache its core static
  assets offline. The manifest icon is a placeholder built from an
  existing photo - **swap in real 192x192/512x512 PNG icons** for a
  fully compliant install experience.
- **Event calendar** - a month-grid calendar view at `/event/calendar`
  (linked from the Events page) showing events on their actual dates,
  with previous/next month navigation.
- **Secret admin login link** - the visible "Admin" nav links were
  removed; every page's footer instead has a small, unlabeled dot that
  quietly links to `/login`.

**Not included yet:** a visitor analytics dashboard. That needs its own
tracking model and middleware to do properly (page-view logging, unique
visitor counts, a charts view) rather than being bolted on alongside
everything else - happy to build it as a focused follow-up if you'd
like it next.

---

## 1. Local Setup

### Prerequisites
- Python 3.11+ (project pinned to 3.12.4 for deployment)

### Steps

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your local .env file
cp .env.example .env
```

### Generate your secrets

```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the result into `.env`:

```
SECRET_KEY=<paste generated hex string>
FLASK_ENV=development
SESSION_COOKIE_SECURE=false
```

### Run it

```bash
python run.py
```

Visit `http://127.0.0.1:5000`. On first launch the app automatically:
1. Creates all database tables (`instance/app.db`).
2. Seeds them with your original site content (faculty, notices,
   feature cards, photo albums) so nothing looks empty.
3. Creates an admin account with username `admin` and password
   `Admin@123` if no admin account exists yet - no setup required.
   **Log in and change this password immediately** under
   *Change Password* in the sidebar.

### Overriding the default admin credentials (optional)

You never have to do this - it's only useful if you want a specific
username/password from the very first boot instead of the default.

Either:

**Option A - via environment variable, before first run:**
```bash
python -c "from werkzeug.security import generate_password_hash as g; print(g('your-strong-password'))"
```
Put the result in `.env` as `ADMIN_PASSWORD_HASH=...` (and optionally
`ADMIN_USERNAME=...`) before starting the app for the first time.

**Option B - via the CLI, any time:**
```bash
flask --app run create-admin
```
This prompts for a username, role (`admin` or `developer`), and
password, and writes the hash straight to the database - use it to
create additional admins, a developer account, or reset a lost password.

### Importing your old data

If you have an existing `instance/database.db` from the previous
version of this site with notices/messages in it, run:

```bash
flask --app run migrate-legacy
```

This copies any notices/messages that aren't already present into the
new database. Safe to re-run.

---

## 2. Environment Variables

| Variable               | Required | Description                                                                 |
|-------------------------|:--------:|-------------------------------------------------------------------------------|
| `FLASK_ENV`              | No       | `development` or `production` (default: `production`)                        |
| `SECRET_KEY`             | **Yes**  | Random secret used to sign sessions/CSRF tokens. Generate with `secrets.token_hex(32)`. |
| `ADMIN_USERNAME`         | No       | Overrides the default admin username (`admin`) if set before first run        |
| `ADMIN_PASSWORD_HASH`    | No       | Overrides the default admin password if set before first run - without it, a default account (`admin` / `Admin@123`) is created automatically |
| `DEVELOPER_USERNAME`     | No       | Username used only when seeding the developer account (default: `developer`)  |
| `DEVELOPER_PASSWORD_HASH`| No       | Werkzeug password hash used only when seeding the developer account; if unset, no developer account is created automatically |
| `DATABASE_PATH`          | No       | Path to the SQLite file (default: `instance/app.db`)                          |
| `DATABASE_URL`           | No       | Full SQLAlchemy URL - set this to use Postgres/MySQL instead of SQLite         |
| `SESSION_COOKIE_SECURE`  | No       | `true` in production (HTTPS only), `false` for local HTTP dev                 |

`SECRET_KEY` is required in production - the app refuses to start
without it. Every other variable in this table is optional.

---

## 3. Deploying to Railway

1. **Push this project to a GitHub repository.**

2. **Create a new Railway project** from that repo (Railway auto-detects
   Python via `runtime.txt` and `requirements.txt`).

3. **Set environment variables** in Railway's *Variables* tab:
   - `FLASK_ENV=production`
   - `SECRET_KEY=<your generated value>` (required)
   - `SESSION_COOKIE_SECURE=true`
   - Optionally `ADMIN_USERNAME` / `ADMIN_PASSWORD_HASH` if you want
     specific admin credentials from the start - otherwise the app
     creates the default `admin` / `Admin@123` account for you.

4. **Start command** - Railway uses the `Procfile` automatically:
   ```
   web: gunicorn run:app --bind 0.0.0.0:$PORT --workers 3 --log-file -
   ```

5. **Deploy.** Railway assigns a public URL and injects `$PORT`
   automatically. On first boot the app creates its tables and seeds
   initial content and your admin user.

### A note on persistence (SQLite + uploaded files)

Railway's filesystem is ephemeral on redeploy unless you attach a
**volume**. Mount a Railway volume at the `instance/` directory
*and* at `static/uploads/` (Project → Settings → Volumes) so your
database and any images/PDFs uploaded through the admin panel survive
redeploys. Alternatively, set `DATABASE_URL` to a managed Postgres
instance (e.g. Railway's own Postgres plugin) for the database, and
keep the uploads volume for files.

---

## 4. Admin Panel

- Login: `/login`
- Dashboard: `/admin/dashboard`
- Home Page: `/admin/home` (+ `/admin/home/stats`, `/admin/home/features`, `/admin/home/cta`)
- Faculty: `/admin/faculty`
- Events: `/admin/events`
- Notices: `/admin/notices`
- About College: `/admin/about`
- Contact: `/admin/contact`
- Gallery: `/admin/gallery`
- Website Settings: `/admin/settings`
- Developer Tools (developer role only): `/admin/developer-tools`
- Database Backup: `/admin/backup`
- Faculty CSV export/import: `/admin/faculty/export.csv`, `/admin/faculty/import`
- Notices CSV export/import: `/admin/notices/export.csv`, `/admin/notices/import`
- Messages: `/admin/messages`
- Change Password: `/admin/change-password`
- Logout: `/logout`

Public-facing additions: global search at `/search?q=...` and the event
calendar at `/event/calendar`.

All `/admin/*` routes require a logged-in session and otherwise redirect
to `/login`. Every form uses CSRF tokens; every delete action requires
a JavaScript confirmation dialog before submitting.

---

## 5. Security Notes

- Passwords are hashed with Werkzeug's PBKDF2 implementation - never
  stored or logged in plaintext.
- CSRF protection is enabled globally (`Flask-WTF`'s `CSRFProtect`).
- File uploads are validated by extension (images: jpg/jpeg/png/gif/webp;
  notices: pdf) both in the form layer and the storage layer, saved
  under randomized filenames so a visitor can never guess or overwrite
  another upload, and request size is capped (`MAX_CONTENT_LENGTH`).
- Session cookies are `HttpOnly`, `SameSite=Lax`, and `Secure` in
  production.
- No credentials are hardcoded anywhere in source control; the only
  values ever placed in `.env`/Railway variables are used to seed the
  *first* admin account, after which credentials live (hashed) in the
  database and are changed via the dashboard.

---

## 6. Database Migrations

This project uses SQLAlchemy's `db.create_all()` at startup, which
creates any missing tables but does not alter existing ones. For a
site this size that's sufficient for initial deployment; if you later
change a model's columns, the simplest path is:

```bash
flask --app run shell
>>> from app.models import db
>>> db.drop_all()   # WARNING: destructive - back up first
>>> db.create_all()
```

For ongoing, non-destructive schema migrations as the project grows,
add `Flask-Migrate` (Alembic) - it isn't included here to keep the
dependency list minimal, but integrates cleanly with the existing
`db` object in `app/models.py`.

---

## 7. What Changed From the Original

- Notices, messages, faculty, events, gallery photos, About content,
  contact details, and site settings all moved from hardcoded
  templates/static folders into a normalized SQLAlchemy schema.
- The public `/notices` page previously received data from the
  database but the template ignored it and showed static HTML; this
  is now fixed - notices genuinely come from the database.
- `/etnic`, `/building`, and `/gallery` (previously simple static-folder
  browsers, `/gallery` was non-functional since no images lived in
  its expected folder) now read from the new **Gallery** module so an
  administrator can add, caption, and organize photos into albums
  without shell/FTP access.
- `/event` (previously just a static photo folder) now lists real
  **Event** entries with a date, venue, description, and status, each
  with its own photo gallery; the original photos were preserved as a
  general "Event Gallery" album beneath the list.
- A new `/about` page was added for the About College module (no
  equivalent page existed before).
- Admin authentication moved from a single environment-variable
  username/hash pair to a proper `admin_users` database table, with a
  self-service "Change Password" page.
