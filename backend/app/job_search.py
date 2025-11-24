# job_search.py
# Multi-source job aggregation module

import requests
import feedparser
from typing import List, Dict, Any, Set
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# -----------------------------
# API CREDENTIALS
# -----------------------------
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
JOOBLE_KEY = os.getenv("JOOBLE_KEY", "")
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")


# -----------------------------
# DYNAMIC KEYWORD GENERATOR
# -----------------------------
def generate_keywords(profile: Dict[str, Any]) -> List[str]:
    """Generate search keywords from profile data."""
    keywords = set()

    # Primary role - highest priority
    role = profile.get("role", "")
    if role and isinstance(role, str) and role.lower() not in ['null', 'none', '']:
        keywords.add(role.strip())
    
    # Skills - add ALL relevant skills
    skills = profile.get("skills", [])
    if isinstance(skills, list):
        for skill in skills:
            if skill and isinstance(skill, str) and len(skill.strip()) > 2:
                keywords.add(skill.strip())
    
    # Experience details - extract roles and companies
    experience_details = profile.get("experience_details", [])
    if isinstance(experience_details, list):
        for exp in experience_details:
            if isinstance(exp, dict):
                exp_role = exp.get("role", "")
                if exp_role and isinstance(exp_role, str):
                    keywords.add(exp_role.strip())
                # Also add company industry/type if relevant
                company = exp.get("company", "")
                if company and isinstance(company, str):
                    keywords.add(company.strip())
    
    # Education - add field of study
    education = profile.get("education", [])
    if isinstance(education, list):
        for edu in education:
            if isinstance(edu, dict):
                degree = edu.get("degree", "")
                if degree and isinstance(degree, str):
                    keywords.add(degree.strip())
    
    # Certifications - add as keywords
    certifications = profile.get("certifications", [])
    if isinstance(certifications, list):
        for cert in certifications:
            if cert and isinstance(cert, str) and len(cert.strip()) > 2:
                keywords.add(cert.strip())
    
    # Remove any null, empty, or invalid keywords
    keywords = {k for k in keywords if k and isinstance(k, str) and k.lower() not in ['null', 'none', 'n/a', '']}
    
    # Prioritize role and skills, limit total to avoid too many API calls
    keyword_list = list(keywords)
    # Put role first if it exists
    if role and role in keyword_list:
        keyword_list.remove(role)
        keyword_list.insert(0, role)
    
    return keyword_list[:8]  # Increased from 5 to 8 for better coverage


# -----------------------------
# ADZUNA API
# -----------------------------
def fetch_adzuna(keywords: List[str], location: str = "India") -> List[Dict[str, Any]]:
    """Fetch jobs from Adzuna API."""
    results = []
    
    try:
        for kw in keywords[:3]:  # Limit to 3 keywords to reduce API calls
            params = {
                "app_id": ADZUNA_APP_ID,
                "app_key": ADZUNA_APP_KEY,
                "results_per_page": 20,
                "what": kw,
                "where": location
            }
            url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
            r = requests.get(url, params=params, timeout=10)

            if r.status_code == 200:
                data = r.json()
                for job in data.get("results", []):
                    results.append({
                        "source": "Adzuna",
                        "title": job.get("title", ""),
                        "company": job.get("company", {}).get("display_name", "N/A"),
                        "location": job.get("location", {}).get("display_name", location),
                        "url": job.get("redirect_url", ""),
                        "description": job.get("description", "")[:300],  # Truncate long descriptions
                        "salary": job.get("salary_max", "Not specified")
                    })
    except Exception as e:
        print(f"Adzuna API error: {e}")
    
    return results


