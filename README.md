# Titans Fitness Studio 🏋️

A full-stack gym management web app with role-based dashboards and an AI fitness assistant (FitBuddy).

---

## What does this project do?

| Feature | Description |
|---|---|
| **Login / Signup** | Members, trainers, and admins all log in through the same page and get sent to their own dashboard |
| **Member Dashboard** | Track workouts, water intake, calories, and studio classes |
| **Trainer Dashboard** | View client roster, today's sessions, and assign workout routines |
| **Admin Dashboard** | See revenue stats, member count, and equipment maintenance tickets |
| **FitBuddy AI** | A chat assistant powered by a local Ollama LLM (falls back to smart offline replies) |

---

## Project Structure

```
html-ca/
│
├── main.py                  ← App entry point. Starts the server.
├── .env                     ← Your environment variables (DEMO, OLLAMA_MODEL)
├── requirements.txt         ← All Python packages needed
├── feedback.json            ← Static feedback data shown on the homepage
│
├── static/                  ← All HTML, CSS, and JS files served to the browser
│   ├── index.html           ← Homepage
│   ├── login.html           ← Login page
│   ├── signup.html          ← Signup page
│   ├── member-dashboard.html
│   ├── trainer-dashboard.html
│   ├── admin-dashboard.html
│   ├── script.js            ← Shared JavaScript (login form, signup form, feedback cards)
│   └── background.jpg       ← Gym background image
│
├── app/
│   ├── api/                 ← API endpoints (what the frontend talks to)
│   │   ├── auth.py          ← /api/login, /api/signup, /api/demo-mode
│   │   ├── chat.py          ← /api/chat  (FitBuddy AI)
│   │   ├── member.py        ← /api/member (dashboard data)
│   │   ├── trainer.py       ← /api/trainer
│   │   └── admin.py         ← /api/admin
│   │
│   ├── core/
│   │   └── db.py            ← Database logic (SQLite). All table creation and queries.
│   │
│   └── agent/               ← FitBuddy AI brain
│       ├── runner.py        ← Streams replies from Ollama; falls back offline
│       ├── prompt_builder.py← Builds the system prompt from Markdown files
│       ├── IDENTITY.md      ← Who FitBuddy is
│       ├── SOUL.md          ← FitBuddy's personality and tone
│       ├── TOOLS.md         ← Tools FitBuddy can call (e.g. log injury)
│       └── USER.md          ← Rules for how FitBuddy talks to different roles
│
└── data/
    └── users/
        └── users.db         ← SQLite database file (auto-created on first run)
```

---

## How to Run Locally

### 1. Install Python packages

```bash
pip install -r requirements.txt
```

### 2. Set up your environment

The `.env` file is already in the project. Open it and check the `DEMO` setting:

```
DEMO=on   ← shows demo quick-fill buttons on the login page
```

### 3. Start the server

```bash
uvicorn main:app --reload
```

Then open your browser at **http://localhost:8000**

> `--reload` means the server restarts automatically when you save a file. Very useful while developing!

---

## Environment Variables (`.env`)

| Variable | Values | What it does |
|---|---|---|
| `DEMO` | `on` / `off` | **on** shows quick-fill login buttons and allows demo admin shortcut. **off** is production mode — only real database users can log in. |
| `OLLAMA_MODEL` | e.g. `qwen2.5:3b` | Forces a specific AI model. Leave blank to auto-detect. |

> ⚠️ **Never commit your `.env` file to Git.** It is already listed in `.gitignore`.

---

## Demo Accounts (only visible when `DEMO=on`)

| Role | Email | Password |
|---|---|---|
| Admin | `admin@123` | `gym123` |
| Member | `rohan.sharma@gmail.com` | `gym123` |
| Trainer | `ananya.verma@titans.com` | `gym123` |

---

## How the Login Flow Works

```
Browser (login.html)
      │
      │  POST /api/login  { email, password }
      ▼
FastAPI (auth.py)
      │
      │  db.verify_login(email, password)
      ▼
SQLite (users.db)
      │
      │  Returns user row if password matches
      ▼
FastAPI sends back:
  { redirect_url: "/member-dashboard.html" }
      │
      ▼
Browser redirects to the correct dashboard
```

---

## How the Database Works (`db.py`)

Everything is stored in a single SQLite file (`data/users/users.db`).

**Tables:**

| Table | Stores |
|---|---|
| `users` | Accounts (username, email, hashed password, role) |
| `member_profiles` | Member stats (streak, water, calories, plan) |
| `member_workouts` | Each member's exercise list |
| `studio_classes` | Upcoming group classes |
| `trainer_clients` | Clients assigned to each trainer |
| `trainer_sessions` | Trainer's daily schedule |
| `maintenance_tickets` | Gym equipment status |
| `assigned_routines` | Routines pushed by trainers to clients |

**Passwords** are hashed with SHA-256 before being saved — they are never stored as plain text.

---

## How the AI Assistant Works (`app/agent/`)

```
User types a message in the dashboard
      │
      │  POST /api/chat  { message, user_name, user_role }
      ▼
runner.py
      │
      ├── Is Ollama running locally?
      │       YES → stream reply from the LLM model
      │       NO  → use the offline fallback engine (pre-written smart replies)
      │
      └── Did the model call a tool?
              YES → run the tool (e.g. log_member_injury), send result back to model
              NO  → stream the reply directly to the browser
```

The AI's personality comes from 4 Markdown files in `app/agent/`:
- **IDENTITY.md** — who FitBuddy is
- **SOUL.md** — how it talks (tone, style)
- **USER.md** — rules per role (member vs trainer vs admin)
- **TOOLS.md** — what actions it can trigger in the backend

---

## API Endpoints Quick Reference

| Method | URL | What it does |
|---|---|---|
| POST | `/api/login` | Log in a user |
| POST | `/api/signup` | Create a new account |
| GET | `/api/demo-mode` | Returns `{ demo: true/false }` — used by the login page |
| POST | `/api/chat` | Send a message to FitBuddy |
| GET | `/api/member` | Get member dashboard data |
| GET | `/api/trainer` | Get trainer dashboard data |
| GET | `/api/admin` | Get admin dashboard data |
| GET | `/api/feedback` | Get testimonial feedback cards |

You can explore all endpoints interactively at **http://localhost:8000/docs**

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Database | SQLite (via Python's built-in `sqlite3`) |
| Frontend | HTML, CSS, Vanilla JavaScript |
| AI | Ollama (local LLM, e.g. Qwen 2.5) |
| Server | Uvicorn (ASGI server) |
