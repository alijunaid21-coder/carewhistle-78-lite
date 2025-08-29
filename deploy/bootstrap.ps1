# ===================== CareWhistle Finalee 4 (Windows, MySQL/MariaDB) =====================
$BASE   = Join-Path $env:USERPROFILE "Documents\carewhistle-finalee4"
$APPDIR = Join-Path $BASE "app"
$TPL    = Join-Path $APPDIR "templates"
$ADMT   = Join-Path $TPL "admin"
$MGRT   = Join-Path $TPL "manager"
$STAT   = Join-Path $APPDIR "static"

New-Item -ItemType Directory -Force -Path $BASE,$APPDIR,$TPL,$ADMT,$MGRT,$STAT | Out-Null

# ---------------- requirements.txt ----------------
@'
flask==3.0.3
waitress==3.0.0
SQLAlchemy==2.0.29
PyMySQL==1.1.0
python-dotenv==1.0.1
flask-talisman==1.1.0
langdetect==1.0.9
vaderSentiment==3.3.2
'@ | Set-Content -Encoding UTF8 (Join-Path $BASE "requirements.txt")

# ---------------- .env (edit DB if needed) ----------------
@'
FLASK_ENV=production
SECRET_KEY=change-me
APP_NAME=CareWhistle — Finalee 4
# MariaDB/MySQL URL (change if your DB creds differ)
DATABASE_URL=mysql+pymysql://careuser:Spaceship234@127.0.0.1:3306/carewhistle?charset=utf8mb4
# Payments placeholder (0 = disabled)
PAYMENTS_ENABLED=0
STRIPE_SECRET_KEY=
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
'@ | Set-Content -Encoding UTF8 (Join-Path $APPDIR ".env")

