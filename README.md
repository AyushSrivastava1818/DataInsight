# DataInsight AI

DataInsight AI is a production-grade, full-stack, AI-powered data analytics and profiles workstation. Modeled after analytical suites like Tableau, Power BI, and Pandas, it lets users upload any CSV file (up to 100 MB), run interactive data cleaning operations, execute descriptive EDA statistical calculations, draw responsive dashboards, generate AI insights, chat with datasets, and compile publication-ready PDF reports.

## Features

1. **Modern Premium UI**: Built with a dark/light responsive glassmorphic palette.
2. **Drag & Drop Upload**: Handles CSV files up to 100 MB. Compiles columns, counts, and initial Data Quality Scores out of 100.
3. **Data Cleaning Workstation**:
   - Impute missing entries via mean, median, mode, forward-fill, or backward-fill.
   - Restrict outlier lines via IQR / Z-score thresholds (capping or removing records).
   - Sanitize text cells (white spaces trimming, upper/lower/title casing, stripping special characters).
   - Delete/rename columns and construct custom calculated variables using math equations.
4. **Exploratory Data Analysis (EDA)**: Descriptive metrics for all features, category frequency grids, bivariate scatter plots, normal histograms, chronologically grouped line trends, and interactive Pearson correlation heatmaps.
5. **AI Insights Deck**: Automatically summarizes dataset behaviors (revenue spikes, correlations, outlier warnings). Utilizes Gemini or OpenAI API keys if defined; otherwise, falls back to a rules-based local analyzer.
6. **AI Chat Analyst**: Submit questions in plain English ("what trends do you observe?", "which columns should I delete?") and receive instant statistical breakdowns.
7. **Publication PDF Compiler**: Generates downloadable PDF reports with metadata cards, cleaning logs audit trails, statistics grids, and embedded matplotlib plots.

---

## Technical Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Recharts, Lucide Icons, Canvas Confetti.
- **Backend**: Python 3.10+, FastAPI, Uvicorn, SQLite, SQLAlchemy.
- **Data Engineering**: Pandas, NumPy, Scikit-learn, Seaborn, Matplotlib, ReportLab.
- **AI Models**: Gemini API Client, OpenAI API Client, rules-based regex fallback parser.

---

## Directory Architecture

```
datainsight-ai/
├── backend/
│   ├── app/
│   │   ├── config.py         # Storage, db, and API key constants
│   │   ├── database.py       # SQLite connection details
│   │   ├── models.py         # SQLAlchemy persistence models
│   │   ├── schemas.py        # Request & response serialization checks
│   │   ├── crud.py           # Database transaction queries
│   │   ├── routers/          # API endpoints (upload, clean, eda, insights, chat, reports)
│   │   └── services/         # Core business code (cleaning, eda, insights, chat, reportlab pdf)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── test_backend.py       # Automated pandas operations test suite
├── frontend/
│   ├── src/
│   │   ├── components/       # Shared navbar, layout, and glass buttons
│   │   ├── pages/            # Landing page, dashboard, cleaning panel, eda views, chat, reports
│   │   ├── services/         # api.ts endpoint configurations
│   │   ├── App.tsx
│   │   └── index.css         # Glassmorphism and dark mode class properties
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml
├── README.md
└── sample_data/
    └── company_sales_demo.csv # Inconsistent CSV dataset for local testing
```

---

## Installation & Getting Started

### Method 1: Local Launch

#### 1. Start the Backend
1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Mac/Linux:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Define environment variables in a `.env` file (Optional):
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```
5. Run the server:
   ```bash
   python app/main.py
   ```
   The backend API will run at `http://localhost:8000`.

#### 2. Start the Frontend
1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install packages:
   ```bash
   npm install --legacy-peer-deps
   ```
3. Launch development server:
   ```bash
   npm run dev
   ```
   The interactive dashboard will launch at `http://localhost:5173`.

---

### Method 2: Docker Containerization

1. Ensure Docker Desktop is running.
2. In the root directory `datainsight-ai`, run:
   ```bash
   docker-compose up --build
   ```
3. Once compiled, access the app at `http://localhost`.

---

## Verification & Testing

Verify Pandas operations and data profiling correctness by running the automated backend test suite:
```bash
cd backend
# With virtualenv active:
python test_backend.py
```
This suite automatically tests missing value imputation, duplicate removal, outlier capping, casing sanitizations, calculated columns, and health index rankings.
