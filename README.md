# 🚀 DataInsight AI

> AI-powered data cleaning, exploratory data analysis, intelligent insights, and report generation platform built with **React, TypeScript, FastAPI, and Python**.

![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)
![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite)
![Vercel](https://img.shields.io/badge/Frontend-Vercel-black?logo=vercel)
![Railway](https://img.shields.io/badge/Backend-Railway-0B0D0E)

---

## 🌐 Live Demo

**Application:**  
👉 https://data-insight-jade.vercel.app

**Backend API:**  
👉 https://datainsight-production.up.railway.app

**API Documentation:**  
👉 https://datainsight-production.up.railway.app/docs

---

# 📖 Overview

DataInsight AI is a full-stack intelligent data analytics platform designed to simplify the process of exploring, cleaning, and understanding CSV datasets.

Users can upload datasets, perform automated data cleaning operations, generate exploratory data analysis (EDA), receive AI-powered insights, interact with their datasets through an AI assistant, and export professional reports.

The application is built with a modern React frontend and a FastAPI backend, providing a fast and scalable analytics experience.

---

# ✨ Features

## 📂 Dataset Management

- Upload CSV datasets
- Dataset versioning
- Multiple dataset support
- Dataset preview
- Metadata management

---

## 🧹 Data Cleaning

- Missing value imputation
- Duplicate removal
- Data type correction
- Text cleaning
- Outlier detection
- Column operations
  - Rename
  - Delete
  - Create computed columns

---

## 📊 Exploratory Data Analysis

- Dataset overview
- Shape & memory usage
- Missing value analysis
- Data type summary
- Descriptive statistics
- Correlation matrix
- Categorical analysis
- Time-series detection
- Data quality score

---

## 🤖 AI Insights

Generate intelligent insights including:

- Trends
- Correlations
- Anomalies
- Recommendations

---

## 💬 AI Chat Assistant

Interact with your dataset using natural language.

Example questions:

- Which columns contain missing values?
- What are the strongest correlations?
- Explain the quality score.
- Summarize the dataset.

---

## 📑 Report Generation

Export reports in:

- CSV
- PDF

---

# 🏗️ Tech Stack

## Frontend

- React 19
- TypeScript
- Vite
- Tailwind CSS
- Lucide React
- Recharts

## Backend

- FastAPI
- Python
- SQLAlchemy
- Pandas
- SQLite
- Uvicorn

## Deployment

- Vercel (Frontend)
- Railway (Backend)

---

# 📁 Project Structure

```
DataInsight/
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── models.py
│   │   └── main.py
│   │
│   ├── requirements.txt
│   └── Dockerfile
│
└── README.md
```

---

# ⚡ Getting Started

## Clone Repository

```bash
git clone https://github.com/AyushSrivastava1818/DataInsight.git

cd DataInsight
```

---

# Backend Setup

```bash
cd backend

python -m venv .venv

source .venv/bin/activate
```

Windows

```powershell
.venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run backend

```bash
uvicorn app.main:app --reload
```

Backend runs at

```
http://localhost:8000
```

---

# Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend runs at

```
http://localhost:5173
```

---

# Environment Variables

## Frontend

Create `.env`

```env
VITE_API_URL=http://localhost:8000/api
```

Production

```env
VITE_API_URL=https://datainsight-production.up.railway.app
```

---

## Backend

Example `.env`

```env
SECRET_KEY=your_secret_key

DATABASE_URL=sqlite:///./datainsight.db

SUPABASE_URL=your_supabase_url

SUPABASE_KEY=your_supabase_key
```

---

# API Documentation

Interactive Swagger documentation is available at:

https://datainsight-production.up.railway.app/docs

---

# Future Improvements

- User workspaces
- Dashboard analytics
- Team collaboration
- More AI models
- Cloud storage integration
- Advanced visualizations
- Scheduled reports
- Dark mode enhancements
- User authentication with private workspaces
- User-specific dataset history
- One-click "Clear Analysis History"
- Cloud storage for uploaded datasets
- Export reports in multiple formats

---

# Deployment

Frontend

- Vercel

Backend

- Railway

---

# Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/amazing-feature
```

3. Commit your changes

```bash
git commit -m "Add amazing feature"
```

4. Push

```bash
git push origin feature/amazing-feature
```

5. Open a Pull Request

---

# License

This project is licensed under the MIT License.

---

# Author

**Ayush Srivastava**

GitHub

https://github.com/AyushSrivastava1818

---

⭐ If you found this project useful, consider giving it a star!