# -----------------------------
# JOOBLE API
# -----------------------------
def fetch_jooble(keywords: List[str], location: str = "India") -> List[Dict[str, Any]]:
    """Fetch jobs from Jooble API."""
    results = []
    
    try:
        url = f"https://in.jooble.org/api/{JOOBLE_KEY}"
        
        for kw in keywords[:3]:  # Limit to 3 keywords
            payload = {"keywords": kw, "location": location}
            r = requests.post(url, json=payload, timeout=10)

            if r.status_code == 200:
                data = r.json()
                for job in data.get("jobs", []):
                    results.append({
                        "source": "Jooble",
                        "title": job.get("title", ""),
                        "company": job.get("company", "N/A"),
                        "location": job.get("location", location),
                        "url": job.get("link", ""),
                        "description": job.get("snippet", "")[:300],
                        "salary": job.get("salary", "Not specified")
                    })
    except Exception as e:
        print(f"Jooble API error: {e}")
    
    return results


# -----------------------------
# SERPAPI GOOGLE JOBS
# -----------------------------
def fetch_serpapi(keywords: List[str], location: str = "India") -> List[Dict[str, Any]]:
    """Fetch jobs from Google Jobs via SerpAPI."""
    results = []
    
    try:
        for kw in keywords[:3]:  # Limit to 3 keywords
            params = {
                "engine": "google_jobs",
                "q": kw,
                "location": location,
                "api_key": SERPAPI_KEY
            }
            url = "https://serpapi.com/search"
            r = requests.get(url, params=params, timeout=10)

            if r.status_code == 200:
                data = r.json()
                for job in data.get("jobs_results", []):
                    apply_link = ""
                    apply_options = job.get("apply_options", [])
                    if apply_options and len(apply_options) > 0:
                        apply_link = apply_options[0].get("link", "")
                    
                    results.append({
                        "source": "Google Jobs",
                        "title": job.get("title", ""),
                        "company": job.get("company_name", "N/A"),
                        "location": job.get("location", location),
                        "url": apply_link,
                        "description": job.get("description", "")[:300],
                        "salary": "Not specified"
                    })
    except Exception as e:
        print(f"SerpAPI error: {e}")
    
    return results


