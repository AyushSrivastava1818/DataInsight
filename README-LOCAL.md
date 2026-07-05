# DataInsight AI 🚀

**All-in-one AI-powered CSV data analysis, cleaning, profiling, and report generation — 100% local.**

---

## 🎯 Quick Start

### First Time?

1. **Make sure Node.js and Python are installed**
2. **From the project root, run ONE command:**

```bash
npm run dev
```

That's it! The app will:

- ✅ Install dependencies
- ✅ Start the backend (port 8000)
- ✅ Start the frontend (port 5173)
- ✅ Create the SQLite database automatically
- ✅ Open your browser

**Then visit:** http://localhost:5173

---

## 📁 Project Structure

```
datainsight-ai/
├── backend/              # FastAPI server (Python)
│   ├── .venv/           # Virtual environment (auto-created)
│   ├── app/
│   ├── storage/         # Your uploaded CSVs stored here
│   ├── datainsight.db   # SQLite database (auto-created)
│   └── requirements.txt
│
├── frontend/             # React + Vite (TypeScript)
│   ├── src/
│   ├── vite.config.ts   # Already configured for /api proxy
│   └── package.json
│
├── start-dev.ps1        # PowerShell launcher (no browser knowledge needed)
├── start-dev.bat        # Batch file launcher (for Windows)
├── STARTUP.md           # Detailed startup guide
└── package.json         # Root entry point
```

---

## 🔄 How It Works

1. **Upload CSV** → Stored in `backend/storage/`
2. **Analysis** → Profiling, EDA, insights computed locally
3. **Cleaning** → Impute missing values, remove duplicates, cap outliers
4. **Export** → Download cleaned CSV or generate PDF report
5. **Chat** → Ask questions about your data (local LLM fallback)

**Everything stays on your machine — no cloud uploads.**

---

## ⚙️ Setup (First Time Only)

### Prerequisites

- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))

### Automatic Setup

```bash
npm run dev
```

This will:

- Install frontend dependencies
- Install backend dependencies
- Create Python virtual environment
- Initialize SQLite database

### Manual Setup (if needed)

```bash
# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

---

## 🚀 Running the App

### Option 1: One Command (Recommended)

```bash
npm run dev
```

### Option 2: Batch File (Windows)

Double-click: `start-dev.bat`

### Option 3: PowerShell Script

```bash
.\start-dev.ps1
```

### Option 4: Manual (Two Terminals)

**Terminal 1 - Backend:**

```bash
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**

```bash
cd frontend
npm run dev
```

Then visit: http://localhost:5173

---

## 🔧 Configuration

All configs are pre-set for **local development**. No additional setup needed.

### Environment Files

- `backend/.env` - Backend configuration (SQLite, OpenAI keys, etc.)
- `frontend/.env` - Frontend configuration (API URL)

### To use Supabase or OpenAI (Optional)

Edit `backend/.env` with your API keys. See `backend/.env.example`.

---

## 📊 Features

- ✅ **CSV Upload** - Drag & drop or browse, up to 100 MB
- ✅ **Data Profiling** - Auto-generated quality scores, stats, correlations
- ✅ **Cleaning** - Impute nulls, deduplicate, handle outliers, standardize text
- ✅ **EDA** - Histograms, correlation heatmaps, time series detection
- ✅ **AI Insights** - Automatic business recommendations (local fallback included)
- ✅ **Chat** - Ask questions about your data
- ✅ **Export** - CSV & PDF reports with audit trails
- ✅ **Version History** - Track all cleaning actions

---

## 🐛 Troubleshooting

### "Port already in use"

```bash
# Kill lingering processes and restart
Get-Process python, node -ErrorAction SilentlyContinue | Stop-Process -Force
npm run dev
```

### "Backend not starting"

Make sure:

- Python 3.9+ is installed
- Virtual environment exists at `backend/.venv`
- `backend/.env` file is present

### "Upload fails with 'Failed to fetch'"

Check:

- Backend is running (should see logs in terminal)
- Frontend is on http://localhost:5173
- No CORS errors in browser console

### "Database locked error"

- Close all browser tabs and restart the backend
- Only one instance of the backend should be running

---

## 📈 Performance Tips

- **Large datasets?** Upload files under 50 MB for best performance
- **Slow cleaning?** Close unused browser tabs
- **Rebuilding often?** Use `npm run dev` instead of building

---

## 📝 Commands

| Command                                         | Effect                        |
| ----------------------------------------------- | ----------------------------- |
| `npm run dev`                                   | Start both backend & frontend |
| `npm run build`                                 | Build frontend for production |
| `cd backend && pip install -r requirements.txt` | Install Python dependencies   |
| `cd frontend && npm install`                    | Install Node dependencies     |

---

## 💾 Your Data

- **Uploaded CSVs** → Stored in `backend/storage/` (local, not cloud)
- **Database** → SQLite at `backend/datainsight.db` (local, encrypted)
- **No tracking** → No analytics, no telemetry, completely private

---

## 🛠️ Development

### Adding Backend Routes

Edit files in `backend/app/routers/`

### Adding Frontend Pages

Edit files in `frontend/src/pages/`

### Modifying Services

Backend services: `backend/app/services/`  
Frontend services: `frontend/src/services/`

---

## 📞 Need Help?

1. **Check [STARTUP.md](STARTUP.md)** for detailed startup guide
2. **Review error messages** - they usually point to the issue
3. **Restart the app** - `Ctrl+C` in terminals, then `npm run dev`

---

## 📄 License

Local development use. See LICENSE for details.

---

**Ready? Run:** `npm run dev`  
**Then visit:** http://localhost:5173
