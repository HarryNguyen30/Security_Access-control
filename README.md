# Security & Access Control API

A **Flask**-based HTTP service that demonstrates **authenticated multi-user access** with **multi-factor authentication (MFA)**, **role-based administration**, and **mandatory access control** inspired by the **Biba integrity model**. A separate **CLI client** drives the workflow by calling the REST-style JSON API.

**Live demo:** [https://security-access-control.onrender.com/](https://security-access-control.onrender.com/)  
**Repository:** [github.com/HarryNguyen30/Security_Access-control](https://github.com/HarryNguyen30/Security_Access-control)

---

## Concept & goals

Organizations often store resources at different **sensitivity levels**. Not every user should read or write every resource. This project models that idea with:

- **Security labels** mapped to numeric levels: `UNCLASSIFIED` (1), `SECRET` (2), `TOP_SECRET` (3).
- **Biba-style rules** (simplified for teaching and demonstration):
  - **No read down** — a subject may read a resource only if their level is **less than or equal to** the resource’s level (`can_read`).
  - **No write up** — a subject may write a resource only if their level is **greater than or equal to** the resource’s level (`can_write`).
- **Authentication** via bcrypt-hashed passwords.
- **MFA** — after password verification, a one-time code is issued (email when Mailgun is configured; otherwise logged for demo environments).
- **Session tokens** — short-lived tokens (15 minutes) for subsequent API use in the sample client flow.

Admins manage users (create, update security level and group, delete). Clients access **expenses**, **timesheets**, **meeting minutes**, and **roster** data according to their clearance.

---

## Architecture

| Component | Role |
|-----------|------|
| **`src/server.py`** | Flask application: JSON API, user store, token/MFA handling, Biba checks, file-backed demo data under `data/`. |
| **`src/client.py`** | Interactive terminal client using `requests`; points at the server via `SERVER_URL`. |
| **`data/`** | Sample persistence (`users.txt`, `expenses.txt`, etc.). On free PaaS tiers the filesystem is often **ephemeral** — data may reset on restart. |

The **deployed web service runs only the server**. The client is meant to run **locally** (or anywhere with Python) and call the public base URL.

---

## Tech stack

- Python 3.10+
- Flask, Gunicorn (production process)
- bcrypt (password hashing)
- requests (HTTP client & Mailgun API calls)
- Optional: Mailgun for outbound email (MFA and welcome emails)

---

## Quick start (local)

### 1. Clone and install

```bash
git clone https://github.com/HarryNguyen30/Security_Access-control.git
cd Security_Access-control
pip install -r requirements.txt
```

### 2. Start the API

```bash
cd src
python server.py
```

Default bind: `http://127.0.0.1:2250` (override with `HOST` and `PORT` environment variables).

### 3. Run the CLI client (second terminal)

```bash
cd src
python client.py
```

To use a **remote** server:

```bash
export SERVER_URL=https://security-access-control.onrender.com
python client.py
```

### 4. Obtain the `root` password

On first startup the server generates a random `root` password and prints it:

```text
Generated root password: <plaintext>
```

- **Local:** check the terminal running `server.py` or Gunicorn.
- **Render:** open the service **Logs** and search for `Generated root password`.

> **Note:** Each cold start may regenerate credentials for `root` in this demo design. Treat logs accordingly in shared environments.

---

## Environment variables

| Variable | Purpose |
|----------|---------|
| `HOST` | Bind address for `python server.py` (default `127.0.0.1`). |
| `PORT` | Listen port (default `2250` locally; set automatically on Render). |
| `SERVER_URL` | Base URL for `client.py` (no trailing slash). |
| `MAILGUN_API_KEY` | Mailgun private API key for sending email. |
| `MAILGUN_DOMAIN` | Mailgun domain (e.g. `mg.example.com` or sandbox domain). |
| `MAILGUN_FROM` | Optional `From` header; default `SENG2250 <noreply@<MAILGUN_DOMAIN>>`. |

If Mailgun variables are **not** set, MFA and welcome emails are **not** sent; message content is printed to **server logs** instead (useful for demos without email setup).

---

## API overview

All business routes expect **`POST`** with **`Content-Type: application/json`** unless noted.

| Endpoint | Description |
|----------|-------------|
| `GET /` | Service metadata. |
| `GET /health` | Liveness check for monitoring / load balancers. |
| `POST /verify_password` | Body: `username`, `password`. |
| `POST /send_mfa` | Body: `username` — issues MFA code (email or log). |
| `POST /verify_mfa` | Body: `username`, `mfa_code`. |
| `POST /generate_token` | Body: `username` — returns session token. |
| `POST /validate_token` | Body: `token` — checks expiry (15 minutes). |
| `POST /admin_console` | Admin-only; body includes `action`: `add_user`, `modify_user`, `delete_user`, plus auth fields. |
| `POST /audit_expenses`, `/add_expense` | Expenses (TOP_SECRET resource). |
| `POST /audit_timesheets`, `/submit_timesheet` | Timesheets (TOP_SECRET). |
| `POST /view_meeting_minutes`, `/add_meeting_minutes` | Meeting minutes (SECRET). |
| `POST /view_roster`, `/roster_shift` | Roster (UNCLASSIFIED). |

Typical **client** flow: verify password → send MFA → verify MFA → generate token → call resource endpoints with the token validated by the client before each request (server enforces Biba using `username` in the JSON body).

---

## Production-style run (Gunicorn)

From the **repository root**:

```bash
gunicorn --chdir src server:app --bind 0.0.0.0:2250 --workers 1
```

Use **`--workers 1`** for this demo: in-memory token/MFA state is not shared across workers.

---

## Deployment (Render)

- **Build:** `pip install -r requirements.txt`
- **Start:** `gunicorn --chdir src server:app --bind 0.0.0.0:$PORT --workers 1`

Do **not** set the start command to the literal word `Procfile`; use the Gunicorn command above (or rely on a correctly configured Blueprint).

---

## Security & limitations (read before production use)

- **Demo / portfolio scope:** This is an academic-style system. It is **not** hardened for real production (e.g. `eval` when loading `users.txt`, plaintext password in logs, no HTTPS enforcement on your side beyond the platform, minimal input validation).
- **Secrets:** Never commit API keys; use environment variables only.
- **Data persistence:** Free-tier hosts may lose `data/` on restart; use a real database for production.

---

## License & attribution

Coursework-derived project (SENG2250). Adapt README and code reuse according to your institution’s academic integrity rules.

---

## Author

**Minh Tien Nguyen** — portfolio demonstration of secure API design, MFA flow, and mandatory access control concepts.
