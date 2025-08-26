import os, sqlite3, secrets, random, stripe, paypalrestsdk
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, send_from_directory
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "CareWhistle v78-lite"
BASE_DIR = os.path.dirname(__file__)
DB_PATH  = os.path.join(BASE_DIR, "carewhistle.db")
MEDIA_DIR= os.path.join(BASE_DIR, "media")

STATUSES   = ["new","in_review","awaiting_info","resolved","closed"]
CATEGORIES = ["Bribery","Fraud","Harassment","GDPR","Safety","Money laundering","Other"]

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY","dev-secret-change-me"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=25*1024*1024
)

# --- Stripe ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_dummy")

# --- PayPal ---
paypalrestsdk.configure({
    "mode": "sandbox",  # change to live when ready
    "client_id": os.getenv("PAYPAL_CLIENT_ID", "dummy"),
    "client_secret": os.getenv("PAYPAL_CLIENT_SECRET", "dummy")
})

def now_iso(): return datetime.now(timezone.utc).isoformat()

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    db=get_db(); c=db.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS companies(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      code TEXT UNIQUE NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL CHECK(role IN ('admin','manager')),
      company_id INTEGER,
      created_at TEXT NOT NULL,
      FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS reports(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      company_id INTEGER NOT NULL,
      company_code TEXT NOT NULL,
      subject TEXT,
      content TEXT NOT NULL,
      category TEXT NOT NULL,
      status TEXT NOT NULL,
      reporter_contact TEXT,
      anon_token TEXT UNIQUE NOT NULL,
      anon_pin TEXT NOT NULL,
      created_at TEXT NOT NULL,
      done_so_far TEXT,
      wants_feedback TEXT,
      memorable TEXT,
      FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
    );
    -- messages.channel: 'rep' (admin<->reporter), 'mgr' (admin<->manager)
    CREATE TABLE IF NOT EXISTS messages(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      report_id INTEGER NOT NULL,
      channel TEXT NOT NULL CHECK(channel IN ('rep','mgr')),
      sender TEXT NOT NULL CHECK(sender IN ('admin','manager','reporter')),
      body TEXT NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY(report_id) REFERENCES reports(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS settings(
      key TEXT PRIMARY KEY,
      value TEXT,
      updated_at TEXT NOT NULL
    );
    """)
    # Seed company, admin, manager, demo reports if empty
    if c.execute("SELECT COUNT(*) FROM companies").fetchone()[0]==0:
        for nm in ["Bright Care","CycleSoft","Acme Health"]:
            code = gen_code()
            c.execute("INSERT INTO companies(name,code,created_at) VALUES(?,?,?)",(nm,code,now_iso()))
    if c.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]==0:
        from werkzeug.security import generate_password_hash
        c.execute("INSERT INTO users(email,password_hash,role,company_id,created_at) VALUES(?,?,?,?,?)",
                  ("admin@admin.com", generate_password_hash("password"), "admin", None, now_iso()))
    if c.execute("SELECT COUNT(*) FROM users WHERE role='manager'").fetchone()[0]==0:
        from werkzeug.security import generate_password_hash
        comp = c.execute("SELECT id FROM companies ORDER BY id LIMIT 1").fetchone()
        if comp:
            c.execute("INSERT INTO users(email,password_hash,role,company_id,created_at) VALUES(?,?,?,?,?)",
                      ("manager@brightcare.com", generate_password_hash("manager1"), "manager", comp["id"], now_iso()))
    if c.execute("SELECT COUNT(*) FROM reports").fetchone()[0]==0:
        comps=c.execute("SELECT id,code FROM companies").fetchall()
        for i in range(8):
            cc = comps[i%len(comps)]
            token = secrets.token_urlsafe(10)
            pin   = str(random.randint(100000,999999))
            c.execute("""INSERT INTO reports(company_id,company_code,subject,content,category,status,reporter_contact,anon_token,anon_pin,created_at)
                         VALUES (?,?,?,?,?,?,?,?,?,?)""",
                         (cc["id"], cc["code"], f"Demo subject {i+1}", f"Demo content {i+1}", random.choice(CATEGORIES),
                          random.choice(STATUSES), "", token, pin, now_iso()))
            rid=c.lastrowid
            c.execute("INSERT INTO messages(report_id,channel,sender,body,created_at) VALUES (?,?,?,?,?)",
                      (rid,"rep","reporter","Hello, I want to remain anonymous.", now_iso()))
            c.execute("INSERT INTO messages(report_id,channel,sender,body,created_at) VALUES (?,?,?,?,?)",
                      (rid,"mgr","admin","Manager, we received a report. Please stand by.", now_iso()))
    # settings placeholders
    defaults = {
      "smtp_url":"", "stripe_key":"", "paypal_key":"", "pg_url":"", "mongo_url":"",
      "openai_key":"", "youtube_url":""
    }
    for k,v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings(key,value,updated_at) VALUES(?,?,?)", (k,v,now_iso()))
    db.commit(); db.close()

def gen_code():
    alphabet="ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(5))

# ----------------- auth helpers
def login_required(f):
    @wraps(f)
    def _w(*a,**k):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
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

def current_user():
    if "user_id" not in session: return None
    return {"id":session["user_id"],"email":session["email"],"role":session["role"],"company_id":session.get("company_id")}

def get_setting(key):
    db=get_db(); r=db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone(); db.close()
    return r["value"] if r else ""

def set_setting(key,val):
    db=get_db(); db.execute("REPLACE INTO settings(key,value,updated_at) VALUES(?,?,?)", (key,val,now_iso())); db.commit(); db.close()

# ----------------- routes: public
@app.route("/")
def home():
    return render_template("index.html", title="CareWhistle", youtube_url=get_setting("youtube_url"))

@app.route("/how")
def how(): return render_template("how.html", title="How it works")

@app.route("/pricing")
def pricing(): return render_template("pricing.html", title="Plans & Pricing")


@app.route("/checkout/stripe", methods=["POST"])
def checkout_stripe():
    try:
        session_stripe = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "unit_amount": 15000,
                    "product_data": {"name": "CareWhistle Annual Plan"},
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=url_for("pricing", _external=True) + "?success=1",
            cancel_url=url_for("pricing", _external=True) + "?canceled=1",
        )
        return redirect(session_stripe.url, code=303)
    except Exception as e:
        flash("Stripe error: " + str(e), "danger")
        return redirect(url_for("pricing"))


@app.route("/checkout/paypal", methods=["POST"])
def checkout_paypal():
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": url_for("pricing", _external=True) + "?paypal=success",
            "cancel_url": url_for("pricing", _external=True) + "?paypal=canceled"
        },
        "transactions": [{
            "item_list": {"items": [{
                "name": "CareWhistle Annual Plan",
                "sku": "cw-plan",
                "price": "150.00",
                "currency": "GBP",
                "quantity": 1
            }]},
            "amount": {"total": "150.00", "currency": "GBP"},
            "description": "Annual subscription"
        }]
    })

    if payment.create():
        for link in payment.links:
            if link.method == "REDIRECT":
                return redirect(link.href)
    flash("PayPal error: " + str(payment.error), "danger")
    return redirect(url_for("pricing"))

def make_captcha():
    a,b = random.randint(1,9), random.randint(1,9)
    session["captcha"]=(a,b,a+b); return a,b

@app.route("/report", methods=["GET","POST"])
def report():
    if request.method=="POST":
        a = session.get("captcha",(0,0,0))
        try: ans=int(request.form.get("captcha_answer") or "0")
        except: ans=0
        if ans!=a[2]:
            flash("CAPTCHA wrong. Please try again.","warning"); 
            a,b = make_captcha()
            return render_template("report.html", captcha_a=a, captcha_b=b, categories=CATEGORIES)

        code=(request.form.get("company_code") or "").strip().upper()
        db=get_db()
        comp=db.execute("SELECT id,code FROM companies WHERE code=?", (code,)).fetchone()
        if not comp:
            db.close(); flash("Invalid Company Code.","danger")
            a,b = make_captcha()
            return render_template("report.html", captcha_a=a, captcha_b=b, categories=CATEGORIES)

        subject=(request.form.get("subject") or "").strip()
        content=(request.form.get("content") or "").strip()
        category=(request.form.get("category") or "Other").strip()
        contact=(request.form.get("contact") or "").strip()
        done_so_far=(request.form.get("done_so_far") or "").strip()
        wants_feedback=(request.form.get("wants_feedback") or "").strip()
        memorable=(request.form.get("memorable") or "").strip()

        if not content:
            db.close(); flash("Please describe your concern.","warning")
            a,b = make_captcha()
            return render_template("report.html", captcha_a=a, captcha_b=b, categories=CATEGORIES)

        token=secrets.token_urlsafe(12); pin=f"{secrets.randbelow(900000)+100000}"
        db.execute("""INSERT INTO reports(company_id,company_code,subject,content,category,status,reporter_contact,anon_token,anon_pin,created_at,done_so_far,wants_feedback,memorable)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                   (comp["id"], comp["code"], subject, content, category, "new", contact, token, pin, now_iso(), done_so_far, wants_feedback, memorable))
        rid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("INSERT INTO messages(report_id,channel,sender,body,created_at) VALUES (?,?,?,?,?)",
                   (rid,"rep","reporter","Report submitted.", now_iso()))
        db.execute("INSERT INTO messages(report_id,channel,sender,body,created_at) VALUES (?,?,?,?,?)",
                   (rid,"mgr","admin","We received a report for your company. Admin will update you here.", now_iso()))
        db.commit(); db.close()
        return render_template("report_success.html", token=token, pin=pin)
    a,b = make_captcha()
    return render_template("report.html", captcha_a=a, captcha_b=b, categories=CATEGORIES)

@app.route("/follow", methods=["GET","POST"])
def follow():
    if request.method=="POST":
        token=(request.form.get("token") or "").strip(); pin=(request.form.get("pin") or "").strip()
        db=get_db(); r=db.execute("SELECT * FROM reports WHERE anon_token=? AND anon_pin=?", (token,pin)).fetchone(); db.close()
        if not r:
            flash("Invalid code.","danger"); return render_template("follow.html")
        session.setdefault("report_access",{})[token]=pin; session.modified=True
        return redirect(url_for("follow_thread", token=token))
    return render_template("follow.html")

def reporter_access_required(f):
    @wraps(f)
    def _w(token,*a,**k):
        if not session.get("report_access",{}).get(token): return redirect(url_for("follow"))
        return f(token,*a,**k)
    return _w

@app.route("/follow/<token>")
@reporter_access_required
def follow_thread(token):
    db=get_db()
    r=db.execute("SELECT id,company_code,anon_token,status FROM reports WHERE anon_token=?", (token,)).fetchone()
    msgs=db.execute("SELECT created_at,sender,body FROM messages WHERE report_id=? AND channel='rep' ORDER BY id", (r["id"],)).fetchall()
    db.close()
    return render_template("follow_thread.html", r=r, msgs=msgs)

@app.route("/follow/<token>/message", methods=["POST"])
@reporter_access_required
def follow_message(token):
    body=(request.form.get("body") or "").strip()
    if not body: return redirect(url_for("follow_thread", token=token))
    db=get_db(); rid=db.execute("SELECT id FROM reports WHERE anon_token=?", (token,)).fetchone()["id"]
    db.execute("INSERT INTO messages(report_id,channel,sender,body,created_at) VALUES (?,?,?,?,?)", (rid,"rep","reporter",body,now_iso()))
    db.commit(); db.close()
    flash("Message sent.","success")
    return redirect(url_for("follow_thread", token=token))

# ----------------- auth
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        from werkzeug.security import check_password_hash
        email=(request.form.get("email") or "").strip().lower()
        pw   =(request.form.get("password") or "")
        db=get_db(); u=db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone(); db.close()
        if not u or not check_password_hash(u["password_hash"], pw):
            flash("Invalid credentials.","danger"); return render_template("login.html")
        session.update({"user_id":u["id"],"email":u["email"],"role":u["role"],"company_id":u["company_id"]})
        return redirect(url_for("admin_dashboard" if u["role"]=="admin" else "manager_overview"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); flash("Logged out.","info"); return redirect(url_for("home"))

# ----------------- admin
@app.route("/admin")
@login_required
@role_required("admin")
def admin_dashboard():
    db=get_db()
    stats=db.execute("""
      SELECT
        SUM(CASE WHEN status='new' THEN 1 ELSE 0 END) as new,
        SUM(CASE WHEN status IN ('in_review','awaiting_info') THEN 1 ELSE 0 END) as inproc,
        SUM(CASE WHEN status IN ('resolved','closed') THEN 1 ELSE 0 END) as closed
      FROM reports
    """).fetchone()
    monthly=db.execute("SELECT substr(created_at,1,7) ym, COUNT(*) cnt FROM reports GROUP BY ym ORDER BY ym").fetchall()
    bycat=db.execute("SELECT category, COUNT(*) cnt FROM reports GROUP BY category ORDER BY cnt DESC").fetchall()
    bystatus=db.execute("SELECT status, COUNT(*) cnt FROM reports GROUP BY status").fetchall()
    companies=db.execute("""
      SELECT c.id,c.name,c.code,
        SUM(CASE WHEN r.status='new' THEN 1 ELSE 0 END) newc,
        SUM(CASE WHEN r.status IN ('in_review','awaiting_info') THEN 1 ELSE 0 END) inpc,
        SUM(CASE WHEN r.status IN ('resolved','closed') THEN 1 ELSE 0 END) clos
      FROM companies c LEFT JOIN reports r ON r.company_id=c.id GROUP BY c.id ORDER BY c.name
    """).fetchall()
    # avg first response
    rs=db.execute("SELECT id,created_at FROM reports").fetchall()
    import datetime as dt
    total=0; n=0
    for r in rs:
        m=db.execute("SELECT created_at FROM messages WHERE report_id=? AND sender IN ('admin','manager') ORDER BY id LIMIT 1",(r["id"],)).fetchone()
        if m:
            t0=dt.datetime.fromisoformat(r["created_at"]); t1=dt.datetime.fromisoformat(m["created_at"])
            total += (t1-t0).total_seconds()/3600; n+=1
    avg_hours=round(total/n,1) if n else 0
    db.close()
    return render_template("admin/dashboard.html", stats=stats, monthly=monthly, bycat=bycat, bystatus=bystatus, companies=companies, avg_hours=avg_hours)

@app.route("/admin/companies", methods=["GET","POST"])
@login_required
@role_required("admin")
def admin_companies():
    db=get_db()
    if request.method=="POST":
        name=(request.form.get("name") or "").strip()
        code=(request.form.get("code") or "").strip().upper()
        if not code: code=gen_code()
        try:
            db.execute("INSERT INTO companies(name,code,created_at) VALUES(?,?,?)",(name,code,now_iso()))
            db.commit(); flash("Company added.","success")
        except sqlite3.IntegrityError:
            flash("Company code already exists.","danger")
        return redirect(url_for("admin_companies"))
    companies=db.execute("SELECT * FROM companies ORDER BY name").fetchall()
    db.close()
    return render_template("admin/companies.html", companies=companies)

@app.route("/admin/company/<int:company_id>")
@login_required
@role_required("admin")
def admin_company(company_id):
    db=get_db()
    c=db.execute("SELECT * FROM companies WHERE id=?", (company_id,)).fetchone()
    if not c: abort(404)
    stats=db.execute("""
      SELECT
        SUM(CASE WHEN status='new' THEN 1 ELSE 0 END) as new,
        SUM(CASE WHEN status IN ('in_review','awaiting_info') THEN 1 ELSE 0 END) as inproc,
        SUM(CASE WHEN status IN ('resolved','closed') THEN 1 ELSE 0 END) as closed
      FROM reports WHERE company_id=?
    """,(company_id,)).fetchone()
    monthly=db.execute("SELECT substr(created_at,1,7) ym, COUNT(*) cnt FROM reports WHERE company_id=? GROUP BY ym ORDER BY ym",(company_id,)).fetchall()
    bycat=db.execute("SELECT category, COUNT(*) cnt FROM reports WHERE company_id=? GROUP BY category ORDER BY cnt DESC",(company_id,)).fetchall()
    recent=db.execute("SELECT id,status,created_at FROM reports WHERE company_id=? ORDER BY id DESC LIMIT 12",(company_id,)).fetchall()
    db.close()
    return render_template("admin/company_dashboard.html", company=c, stats=stats, monthly=monthly, bycat=bycat, recent=recent)

@app.route("/admin/company/<int:company_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def admin_company_delete(company_id):
    db=get_db(); db.execute("DELETE FROM companies WHERE id=?", (company_id,)); db.commit(); db.close()
    flash("Company deleted (with its reports).","info")
    return redirect(url_for("admin_companies"))

@app.route("/admin/reports")
@login_required
@role_required("admin")
def admin_reports():
    q=(request.args.get("q") or "").strip()
    status=(request.args.get("status") or "")
    category=(request.args.get("category") or "")
    code=(request.args.get("company_code") or "").strip().upper()
    args=[]; sql="SELECT id,company_code,category,status,created_at FROM reports WHERE 1=1"
    if q: sql+=" AND (subject LIKE ? OR content LIKE ?)"; args += [f"%{q}%",f"%{q}%"]
    if status: sql+=" AND status=?"; args.append(status)
    if category: sql+=" AND category=?"; args.append(category)
    if code: sql+=" AND company_code=?"; args.append(code)
    sql+=" ORDER BY id DESC"
    db=get_db(); rows=db.execute(sql, tuple(args)).fetchall(); db.close()
    return render_template("admin/reports.html", rows=rows, q=q, status=status, category=category, company_code=code, categories=CATEGORIES, statuses=STATUSES)

@app.route("/admin/report/<int:rid>", methods=["GET","POST"])
@login_required
@role_required("admin")
def admin_report_detail(rid):
    db=get_db()
    r=db.execute("SELECT * FROM reports WHERE id=?", (rid,)).fetchone()
    if not r: abort(404)
    if request.method=="POST":
        act=request.form.get("action")
        if act=="status":
            s=(request.form.get("status") or r["status"]).strip()
            if s in STATUSES: db.execute("UPDATE reports SET status=? WHERE id=?", (s,rid))
        elif act=="msg_rep":
            body=(request.form.get("body") or "").strip()
            if body: db.execute("INSERT INTO messages(report_id,channel,sender,body,created_at) VALUES (?,?,?,?,?)", (rid,"rep","admin",body,now_iso()))
        elif act=="msg_mgr":
            body=(request.form.get("body") or "").strip()
            if body: db.execute("INSERT INTO messages(report_id,channel,sender,body,created_at) VALUES (?,?,?,?,?)", (rid,"mgr","admin",body,now_iso()))
        db.commit()
    msgs_rep=db.execute("SELECT created_at,sender,body FROM messages WHERE report_id=? AND channel='rep' ORDER BY id",(rid,)).fetchall()
    msgs_mgr=db.execute("SELECT created_at,sender,body FROM messages WHERE report_id=? AND channel='mgr' ORDER BY id",(rid,)).fetchall()
    db.close()
    return render_template("admin/report_detail.html", r=r, msgs_rep=msgs_rep, msgs_mgr=msgs_mgr, statuses=STATUSES)

@app.route("/admin/users", methods=["GET","POST"])
@login_required
@role_required("admin")
def admin_users():
    db=get_db()
    if request.method=="POST":
        from werkzeug.security import generate_password_hash
        email=(request.form.get("email") or "").strip().lower()
        pw=(request.form.get("password") or "")
        cid=request.form.get("company_id") or ""
        try: cid=int(cid) if cid else None
        except: cid=None
        if not email or not pw:
            flash("Email & password required.","warning"); return redirect(url_for("admin_users"))
        try:
            db.execute("INSERT INTO users(email,password_hash,role,company_id,created_at) VALUES (?,?,?,?,?)",
                       (email, generate_password_hash(pw), "manager", cid, now_iso()))
            db.commit(); flash("Manager created.","success")
        except sqlite3.IntegrityError: flash("Email already exists.","danger")
        return redirect(url_for("admin_users"))
    users=db.execute("""SELECT u.id,u.email,u.role,u.company_id,c.name as company,c.code FROM users u
                        LEFT JOIN companies c ON c.id=u.company_id
                        ORDER BY (u.role='admin') DESC, u.email""").fetchall()
    companies=db.execute("SELECT id,name,code FROM companies ORDER BY name").fetchall()
    db.close()
    return render_template("admin/users.html", users=users, companies=companies)

@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def admin_user_delete(user_id):
    if session.get("user_id")==user_id:
        flash("You cannot delete yourself.","warning"); return redirect(url_for("admin_users"))
    db=get_db(); db.execute("DELETE FROM users WHERE id=? AND role!='admin'",(user_id,)); db.commit(); db.close()
    flash("User deleted.","info"); return redirect(url_for("admin_users"))

@app.route("/admin/media", methods=["GET","POST"])
@login_required
@role_required("admin")
def admin_media():
    if request.method=="POST":
        f=request.files.get("file")
        if f and f.filename:
            name=os.path.basename(f.filename)
            safe="".join(ch for ch in name if ch.isalnum() or ch in "._-")
            f.save(os.path.join(MEDIA_DIR, safe))
            flash("Uploaded.","success")
        return redirect(url_for("admin_media"))
    files=sorted([fn for fn in os.listdir(MEDIA_DIR) if os.path.isfile(os.path.join(MEDIA_DIR,fn))])
    return render_template("admin/media.html", files=files)

@app.route("/admin/media/delete/<path:fname>", methods=["POST"])
@login_required
@role_required("admin")
def admin_media_delete(fname):
    p=os.path.join(MEDIA_DIR, os.path.basename(fname))
    if os.path.exists(p): os.remove(p); flash("Deleted.","info")
    return redirect(url_for("admin_media"))

@app.route("/media/<path:filename>")
def media_file(filename):
    return send_from_directory(MEDIA_DIR, filename)

@app.route("/admin/settings", methods=["GET","POST"])
@login_required
@role_required("admin")
def admin_settings():
    if request.method=="POST":
        for k in ["smtp_url","stripe_key","paypal_key","pg_url","mongo_url","openai_key","youtube_url"]:
            set_setting(k, request.form.get(k) or "")
        flash("Saved.","success"); return redirect(url_for("admin_settings"))
    settings={k:get_setting(k) for k in ["smtp_url","stripe_key","paypal_key","pg_url","mongo_url","openai_key","youtube_url"]}
    return render_template("admin/settings.html", settings=settings)

@app.route("/admin/notifications")
@login_required
@role_required("admin")
def admin_notifications():
    notes=[]
    db=get_db()
    new=db.execute("SELECT COUNT(*) c FROM reports WHERE status='new'").fetchone()["c"]
    if new: notes.append(f"{new} report(s) are new.")
    db.close()
    return render_template("admin/notifications.html", notes=notes)

# ----------------- manager
@app.route("/manager")
@login_required
@role_required("manager")
def manager_overview():
    cid=session.get("company_id")
    db=get_db()
    stats=db.execute("""
      SELECT
        SUM(CASE WHEN status='new' THEN 1 ELSE 0 END) as new,
        SUM(CASE WHEN status IN ('in_review','awaiting_info') THEN 1 ELSE 0 END) as inproc,
        SUM(CASE WHEN status IN ('resolved','closed') THEN 1 ELSE 0 END) as closed,
        (SELECT COUNT(*) FROM reports WHERE company_id=?) as assigned
    """,(cid,)).fetchone()
    monthly=db.execute("SELECT substr(created_at,1,7) ym, COUNT(*) cnt FROM reports WHERE company_id=? GROUP BY ym ORDER BY ym",(cid,)).fetchall()
    bycat=db.execute("SELECT category, COUNT(*) cnt FROM reports WHERE company_id=? GROUP BY category ORDER BY cnt DESC",(cid,)).fetchall()
    db.close()
    return render_template("manager/overview.html", stats=stats, monthly=monthly, bycat=bycat)

@app.route("/manager/messages")
@login_required
@role_required("manager")
def manager_messages():
    cid=session.get("company_id"); db=get_db()
    rows=db.execute("""SELECT r.id, r.company_code, MAX(m.created_at) AS updated
                       FROM reports r LEFT JOIN messages m ON m.report_id=r.id AND m.channel='mgr'
                       WHERE r.company_id=? GROUP BY r.id ORDER BY r.id DESC""",(cid,)).fetchall()
    db.close()
    return render_template("manager/messages.html", reports=rows)

@app.route("/manager/messages/<int:rid>", methods=["GET","POST"])
@login_required
@role_required("manager")
def manager_messages_thread(rid):
    cid=session.get("company_id")
    db=get_db()
    r=db.execute("SELECT id,company_id,company_code FROM reports WHERE id=?", (rid,)).fetchone()
    if not r or r["company_id"]!=cid: db.close(); abort(403)
    if request.method=="POST":
        body=(request.form.get("body") or "").strip()
        if body: db.execute("INSERT INTO messages(report_id,channel,sender,body,created_at) VALUES (?,?,?,?,?)",(rid,"mgr","manager",body,now_iso())); db.commit()
    msgs=db.execute("SELECT created_at,sender,body FROM messages WHERE report_id=? AND channel='mgr' ORDER BY id",(rid,)).fetchall()
    db.close()
    return render_template("manager/messages_thread.html", rid=rid, company_code=r["company_code"], msgs=msgs)

@app.route("/manager/notifications")
@login_required
@role_required("manager")
def manager_notifications():
    notes=[]
    cid=session.get("company_id"); db=get_db()
    cnt=db.execute("""SELECT COUNT(*) c FROM messages m JOIN reports r ON r.id=m.report_id
                      WHERE r.company_id=? AND m.channel='mgr' AND m.sender='admin'
                      AND datetime(m.created_at) > datetime('now','-7 day')""",(cid,)).fetchone()["c"]
    if cnt: notes.append(f"{cnt} new admin message(s) in last 7 days.")
    db.close()
    return render_template("manager/notifications.html", notes=notes)

# ----------------- errors
@app.errorhandler(403)
def e403(e): return render_template("error.html", code=403, message="Forbidden"), 403
@app.errorhandler(404)
def e404(e): return render_template("error.html", code=404, message="Not Found"), 404

if __name__=="__main__":
    os.makedirs(MEDIA_DIR, exist_ok=True)
    init_db()
    app.run(debug=True)
