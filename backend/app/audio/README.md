# Audio TTS Files for Questions

This directory contains Text-to-Speech (TTS) audio files for resume questions in multiple languages.

## Directory Structure

```
audio/
├── hi/          # Hindi
├── en/          # English
├── bn/          # Bengali
├── ta/          # Tamil
├── te/          # Telugu
├── ml/          # Malayalam
├── mr/          # Marathi
├── gu/          # Gujarati
├── pa/          # Punjabi
├── or/          # Odia
├── as/          # Assamese
└── [other language codes]/
```

## File Naming Convention

Each audio file should be named according to the question ID:
- `q1.mp3` - Question 1 (Full Name)
- `q2.mp3` - Question 2 (Role/Job Title)
- `q3.mp3` - Question 3 (Years of Experience)
- ... and so on up to `q15.mp3`

## Questions List

1. What is your full name?
2. What role or job title are you applying for?
3. How many years of experience do you have?
4. Tell me about your work experience
5. What are your key skills?
6. What languages do you speak?
7. Where are you located?
8. Tell me about your education
9. Do you have any certifications?
10. What is your phone number?
11. What is your email address?
12. Can you give a brief professional summary?
13. What type of work are you looking for?
14. Do you operate any machines or vehicles?
15. Do you have any referrals or additional information?

## How to Add Audio Files

### Option 1: Using Text-to-Speech Tools

You can generate audio files using online TTS tools:
- **Google Cloud TTS**: https://cloud.google.com/text-to-speech
- **Amazon Polly**: https://aws.amazon.com/polly/
- **Microsoft Azure TTS**: https://azure.microsoft.com/en-us/services/cognitive-services/text-to-speech/

### Option 2: Recording Your Own Voice

1. Record the question in the target language
2. Export as MP3 format
3. Name the file as `q{id}.mp3` (e.g., `q1.mp3`)
4. Place in the appropriate language folder

### Option 3: Using Python TTS Libraries

```python
from gtts import gTTS
import os

questions = {
    1: "What is your full name?",
    2: "What role or job title are you applying for?",
    # ... add all questions
}

language = "hi"  # Hindi
output_dir = f"audio/{language}/"

for qid, text in questions.items():
    tts = gTTS(text=text, lang=language, slow=False)
    tts.save(f"{output_dir}q{qid}.mp3")
```

## Audio Requirements

- **Format**: MP3
- **Bitrate**: 128kbps or higher recommended
- **Sample Rate**: 44.1kHz or 48kHz
- **Channels**: Mono or Stereo
- **Duration**: Keep concise (under 10 seconds per question)

## Behavior

- Audio auto-plays when a new question loads
- User can replay audio using the 🔁 button
- Audio stops automatically when:
  - User clicks Record button
  - User clicks Submit button
  - User clicks Re-record button
  - User moves to the next question
- If audio file is not found, displays: "TTS not available for this language"

## Testing

After adding audio files, test by:

1. Start the backend server
2. Navigate to the Q&A screen
3. Select the language
4. Verify audio plays automatically
5. Test replay button functionality
6. Check that audio stops when recording starts

## Support

If you need help generating audio files for specific languages, please refer to the project documentation or contact the development team.
