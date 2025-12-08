import os
import httpx
import asyncio
from typing import Dict, List, Any

TRANSLATION_SERVICE_URL = os.getenv("TRANSLATION_SERVICE_URL", "https://0xmathew-jobsathi-translation.hf.space")

# FLORES-200 Code Mapping
LANG_CODE_MAP = {
    "en": "eng_Latn",
    "as": "asm_Beng",
    "bn": "ben_Beng",
    "brx": "brx_Deva",
    "doi": "doi_Deva",
    "gom": "gom_Deva",
    "gu": "guj_Gujr",
    "hi": "hin_Deva",
    "kn": "kan_Knda",
    "ks": "kas_Arab",
    "ks-deva": "kas_Deva",
    "mai": "mai_Deva",
    "ml": "mal_Mlym",
    "mr": "mar_Deva",
    "mni": "mni_Beng",
    "mni-mtei": "mni_Mtei",
    "npi": "npi_Deva",
    "or": "ory_Orya",
    "pa": "pan_Guru",
    "sa": "san_Deva",
    "sat": "sat_Olck",
    "sd": "snd_Arab",
    "sd-deva": "snd_Deva",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "ur": "urd_Arab",
}

# Simple in-memory cache: {(text, source_lang, target_lang): translated_text}
TRANSLATION_CACHE = {}

async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate text using the external Translation Space.
    """
    if not text or not text.strip():
        return text

    if source_lang == target_lang:
        return text
        
    # Check cache first
    cache_key = (text, source_lang, target_lang)
    if cache_key in TRANSLATION_CACHE:
        return TRANSLATION_CACHE[cache_key]
        
    src_code = LANG_CODE_MAP.get(source_lang)
    tgt_code = LANG_CODE_MAP.get(target_lang)
    
    if not src_code or not tgt_code:
        print(f"Warning: Unsupported language code {source_lang} or {target_lang}")
        return text

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TRANSLATION_SERVICE_URL}/translate",
                json={
                    "inputs": [text],
                    "source_lang": src_code,
                    "target_lang": tgt_code
                },
                timeout=60.0
            )
            response.raise_for_status()
            translations = response.json().get("translations", [])
            result = translations[0] if translations else text
            
            # Update cache on success
            TRANSLATION_CACHE[cache_key] = result
            return result
    except Exception as e:
        print(f"Translation error: {e}")
        return text

async def translate_ui_elements(elements: Dict[str, str], target_lang: str) -> Dict[str, str]:
    """
    Translate a dictionary of UI strings using batched requests.
    """
    # 0. Fast path for English or empty
    if target_lang == "en" or not elements:
        return elements

    # 1. Setup
    keys = list(elements.keys())
    values = [elements[k] for k in keys]
    
    src_code = LANG_CODE_MAP.get("en")
    tgt_code = LANG_CODE_MAP.get(target_lang)
    
    if not src_code or not tgt_code:
        print(f"Translation Warning: Unsupported language pair en -> {target_lang}")
        return elements

    print(f"Translating {len(values)} elements to {target_lang} ({tgt_code}) via {TRANSLATION_SERVICE_URL}")

    # 2. Chunking - smaller batches for CPU-bound model
    BATCH_SIZE = 10 
    translated_values = []
    
    async with httpx.AsyncClient(timeout=180.0) as client:  # 3 minute timeout for slow CPU inference
        for i in range(0, len(values), BATCH_SIZE):
            chunk = values[i:i + BATCH_SIZE]
            chunk_result = chunk # Default to original if fail
            
            # Retry loop
            for attempt in range(3):
                try:
                    response = await client.post(
                        f"{TRANSLATION_SERVICE_URL}/translate",
                        json={
                            "inputs": chunk,
                            "source_lang": src_code,
                            "target_lang": tgt_code
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "translations" in data and isinstance(data["translations"], list):
                            received = data["translations"]
                            if len(received) == len(chunk):
                                chunk_result = received
                                print(f"Chunk {i//BATCH_SIZE + 1} translated successfully")
                                break # Success
                            else:
                                print(f"Translation Mismatch: Sent {len(chunk)}, got {len(received)}")
                        else:
                            print(f"Translation Invalid Response: {data}")
                    elif response.status_code == 429:
                        wait = (attempt + 1) * 2
                        print(f"Translation Rate Limit (429). Retrying in {wait}s...")
                        await asyncio.sleep(wait)
                        continue
                    else:
                        print(f"Translation HTTP Error {response.status_code}: {response.text}")
                        break # Non-retriable
                        
                except httpx.TimeoutException:
                    print(f"Translation Timeout for chunk {i//BATCH_SIZE + 1} (attempt {attempt + 1})")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"Translation Exception: {type(e).__name__}: {e}")
                    await asyncio.sleep(1)
            
            translated_values.extend(chunk_result)
            # Nice delay
            await asyncio.sleep(0.5)

    # 3. Reconstruct
    result = {}
    for k, v in zip(keys, translated_values):
        result[k] = v
        
    return result
