# VALENCE — Voice-to-Rights Civic Shield

> **Speak once. Make them answer.**  
> Built for the **Scaler × Wispr Flow "India Runs on Voice" Hackathon**.

VALENCE is a voice-first civic accountability engine that turns raw spoken grievances in **7 regional languages** (English, Hinglish, Hindi, Tamil, Marathi, Telugu, Bengali) into legally enforceable leverage:

- **In-Ear Audio Defense Script:** Speaks calm, legally accurate counter-statements back in your chosen regional language.
- **Form-A RTI Petition (Section 6(1) & Section 20):** Automatically drafts an RTI demanding internal work orders and inspection logs—triggering personal officer liability (₹250/day fine up to ₹25,000 under Section 20).
- **CPGRAMS Statutory Grievance:** Pre-formatted complaint mapped to Indian Citizen Charters and mandatory SLAs.
- **Persistent SQLite Case Ledger:** Tracks every logged grievance from `Drafted` → `RTI Filed` → `Resolved`, with `.txt` dossier export.

---

## Tech Stack

- **Frontend:** React + Vite + CSS (Deep Navy `#14213D`, Cream `#F4EDE0`, Burnished Amber `#E09F3E` with fluted vertical glass refraction), Web Speech API (`SpeechRecognition` & `speechSynthesis`), and Web Audio API live waveform monitoring.
- **Backend:** FastAPI + Python + SQLite (`backend/db.py`, `backend/engine.py`, `backend/main.py`).
- **AI Layer:** Built-in zero-key regional statutory RAG engine + optional Gemini (`GEMINI_API_KEY`) enrichment.

---

## Quick Start

### 1. Build Frontend
```bash
cd frontend
npm install
npm run build
```

### 2. Run Backend + Serve App
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000** in your browser (or double-click `start_valence.bat` on Windows).
