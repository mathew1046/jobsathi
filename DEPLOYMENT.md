# 🚀 Deployment Guide: Free Hosting

This guide will help you deploy JobSathi for free using **Hugging Face Spaces** (Backend) and **Vercel** (Frontend).

## 1. Backend Deployment (Hugging Face Spaces)

We will deploy the Python backend (ASR Model + API) to Hugging Face Spaces.

1.  **Create a Space**:
    *   Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click **Create new Space**.
    *   **Space name**: `jobsathi-backend` (or similar).
    *   **License**: MIT.
    *   **Select the Space SDK**: `Docker`.
    *   **Choose a hardware**: `CPU Basic (Free)` (2 vCPU, 16GB RAM).
    *   Click **Create Space**.

2.  **Upload Code**:
    *   On your new Space page, click the **Files** tab.
    *   Click **Add file** -> **Upload files**.
    *   You need to upload your `Dockerfile.hf` but rename it to `Dockerfile`.
    *   **Crucial Step**: Since your code is in a subfolder (`backend/`), the easiest way is to structure the Space like this:
        *   `Dockerfile` (The content of `Dockerfile.hf`)
        *   `requirements.txt` (The content of `backend/app/requirements.txt`)
        *   `main.py` (The content of `backend/app/main.py`)
        *   `job_search.py` (The content of `backend/app/job_search.py`)
        *   `database/` (Empty folder)
    
    *   **Alternative (Easier for Git users)**:
        If you are pushing this whole repo to GitHub, you can connect your Hugging Face Space to your GitHub repo, but you'll need to configure the Dockerfile path.
        
        **Simplest Manual Method**:
        1. Clone your HF Space locally: `git clone https://huggingface.co/spaces/YOUR_USERNAME/jobsathi-backend`
        2. Copy the contents of `backend/app/*` into this folder.
        3. Copy `Dockerfile.hf` into this folder and rename it to `Dockerfile`.
        4. `git add .`, `git commit -m "Deploy"`, `git push`.

3.  **Configure Secrets**:
    *   Go to the **Settings** tab of your Space.
    *   Scroll to **Variables and secrets**.
    *   Click **New secret**.
    *   Name: `GEMINI_API_KEY`
    *   Value: (Paste your Gemini API Key)
    *   Add other keys if you have them (`ADZUNA_APP_ID`, etc.).

4.  **Get the URL**:
    *   Once built (Status: **Running**), click the "Embed this space" button or look at the URL.
    *   It will look like: `https://yourusername-jobsathi-backend.hf.space`
    *   **Note**: This is your `VITE_API_BASE_URL`.

---

## 2. Frontend Deployment (Vercel)

1.  **Push to GitHub**:
    *   Ensure your project is pushed to a GitHub repository.

2.  **Import to Vercel**:
    *   Go to [vercel.com](https://vercel.com) -> **Add New Project**.
    *   Select your `jobsathi` repository.

3.  **Configure Project**:
    *   **Framework Preset**: Vite (should be detected automatically).
    *   **Root Directory**: Click `Edit` and select `frontend`.
    *   **Environment Variables**:
        *   Key: `VITE_API_BASE_URL`
        *   Value: `https://yourusername-jobsathi-backend.hf.space` (The URL from Step 1).
        *   *Important*: Make sure there is NO trailing slash `/` at the end of the URL.

4.  **Deploy**:
    *   Click **Deploy**.
    *   Wait for the build to finish.

## 3. Verification

1.  Open your Vercel URL (e.g., `https://jobsathi.vercel.app`).
2.  Try recording audio.
3.  If it works, you are live! 🚀

## ⚠️ Important Note on Data Persistence

Since we are using the free tier of Hugging Face Spaces:
*   The server will "sleep" after 48 hours of inactivity. The first request after sleep will take 1-2 minutes to start.
*   **Files are ephemeral**: Any resumes generated and saved in the `database/` folder will be **deleted** when the Space restarts or sleeps.
*   **Solution**: Download your resume immediately after generation.