# ---------------- static/style.css (light theme) ----------------
@'
:root{
  --ink:#0b132b; --muted:#5b657a; --bg:#f7f9fc; --card:#ffffff; --line:#eef1f6;
  --blue:#1d4ed8; --blue-2:#2563eb; --accent:#0ea5e9; --green:#10b981; --warn:#f59e0b; --danger:#ef4444;
}
*{box-sizing:border-box} html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 Inter,Segoe UI,Roboto,Arial,sans-serif}
a{color:var(--blue-2);text-decoration:none} a:hover{text-decoration:underline}
.container{max-width:1150px;margin:0 auto;padding:22px}
.nav{position:sticky;top:0;background:#fff;border-bottom:1px solid var(--line);display:flex;gap:14px;align-items:center;padding:12px 18px;z-index:20}
.brand{display:flex;gap:10px;align-items:center;font-weight:900;font-size:18px;letter-spacing:.2px}
.whistle{width:28px;height:20px}
.tabs a{padding:8px 12px;border-radius:10px;color:#223}
.tabs a.active,.tabs a:hover{background:#eff3fb}
.btn{display:inline-block;padding:10px 16px;border-radius:12px;background:var(--blue);color:#fff;font-weight:700;border:1px solid #163aa7}
.btn.secondary{background:#fff;color:#223;border:1px solid var(--line)}
.btn.success{background:var(--green)} .btn.warn{background:var(--warn)} .btn.danger{background:var(--danger)}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px;box-shadow:0 6px 16px rgba(10,25,60,.06)}
.grid{display:grid;gap:16px}.grid.cols-4{grid-template-columns:repeat(4,1fr)}.grid.cols-3{grid-template-columns:repeat(3,1fr)}.grid.cols-2{grid-template-columns:repeat(2,1fr)}
@media (max-width:980px){.grid.cols-4,.grid.cols-3{grid-template-columns:1fr}}
.table{width:100%;border-collapse:collapse;font-size:14px}
.table th,.table td{padding:10px 8px;border-bottom:1px solid var(--line);text-align:left}
.input,select,textarea{width:100%;padding:11px 12px;border-radius:12px;border:1px solid var(--line);background:#fff;color:var(--ink)}
.badge{padding:4px 10px;border-radius:999px;background:#e9eefc;color:#274;display:inline-block;font-size:12px;font-weight:800}
.hero h1{font-size:40px;margin:.2rem 0 10px} .hero .lead{color:var(--muted);font-size:18px}
.sidebar{width:250px;background:#fff;border:1px solid var(--line);border-radius:14px;height:fit-content;position:sticky;top:82px}
.sidebar a{display:block;padding:10px 12px;border-radius:10px;color:#223;margin:4px 6px}
.sidebar a.active,.sidebar a:hover{background:#eff3fb}
.layout{display:flex;gap:16px} .main{flex:1}
.kickers{display:flex;gap:10px;flex-wrap:wrap}
.kicker{background:#eff3fb;border:1px solid var(--line);padding:6px 10px;border-radius:999px;font-size:12px;color:#1b3168}
.flash{margin:12px 0;padding:10px 12px;border-radius:10px;background:#f0f5ff;border:1px solid var(--line)}
footer{opacity:.7;padding:32px;text-align:center}
.pricing{display:grid;gap:16px;grid-template-columns:repeat(3,1fr)} @media (max-width:980px){.pricing{grid-template-columns:1fr}}
.plan{border:2px solid var(--blue);border-radius:16px}
.big{font-size:28px;font-weight:900}
'@ | Set-Content -Encoding UTF8 (Join-Path $STAT "style.css")

# ---------------- templates/layout.html ----------------
@'
<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title or settings.get("app_name","CareWhistle") }}</title>
<link rel="stylesheet" href="{{ url_for("static", filename="style.css") }}">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
</head><body>
<div class="nav">
  <a class="brand" href="{{ url_for('home') }}">
    <svg class="whistle" viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path d="M12 40c0-16 13-28 29-28h25a14 14 0 0 1 0 28H49a13 13 0 0 0-13 13v7H28C19 60 12 51 12 40z" fill="#2563eb"/>
      <circle cx="66" cy="34" r="6" fill="#0b132b"/><path d="M86 20c9 2 18 9 20 20-1 14-13 23-22 25 8-10 8-35 2-45z" fill="#0ea5e9"/>
    </svg><span>CareWhistle</span>
  </a>
  <div class="tabs">
    <a href="{{ url_for('home') }}" class="{% if active=='home' %}active{% endif %}">Home</a>
    <a href="{{ url_for('how') }}"  class="{% if active=='how' %}active{% endif %}">How it works</a>
    <a href="{{ url_for('report') }}" class="{% if active=='report' %}active{% endif %}">Make a Report</a>
    <a href="{{ url_for('pricing') }}" class="{% if active=='pricing' %}active{% endif %}">Plans & Pricing</a>
    <a href="{{ url_for('health') }}" class="{% if active=='health' %}active{% endif %}">DB check</a>
  </div>
  <div style="flex:1"></div>
  <div class="tabs">
    <a class="btn secondary" href="{{ url_for('follow') }}">Case Portal</a>
    {% if session.get('user_id') %}
      {% if session.get('role')=='admin' %}<a class="btn secondary" href="{{ url_for('admin_dashboard') }}">Admin</a>
      {% elif session.get('role')=='manager' %}<a class="btn secondary" href="{{ url_for('manager_reports') }}">Manager</a>{% endif %}
      <a class="btn" href="{{ url_for('logout') }}">Logout</a>
    {% else %}<a class="btn" href="{{ url_for('login') }}">Login</a>{% endif %}
  </div>
</div>

{% with msgs = get_flashed_messages(with_categories=True) %}
  {% if msgs %}<div class="container">{% for c,m in msgs %}<div class="flash">{{ m }}</div>{% endfor %}</div>{% endif %}
{% endwith %}

{% block body %}{% endblock %}
<footer>© 2025 CareWhistle • Contact: {{ settings.get('contact_email','info@carewhistle.com') }}</footer>
</body></html>
'@ | Set-Content -Encoding UTF8 (Join-Path $TPL "layout.html")

# ---------------- templates/index.html ----------------
@'
{% extends "layout.html" %}{% block body %}
<div class="container hero">
  <div class="card">
    <h1>One of the most secure Whistleblowing systems in the UK.</h1>
    <p class="lead">Modern, secure and anonymous reporting that protects your company, your staff and your service users.</p>
    <div class="kickers">
      <span class="kicker">Anonymous</span><span class="kicker">Multi-tenant</span><span class="kicker">GDPR-ready</span><span class="kicker">ISO27001-friendly</span>
    </div>
    <p style="margin-top:10px">
      <a class="btn success" href="{{ url_for('report') }}">Make a Report</a>
      <a class="btn secondary" href="{{ url_for('how') }}">How it works</a>
      <a class="btn" href="{{ url_for('pricing') }}">Pricing</a>
    </p>
    {% if settings.get('home_video_url') %}
    <div style="margin-top:14px">
      <iframe style="width:100%;height:420px;border:0;border-radius:12px" src="{{ settings.get('home_video_url') }}" allowfullscreen></iframe>
    </div>
    {% endif %}
  </div>
</div>

<div class="container grid cols-3">
  <div class="card"><h3>Why CareWhistle?</h3><p>Service Commissioners and Regulators expect the highest standards. We enable early, safe reporting so issues are addressed fast and fairly.</p></div>
  <div class="card"><h3>Anonymous & secure</h3><p>Report anonymously or confidentially, get a case code & PIN, and chat through a secure portal.</p></div>
  <div class="card"><h3>Who we help</h3><p>Care providers, supported living & domiciliary care, day services, Ofsted settings, GP & dental practices — and more.</p></div>
</div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $TPL "index.html")

# ---------------- templates/how.html ----------------
@'
{% extends "layout.html" %}{% block body %}
<div class="container">
  <div class="card">
    <h2>How our whistleblowing service works</h2>
    <p>Employees see, hear and experience difficult issues and can be afraid to raise concerns. Early knowledge lets organisations act confidently and effectively.</p>
    <h3>What we provide</h3>
    <ul>
      <li>Free onboarding & set-up, branded posters, unlimited recipients</li>
      <li>Anonymous, password-protected disclosure process, 24/7 reporting</li>
      <li>Secure online portal, trained intake advisors, impartial service</li>
      <li>Strict data standards, toolkit, updates & relationship management</li>
    </ul>
  </div>
</div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $TPL "how.html")

# ---------------- templates/pricing.html ----------------
@'
{% extends "layout.html" %}{% block body %}
<div class="container">
  <h2>Plans & Pricing</h2>
  <div class="pricing">
    <div class="card plan">
      <h2>All-in One</h2>
      <div class="big">£150 <span style="font-size:14px">/ year</span></div>
      <ul>
        <li>Unlimited reports & recipients</li><li>Multi-tenant</li><li>Case portal & chat</li>
        <li>Admin controls & CSV export</li><li>AI triage & insights</li>
      </ul>
      <p><a class="btn" href="{{ url_for('pay') }}">Pay (configure later)</a></p>
    </div>
    <div class="card"><h3>Price Promise</h3><p>The price you see is the price you pay — regardless of how many sites you have.</p></div>
    <div class="card"><h3>Need help?</h3><p>Email <b>{{ settings.get('contact_email','info@carewhistle.com') }}</b></p></div>
  </div>
</div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $TPL "pricing.html")

# ---------------- templates/report.html ----------------
@'
{% extends "layout.html" %}{% block body %}
<div class="container">
  <h2>Submit a report</h2>
  <form method="post" class="grid cols-2 card">
    <div><label>Company ID</label><input class="input" name="company_code" required placeholder="e.g. BC001"></div>
    <div><label>Category</label><select name="category">{% for c in categories %}<option>{{ c }}</option>{% endfor %}</select></div>
    <div><label>Subject</label><input class="input" name="subject" required maxlength="140"></div>
    <div><label>Severity</label><select name="severity">{% for i in range(1,6) %}<option>{{ i }}</option>{% endfor %}</select></div>
    <div style="grid-column:1/-1"><label>Description</label><textarea name="content" rows="6" required></textarea></div>
    <div><label>Stay anonymous?</label><select name="anonymous"><option value="yes">Yes</option><option value="no">No</option></select></div>
    <div><label>Contact (optional)</label><input class="input" name="contact"></div>
    <div style="grid-column:1/-1"><label>Actions taken</label><textarea name="actions_taken" rows="3"></textarea></div>
    <div><label>Feedback after investigation?</label><select name="feedback_opt_in"><option value="yes">Yes</option><option value="no">No</option></select></div>
    <div><label>Memorable word</label><input class="input" name="memorable_word"></div>
    <div><label>Preferred contact</label><input class="input" name="preferred_contact"></div>
    <div><label>Best time to contact</label><input class="input" name="preferred_time"></div>
    <div style="grid-column:1/-1"><button class="btn success">Send report</button></div>
  </form>
</div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $TPL "report.html")

# ---------------- success & follow templates ----------------
@'
{% extends "layout.html" %}{% block body %}
<div class="container card">
  <h2>Report submitted</h2>
  <p>Save your case credentials:</p>
  <p><b>Case code:</b> <code>{{ token }}</code> &nbsp; <b>PIN:</b> <code>{{ pin }}</code> &nbsp; <b>CareWhistle ID:</b> <code>{{ care_id }}</code></p>
  <p><a class="btn" href="{{ url_for('follow') }}">Open the case portal</a></p>
</div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $TPL "report_success.html")

@'
{% extends "layout.html" %}{% block body %}
<div class="container card">
  <h2>Follow your case</h2>
  <form method="post" class="grid cols-3">
    <div><label>Case code</label><input class="input" name="token" required></div>
    <div><label>PIN</label><input class="input" name="pin" required></div>
    <div style="align-self:end"><button class="btn">Open</button></div>
  </form>
</div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $TPL "follow.html")

@'
{% extends "layout.html" %}{% block body %}
<div class="container">
  <h2>Case #{{ r.id }} — {{ r.subject }} <span class="badge">{{ r.status }}</span></h2>
  <div class="card">{% for m in msgs %}
    <div style="margin-bottom:10px"><div style="color:#667">{{ m.created_at }} — {{ m.sender }}</div><div>{{ m.body }}</div></div>
  {% endfor %}</div>
  <form method="post" action="{{ url_for('follow_message', token=r.anon_token) }}" class="card" style="margin-top:12px">
    <label>Send a message to the investigator</label>
    <textarea name="body" rows="3" class="input" required></textarea>
    <div style="margin-top:8px"><button class="btn">Send</button></div>
  </form>
</div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $TPL "follow_thread.html")

# ---------------- auth & errors ----------------
@'
{% extends "layout.html" %}{% block body %}
<div class="container card">
  <h2>Login</h2>
  <form method="post" class="grid cols-2">
    <div><label>Email</label><input class="input" name="email" required value="{{ request.form.email or '' }}"></div>
    <div><label>Password</label><input class="input" type="password" name="password" required></div>
    <div style="grid-column:1/-1"><button class="btn">Login</button></div>
  </form>
</div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $TPL "login.html")

@'
{% extends "layout.html" %}{% block body %}
<div class="container card">
  <h2>Error {{ code }}</h2><p>{{ message }}</p>
</div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $TPL "error.html")

