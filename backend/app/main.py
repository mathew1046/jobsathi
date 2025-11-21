# jobsathi_api.py
# ASR + LLM-powered resume builder backend

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import tempfile
import os
import asyncio
import torch
import torchaudio
from transformers import AutoModel
import httpx
from typing import List, Dict, Any, Optional
import json
import google.generativeai as genai
from datetime import datetime
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER

app = FastAPI(title="JobSathi API - Resume Builder", version="6.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Device and model IDs
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
ASR_MODEL_ID = "ai4bharat/indic-conformer-600m-multilingual"

# Database directory for storing responses
DATABASE_DIR = os.path.join(os.path.dirname(__file__), "database")
os.makedirs(DATABASE_DIR, exist_ok=True)

# Gemini LLM configuration
GEMINI_API_KEY = "AIzaSyDXNy1EXRlMnUYmoJYesy94SiDSc_rEYw8"
genai.configure(api_key=GEMINI_API_KEY)

# Configuration for Gemini
GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
}

# Initialize the model
# Using gemini-1.5-flash as it is fast and cost-effective
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-lite",
    generation_config=GENERATION_CONFIG,
)

# -----------------------
# Globals and locks
# -----------------------
_asr_model = None
asr_lock = asyncio.Lock()

# Session storage: {session_id: {"responses": [], "metadata": {}}}
session_storage = {}

# Language maps
LANGUAGE_NAME = {
    "as": "Assamese", "awa": "Awadhi", "bn": "Bengali", "bho": "Bhojpuri",
    "brx": "Bodo", "doi": "Dogri", "en": "English", "gom": "Goan Konkani",
    "gu": "Gujarati", "hi": "Hindi", "kn": "Kannada", "kas": "Kashmiri",
    "mai": "Maithili", "ml": "Malayalam", "mr": "Marathi", "mni": "Manipuri",
    "nep": "Nepali", "or": "Odia", "pa": "Punjabi", "sa": "Sanskrit",
    "sat": "Santali", "snd": "Sindhi", "te": "Telugu", "ta": "Tamil", "ur": "Urdu"
}

# -----------------------
# Utility functions
# -----------------------
def preprocess_audio(waveform, sample_rate, target_sr=16000):
    # convert to mono
    if waveform.ndim > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    # resample if required
    if sample_rate != target_sr:
        try:
            waveform = torchaudio.functional.resample(waveform, sample_rate, target_sr)
        except Exception as e:
            print(f"Resample failed: {e}, trying transforms.Resample")
            resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=target_sr)
            waveform = resampler(waveform)
    waveform = waveform.to(torch.float32)
    if waveform.ndim == 1:
        waveform = waveform.unsqueeze(0)
    return waveform

# -----------------------
# ASR model lifecycle
# -----------------------
async def load_asr_model():
    global _asr_model
    async with asr_lock:
        if _asr_model is None:
            print("Loading ASR model...")
            _asr_model = AutoModel.from_pretrained(ASR_MODEL_ID, trust_remote_code=True).to(DEVICE)
            print("ASR model loaded")
    return _asr_model

def unload_asr_model():
    global _asr_model
    if _asr_model:
        print("Unloading ASR model to free memory")
        del _asr_model
        _asr_model = None
        torch.cuda.empty_cache()

async def run_asr(audio_tensor, source_lang):
    model = await load_asr_model()
    try:
        with torch.inference_mode():
            out = model(audio_tensor, source_lang, "rnnt")
            if isinstance(out, dict):
                return out.get("text", "").strip()
            return str(out).strip()
    except Exception as e:
        raise RuntimeError(f"ASR failed: {e}")

# -----------------------
# Audio loader helper
# -----------------------
def save_temp_file_and_load(audio_bytes, filename_hint):
    tmp_path = None
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename_hint)[1] or ".wav") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        try:
            waveform, sr = torchaudio.load(tmp_path)
            print(f"Loaded with torchaudio (auto): shape {waveform.shape}, sr {sr}")
        except Exception as e:
            print(f"torchaudio.load auto failed: {e}. Trying mp3 format fallback.")
            waveform, sr = torchaudio.load(tmp_path, format="mp3")
            print(f"Loaded as mp3: shape {waveform.shape}, sr {sr}")
        return tmp_path, waveform, sr
    except Exception as e:
        raise

# -----------------------
# Endpoints
# -----------------------