# -----------------------------
# MERGE & REMOVE DUPLICATES
# -----------------------------
def merge_results(*sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge job results and remove duplicates."""
    seen: Set[tuple] = set()
    final = []

    for source in sources:
        for job in source:
            # Create unique identifier
            uid = (
                str(job.get("title", "")).lower().strip(),
                str(job.get("company", "")).lower().strip(),
                str(job.get("location", "")).lower().strip()
            )
            
            if uid not in seen and job.get("title"):
                seen.add(uid)
                final.append(job)

    return final


# -----------------------------
# RELEVANCE SCORING
# -----------------------------
def score_relevance(job: Dict[str, Any], profile: Dict[str, Any]) -> int:
    """Score job relevance based on profile match."""
    score = 0
    
    job_title = str(job.get("title", "")).lower()
    job_desc = str(job.get("description", "")).lower()
    
    # Check role match (highest weight)
    role = profile.get("role", "")
    if role and isinstance(role, str) and role.lower() not in ['null', 'none', '']:
        role_lower = role.lower()
        if role_lower in job_title:
            score += 15
        if role_lower in job_desc:
            score += 7
    
    # Check skills match
    skills = profile.get("skills", [])
    if isinstance(skills, list):
        for skill in skills:
            if isinstance(skill, str) and skill.lower() not in ['null', 'none', '']:
                skill_lower = skill.lower()
                if skill_lower in job_title:
                    score += 10
                if skill_lower in job_desc:
                    score += 4
            elif isinstance(skill, dict):
                # Handle skill objects with name/level properties
                skill_name = str(skill.get('name', skill.get('skill', ''))).lower()
                if skill_name and skill_name not in ['null', 'none', '']:
                    if skill_name in job_title:
                        score += 10
                    if skill_name in job_desc:
                        score += 4
    
    # Check certifications match
    certifications = profile.get("certifications", [])
    if isinstance(certifications, list):
        for cert in certifications:
            if isinstance(cert, str) and cert.lower() not in ['null', 'none', '']:
                cert_lower = cert.lower()
                if cert_lower in job_title or cert_lower in job_desc:
                    score += 8
            elif isinstance(cert, dict):
                # Handle cert objects
                cert_name = str(cert.get('name', cert.get('certification', ''))).lower()
                if cert_name and cert_name not in ['null', 'none', '']:
                    if cert_name in job_title or cert_name in job_desc:
                        score += 8
    
    # Check education/degree match
    education = profile.get("education", [])
    if isinstance(education, list):
        for edu in education:
            if isinstance(edu, dict):
                degree = edu.get("degree", "")
                if degree and isinstance(degree, str):
                    degree_lower = degree.lower()
                    if degree_lower and degree_lower not in ['null', 'none', '']:
                        if degree_lower in job_title or degree_lower in job_desc:
                            score += 6
    
    # Check experience level match
    experience_years = profile.get("experience_years")
    if experience_years and str(experience_years).lower() not in ['null', 'none', '0']:
        try:
            years = int(experience_years)
            # Check if job mentions experience requirements
            if years >= 5 and ('senior' in job_title or 'lead' in job_title):
                score += 5
            elif years >= 2 and years < 5 and ('mid' in job_title or 'intermediate' in job_title):
                score += 5
            elif years < 2 and ('junior' in job_title or 'entry' in job_title or 'fresher' in job_title):
                score += 5
        except:
            pass
    
    # Check location match
    profile_location = str(profile.get("location", "")).lower() if profile.get("location") else ""
    job_location = str(job.get("location", "")).lower() if job.get("location") else ""
    if profile_location and profile_location not in ['null', 'none', '']:
        if profile_location in job_location:
            score += 8
        # Partial match for city/state
        location_parts = profile_location.split()
        for part in location_parts:
            if len(part) > 2 and part in job_location:
                score += 3
                break
    
    # Check languages if specified
    languages = profile.get("languages", [])
    if isinstance(languages, list):
        for lang in languages:
            if isinstance(lang, str) and lang.lower() not in ['null', 'none', 'english']:
                lang_lower = lang.lower()
                if lang_lower in job_desc:
                    score += 4
            elif isinstance(lang, dict):
                # Handle language objects with language/proficiency properties
                lang_name = str(lang.get('language', lang.get('name', ''))).lower()
                if lang_name and lang_name not in ['null', 'none', 'english']:
                    if lang_name in job_desc:
                        score += 4
    
    return score


# -----------------------------
# MAIN FUNCTION
# -----------------------------
def search_jobs(profile: Dict[str, Any], min_score: int = 5) -> List[Dict[str, Any]]:
    """
    Search for jobs across multiple sources based on profile.
    
    Args:
        profile: User profile dict with role, skills, location, etc.
        min_score: Minimum relevance score to include job
    
    Returns:
        List of relevant job postings sorted by relevance
    """
    print("🔍 Searching jobs for profile...")
    
    # Generate keywords
    keywords = generate_keywords(profile)
    print(f"📋 Keywords: {keywords}")
    
    # Get location from profile with fallback
    location = profile.get("location", "")
    if not location or (isinstance(location, str) and location.lower() in ['null', 'none', '']):
        location = "India"  # Default fallback
    else:
        location = str(location)  # Ensure it's a string
    print(f"📍 Location: {location}")
    
    # Fetch from all sources
    adzuna_jobs = fetch_adzuna(keywords, location)
    jooble_jobs = fetch_jooble(keywords, location)
    serpapi_jobs = fetch_serpapi(keywords, location)
    
    print(f"✅ Fetched: {len(adzuna_jobs)} from Adzuna, {len(jooble_jobs)} from Jooble, {len(serpapi_jobs)} from SerpAPI")
    
    # Merge and deduplicate
    all_jobs = merge_results(adzuna_jobs, jooble_jobs, serpapi_jobs)
    print(f"🔄 Merged to {len(all_jobs)} unique jobs")
    
    # Score and filter jobs
    scored_jobs = []
    for job in all_jobs:
        relevance = score_relevance(job, profile)
        if relevance >= min_score:
            job["relevance_score"] = relevance
            scored_jobs.append(job)
    
    # Sort by relevance
    scored_jobs.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    print(f"✨ Returning {len(scored_jobs)} relevant jobs (min score: {min_score})")
    
    return scored_jobs
