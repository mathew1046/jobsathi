import os
import httpx
import asyncio

TTS_SERVICE_URL = os.getenv("TTS_SERVICE_URL", "http://localhost:7861")

async def generate_audio(text: str, language: str) -> bytes:
    """
    Generate audio from text using the external TTS Space.
    """
    max_retries = 3
    base_delay = 1.0

    for attempt in range(max_retries):
        try:
            # We can customize the description based on language if needed
            # For now, we use a generic description or one that fits the context
            description = "A female speaker delivering a clear and professional speech."
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{TTS_SERVICE_URL}/tts",
                    json={
                        "text": text,
                        "description": description
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                return response.content
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                wait_time = base_delay * (2 ** attempt)
                print(f"TTS 429 error, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
            print(f"TTS HTTP error: {e}")
            return None
        except Exception as e:
            print(f"TTS error: {e}")
            return None
    
    print("TTS failed after max retries")
    return None