@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...), source_language: str = Form("hi")):
    """ASR-only endpoint - returns transcribed text for frontend translation."""
    print(f"Transcribe called with language: {source_language}, file: {audio.filename}")
    if source_language not in LANGUAGE_NAME:
        print(f"Unsupported language: {source_language}")
        raise HTTPException(status_code=400, detail="Unsupported language")

    audio_bytes = await audio.read()
    print(f"Audio bytes length: {len(audio_bytes)}")
    if not audio_bytes:
        raise HTTPException(400, "Empty audio")

    tmp_path = None
    try:
        tmp_path, waveform, sr = save_temp_file_and_load(audio_bytes, audio.filename)
        waveform = preprocess_audio(waveform, sr)
        print(f"Preprocessed waveform shape: {waveform.shape}")

        transcript = await run_asr(waveform.to(DEVICE), source_language)
        print(f"ASR transcript: {transcript}")

        if not transcript:
            unload_asr_model()
            raise HTTPException(400, "ASR returned empty")

        unload_asr_model()
        return {
            "status": "success",
            "data": {
                "original_text": transcript,
                "detected_language": source_language,
                "language_label": LANGUAGE_NAME[source_language]
            }
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
            print(f"Temp file removed: {tmp_path}")

# -----------------------
# LLM Integration
# -----------------------

async def call_gemini(prompt: str, system_message: str = "You are a helpful assistant that extracts structured data from text.") -> Dict[str, Any]:
    """Call Gemini API with given prompt and return JSON response."""
    try:
        # Combine system message and prompt as Gemini 1.5 Flash handles context well
        full_prompt = f"System: {system_message}\n\nUser: {prompt}"
        
        # Generate content asynchronously
        response = await model.generate_content_async(full_prompt)
        content = response.text
        
        # Try to parse JSON from response
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # If response contains markdown code blocks, extract JSON
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            return {"raw_response": content}
            
    except Exception as e:
        print(f"Gemini API error: {e}")
        # Fallback or detailed error logging
        if hasattr(e, 'response'):
             print(f"Gemini feedback: {e.response.prompt_feedback}")
        raise HTTPException(status_code=500, detail=f"LLM API failed: {str(e)}")

@app.post("/start_session")
async def start_session():
    """Create a new session for the user."""
    session_id = str(uuid.uuid4())
    session_storage[session_id] = {
        "responses": [],
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "completed": False
        }
    }
    print(f"Created session: {session_id}")
    return {"status": "success", "session_id": session_id}

@app.post("/ask_llm")
async def ask_llm(payload: Dict[str, Any] = Body(...)):
    """
    Accepts transcript and question, sends to LLM, returns structured JSON.
    Stores response in session.
    Payload: { "session_id": "...", "transcript": "...", "question": "...", "field": "...", "question_id": 1 }
    """
    session_id = payload.get("session_id")
    transcript = payload.get("transcript", "")
    question = payload.get("question", "")
    field = payload.get("field", "answer")
    question_id = payload.get("question_id", 0)
    
    if not session_id or session_id not in session_storage:
        raise HTTPException(status_code=400, detail="Invalid or missing session_id")
    
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript is required")
    
    prompt = f"""Question: {question}
User's answer (in English or other language): {transcript}

Task 1: Translate the user's answer to English if it is not already in English.
Task 2: Extract the requested resume field from the text.

Return a JSON object with TWO keys:
1. 'translation': The English translation of the user's answer.
2. 'extracted_data': A small JSON object with the key '{field}' containing the extracted value.

Example format:
{{
  "translation": "My name is Ramesh Kumar.",
  "extracted_data": {{ "name": "Ramesh Kumar" }}
}}

Return ONLY the JSON, no explanations."""
    
    result = await call_gemini(prompt)
    
    # Store in session
    response_data = {
        "question_id": question_id,
        "field": field,
        "question": question,
        "asr_output": transcript,
        "translated_text": result.get("translation", ""),
        "llm_output": result.get("extracted_data", {}),
        "timestamp": datetime.now().isoformat()
    }
    
    session_storage[session_id]["responses"].append(response_data)
    print(f"Added response to session {session_id}, total: {len(session_storage[session_id]['responses'])}")

    return {
        "status": "success",
        "data": result.get("extracted_data", {}),
        "translation": result.get("translation", "")
    }

