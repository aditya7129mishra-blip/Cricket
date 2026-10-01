# BDPL Tournament Manager

A FastAPI application for managing BDPL tournament setup, teams, players, fixtures, live scores, and awards.

## Run locally

Use Python 3.10 or newer. From this folder, run these commands in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --reload
```

Open <http://127.0.0.1:8000>. Interactive API documentation is at <http://127.0.0.1:8000/docs>.

The app creates `bdpl.db` in this folder on first startup. The database and Python cache are excluded by `.gitignore`.

## Project files

- `app.py`: FastAPI application and SQLite API
- `templates/index.html`: Tournament manager interface
- `templates/overview.html`: Alternate read-only overview
- `static/`: Static assets
- `render.yaml`: Render deployment configuration