# ---------------- admin templates ----------------
@'
{% extends "layout.html" %}{% block body %}
<div class="layout">
  <div class="sidebar">
    <div style="font-weight:800;margin:10px">Admin</div>
    <a href="{{ url_for('admin_dashboard') }}" class="{% if request.endpoint=='admin_dashboard' %}active{% endif %}">Overview</a>
    <a href="{{ url_for('admin_companies') }}" class="{% if request.endpoint=='admin_companies' %}active{% endif %}">Companies</a>
    <a href="{{ url_for('admin_reports_all') }}" class="{% if request.endpoint=='admin_reports_all' %}active{% endif %}">Reports</a>
    <a href="{{ url_for('admin_users') }}" class="{% if request.endpoint=='admin_users' %}active{% endif %}">Users</a>
    <a href="{{ url_for('admin_settings') }}" class="{% if request.endpoint=='admin_settings' %}active{% endif %}">Settings</a>
  </div>
  <div class="main">{% block admin %}{% endblock %}</div>
</div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $ADMT "frame.html")

@'
{% extends "admin/frame.html" %}{% block admin %}
<h2>Overview</h2>
<div class="grid cols-4">
  <div class="card"><div>New</div><div class="big">{{ stats.new_count or 0 }}</div></div>
  <div class="card"><div>In process</div><div class="big">{{ stats.inproc or 0 }}</div></div>
  <div class="card"><div>Closed</div><div class="big">{{ stats.closed or 0 }}</div></div>
  <div class="card"><div>Avg first response</div><div class="big">{{ avg_response_hours }}h</div></div>
