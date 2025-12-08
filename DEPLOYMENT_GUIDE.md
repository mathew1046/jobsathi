# JobSathi Distributed Architecture Deployment Guide

This comprehensive guide details the steps to deploy the JobSathi platform using a distributed architecture across three Hugging Face Spaces.

## 🏗️ Architecture Overview

The system is split into three independent services to ensure modularity, scalability, and better resource management:

1.  **Space 1: Translation Service** (`jobsathi-translation`)
    *   **Model:** `ai4bharat/indictrans2-en-indic-1B`
    *   **Function:** Handles all text translation between English and Indic languages.
    *   **Hardware:** GPU Required (T4 Small or A10G).

2.  **Space 2: Text-to-Speech (TTS) Service** (`jobsathi-tts`)
    *   **Model:** `ai4bharat/indic-parler-tts`
    *   **Function:** Generates audio from text for dynamic voice interaction.
    *   **Hardware:** GPU Required (T4 Small).

3.  **Space 3: Central Backend** (`jobsathi-backend`)
    *   **Models:** `ai4bharat/indic-conformer-600m-multilingual` (ASR) & Google Gemini (LLM).
    *   **Function:** Orchestrates the application, manages sessions, connects to DB, and calls Space 1 & 2.
    *   **Hardware:** GPU Required (T4 Small or A10G).

---

## 📋 Prerequisites

