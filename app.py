import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

DB_PATH = os.path.join(os.path.dirname(__file__), "carewhistle.db")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="dev-secret")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    db = get_db()
    c = db.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS companies(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            company_id INTEGER,
            created_at TEXT NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS reports(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            company_code TEXT NOT NULL,
            subject TEXT,
            content TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL,
            reporter_contact TEXT,
            anon_token TEXT NOT NULL,
            anon_pin TEXT NOT NULL,
            created_at TEXT NOT NULL,
            manager_id INTEGER
        )
        """
    )
    # Seed data if empty
    if c.execute("SELECT COUNT(*) FROM companies").fetchone()[0] == 0:
        c.execute(
            "INSERT INTO companies(name, code, created_at) VALUES (?,?,?)",
            ("Bright Care", "BRIGHT", now_iso()),
        )
    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        comp_id = c.execute("SELECT id FROM companies LIMIT 1").fetchone()[0]
        c.execute(
            "INSERT INTO users(email,password,role,company_id,created_at) VALUES (?,?,?,?,?)",
            ("admin@admin.com", "password", "admin", None, now_iso()),
        )
        c.execute(
            "INSERT INTO users(email,password,role,company_id,created_at) VALUES (?,?,?,?,?)",
            ("manager@brightcare.com", "manager1", "manager", comp_id, now_iso()),
        )
    if c.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 0:
        comp = c.execute("SELECT id, code FROM companies LIMIT 1").fetchone()
        c.execute(
            """
            INSERT INTO reports(
                company_id, company_code, subject, content, category, status,
                reporter_contact, anon_token, anon_pin, created_at, manager_id
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                comp["id"],
                comp["code"],
                "Demo subject",
                "Demo content",
                "Other",
                "new",
                "",
                "token",
                "123456",
                now_iso(),
                None,
            ),
        )
    db.commit()
    db.close()


init_db()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/how", response_class=HTMLResponse)
async def how(request: Request):
    return templates.TemplateResponse("how.html", {"request": request})


@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    db = get_db()
    user = db.execute(
        "SELECT id, role, company_id, password FROM users WHERE email=?", (email,)
    ).fetchone()
    db.close()
    if user and user["password"] == password:
        request.session["user_id"] = user["id"]
        request.session["role"] = user["role"]
        request.session["company_id"] = user["company_id"]
        return HTMLResponse("Overview")
    return HTMLResponse("Invalid credentials", status_code=401)


@app.get("/report", response_class=HTMLResponse)
async def report_form(request: Request):
    return templates.TemplateResponse("report.html", {"request": request})


@app.get("/follow", response_class=HTMLResponse)
async def follow_form(request: Request):
    return templates.TemplateResponse("follow.html", {"request": request})


@app.get("/follow/{token}", response_class=HTMLResponse)
async def follow_thread(request: Request, token: str):
    return templates.TemplateResponse("follow_thread.html", {"request": request, "token": token})


@app.get("/manager/messages", response_class=HTMLResponse)
async def manager_messages(request: Request):
    if request.session.get("role") != "manager":
        return HTMLResponse(status_code=403)
    uid = request.session.get("user_id")
    db = get_db()
    count = db.execute(
        "SELECT COUNT(*) FROM reports WHERE manager_id=?", (uid,)
    ).fetchone()[0]
    db.close()
    if count:
        return HTMLResponse("Open")
    return HTMLResponse("")


@app.post("/admin/report/{rid}", response_class=HTMLResponse)
async def admin_report(
    request: Request,
    rid: int,
    action: str = Form(...),
    manager_id: int = Form(...),
):
    if request.session.get("role") != "admin":
        return HTMLResponse(status_code=403)
    if action == "assign":
        db = get_db()
        db.execute("UPDATE reports SET manager_id=? WHERE id=?", (manager_id, rid))
        db.commit()
        db.close()
    return HTMLResponse("OK")


@app.post("/chatbot")
async def chatbot(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}
    message = data.get("message") if isinstance(data, dict) else None
    if not message:
        return JSONResponse({"reply": "Please say something."})
    if message.lower() == "how do i file a report?":
        return JSONResponse({"reply": "Go to the Make a Report page"})
    reply = (
        "For whistleblowing questions, please consult our guidelines. You said: "
        f"{message}"
    )
    return JSONResponse({"reply": reply})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