</div>
<h3 style="margin-top:16px">Latest</h3>
<div class="card"><table class="table">
  <tr><th>ID</th><th>CareWhistle ID</th><th>Subject</th><th>Company</th><th>Status</th><th></th></tr>
  {% for r in latest %}
    <tr><td>{{ r.id }}</td><td>{{ r.care_id }}</td><td>{{ r.subject }}</td><td>{{ r.company }}</td><td>{{ r.status }}</td>
      <td><a class="btn secondary" href="{{ url_for('report_detail', rid=r.id) }}">Open</a></td></tr>
  {% endfor %}
</table></div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $ADMT "dashboard.html")

@'
{% extends "admin/frame.html" %}{% block admin %}
<h2>Companies</h2>
<div class="card">
  <form method="post" class="grid cols-4">
    <div><label>Name</label><input class="input" name="name" required></div>
    <div><label>Company ID (5 chars)</label><input class="input" name="code" maxlength="5" required></div>
    <div><label>Country</label><input class="input" name="country"></div>
    <div style="align-self:end"><button class="btn">Add company</button></div>
  </form>
</div>
<div class="card" style="margin-top:12px"><table class="table">
  <tr><th>ID</th><th>Name</th><th>Code</th><th>Country</th><th>Created</th><th></th></tr>
  {% for c in companies %}
    <tr><td>{{ c.id }}</td><td>{{ c.name }}</td><td>{{ c.code }}</td><td>{{ c.country or '' }}</td><td>{{ c.created_at.date() }}</td>
      <td>
        <form method="post" action="{{ url_for('admin_delete_company', company_id=c.id) }}" onsubmit="return confirm('Delete company and its reports?')" style="display:inline">
          <button class="btn danger">Delete</button></form>
      </td></tr>
  {% endfor %}
</table></div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $ADMT "companies.html")

@'
{% extends "admin/frame.html" %}{% block admin %}
<h2>Users</h2>
<div class="card">
  <form method="post" class="grid cols-4">
    <div><label>Email</label><input class="input" name="email" required></div>
    <div><label>Password</label><input class="input" name="password" required></div>
    <div><label>Company (manager)</label>
      <select name="company_id"><option value="">— none —</option>
        {% for c in companies %}<option value="{{ c.id }}">{{ c.name }} ({{ c.code }})</option>{% endfor %}
      </select></div>
    <div style="align-self:end"><button class="btn">Create manager</button></div>
  </form>
</div>
<div class="card" style="margin-top:12px"><table class="table">
  <tr><th>ID</th><th>Email</th><th>Role</th><th>Company</th><th></th></tr>
  {% for u in users %}
  <tr><td>{{ u.id }}</td><td>{{ u.email }}</td><td>{{ u.role }}</td><td>{{ u.company or '' }}</td>
    <td>{% if u.role!='admin' %}
      <form method="post" action="{{ url_for('admin_delete_user', user_id=u.id) }}" onsubmit="return confirm('Delete user?')" style="display:inline">
        <button class="btn danger">Delete</button></form>{% endif %}
    </td></tr>
  {% endfor %}
</table></div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $ADMT "users.html")

@'
{% extends "admin/frame.html" %}{% block admin %}
<h2>Reports</h2>
<div class="card">
  <form class="grid cols-5" method="get">
    <div><label>Search</label><input class="input" name="q" value="{{ q or '' }}"></div>
    <div><label>Company</label><select name="company_id"><option value="">All</option>{% for c in companies %}<option value="{{ c.id }}" {% if c.id|string==company_id %}selected{% endif %}>{{ c.name }}</option>{% endfor %}</select></div>
    <div><label>Status</label><select name="status"><option value="">Any</option>{% for s in STATUSES %}<option value="{{ s }}" {% if s==status %}selected{% endif %}>{{ s }}</option>{% endfor %}</select></div>
    <div><label>Category</label><select name="category"><option value="">Any</option>{% for c in CATEGORIES %}<option {% if c==category %}selected{% endif %}>{{ c }}</option>{% endfor %}</select></div>
    <div style="align-self:end"><button class="btn secondary">Filter</button> <a class="btn" href="{{ url_for('admin_export_csv') }}">Export CSV</a></div>
  </form>
</div>
<div class="card"><table class="table">
  <tr><th>ID</th><th>CareWhistle ID</th><th>Subject</th><th>Company</th><th>Cat</th><th>Sev</th><th>Status</th><th>Created</th><th></th></tr>
  {% for r in rows %}
  <tr><td>{{ r.id }}</td><td>{{ r.care_id }}</td><td>{{ r.subject }}</td><td>{{ r.company }}</td><td>{{ r.category }}</td><td>{{ r.severity }}</td><td>{{ r.status }}</td><td>{{ r.created_at.date() }}</td>
    <td><a class="btn secondary" href="{{ url_for('report_detail', rid=r.id) }}">Open</a></td></tr>
  {% endfor %}
</table></div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $ADMT "reports.html")

