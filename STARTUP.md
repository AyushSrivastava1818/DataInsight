# 🚀 DataInsight AI - Quick Start Guide

## One-Command Startup (Recommended)

From the **project root** folder, run:

```bash
npm run dev
```

This will automatically:

- Start the **backend** on `http://localhost:8000`
- Start the **frontend** on `http://localhost:5173`
- Create/initialize the database automatically

Then open your browser to: **http://localhost:5173**

---

## Manual Startup (Two Terminals)

If you prefer more control, open **two separate terminals**:

### Terminal 1: Backend

```bash
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

Then open: **http://localhost:5173**

---

## Troubleshooting

### Issue: Port Already in Use

**Solution:** Kill old processes and restart

```bash
Get-Process python, node -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
npm run dev
```

### Issue: Backend Not Starting

**Check:** The `backend/.venv` folder exists  
**Fix:** Make sure you're using the project's Python virtual environment, NOT system Python

### Issue: Upload Still Fails

**Check:** Both Backend and Frontend are showing in terminal output  
**Verify:** Backend responds at http://localhost:8000 (you should see JSON response)

---

## What Gets Created

After first upload:

- ✅ `backend/datainsight.db` - SQLite database (your data persists here)
- ✅ `backend/storage/dataset_*.csv` - Your uploaded CSV files
- ✅ All cleaning/export operations saved automatically

Your data is **completely local** - nothing sent to cloud unless you configure Supabase.

---

## Quick Commands

| Command                                                                                       | What it does                  |
| --------------------------------------------------------------------------------------------- | ----------------------------- |
| `npm run dev`                                                                                 | Start both backend & frontend |
| `cd frontend && npm run build`                                                                | Build for production          |
| `cd backend && .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000` | Run backend only              |
