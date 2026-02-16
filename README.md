# Daily Messaging Balance Sheet

Minimal Flask app to track daily message entries and show a simple balance sheet per day.

Quick start

1. Create a Python virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the app:

```bash
python app.py
```

3. Open http://localhost:5000 in your browser.

Data is stored in `data.db` in the project root (created automatically).

Notes
- Endpoints:
  - `GET /api/messages?date=YYYY-MM-DD` list messages
  - `POST /api/messages` create message JSON `{date,description,amount}`
  - `GET /api/balance?date=YYYY-MM-DD` returns daily total
  - `GET /api/export?date=YYYY-MM-DD` export CSV for a date (login required)
  - `GET /api/monthly?year=YYYY&month=MM` monthly summary

  New features added:
  - Registration: `POST /register` with JSON `{username,password}`
  - Password reset: `POST /reset-request` with JSON `{username}` returns a token, then `POST /reset` with `{token,new_password}` to complete.
  - Require login to create messages and to export CSVs. Use `/login` and `/logout` endpoints.
  - CSV export now supports ranges: `GET /api/export?start=YYYY-MM-DD&end=YYYY-MM-DD` (login required)
  - Monthly exports: `GET /api/monthly?year=YYYY&month=MM&format=csv|pdf|json` — `pdf` requires `reportlab`.

  UI changes
  - The frontend includes registration and password-reset controls, start/end date range export inputs, and a monthly format selector (JSON/CSV/PDF).

Auth
- A default admin user is created on first run. Set `ADMIN_PASS` env var to change the initial password.
- Login via `POST /login` with JSON `{username,password}`; logout via `POST /logout`.

Frontend
- The UI includes login fields, an Export CSV button (requires login), and a monthly summary view.

SMTP / Email
- To enable emailed reset tokens set the following env vars:
  - `SMTP_HOST` (e.g., smtp.example.com)
  - `SMTP_PORT` (e.g., 587)
  - `SMTP_USER` and `SMTP_PASS` (if your SMTP server requires auth)
  - `SMTP_FROM` (the From address for outgoing emails)

Roles
- Users have a `role` (`user` or `admin`). Admins can export data and assign roles when creating users.

Pagination
- `GET /api/messages` supports `?page=1&per_page=50` and returns `{items:[...], page, per_page, total}`.
# may