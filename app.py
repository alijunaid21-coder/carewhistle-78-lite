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
DATABASE_URL = os.environ.get("DATABASE_URL","mysql+pymysql://careuser:Spaceship234@127.0.0.1:3306/carewhistle?charset=utf8mb4")
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

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=1800)
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
@login_required
@role_required("admin")
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
@login_required
@role_required("admin")
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
@login_required
@role_required("admin")
def admin_export_csv():
    with Session() as s:
        rows=s.query(Report, Company.name.label("company")).join(Company).order_by(Report.created_at.desc()).all()
    sio=StringIO(); w=csv.writer(sio)
    w.writerow(["id","care_id","subject","content","category","severity","status","created_at","company","company_code"])
    for r in rows:
        R=r.Report; w.writerow([R.id,R.care_id,R.subject,R.content,R.category,R.severity,R.status,R.created_at.isoformat(),r.company,R.company_code])
    return Response(sio.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=reports.csv"})

@app.route("/admin/report/<int:rid>", methods=["GET","POST"])
@login_required
@role_required("admin","manager")
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
@login_required
@role_required("admin")
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
@login_required
@role_required("admin")
def admin_delete_user(user_id):
    if session.get("user_id")==user_id: flash("You cannot delete yourself.","warning"); return redirect(url_for("admin_users"))
    with Session() as s:
        u=s.get(User,user_id)
        if u and u.role!="admin": s.delete(u); s.commit(); flash("User deleted.","info")
    return redirect(url_for("admin_users"))

@app.route("/admin/companies", methods=["GET","POST"])
@login_required
@role_required("admin")
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
@login_required
@role_required("admin")
def admin_delete_company(company_id):
    with Session() as s:
        c=s.get(Company,company_id)
        if c: s.delete(c); s.commit(); flash("Company deleted (and its reports).","info")
    return redirect(url_for("admin_companies"))

@app.route("/admin/settings", methods=["GET","POST"])
@login_required
@role_required("admin")
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
@login_required
@role_required("manager")
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