@'
{% extends "admin/frame.html" %}{% block admin %}
<h2>Report #{{ r.id }} — {{ r.subject }}</h2>
<div class="grid cols-2">
  <div class="card">
    <div><b>CareWhistle ID:</b> {{ r.care_id }}</div>
    <div><b>Company:</b> {{ r.company.name }} ({{ r.company_code }})</div>
    <div><b>Category:</b> {{ r.category }} • <b>Severity:</b> {{ r.severity }}</div>
    <div><b>Status:</b> {{ r.status }}</div>
    <div><b>Created:</b> {{ r.created_at }}</div>
    <p style="margin-top:10px">{{ r.content }}</p>
    <form method="post" style="margin-top:10px">
      <input type="hidden" name="action" value="status">
      <label>Change status</label>
      <select name="status">{% for s in STATUSES %}<option value="{{ s }}" {% if s==r.status %}selected{% endif %}>{{ s }}</option>{% endfor %}</select>
      <button class="btn secondary" style="margin-top:8px">Update</button>
    </form>
  </div>
  <div class="card">
    <h3>Conversation</h3>
    <div style="max-height:360px;overflow:auto;border:1px solid var(--line);padding:10px;border-radius:10px;background:#fff">
      {% for m in msgs %}
        <div style="margin-bottom:10px"><div style="color:#667">{{ m.created_at }} — {{ m.sender }} {% if m.user %}({{ m.user.email }}){% endif %}</div><div>{{ m.body }}</div></div>
      {% endfor %}
    </div>
    <form method="post" style="margin-top:10px">
      <input type="hidden" name="action" value="message">
      <label>Post a message</label>
      <textarea name="body" rows="3" class="input" required></textarea>
      <button class="btn" style="margin-top:8px">Send</button>
    </form>
  </div>
</div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $ADMT "report_detail.html")

# ---------------- manager templates ----------------
@'
{% extends "layout.html" %}{% block body %}
<div class="container">
  <h2>Reports for your company</h2>
  <div class="card"><table class="table">
    <tr><th>ID</th><th>CareWhistle ID</th><th>Subject</th><th>Category</th><th>Severity</th><th>Status</th><th>Created</th><th></th></tr>
    {% for r in rows %}
      <tr><td>{{ r.id }}</td><td>{{ r.care_id }}</td><td>{{ r.subject }}</td><td>{{ r.category }}</td><td>{{ r.severity }}</td><td>{{ r.status }}</td><td>{{ r.created_at.date() }}</td>
        <td><a class="btn secondary" href="{{ url_for('report_detail', rid=r.id) }}">Open</a></td></tr>
    {% endfor %}
  </table></div>
</div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $MGRT "reports.html")

# ---------------- app.py ----------------
@'
import os, secrets, csv, re
from datetime import datetime, timezone
from io import StringIO
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, Response
from flask_talisman import Talisman
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, select, func, String, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from dotenv import load_dotenv

# Optional AI helpers
try:
    from langdetect import detect as _detect_lang
except Exception:
    _detect_lang = None
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _vader = SentimentIntensityAnalyzer()
except Exception:
    _vader = None

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

APP_NAME   = os.environ.get("APP_NAME","CareWhistle — Finalee 4")
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://careuser:Spaceship234@127.0.0.1:3306/carewhistle?charset=utf8mb4",
)
PAYMENTS_ENABLED = os.environ.get("PAYMENTS_ENABLED","0") == "1"
SECRET_KEY = os.environ.get("SECRET_KEY","change-me")

STATUSES   = ["new","in_review","awaiting_info","resolved","closed"]
CATEGORIES = ["Bribery","Fraud","Harassment","GDPR","Safety","Money laundering","Other"]

class Base(DeclarativeBase): pass

class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(5), nullable=False, unique=True)
    country: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reports: Mapped[list["Report"]] = relationship(back_populates="company")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'admin'|'manager'
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    company: Mapped[Company | None] = relationship()

class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    care_id: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    severity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    company_code: Mapped[str] = mapped_column(String(5), nullable=False)
    reporter_contact: Mapped[str | None] = mapped_column(String(255))
    anon_token: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    anon_pin: Mapped[str] = mapped_column(String(12), nullable=False)
    anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    actions_taken: Mapped[str | None] = mapped_column(Text)
    feedback_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    memorable_word: Mapped[str | None] = mapped_column(String(255))
    preferred_contact: Mapped[str | None] = mapped_column(String(255))
    preferred_time: Mapped[str | None] = mapped_column(String(255))
    assignee_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    company: Mapped[Company] = relationship(back_populates="reports")
    messages: Mapped[list["Message"]] = relationship(back_populates="report", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"))
    sender: Mapped[str] = mapped_column(String(20))  # 'reporter'|'manager'|'admin'
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    report: Mapped[Report] = relationship(back_populates="messages")
    user:   Mapped[User | None] = relationship()

class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text)

gine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=1800)
Session = sessionmaker(bind=engine, expire_on_commit=False)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Security headers (CSP kept permissive for inline CSS/Chart.js)
Talisman(app,
    content_security_policy = {
        "default-src": ["'self'"],
        "style-src": ["'self'","'unsafe-inline'"],
        "script-src": ["'self'","https://cdn.jsdelivr.net"],
        "img-src": ["'self'","data:"]
    },
    force_https = False,  # set True when behind HTTPS
    session_cookie_secure=True,
    session_cookie_http_only=True,
    session_cookie_samesite="Lax"
)

def now_iso(): return datetime.now(timezone.utc).isoformat()

def init_db():
    Base.metadata.create_all(bind=engine)
    with Session() as s:
        # Seed settings
        if not s.get(Setting, "contact_email"):
            s.add_all([
                Setting(key="contact_email", value="info@carewhistle.com"),
                Setting(key="home_video_url", value=""),
                Setting(key="app_name", value=APP_NAME)
            ])
        # Seed demo companies
        if s.query(Company).count()==0:
            s.add_all([
                Company(name="Bright Care", code="BC001", country="UK"),
                Company(name="CycleSoft",  code="CS001", country="US"),
                Company(name="Acme Health",code="AH001", country="DE"),
            ])
        # Seed admin
        if not s.query(User).filter_by(role="admin").first():
            s.add(User(email="info@carewhistle.com",
                       password_hash=generate_password_hash("Aireville122"),
                       role="admin"))
        s.commit()