*   **Hugging Face Account:** With payment method added (for GPU Spaces).
*   **Google Gemini API Key:** Get it from [Google AI Studio](https://aistudio.google.com/).
*   **Adzuna API ID & Key:** (Optional) For job search functionality.
*   **SerpAPI Key:** (Optional) For Google Jobs search.

---

## 🚀 Step 1: Deploy Translation Service (Space 1)

This space runs the `IndicTrans2` model.

1.  **Create New Space:**
    *   Go to Hugging Face -> New Space.
    *   **Name:** `jobsathi-translation`
    *   **License:** Apache 2.0
    *   **SDK:** `Docker` (Select "Blank" Docker template).
    *   **Hardware:** Select **NVIDIA T4 Small** (or A10G if available).

2.  **Upload Files:**
    Navigate to the `Files` tab of your new Space and upload the contents of `deploy/space_translation/`:
    *   `app.py`
    *   `requirements.txt`
    *   `Dockerfile` (Create this file in the Space if not present locally).

    **Dockerfile Content for Translation Space:**
    ```dockerfile
    FROM python:3.10-slim

    WORKDIR /app

    # Install system dependencies
    RUN apt-get update && apt-get install -y \
        git \
        && rm -rf /var/lib/apt/lists/*

    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    COPY . .

    # Expose port 7860 for Hugging Face
    EXPOSE 7860

    CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
    ```

3.  **Build & Run:**
    *   Commit the files. The Space will automatically start building.
    *   Wait for the status to turn **Running**.
    *   **Copy the Direct URL:** Click on the "Embed this space" menu (top right) -> "Direct URL". It will look like `https://username-jobsathi-translation.hf.space`. **Save this URL.**

---

## 🚀 Step 2: Deploy TTS Service (Space 2)

This space runs the `Indic-Parler-TTS` model.

1.  **Create New Space:**
    *   **Name:** `jobsathi-tts`
    *   **SDK:** `Docker`.
    *   **Hardware:** **NVIDIA T4 Small**.

2.  **Upload Files:**
    Upload contents of `deploy/space_tts/`:
    *   `app.py`
    *   `requirements.txt`
    *   `Dockerfile`

    **Dockerfile Content for TTS Space:**
    ```dockerfile
    FROM python:3.10-slim

    WORKDIR /app

    # Install system dependencies including BLAS/LAPACK for scipy
    RUN apt-get update && apt-get install -y \
        git \
        libsndfile1 \
        build-essential \
        gfortran \
        libopenblas-dev \
        liblapack-dev \
        && rm -rf /var/lib/apt/lists/*

    COPY requirements.txt .
    RUN pip install --no-cache-dir --upgrade pip && \
        pip install --no-cache-dir -r requirements.txt

    COPY . .

    EXPOSE 7860

    CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
    ```

3.  **Build & Run:**
    *   Commit and wait for build.
    *   **Copy the Direct URL:** e.g., `https://username-jobsathi-tts.hf.space`. **Save this URL.**

---

## 🚀 Step 3: Deploy Central Backend (Space 3)

This is your main API that the frontend connects to.

1.  **Create New Space:**
    *   **Name:** `jobsathi-backend`
    *   **SDK:** `Docker`.
    *   **Hardware:** **NVIDIA T4 Small** (Required for ASR).

2.  **Upload Files:**
    Upload the contents of your `backend/` folder. Ensure you have:
    *   `app/` folder (containing `main.py`, `services/`, etc.)
    *   `requirements.txt`
    *   `Dockerfile`

    **Dockerfile Content for Backend:**
    *(Use this specific Dockerfile content, do not use the generic Dockerfile.hf from the repo as it requires specific path adjustments)*
    ```dockerfile
    FROM python:3.10-slim

    WORKDIR /code

    # Install system dependencies for Audio & PDF generation
    RUN apt-get update && apt-get install -y \
        ffmpeg \
        libsndfile1 \
        build-essential \
        && rm -rf /var/lib/apt/lists/*

    # Copy requirements from the app folder
    COPY ./app/requirements.txt /code/requirements.txt
    RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

    # Copy the app folder
    COPY ./app /code/app

    # Create database directory
    RUN mkdir -p /code/app/database

    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
    ```

3.  **Configure Environment Variables:**
    Go to **Settings** -> **Variables and secrets** in your Backend Space and add:

    | Variable Name | Value | Description |
    | :--- | :--- | :--- |
    | `GEMINI_API_KEY` | `AIzaSy...` | Your Google Gemini API Key |
    | `TRANSLATION_SERVICE_URL` | `https://...` | URL from Step 1 |
    | `TTS_SERVICE_URL` | `https://...` | URL from Step 2 |
    | `ASR_MODEL_ID` | `ai4bharat/indic-conformer-600m-multilingual` | ASR Model ID |
    | `ADZUNA_APP_ID` | `...` | (Optional) Adzuna App ID |
    | `ADZUNA_APP_KEY` | `...` | (Optional) Adzuna App Key |

4.  **Build & Run:**
    *   Commit changes.
    *   Wait for the Space to become **Running**.
    *   **Copy the Direct URL:** e.g., `https://username-jobsathi-backend.hf.space`.

---

## 🚀 Step 4: Frontend Deployment

You can deploy the frontend to Vercel, Netlify, or even a static Hugging Face Space.

1.  **Configure Environment:**
    *   In your local `frontend/` folder, create or update `.env`:
        ```env
        VITE_API_BASE_URL=https://username-jobsathi-backend.hf.space
        ```
        *(Replace with your actual Backend Space URL)*

2.  **Deploy to Vercel (Recommended):**
    *   Push your code to GitHub.
    *   Import project in Vercel.
    *   In Vercel Project Settings -> **Environment Variables**, add:
        *   `VITE_API_BASE_URL`: `https://username-jobsathi-backend.hf.space`
    *   Deploy.

---

## ✅ Verification Checklist

1.  **Translation:** Open the app, select "Hindi". Does the text change to Hindi script? (Verifies Space 1 connection).
2.  **TTS:** Start the interview. Do you hear the question spoken in Hindi? (Verifies Space 2 connection).
3.  **ASR:** Speak an answer. Does the system transcribe it correctly? (Verifies Backend ASR).
4.  **Resume:** Complete the flow. Is the PDF generated? (Verifies Backend Logic).

## 🛠️ Troubleshooting

*   **500 Error on Translation/TTS:** Check the logs of Space 1 or Space 2. Ensure they are in "Running" state and not "Sleeping".
*   **CORS Errors:** The Backend `main.py` is configured to allow `*`. If issues persist, ensure your Frontend URL is in the `allow_origins` list in `main.py`.
*   **Audio Not Playing:** Ensure the browser allows autoplay. Check the Network tab to see if the call to `/get-question-audio` returns a valid WAV file.
