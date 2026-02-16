from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_file, make_response
import sqlite3
import os
from datetime import datetime, date, timedelta
from io import StringIO, BytesIO
import csv
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except Exception:
    # reportlab is optional — export PDF will error if not installed
    reportlab = None

DB = os.path.join(os.path.dirname(__file__), 'data.db')

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    first = not os.path.exists(DB)
    conn = get_db()
    conn.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, date TEXT, description TEXT, amount REAL)')
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)')
    conn.commit()
    # create default admin user if none exist
    cur = conn.execute('SELECT COUNT(*) as c FROM users')
    if cur.fetchone()['c'] == 0:
        admin_pass = os.environ.get('ADMIN_PASS', 'admin')
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', generate_password_hash(admin_pass)))
        conn.commit()
    # ensure optional columns exist on users table (email, role, reset token/expiry)
    cols = {r['name'] for r in conn.execute("PRAGMA table_info('users')").fetchall()}
    if 'email' not in cols:
        try:
            conn.execute('ALTER TABLE users ADD COLUMN email TEXT')
        except Exception:
            pass
    if 'role' not in cols:
        try:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        except Exception:
            pass
    if 'reset_token' not in cols:
        try:
            conn.execute('ALTER TABLE users ADD COLUMN reset_token TEXT')
        except Exception:
            pass
    if 'reset_expiry' not in cols:
        try:
            conn.execute('ALTER TABLE users ADD COLUMN reset_expiry TEXT')
        except Exception:
            pass
    conn.commit()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')
init_db()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if session.get('user'):
            return f(*args, **kwargs)
        return jsonify({'error':'authentication required'}), 401
    return wrapped


def role_required(role):
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            u = session.get('user')
            if not u:
                return jsonify({'error':'authentication required'}), 401
            conn = get_db()
            row = conn.execute('SELECT role FROM users WHERE username = ?', (u,)).fetchone()
            if not row or row['role'] != role:
                return jsonify({'error':'forbidden'}), 403
            return f(*args, **kwargs)
        return wrapped
    return decorator

@app.route('/')
def index():
    return render_template('index.html', user=session.get('user'))

@app.route('/login', methods=['POST'])
def login():
    data = request.form or request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error':'missing credentials'}), 400
    conn = get_db()
    row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if row and check_password_hash(row['password'], password):
        session['user'] = username
        session['role'] = row['role'] if 'role' in row.keys() else 'user'
        return jsonify({'ok':True, 'user':username, 'role': session['role']})
    return jsonify({'error':'invalid credentials'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'ok':True})

@app.route('/api/messages', methods=['GET','POST'])
def messages():
    conn = get_db()
    if request.method == 'POST':
        if not session.get('user'):
            return jsonify({'error':'authentication required'}), 401
        data = request.get_json() or {}
        date_str = data.get('date') or datetime.utcnow().strftime('%Y-%m-%d')
        description = data.get('description','')
        amount = float(data.get('amount') or 0)
        cur = conn.execute('INSERT INTO messages (date, description, amount) VALUES (?, ?, ?)', (date_str, description, amount))
        conn.commit()
        return jsonify({'id': cur.lastrowid, 'date': date_str, 'description': description, 'amount': amount}), 201

    # GET: support optional ?date=YYYY-MM-DD or pagination ?page=1&per_page=50
    date_q = request.args.get('date')
    page = int(request.args.get('page') or 1)
    per_page = int(request.args.get('per_page') or 50)
    if page < 1: page = 1
    offset = (page-1)*per_page
    if date_q:
        cur = conn.execute('SELECT COUNT(*) as c FROM messages WHERE date = ?', (date_q,))
        total = cur.fetchone()['c']
        rows = conn.execute('SELECT * FROM messages WHERE date = ? ORDER BY id DESC LIMIT ? OFFSET ?', (date_q, per_page, offset)).fetchall()
    else:
        cur = conn.execute('SELECT COUNT(*) as c FROM messages')
        total = cur.fetchone()['c']
        rows = conn.execute('SELECT * FROM messages ORDER BY date DESC, id DESC LIMIT ? OFFSET ?', (per_page, offset)).fetchall()
    result = [dict(r) for r in rows]
    return jsonify({'items': result, 'page': page, 'per_page': per_page, 'total': total})

@app.route('/api/balance', methods=['GET'])
def balance():
    conn = get_db()
    date_q = request.args.get('date') or datetime.utcnow().strftime('%Y-%m-%d')
    row = conn.execute('SELECT COALESCE(SUM(amount),0) as total FROM messages WHERE date = ?', (date_q,)).fetchone()
    total = row['total'] if row else 0
    return jsonify({'date': date_q, 'total': total})

@app.route('/api/export', methods=['GET'])
@role_required('admin')
def export_csv():
    conn = get_db()
    # support date or range export
    start = request.args.get('start')
    end = request.args.get('end')
    if start and end:
        rows = conn.execute('SELECT * FROM messages WHERE date >= ? AND date <= ? ORDER BY date, id', (start, end)).fetchall()
        filename = f'messages_{start}_to_{end}.csv'
    else:
        date_q = request.args.get('date')
        if date_q:
            rows = conn.execute('SELECT * FROM messages WHERE date = ? ORDER BY id', (date_q,)).fetchall()
            filename = f'messages_{date_q}.csv'
        else:
            rows = conn.execute('SELECT * FROM messages ORDER BY date, id').fetchall()
            filename = f'messages_all.csv'

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['id','date','description','amount'])
    for r in rows:
        writer.writerow([r['id'], r['date'], r['description'], r['amount']])
    output = si.getvalue()
    return (output, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename="{filename}"'
    })
