# ProofGuard-Hacknex
<<<<<<< HEAD

This repository contains both the frontend (React/Vite) and backend (FastAPI) for the application.

## Prerequisites

- Node.js (for frontend)
- Python 3.8+ (for backend)

---

## 1. Running the Backend

The backend is built with FastAPI and runs on Python. 

1. Open a terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. (Optional but recommended) Create and activate a virtual environment:
   **Windows:**
   ```bash
   py -m venv venv
   venv\Scripts\activate
   ```
   *(If you get a script execution policy error here, run this command once as Administrator or in your terminal: `Set-ExecutionPolicy Unrestricted -Scope CurrentUser`)*
   **macOS/Linux:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the development server:
   ```bash
   py run.py
   ```
   *The server will start on `http://127.0.0.1:8000` with hot-reloading enabled.*

---

## 2. Running the Frontend

The frontend is built with React, Tailwind CSS, and Vite.

1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install the dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```
   *The Vite server will start. Check your terminal output for the local URL (usually `http://localhost:5173`).*
=======
**Proof-Carrying Data Analyst** is an Agentic GenAI system that analyzes data, generates executable code, verifies the results, and provides trustworthy answers with supporting evidence. It is designed to handle messy data, detect errors and ambiguity, and ensure that analytical results are correct, reproducible, and verifiable.
>>>>>>> d499a18c9e59a1d71317435fe726800c395b3227
