# Expense Goat — Vulnerable Django Demo App

A small Django expense reimbursement demo with **intentional** secure and insecure authorization patterns for AI-powered detection demos.

## Stack

- Python 3.10+
- Django 4.x / 5.x
- SQLite (default)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cd /path/to/ExpenseGoat
python manage.py migrate
python manage.py seed_demo_data
```

## Run

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ and log in with a demo user.

## Demo Users (from `seed_demo_data`)

| User   | Role     | Department  | Password |
|--------|----------|-------------|----------|
| alice  | Employee | Engineering | `demo1234` |
| bob    | Manager  | Engineering | `demo1234` |
| cathy  | Employee | Sales       | `demo1234` |
| dave   | Manager  | Sales       | `demo1234` |
| frank  | Finance  | (HR/Eng)    | `demo1234` |

## Pages

- **Auth:** `/login/`, `/logout/`
- **Expenses:** `/expenses/`, `/expenses/new/`, `/expenses/<id>/`, `/expenses/<id>/edit/`, `/expenses/<id>/submit/`
- **Manager:** `/manage/queue/`, `/manage/expenses/<id>/review/`
- **Finance:** `/finance/export/`, `/finance/expenses/<id>/mark_paid/`
- **Receipts:** `/expenses/<id>/receipts/upload/`, `/receipts/<id>/download/`

## API (JSON)

- **Endpoints:** `GET /api/me/expenses`, `POST /api/expenses`, `GET /api/expenses/<id>/`, `POST /api/expenses/<id>/update_amount/`, `GET /api/manage/department_expenses`, `POST /api/manage/expenses/<id>/decision/`, `GET /api/finance/export/`, `POST /api/profile/update_department/`

This app is for **demo and detection testing only** — do not use in production.