@app.route('/api/monthly', methods=['GET'])
def monthly_summary():
    conn = get_db()
    year = request.args.get('year')
    month = request.args.get('month')
    fmt = request.args.get('format', 'json')
    if not year or not month:
        today = date.today()
        year = str(today.year)
        month = f"{today.month:02d}"
    start = f"{year}-{month}-01"
    # compute next month for range end
    y = int(year); m = int(month)
    if m == 12:
        ny, nm = y+1, 1
    else:
        ny, nm = y, m+1
    end = f"{ny}-{nm:02d}-01"

    rows = conn.execute('SELECT date, COALESCE(SUM(amount),0) as total FROM messages WHERE date >= ? AND date < ? GROUP BY date ORDER BY date', (start, end)).fetchall()
    total_row = conn.execute('SELECT COALESCE(SUM(amount),0) as total FROM messages WHERE date >= ? AND date < ?', (start, end)).fetchone()
    days = [dict(r) for r in rows]
    if fmt == 'csv':
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['date','total'])
        for r in rows:
            writer.writerow([r['date'], r['total']])
        output = si.getvalue()
        filename = f'monthly_{year}_{month}.csv'
        return (output, 200, {'Content-Type':'text/csv','Content-Disposition':f'attachment; filename="{filename}"'})
    if fmt == 'pdf':
        if 'reportlab' not in globals():
            return jsonify({'error':'PDF export requires reportlab'}), 500
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        text = c.beginText(40, 750)
        text.textLine(f'Monthly summary for {year}-{month} Total: {float(total_row["total"] or 0):.2f}')
        text.textLine('')
        for r in rows:
            text.textLine(f"{r['date']}: {float(r['total']):.2f}")
        c.drawText(text)
        c.showPage()
        c.save()
        buf.seek(0)
        resp = make_response(buf.read())
        resp.headers.set('Content-Type','application/pdf')
        resp.headers.set('Content-Disposition', f'attachment; filename=monthly_{year}_{month}.pdf')
        return resp

    return jsonify({'year': year, 'month': month, 'total': total_row['total'] if total_row else 0, 'by_day': days})


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    requested_role = data.get('role')
    if not username or not password:
        return jsonify({'error':'missing fields'}), 400
    conn = get_db()
    try:
        role = 'user'
        # only allow setting role if the requester is admin
        if requested_role and session.get('user'):
            cur = conn.execute('SELECT role FROM users WHERE username = ?', (session.get('user'),)).fetchone()
            if cur and cur['role'] == 'admin':
                role = requested_role
        conn.execute('INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)', (username, generate_password_hash(password), email, role))
        conn.commit()
        return jsonify({'ok':True}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error':'username exists'}), 400


@app.route('/reset-request', methods=['POST'])
def reset_request():
    data = request.get_json() or {}
    username = data.get('username')
    if not username:
        return jsonify({'error':'missing username'}), 400
    conn = get_db()
    row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if not row:
        return jsonify({'error':'unknown user'}), 404
    token = secrets.token_urlsafe(16)
    expiry = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    conn.execute('UPDATE users SET reset_token = ?, reset_expiry = ? WHERE username = ?', (token, expiry, username))
    conn.commit()
    # Try to email the token if SMTP is configured and user has an email
    smtp_host = os.environ.get('SMTP_HOST')
    smtp_port = int(os.environ.get('SMTP_PORT') or 0)
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')
    smtp_from = os.environ.get('SMTP_FROM')
    sent = False
    if smtp_host and smtp_port and row.get('email') and smtp_from:
        try:
            import smtplib
            from email.message import EmailMessage
            msg = EmailMessage()
            msg['Subject'] = 'Password reset token'
            msg['From'] = smtp_from
            msg['To'] = row['email']
            msg.set_content(f'Your password reset token is: {token}\nIt expires at {expiry} UTC')
            s = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            s.starttls()
            if smtp_user and smtp_pass:
                s.login(smtp_user, smtp_pass)
            s.send_message(msg)
            s.quit()
            sent = True
        except Exception as e:
            # log error to stdout — continue and return token for local use
            print('SMTP send failed:', e)

    if sent:
        return jsonify({'ok': True, 'sent': True})
    # If email wasn't sent or configured, return token so local users can use it.
    return jsonify({'token': token, 'expiry': expiry})


@app.route('/reset', methods=['POST'])
def reset():
    data = request.get_json() or {}
    token = data.get('token')
    new_password = data.get('new_password')
    if not token or not new_password:
        return jsonify({'error':'missing fields'}), 400
    conn = get_db()
    row = conn.execute('SELECT * FROM users WHERE reset_token = ?', (token,)).fetchone()
    if not row:
        return jsonify({'error':'invalid token'}), 400
    if not row['reset_expiry'] or datetime.fromisoformat(row['reset_expiry']) < datetime.utcnow():
        return jsonify({'error':'token expired'}), 400
    conn.execute('UPDATE users SET password = ?, reset_token = NULL, reset_expiry = NULL WHERE id = ?', (generate_password_hash(new_password), row['id']))
    conn.commit()
    return jsonify({'ok':True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
