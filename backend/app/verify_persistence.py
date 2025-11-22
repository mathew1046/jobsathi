import requests
import json
import os
import time

BASE_URL = "http://localhost:8000"
DATABASE_DIR = "database"

def test_ask_llm():
    print("Testing /ask_llm...")
    payload = {
        "transcript": "Mera naam Rahul hai aur main software engineer hoon.",
        "question": "What is your name?",
        "field": "name"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ask_llm", json=payload)
        response.raise_for_status()
        data = response.json()
        print("Response:", json.dumps(data, indent=2))
        
        # Check if file created
        files = os.listdir(DATABASE_DIR)
        # Simple check if any new file looks like a response
        response_files = [f for f in files if f.startswith("response_")]
        if response_files:
             print(f"SUCCESS: Found response files: {response_files[-1]}")
        else:
             print("FAILURE: No response file found in database/")
             
    except Exception as e:
        print(f"Error testing /ask_llm: {e}")

def test_build_profile():
    print("\nTesting /build_profile...")
    payload = {
        "qa_responses": [
            {
                "question_id": 1,
                "field": "name",
                "extracted_data": {"name": "Rahul Sharma"}
            },
            {
                "question_id": 2,
                "field": "role",
                "extracted_data": {"role": "Software Engineer"}
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/build_profile", json=payload)
        response.raise_for_status()
        data = response.json()
        print("Response:", json.dumps(data, indent=2))
        
        # Check if file created
        files = os.listdir(DATABASE_DIR)
        resume_files = [f for f in files if f.startswith("resume_")]
        if resume_files:
             print(f"SUCCESS: Found resume files: {resume_files[-1]}")
        else:
             print("FAILURE: No resume file found in database/")

    except Exception as e:
        print(f"Error testing /build_profile: {e}")

if __name__ == "__main__":
    # Ensure we are in the right dir to check files, or use absolute path
    # Assuming script is run from backend/app
    if not os.path.exists(DATABASE_DIR):
        print(f"Warning: {DATABASE_DIR} does not exist yet.")
    
    test_ask_llm()
    time.sleep(2)
    test_build_profile()