def settings_dict():
    with Session() as s:
        return {r.key:r.value for r in s.query(Setting).all()}

# ----- AI helpers -----
def detect_language(text:str)->str:
    try:
        if _detect_lang: return _detect_lang(text)
    except Exception: pass
    return "unknown"
def sentiment_label(text:str)->str:
    if _vader:
        sc=_vader.polarity_scores(text)["compound"]
        return "positive" if sc>=.25 else "negative" if sc<=-.25 else "neutral"
    return "neutral"
def pii_hits(text:str)->int:
    hits=0
    hits += len(re.findall(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, flags=re.I))
    hits += len(re.findall(r"\b(\+?\d[\d \-]{8,}\d)\b", text))
    return hits

# ----- Auth utils -----
from functools import wraps
def login_required(f):
    @wraps(f)
    def _w(*a,**k):
        if "user_id" not in session: return redirect(url_for("login", next=request.path))
        return f(*a,**k)
    return _w
def role_required(*roles):
    def deco(f):
        @wraps(f)
        def _w(*a,**k):
            if session.get("role") not in roles: abort(403)
            return f(*a,**k)
        return _w
    return deco

# ----- Public -----
@app.route("/")
def home(): return render_template("index.html", active="home", settings=settings_dict())
@app.route("/how")
def how(): return render_template("how.html", active="how", settings=settings_dict())
@app.route("/pricing")
def pricing(): return render_template("pricing.html", active="pricing", settings=settings_dict())
@app.route("/pay")
def pay():
    return render_template("error.html", code=501, message="Payments not configured. Set STRIPE_* or PAYPAL_* and enable PAYMENTS_ENABLED=1.", settings=settings_dict()), 501

@app.route("/report", methods=["GET","POST"])
def report():
    if request.method=="POST":
        with Session() as s:
            code=(request.form.get("company_code") or "").strip().upper()
            company=s.query(Company).filter_by(code=code).first()
            if not company:
                flash("Unknown Company ID. Please check with your employer.","danger")
                return render_template("report.html", categories=CATEGORIES, active="report", settings=settings_dict())
            subject=(request.form.get("subject") or "").strip()
            content=(request.form.get("content") or "").strip()
            if not subject or not content:
                flash("Subject and description are required.","warning")
                return render_template("report.html", categories=CATEGORIES, active="report", settings=settings_dict())
            category=(request.form.get("category") or "Other").strip()
            severity=int(request.form.get("severity") or 3)
            contact=(request.form.get("contact") or "").strip()
            anonymous=1 if (request.form.get("anonymous") or "yes")=="yes" else 0
            actions=(request.form.get("actions_taken") or "").strip()
            feedback=1 if (request.form.get("feedback_opt_in") or "no")=="yes" else 0
            memorable=(request.form.get("memorable_word") or "").strip()
            pref_contact=(request.form.get("preferred_contact") or "").strip()
            pref_time=(request.form.get("preferred_time") or "").strip()

            token=secrets.token_urlsafe(12)
            pin=f"{secrets.randbelow(900000)+100000}"
            care_id=f"CW{secrets.token_hex(2).upper()}"

            r=Report(care_id=care_id, subject=subject, content=content, category=category, severity=severity,
                     status="new", created_at=datetime.utcnow(), company_id=company.id, company_code=company.code,
                     reporter_contact=contact, anon_token=token, anon_pin=pin, anonymous=bool(anonymous),
                     actions_taken=actions, feedback_opt_in=bool(feedback), memorable_word=memorable,
                     preferred_contact=pref_contact, preferred_time=pref_time)
            s.add(r); s.flush()
            s.add(Message(report_id=r.id, sender="reporter", body="Report submitted.", created_at=datetime.utcnow()))
            # DO NOT auto-assign to manager (per requirement). Admin will triage.
            s.commit()
            flash("Your report has been submitted.","success")
            return render_template("report_success.html", token=token, pin=pin, care_id=care_id, settings=settings_dict())
    return render_template("report.html", categories=CATEGORIES, active="report", settings=settings_dict())

@app.route("/follow", methods=["GET","POST"])
def follow():
    if request.method=="POST":
        token=(request.form.get("token") or "").strip()
        pin=(request.form.get("pin") or "").strip()
        with Session() as s:
            r=s.query(Report).filter_by(anon_token=token, anon_pin=pin).first()
            if r:
                session.setdefault("report_access",{})[token]=pin; session.modified=True
                return redirect(url_for("follow_thread", token=token))
        flash("Invalid code. Check your token and PIN.","danger")
    return render_template("follow.html", settings=settings_dict())

def reporter_access_required(f):
    @wraps(f)
    def _w(token,*a,**k):
        if not session.get("report_access",{}).get(token): return redirect(url_for("follow"))
        return f(token,*a,**k)
    return _w

@app.route("/follow/<token>")
@reporter_access_required
def follow_thread(token):
    with Session() as s:
        r=s.query(Report).join(Company).filter(Report.anon_token==token).first()
        msgs=s.query(Message).filter_by(report_id=r.id).order_by(Message.created_at).all()
        return render_template("follow_thread.html", r=r, msgs=msgs, settings=settings_dict())

@app.route("/follow/<token>/message", methods=["POST"])
@reporter_access_required
def follow_message(token):
    body=(request.form.get("body") or "").strip()
    if body:
        with Session() as s:
            rid=s.query(Report.id).filter_by(anon_token=token).scalar()
            s.add(Message(report_id=rid, sender="reporter", body=body, created_at=datetime.utcnow()))
            s.commit(); flash("Message sent.","success")
    return redirect(url_for("follow_thread", token=token))

