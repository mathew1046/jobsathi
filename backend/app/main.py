# jobsathi_api.py
# ASR + LLM-powered resume builder backend

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
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
from app.job_search import search_jobs
from dotenv import load_dotenv
from fastapi.responses import Response

# Load environment variables
load_dotenv()

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

# Mount audio files
app.mount("/audio", StaticFiles(directory="app/audio_files"), name="audio")

# Load configuration from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

ASR_MODEL_ID = os.getenv("ASR_MODEL_ID", "ai4bharat/indic-conformer-600m-multilingual")
DEVICE_CONFIG = os.getenv("DEVICE", "auto")
DEVICE = "cuda" if DEVICE_CONFIG == "auto" and torch.cuda.is_available() else "cpu"

# Database directory for storing responses
DATABASE_DIR = os.path.join(os.path.dirname(__file__), "database")
os.makedirs(DATABASE_DIR, exist_ok=True)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Configuration for Gemma (text-only, JSON-friendly)
GENERATION_CONFIG = {
    "temperature": 0.6,
    "top_p": 0.9,
    "top_k": 40,
    "max_output_tokens": 4096,
}

# Initialize the model
# Switched to gemma-3-27b-it to avoid 429s on flash endpoints
model = genai.GenerativeModel(
    model_name="gemma-3-27b-it",
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
    "as": "অসমীয়া", 
    "bn": "বাংলা", 
    "gu": "ગુજરાતી", 
    "hi": "हिन्दी", 
    "kn": "ಕನ್ನಡ", 
    "ml": "മലയാളം", 
    "mr": "मराठी", 
    "or": "ଓଡ଼ିଆ", 
    "pa": "ਪੰਜਾਬੀ", 
    "ta": "தமிழ்", 
    "te": "తెలుగు", 
    "en": "English"
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
            # Try loading with soundfile backend explicitly
            waveform, sr = torchaudio.load(tmp_path, backend="soundfile")
            print(f"Loaded with torchaudio (auto): shape {waveform.shape}, sr {sr}")
        except Exception as e:
            print(f"torchaudio.load auto failed: {e}. Trying mp3 format fallback.")
            # Try loading with soundfile backend explicitly
            waveform, sr = torchaudio.load(tmp_path, format="mp3", backend="soundfile")
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
            # unload_asr_model()  # TEMPORARILY COMMENTED OUT FOR SPEED IMPROVEMENT
            raise HTTPException(400, "ASR returned empty")

        # unload_asr_model()  # TEMPORARILY COMMENTED OUT FOR SPEED IMPROVEMENT
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

def validate_and_clean_data(data: Dict[str, Any], user_text: str = "") -> Dict[str, Any]:
    """
    Validate and clean data to remove common fake/dummy patterns.
    Also validates against actual user responses to ensure data authenticity.
    Returns cleaned data with fake values replaced by null.
    """
    # Common fake patterns
    FAKE_PATTERNS = {
        "email": [
            "example.com", "@example", "john@", "user@", "test@",
            "sample@", "demo@", "placeholder@", "dummy@"
        ],
        "phone": [
            "123-456-7890", "1234567890", "555-", "000-", "111-",
            "+91-1234567890", "+1-123-456-7890"
        ],
        "company": [
            "abc corporation", "xyz company", "example corp", "test company",
            "sample ltd", "demo inc", "placeholder", "unknown company"
        ],
        "school": [
            "university of xyz", "abc university", "example university",
            "test school", "sample college", "xyz institute"
        ],
        "generic": [
            "example", "sample", "test", "demo", "placeholder", "dummy",
            "lorem ipsum", "n/a", "not applicable", "tbd", "to be determined"
        ]
    }
    
    def clean_value(value, field_type="generic"):
        """Clean a single value and verify it appears in user text."""
        if not value:
            return None
        
        if isinstance(value, str):
            value_lower = value.lower().strip()
            
            # Check against patterns
            patterns = FAKE_PATTERNS.get(field_type, []) + FAKE_PATTERNS["generic"]
            for pattern in patterns:
                if pattern in value_lower:
                    print(f"⚠️ Detected fake pattern '{pattern}' in value '{value}' - removing")
                    return None
            
            # Check for very short or suspicious values
            if len(value_lower) < 2 and field_type not in ["name"]:
                return None
            
            # If user_text provided, verify the value appears in it (for important fields)
            if user_text and field_type in ["name", "email", "phone", "company", "school"]:
                # Allow partial matches for names and companies
                value_words = value_lower.split()
                found = any(word in user_text.lower() for word in value_words if len(word) > 2)
                if not found and len(value) > 3:
                    print(f"⚠️ Value '{value}' not found in user responses - removing")
                    return None
                
            return value
        
        return value
    
    # Clean top-level fields
    cleaned = {}
    
    # Name
    cleaned["name"] = clean_value(data.get("name"), "name")
    
    # Email
    email = data.get("email")
    cleaned["email"] = clean_value(email, "email")
    
    # Phone
    phone = data.get("phone")
    cleaned["phone"] = clean_value(phone, "phone")
    
    # Role
    cleaned["role"] = clean_value(data.get("role"))
    
    # Location
    cleaned["location"] = clean_value(data.get("location"))
    
    # Links
    links = data.get("links", {})
    if isinstance(links, dict):
        cleaned_links = {}
        for k, v in links.items():
            cleaned_v = clean_value(v)
            if cleaned_v:
                cleaned_links[k] = cleaned_v
        cleaned["links"] = cleaned_links if cleaned_links else {}
    else:
        cleaned["links"] = {}
    
    # Summary
    cleaned["summary"] = clean_value(data.get("summary"))
    
    # Experience years
    cleaned["experience_years"] = data.get("experience_years")
    
    # Experience details
    exp_details = data.get("experience_details", [])
    if isinstance(exp_details, list):
        cleaned_exp = []
        for exp in exp_details:
            if isinstance(exp, dict):
                cleaned_entry = {
                    "company": clean_value(exp.get("company"), "company"),
                    "role": clean_value(exp.get("role")),
                    "duration": clean_value(exp.get("duration")),
                    "description": clean_value(exp.get("description"))
                }
                # Only include if at least company or role is valid
                if cleaned_entry["company"] or cleaned_entry["role"]:
                    cleaned_exp.append(cleaned_entry)
        cleaned["experience_details"] = cleaned_exp
    else:
        cleaned["experience_details"] = []
    
    # Skills
    skills = data.get("skills", [])
    if isinstance(skills, list):
        cleaned_skills = [clean_value(s) for s in skills if clean_value(s)]
        cleaned["skills"] = cleaned_skills
    else:
        cleaned["skills"] = []
    
    # Education
    education = data.get("education", [])
    if isinstance(education, list):
        cleaned_edu = []
        for edu in education:
            if isinstance(edu, dict):
                cleaned_entry = {
                    "institution": clean_value(edu.get("institution"), "school"),
                    "degree": clean_value(edu.get("degree")),
                    "year": clean_value(edu.get("year"))
                }
                # Only include if at least institution or degree is valid
                if cleaned_entry["institution"] or cleaned_entry["degree"]:
                    cleaned_edu.append(cleaned_entry)
        cleaned["education"] = cleaned_edu
    else:
        cleaned["education"] = []
    
    # Certifications
    certs = data.get("certifications", [])
    if isinstance(certs, list):
        cleaned_certs = [clean_value(c) for c in certs if clean_value(c)]
        cleaned["certifications"] = cleaned_certs
    else:
        cleaned["certifications"] = []
    
    # Languages
    langs = data.get("languages", [])
    if isinstance(langs, list):
        cleaned_langs = [clean_value(l) for l in langs if clean_value(l)]
        cleaned["languages"] = cleaned_langs
    else:
        cleaned["languages"] = []
    
    # Extras
    extras = data.get("extras", {})
    if isinstance(extras, dict):
        cleaned_extras = {}
        for k, v in extras.items():
            cleaned_v = clean_value(v)
            if cleaned_v:
                cleaned_extras[k] = cleaned_v
        cleaned["extras"] = cleaned_extras if cleaned_extras else {}
    else:
        cleaned["extras"] = {}
    
    return cleaned


async def call_gemini(prompt: str, system_message: str = "You are a strict data extraction tool. Extract ONLY what is explicitly stated. NEVER fabricate, invent, or assume information. convert the user statement to formal text without assuming anything") -> Dict[str, Any]:
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
        if hasattr(e, 'response') and e.response:
             try:
                 print(f"Gemini feedback: {e.response.prompt_feedback}")
             except:
                 pass
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

⚠️ CRITICAL RULES - VIOLATING THESE IS STRICTLY FORBIDDEN:
1. Translate the user's answer to English EXACTLY as spoken - word for word. and make the answer formal without assuming anything or adding any information.
2. Extract ONLY the EXACT information the user explicitly stated.
3. NEVER EVER add ANY information that was not directly mentioned by the user.
4. NEVER make assumptions or guesses about missing information.
5. NEVER create placeholder, example, or dummy data.
6. If the user did not provide information for this field, return null or empty string.
7. If the answer is unclear or vague, use null - DO NOT interpret or guess.
8. incase of phone number or year, extract the digits and respond in standard format.
9. Extract the skills from the text and respond it in standard keyword, which can be be further used for matching jobs. only do this for skills field.

You are a DATA EXTRACTION TOOL, not a creative assistant. Your ONLY job is to copy what was said.

Return a JSON object with exactly TWO keys:
1. 'translation': The EXACT English translation - word-for-word, no additions.
2. 'extracted_data': A JSON object with the key '{field}' containing ONLY what the user explicitly said.

CORRECT Examples:
- User: "My name is John" → {{"translation": "My name is John", "extracted_data": {{"name": "John"}}}}
- User: "I have 5 years experience" → {{"translation": "I have 5 years experience", "extracted_data": {{"experience_years": 5}}}}
- User: "some experience" → {{"translation": "some experience", "extracted_data": {{"experience_years": null}}}}
- User: "I don't know" → {{"translation": "I don't know", "extracted_data": {{"{field}": null}}}}

WRONG Examples (NEVER DO THIS):
- User says nothing about email → DO NOT return "example@email.com"
- User says "I'm a driver" → DO NOT add "with 5 years experience" or any other details
- User gives minimal info → DO NOT expand or embellish

Return ONLY valid JSON. No explanations, no markdown, no extra text."""
    
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
    """Generate an ATS-friendly PDF resume from profile data - optimized for blue-collar workers."""
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
    
    contact_style = ParagraphStyle('Contact', parent=normal_style, alignment=TA_CENTER, fontSize=9)
    
    # Name and Role Header
    name = str(profile.get('name', 'Candidate Name'))
    story.append(Paragraph(name.upper(), title_style))
    
    # Desired Role (if specified)
    role = profile.get('role')
    if role:
        role_style = ParagraphStyle('Role', parent=normal_style, alignment=TA_CENTER, fontSize=11, textColor=colors.HexColor('#2c3e50'))
        story.append(Paragraph(str(role), role_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Contact information
    contact_parts = []
    if profile.get('email'):
        contact_parts.append(str(profile['email']))
    if profile.get('phone'):
        contact_parts.append(str(profile['phone']))
    if profile.get('location'):
        contact_parts.append(str(profile['location']))
    
    if contact_parts:
        contact_text = ' | '.join(contact_parts)
        story.append(Paragraph(contact_text, contact_style))
        story.append(Spacer(1, 0.15*inch))
    
    # Professional Summary
    summary = profile.get('summary', '')
    if summary:
        story.append(Paragraph('PROFESSIONAL SUMMARY', heading_style))
        story.append(Paragraph(str(summary), normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Key Availability Info (important for blue-collar jobs)
    availability_parts = []
    if profile.get('shift_availability'):
        availability_parts.append(f"Shift: {profile['shift_availability']}")
    if profile.get('start_date'):
        availability_parts.append(f"Can Start: {profile['start_date']}")
    if profile.get('work_type_preference'):
        availability_parts.append(f"Preference: {profile['work_type_preference']}")
    if profile.get('transportation'):
        availability_parts.append(f"Transport: {profile['transportation']}")
    
    if availability_parts:
        story.append(Paragraph('AVAILABILITY & PREFERENCES', heading_style))
        avail_text = ' | '.join(availability_parts)
        story.append(Paragraph(avail_text, normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Skills & Equipment
    skills = profile.get('skills', [])
    machines = profile.get('machines_operated', [])
    
    if skills and isinstance(skills, list):
        story.append(Paragraph('SKILLS', heading_style))
        skills_text = ' • '.join([str(s) for s in skills if s]) if skills else 'N/A'
        story.append(Paragraph(skills_text, normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    if machines and isinstance(machines, list) and len(machines) > 0:
        story.append(Paragraph('MACHINES/VEHICLES OPERATED', heading_style))
        machines_text = ' • '.join([str(m) for m in machines if m])
        story.append(Paragraph(machines_text, normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Physical Capabilities (important for blue-collar)
    physical = profile.get('physical_capabilities')
    if physical:
        story.append(Paragraph('PHYSICAL CAPABILITIES', heading_style))
        story.append(Paragraph(str(physical), normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Experience
    experience_details = profile.get('experience_details', [])
    experience_years = profile.get('experience_years')
    
    if experience_details and isinstance(experience_details, list):
        exp_title = 'WORK EXPERIENCE'
        if experience_years:
            exp_title += f' ({experience_years} years total)'
        story.append(Paragraph(exp_title, heading_style))
        for exp in experience_details:
            if isinstance(exp, dict):
                company = str(exp.get('company', 'Company'))
                exp_role = str(exp.get('role', 'Role'))
                duration = str(exp.get('duration', '')) if exp.get('duration') else ''
                description = str(exp.get('description', '')) if exp.get('description') else ''
                
                exp_header = f"<b>{exp_role}</b> - {company}"
                if duration:
                    exp_header += f" ({duration})"
                story.append(Paragraph(exp_header, normal_style))
                
                if description:
                    story.append(Paragraph(f"• {description}", normal_style))
                story.append(Spacer(1, 0.08*inch))
            elif isinstance(exp, str):
                story.append(Paragraph(f"• {exp}", normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Education
    education = profile.get('education', [])
    if education and isinstance(education, list):
        story.append(Paragraph('EDUCATION', heading_style))
        for edu in education:
            if isinstance(edu, dict):
                degree = str(edu.get('degree', 'Degree'))
                institution = str(edu.get('institution', 'Institution'))
                year = str(edu.get('year', '')) if edu.get('year') else ''
                
                edu_text = f"<b>{degree}</b> - {institution}"
                if year:
                    edu_text += f" ({year})"
                story.append(Paragraph(edu_text, normal_style))
                story.append(Spacer(1, 0.08*inch))
            elif isinstance(edu, str):
                story.append(Paragraph(f"• {edu}", normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Certifications
    certifications = profile.get('certifications', [])
    if certifications and isinstance(certifications, list) and len(certifications) > 0:
        story.append(Paragraph('CERTIFICATIONS & TRAINING', heading_style))
        for cert in certifications:
            if cert:
                story.append(Paragraph(f"• {str(cert)}", normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Languages
    languages = profile.get('languages', [])
    if languages and isinstance(languages, list) and len(languages) > 0:
        story.append(Paragraph('LANGUAGES', heading_style))
        lang_text = ', '.join([str(lang) for lang in languages if lang])
        story.append(Paragraph(lang_text, normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Work Authorization
    work_auth = profile.get('work_authorization')
    if work_auth:
        story.append(Paragraph('WORK AUTHORIZATION', heading_style))
        story.append(Paragraph(str(work_auth), normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # References (if provided)
    referrals = profile.get('referrals', [])
    if referrals and isinstance(referrals, list) and len(referrals) > 0:
        story.append(Paragraph('REFERENCES', heading_style))
        for ref in referrals:
            if isinstance(ref, dict):
                ref_name = ref.get('name', '')
                ref_contact = ref.get('contact', ref.get('phone', ''))
                ref_relation = ref.get('relation', '')
                ref_text = f"• {ref_name}"
                if ref_relation:
                    ref_text += f" ({ref_relation})"
                if ref_contact:
                    ref_text += f" - {ref_contact}"
                story.append(Paragraph(ref_text, normal_style))
            elif isinstance(ref, str):
                story.append(Paragraph(f"• {ref}", normal_style))
    
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
    
    # Build English text from all translated responses
    english_responses = []
    for item in responses:
        question = item.get("question", "")
        translated_text = item.get("translated_text", "")
        if translated_text:
            english_responses.append(f"Q: {question}\nA: {translated_text}")
    
    # Join all responses into a single English text
    full_english_text = "\n\n".join(english_responses)
    
    # Create ATS-optimized resume using LLM - includes ALL 20 question fields for blue-collar workers
    prompt = f"""Here is a complete interview transcript in English from a job seeker:

{full_english_text}

TASK:
Extract ALL information from the provided English text and convert it into a structured JSON resume. This is for blue-collar workers in India.

ABSOLUTE RULES (must NEVER be broken):
- Do NOT create, guess, or invent any information.
- Do NOT generate placeholder or dummy data (no fake emails, phones, companies, schools, dates, roles, etc.).
- Do NOT infer or assume anything not explicitly stated.
- Do NOT rewrite or improve content except for skill normalization.
- Anything missing must remain null, [], or {{}} exactly as instructed.

ALLOWED ACTIONS:
- Copy all information exactly as written in the source text.
- Standardize skill-like phrases into globally recognized skill names (e.g., "i drive cars" -> "Two Wheeler Driving", "i can lift heavy" -> "Physical Labor").
- Convert all number words into numeric digits (e.g., "five" -> 5).
- Normalize job titles for blue-collar roles (e.g., "delivery boy" -> "Delivery Executive", "driver" -> "Professional Driver").

OUTPUT FORMAT (fill ONLY fields present in the text; everything else stays null/empty):

{{
  "name": null,
  "role": null,
  "email": null,
  "phone": null,
  "location": null,
  "work_authorization": null,
  "machines_operated": [],
  "certifications": [],
  "shift_availability": null,
  "start_date": null,
  "transportation": null,
  "physical_capabilities": null,
  "experience_years": null,
  "experience_details": [],
  "languages": [],
  "work_type_preference": null,
  "skills": [],
  "referrals": [],
  "education": [],
  "summary": null,
  "links": {{}},
  "extras": {{}}
}}

FIELD DEFINITIONS:
- name: Full name of the candidate
- role: Desired job title/role
- email: Email address
- phone: Phone number (digits only)
- location: City, area, or state where they want to work
- work_authorization: Citizen, visa type, or work permit status
- machines_operated: List of machines/vehicles they can operate (bikes, trucks, forklifts, cutting machines, etc.)
- certifications: Training certificates or course completions
- shift_availability: Day shift, night shift, weekend, rotating, etc.
- start_date: When they can start (immediately, 2 weeks, specific date)
- transportation: How they commute (own bike, public transport, company vehicle, etc.)
- physical_capabilities: Ability to do physical work (can lift 50kg, can stand 8 hours, etc.)
- experience_years: Total years of work experience (numeric)
- experience_details: Array of past jobs with {{company, role, duration, description}}
- languages: Languages they speak with proficiency
- work_type_preference: Full-time, part-time, contract, gig work
- skills: Technical and soft skills relevant to blue-collar work
- referrals: References with contact info if provided
- education: Array with {{degree, institution, year}}
- summary: Brief work summary as stated by the candidate

NOTES:
- If the user doesn't provide a value, leave the field null/empty.
- Skill normalization is allowed for blue-collar context.
- Number words must always be converted to digits.
- No assumptions. No hallucinations. No invented data.
"""
    
    result = await call_gemini(prompt, system_message="You are a JSON converter. Your ONLY job is to copy data from input to output structure. You MUST NOT generate, create, or invent ANY data. If a field has no data, output null or []. Outputting fake data is a critical error.")
    # ⚠️ CRITICAL: Validate and clean result to remove fake patterns
    print("🔍 Validating data for fake patterns...")
    
    # Build a validation text from all English responses for cross-checking
    validation_text = " ".join([str(item.get("translated_text", "")).lower() for item in responses])
    
    cleaned_result = validate_and_clean_data(result, validation_text)
    print("✅ Data validation complete")
    
    # Mark session as completed
    session_data["metadata"]["completed"] = True
    session_data["metadata"]["completed_at"] = datetime.now().isoformat()
    session_data["profile"] = cleaned_result
    
    # Save session data and generate PDF
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_name = cleaned_result.get("name")
        safe_name = str(raw_name or "unknown")
        safe_name = safe_name.replace(" ", "_").replace("/", "_")
        
        # Save complete session JSON
        json_filename = os.path.join(DATABASE_DIR, f"session_{timestamp}_{safe_name}.json")
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        print(f"Saved session data to {json_filename}")
        
        # Generate PDF resume
        pdf_filename = os.path.join(DATABASE_DIR, f"resume_{timestamp}_{safe_name}.pdf")
        generate_ats_resume_pdf(cleaned_result, pdf_filename)
        print(f"Generated PDF resume: {pdf_filename}")
        
        # Clean up session from memory
        del session_storage[session_id]
        print(f"Cleaned up session: {session_id}")
        
    except Exception as e:
        print(f"Failed to save session/PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate resume: {str(e)}")
    
    return {
        "status": "success",
        "profile": cleaned_result,
        "pdf_filename": f"resume_{timestamp}_{safe_name}.pdf"
    }

@app.get("/download_resume/{filename}")
async def download_resume(filename: str):
    """Download generated PDF resume."""
    filepath = os.path.join(DATABASE_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Resume not found")
    return FileResponse(filepath, media_type='application/pdf', filename=filename)

@app.post("/search_jobs")
async def search_jobs_endpoint(payload: Dict[str, Any] = Body(...)):
    """
    Search for relevant jobs based on user profile.
    Payload: { "profile": {...} }
    Returns: { "status": "success", "jobs": [...], "count": 25 }
    """
    profile = payload.get("profile")
    
    if not profile:
        raise HTTPException(status_code=400, detail="Profile data is required")
    
    try:
        # Search jobs using the job_search module
        jobs = search_jobs(profile, min_score=3)
        
        return {
            "status": "success",
            "jobs": jobs,
            "count": len(jobs)
        }
    except Exception as e:
        print(f"Job search error: {e}")
        raise HTTPException(status_code=500, detail=f"Job search failed: {str(e)}")

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

@app.api_route("/audio/{language}/{filename}", methods=["GET", "HEAD"])
async def serve_audio(language: str, filename: str):
    """Serve TTS audio files for questions."""
    audio_dir = os.path.join(os.path.dirname(__file__), "audio", language)
    audio_path = os.path.join(audio_dir, filename)
    
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(audio_path, media_type='audio/mpeg')