def generate_ats_resume_pdf(profile: Dict[str, Any], output_path: str):
    """Generate an ATS-friendly PDF resume from profile data."""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=colors.HexColor('#2c3e50'),
        borderPadding=3,
        backColor=colors.HexColor('#ecf0f1')
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.leading = 14
    
    # Name and Contact
    name = profile.get('name', 'Candidate Name')
    story.append(Paragraph(name.upper(), title_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Contact information
    contact_parts = []
    if profile.get('email'):
        contact_parts.append(profile['email'])
    if profile.get('phone'):
        contact_parts.append(profile['phone'])
    if profile.get('location'):
        contact_parts.append(profile['location'])
    
    if contact_parts:
        contact_text = ' | '.join(contact_parts)
        contact_style = ParagraphStyle('Contact', parent=normal_style, alignment=TA_CENTER, fontSize=9)
        story.append(Paragraph(contact_text, contact_style))
        story.append(Spacer(1, 0.15*inch))
    
    # Links
    links = profile.get('links', {})
    if links and isinstance(links, dict):
        link_parts = []
        if links.get('linkedin'):
            link_parts.append(f"LinkedIn: {links['linkedin']}")
        if links.get('github'):
            link_parts.append(f"GitHub: {links['github']}")
        if link_parts:
            link_text = ' | '.join(link_parts)
            story.append(Paragraph(link_text, contact_style))
            story.append(Spacer(1, 0.15*inch))
    
    # Professional Summary
    summary = profile.get('summary', '')
    if summary:
        story.append(Paragraph('PROFESSIONAL SUMMARY', heading_style))
        story.append(Paragraph(summary, normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Skills
    skills = profile.get('skills', [])
    if skills and isinstance(skills, list):
        story.append(Paragraph('SKILLS', heading_style))
        skills_text = ' • '.join(skills) if skills else 'N/A'
        story.append(Paragraph(skills_text, normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Experience
    experience_details = profile.get('experience_details', [])
    if experience_details and isinstance(experience_details, list):
        story.append(Paragraph('PROFESSIONAL EXPERIENCE', heading_style))
        for exp in experience_details:
            if isinstance(exp, dict):
                company = exp.get('company', 'Company')
                role = exp.get('role', 'Role')
                duration = exp.get('duration', '')
                description = exp.get('description', '')
                
                exp_header = f"<b>{role}</b> - {company}"
                if duration:
                    exp_header += f" ({duration})"
                story.append(Paragraph(exp_header, normal_style))
                
                if description:
                    story.append(Paragraph(f"• {description}", normal_style))
                story.append(Spacer(1, 0.08*inch))
    
    # Education
    education = profile.get('education', [])
    if education and isinstance(education, list):
        story.append(Paragraph('EDUCATION', heading_style))
        for edu in education:
            if isinstance(edu, dict):
                degree = edu.get('degree', 'Degree')
                institution = edu.get('institution', 'Institution')
                year = edu.get('year', '')
                
                edu_text = f"<b>{degree}</b> - {institution}"
                if year:
                    edu_text += f" ({year})"
                story.append(Paragraph(edu_text, normal_style))
                story.append(Spacer(1, 0.08*inch))
    
    # Certifications
    certifications = profile.get('certifications', [])
    if certifications and isinstance(certifications, list) and certifications:
        story.append(Paragraph('CERTIFICATIONS', heading_style))
        for cert in certifications:
            if cert:
                story.append(Paragraph(f"• {cert}", normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Languages
    languages = profile.get('languages', [])
    if languages and isinstance(languages, list):
        story.append(Paragraph('LANGUAGES', heading_style))
        lang_text = ', '.join(languages) if languages else 'N/A'
        story.append(Paragraph(lang_text, normal_style))
    
    # Build PDF
    doc.build(story)
    print(f"PDF generated: {output_path}")

@app.post("/build_profile")
async def build_profile(payload: Dict[str, Any] = Body(...)):
    """
    Builds final profile from session data, generates ATS resume PDF.
    Payload: { "session_id": "..." }
    """
    session_id = payload.get("session_id")
    
    if not session_id or session_id not in session_storage:
        raise HTTPException(status_code=400, detail="Invalid or missing session_id")
    
    session_data = session_storage[session_id]
    responses = session_data["responses"]
    
    if not responses:
        raise HTTPException(status_code=400, detail="No responses found in session")
    
    # Merge all Q&A responses
    merged_data = {}
    for item in responses:
        if "llm_output" in item and isinstance(item["llm_output"], dict):
            merged_data.update(item["llm_output"])
    
    # Create ATS-optimized resume using LLM
    prompt = f"""Here is raw resume data collected from a user interview:
{json.dumps(merged_data, indent=2)}

Please create an ATS-optimized professional resume in JSON format. Make it comprehensive and well-structured for Applicant Tracking Systems.

Return a JSON with these fields:
- name (string): Full name
- role (string): Professional title/desired position
- email (string): Email address
- phone (string): Phone number
- location (string): City, State/Country
- links (object): {{"linkedin": "url", "github": "url", "portfolio": "url"}}
- summary (string): Professional summary (3-4 sentences highlighting key achievements and skills)
- experience_years (number): Total years of experience
- experience_details (array): [{{
    "company": "Company Name",
    "role": "Job Title",
    "duration": "Month Year - Month Year",
    "description": "Key achievements and responsibilities"
  }}]
- skills (array): Technical and professional skills
- education (array): [{{
    "degree": "Degree Name",
    "institution": "University Name",
    "year": "Year"
  }}]
- certifications (array): List of certifications
- languages (array): Languages spoken
- extras (object): Any additional relevant information

Use proper formatting, action verbs, and quantifiable achievements where possible. Return ONLY valid JSON."""
    
    result = await call_gemini(prompt, system_message="You are an expert ATS resume writer. Create professional, keyword-rich resumes optimized for Applicant Tracking Systems.")
    
    # Mark session as completed
    session_data["metadata"]["completed"] = True
    session_data["metadata"]["completed_at"] = datetime.now().isoformat()
    session_data["profile"] = result
    
    # Save session data and generate PDF
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = result.get("name", "unknown").replace(" ", "_").replace("/", "_")
        
        # Save complete session JSON
        json_filename = os.path.join(DATABASE_DIR, f"session_{timestamp}_{name}.json")
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        print(f"Saved session data to {json_filename}")
        
        # Generate PDF resume
        pdf_filename = os.path.join(DATABASE_DIR, f"resume_{timestamp}_{name}.pdf")
        generate_ats_resume_pdf(result, pdf_filename)
        print(f"Generated PDF resume: {pdf_filename}")
        
        # Clean up session from memory
        del session_storage[session_id]
        print(f"Cleaned up session: {session_id}")
        
    except Exception as e:
        print(f"Failed to save session/PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate resume: {str(e)}")
    
    return {
        "status": "success",
        "profile": result,
        "pdf_filename": f"resume_{timestamp}_{name}.pdf"
    }

@app.get("/download_resume/{filename}")
async def download_resume(filename: str):
    """Download generated PDF resume."""
    filepath = os.path.join(DATABASE_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Resume not found")
    return FileResponse(filepath, media_type='application/pdf', filename=filename)

@app.post("/build_profile_legacy")
async def build_profile(payload: Dict[str, Any] = Body(...)):
    """
    Accepts array of Q&A JSON responses, merges and normalizes into final profile.
    Payload: { "qa_responses": [{ "question_id": 1, "field": "name", "extracted_data": {...} }, ...] }
    """
    qa_responses = payload.get("qa_responses", [])
    if not qa_responses:
        raise HTTPException(status_code=400, detail="Q&A responses are required")
    
    # Merge all Q&A responses - extract data from nested structure
    merged_data = {}
    for item in qa_responses:
        # Each item has structure: { "question_id": 1, "field": "name", "extracted_data": {...} }
        if "extracted_data" in item and isinstance(item["extracted_data"], dict):
            merged_data.update(item["extracted_data"])
        elif "field" in item and any(k for k in item.keys() if k not in ["question_id", "field", "question", "transcript"]):
            # If data is at top level (legacy format)
            field_data = {k: v for k, v in item.items() if k not in ["question_id", "field", "question", "transcript"]}
            merged_data.update(field_data)
    
    prompt = f"""Here is raw resume data collected from a user interview:
{json.dumps(merged_data, indent=2)}

Please normalize and structure this into a clean professional resume JSON with these fields:
- name (string)
- role (string, job title/desired position)
- experience_years (number)
- experience_details (array of objects with: company, role, duration, description)
- skills (array of strings)
- languages (array of strings)
- location (string)
- education (array of objects with: degree, institution, year)
- certifications (array of strings)
- phone (string)
- email (string)
- summary (string, 2-3 sentences professional summary)
- extras (object for any additional relevant info)

Return ONLY a valid JSON object with all available fields. Use null for missing fields."""
    
    result = await call_gemini(prompt, system_message="You are an expert resume builder that creates structured JSON profiles.")
    
    # Save final resume to database
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = result.get("name", "unknown").replace(" ", "_")
        filename = os.path.join(DATABASE_DIR, f"resume_{timestamp}_{name}.json")
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        print(f"Saved resume to {filename}")
    except Exception as e:
        print(f"Failed to save resume: {e}")
    
    return {
        "status": "success",
        "profile": result
    }

@app.get("/")
async def root():
    return {"message": "JobSathi API - Resume Builder", "version": "6.0.0", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "JobSathi API"}

@app.get("/languages")
def list_languages():
    languages = [{"code": k, "label": v} for k, v in LANGUAGE_NAME.items()]
    return {"status": "success", "languages": languages}

@app.get("/model-status")
def model_status():
    asr_loaded = _asr_model is not None
    return {"asr_model_loaded": asr_loaded, "device": DEVICE}