# ----- Auth -----
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=(request.form.get("email") or "").strip().lower()
        pw=request.form.get("password") or ""
        with Session() as s:
            u=s.query(User).filter_by(email=email).first()
            if not u or not check_password_hash(u.password_hash, pw):
                flash("Invalid credentials.","danger")
                return render_template("login.html", settings=settings_dict())
            session.update({"user_id":u.id,"email":u.email,"role":u.role,"company_id":u.company_id})
            flash("Welcome back!","success")
            return redirect(url_for("admin_dashboard" if u.role=="admin" else "manager_reports"))
    return render_template("login.html", settings=settings_dict())

@app.route("/logout")
def logout():
    session.clear(); flash("Logged out.","info"); return redirect(url_for("home"))

# ----- Admin -----
@app.route("/admin")
@login_required @role_required("admin")
def admin_dashboard():
    with Session() as s:
        stats=s.query(
            func.sum(func.case((Report.status=="new",1), else_=0)).label("new_count"),
            func.sum(func.case((Report.status.in_(["in_review","awaiting_info"]),1), else_=0)).label("inproc"),
            func.sum(func.case((Report.status.in_(["resolved","closed"]),1), else_=0)).label("closed")
        ).one()
        latest=s.query(Report.id,Report.care_id,Report.subject,Report.status,Company.name.label("company")).join(Company).order_by(Report.created_at.desc()).limit(10).all()
        # avg first response
        total=0; n=0
        for r in s.query(Report).all():
            m=s.query(Message).filter(Message.report_id==r.id, Message.sender.in_(["manager","admin"])).order_by(Message.created_at).first()
            if m: total += (m.created_at - r.created_at).total_seconds()/3600; n+=1
        avg=round(total/n,1) if n else 0
        return render_template("admin/dashboard.html", stats=stats, latest=latest, avg_response_hours=avg, settings=settings_dict())

@app.route("/admin/reports")
@login_required @role_required("admin")
def admin_reports_all():
    q=(request.args.get("q") or "").strip()
    status=request.args.get("status") or ""
    category=request.args.get("category") or ""
    company_id=request.args.get("company_id") or ""
    with Session() as s:
        companies=s.query(Company).order_by(Company.name).all()
        qry=s.query(Report, Company.name.label("company")).join(Company)
        if q:
            like=f"%{q}%"; qry=qry.filter((Report.subject.ilike(like)) | (Report.content.ilike(like)) | (Report.care_id.ilike(like)))
        if status: qry=qry.filter(Report.status==status)
        if category: qry=qry.filter(Report.category==category)
        if company_id: qry=qry.filter(Report.company_id==int(company_id))
        rows=[type("R",(object,),dict(id=r.Report.id, care_id=r.Report.care_id, subject=r.Report.subject, company=r.company,
              category=r.Report.category, severity=r.Report.severity, status=r.Report.status, created_at=r.Report.created_at)) for r in qry.order_by(Report.created_at.desc()).all()]
        return render_template("admin/reports.html", rows=rows, q=q, status=status, category=category, company_id=company_id,
                               companies=companies, STATUSES=STATUSES, CATEGORIES=CATEGORIES, settings=settings_dict())

