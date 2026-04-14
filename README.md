## EventSphere (Beginner)

Backend: FastAPI + Postgres (raw SQL).  
Frontend: plain HTML/CSS/JS.

### 1) Database

Create DB + import dump:

```powershell
psql -U postgres -c "CREATE DATABASE eventsphere;"
psql -U postgres -d eventsphere -f "database\\db.sql"
```

### 2) Backend

Copy `.env.example` to `.env` and set values.

Install + run:

```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3) Frontend

```powershell
cd frontend
python -m http.server 5600
```

Open:
- `http://127.0.0.1:5600/admin.html`
- `http://127.0.0.1:5600/search.html`

### Module 2 (23201034) - Customer email reminders (Resend)

Set in `.env`:
- `RESEND_API_KEY`
- `RESEND_FROM`
- optional `TASK_TOKEN`

Send reminders (events happening tomorrow, unpaid milestones):
- `POST /tasks/send-customer-reminders`
- optional header: `X-Task-Token: <TASK_TOKEN>`