@app.route("/admin/reports/export")
@login_required @role_required("admin")
def admin_export_csv():
    with Session() as s:
        rows=s.query(Report, Company.name.label("company")).join(Company).order_by(Report.created_at.desc()).all()
    sio=StringIO(); w=csv.writer(sio)
    w.writerow(["id","care_id","subject","content","category","severity","status","created_at","company","company_code"])
    for r in rows:
        R=r.Report; w.writerow([R.id,R.care_id,R.subject,R.content,R.category,R.severity,R.status,R.created_at.isoformat(),r.company,R.company_code])
    return Response(sio.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=reports.csv"})

@app.route("/admin/report/<int:rid>", methods=["GET","POST"])
@login_required @role_required("admin","manager")
def report_detail(rid):
    with Session() as s:
        r=s.query(Report).join(Company).filter(Report.id==rid).first()
        if not r: abort(404)
        if session.get("role")=="manager" and session.get("company_id")!=r.company_id: abort(403)
        if request.method=="POST":
            action=request.form.get("action")
            if action=="status":
                s.query(Report).filter_by(id=rid).update({"status": request.form.get("status","new")})
            elif action=="message":
                body=(request.form.get("body") or "").strip()
                if body: s.add(Message(report_id=rid, sender=session.get("role"), user_id=session.get("user_id"), body=body, created_at=datetime.utcnow()))
            s.commit()
        msgs=s.query(Message).outerjoin(User, User.id==Message.user_id).filter(Message.report_id==rid).order_by(Message.created_at).all()
        return render_template("admin/report_detail.html", r=r, msgs=msgs, STATUSES=STATUSES, settings=settings_dict())

@app.route("/admin/users", methods=["GET","POST"])
@login_required @role_required("admin")
def admin_users():
    with Session() as s:
        if request.method=="POST":
            email=(request.form.get("email") or "").strip().lower()
            pw=request.form.get("password") or ""
            cid=request.form.get("company_id") or None
            cid=int(cid) if cid else None
            if email and pw:
                s.add(User(email=email, password_hash=generate_password_hash(pw), role="manager", company_id=cid))
                s.commit(); flash("Manager created.","success")
        users=(s.query(User, Company.name.label("company")).outerjoin(Company, Company.id==User.company_id)
               .order_by(User.role.desc(), User.email).all())
        companies=s.query(Company).order_by(Company.name).all()
        ux=[type("U",(object,),dict(id=u.User.id,email=u.User.email,role=u.User.role,company=u.company)) for u in users]
        return render_template("admin/users.html", users=ux, companies=companies, settings=settings_dict())

@app.post("/admin/users/delete/<int:user_id>")
@login_required @role_required("admin")
def admin_delete_user(user_id):
    if session.get("user_id")==user_id: flash("You cannot delete yourself.","warning"); return redirect(url_for("admin_users"))
    with Session() as s:
        u=s.get(User,user_id)
        if u and u.role!="admin": s.delete(u); s.commit(); flash("User deleted.","info")
    return redirect(url_for("admin_users"))

@app.route("/admin/companies", methods=["GET","POST"])
@login_required @role_required("admin")
def admin_companies():
    with Session() as s:
        if request.method=="POST":
            name=(request.form.get("name") or "").strip()
            code=(request.form.get("code") or "").strip().upper()
            country=(request.form.get("country") or "").strip()
            if not name or not code or len(code)>5: flash("Name and 5-char Company ID required.","warning")
            else: s.add(Company(name=name, code=code, country=country)); s.commit(); flash("Company added.","success")
        companies=s.query(Company).order_by(Company.name).all()
        return render_template("admin/companies.html", companies=companies, settings=settings_dict())

@app.post("/admin/companies/delete/<int:company_id>")
@login_required @role_required("admin")
def admin_delete_company(company_id):
    with Session() as s:
        c=s.get(Company,company_id)
        if c: s.delete(c); s.commit(); flash("Company deleted (and its reports).","info")
    return redirect(url_for("admin_companies"))

@app.route("/admin/settings", methods=["GET","POST"])
@login_required @role_required("admin")
def admin_settings():
    with Session() as s:
        if request.method=="POST":
            for k in ["contact_email","home_video_url","app_name"]:
                v=(request.form.get(k) or "").strip()
                st=s.get(Setting,k) or Setting(key=k); st.value=v; s.merge(st)
            s.commit(); flash("Saved.","success")
        return render_template("admin/settings.html", settings=settings_dict())

# ----- Manager -----
@app.route("/manager/reports")
@login_required @role_required("manager")
def manager_reports():
    with Session() as s:
        cid=session.get("company_id")
        rows=s.query(Report).filter_by(company_id=cid).order_by(Report.created_at.desc()).all()
        return render_template("manager/reports.html", rows=rows, settings=settings_dict())

# ----- Health -----
@app.route("/health")
def health():
    try:
        with engine.connect() as c:
            c.exec_driver_sql("SELECT 1")
        msg="DB OK (SELECT 1 returned 1)"
    except Exception as e:
        msg=f"DB ERROR: {e}"
    return render_template("index.html", active="health", title="DB check", settings=settings_dict()) \
           + f'<div class="container"><div class="card" style="margin-top:12px">{msg}</div></div>'

# ----- Errors -----
@app.errorhandler(403)
def e403(e): return render_template("error.html", code=403, message="Forbidden", settings=settings_dict()), 403
@app.errorhandler(404)
def e404(e): return render_template("error.html", code=404, message="Not Found", settings=settings_dict()), 404

if __name__=="__main__":
    init_db()
    print(f"Open http://127.0.0.1:8000  (admin: info@carewhistle.com / Aireville122)")
    from waitress import serve
    serve(app, host="127.0.0.1", port=8000)
'@ | Set-Content -Encoding UTF8 (Join-Path $APPDIR "app.py")

# ---------------- tiny admin settings template ----------------
@'
{% extends "admin/frame.html" %}{% block admin %}
<h2>Settings</h2>
<div class="card">
  <form method="post" class="grid cols-2">
    <div><label>Contact email</label><input class="input" name="contact_email" value="{{ settings.get('contact_email','info@carewhistle.com') }}"></div>
    <div><label>Home video URL (embed)</label><input class="input" name="home_video_url" value="{{ settings.get('home_video_url','') }}"></div>
    <div><label>App name</label><input class="input" name="app_name" value="{{ settings.get('app_name','CareWhistle') }}"></div>
    <div style="grid-column:1/-1"><button class="btn">Save</button></div>
  </form>
</div>
{% endblock %}
'@ | Set-Content -Encoding UTF8 (Join-Path $ADMT "settings.html")

# --------------- Print quick DB bootstrap help (optional) ---------------
Write-Host "`n=== Database connection ===" -ForegroundColor Yellow
Write-Host "Using: $(Get-Content (Join-Path $APPDIR '.env') -Raw | Select-String 'DATABASE_URL' )." -ForegroundColor Yellow
Write-Host "If database/user don't exist, open MariaDB client and run:" -ForegroundColor Yellow
Write-Host @"
CREATE DATABASE IF NOT EXISTS carewhistle CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'careuser'@'localhost' IDENTIFIED BY 'Spaceship234';
GRANT ALL PRIVILEGES ON carewhistle.* TO 'careuser'@'localhost';
FLUSH PRIVILEGES;
"@

# --------------- venv + deps ---------------
Set-Location $APPDIR
if (!(Test-Path ".\venv\Scripts\python.exe")) { python -m venv .\venv }
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install --no-cache-dir -r (Join-Path $BASE "requirements.txt")

# --------------- run ---------------
Write-Host "`nOpen http://127.0.0.1:8000   (admin: info@carewhistle.com / Aireville122)" -ForegroundColor Green
$env:FLASK_APP = "app.py"
.\venv\Scripts\python.exe .\app.py
# ===================== end one-paste =====================
