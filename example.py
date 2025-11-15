import torch
import torchaudio
from transformers import AutoModel, AutoTokenizer, AutoModelForSeq2SeqLM
from IndicTransToolkit.processor import IndicProcessor

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print("Using:", DEVICE)

# -----------------------------
# 1. ASR MODEL (Malayalam)
# -----------------------------
asr_model = AutoModel.from_pretrained(
    "ai4bharat/indic-conformer-600m-multilingual",
    trust_remote_code=True
)

# -----------------------------
# 2. TRANSLATION MODEL (Malayalam → English)
# -----------------------------
trans_model_name = "ai4bharat/indictrans2-indic-en-dist-200M"

tokenizer = AutoTokenizer.from_pretrained(
    trans_model_name,
    trust_remote_code=True
)

trans_model = AutoModelForSeq2SeqLM.from_pretrained(
    trans_model_name,
    trust_remote_code=True,
    dtype=torch.float16 if DEVICE == "cuda" else torch.float32
).to(DEVICE)

ip = IndicProcessor(inference=True)

# -----------------------------
# CHUNKER FUNCTION
# -----------------------------
def chunk_text(text, max_words=180):   # safe for 200M model
    words = text.split()
    chunks = []
    current = []
    
    for w in words:
        current.append(w)
        if len(current) >= max_words:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks


# -----------------------------
# MAIN FUNCTION
# -----------------------------
def transcribe_and_translate(audio_path):
    # Load audio
    wav, sr = torchaudio.load(audio_path)
    wav = torch.mean(wav, dim=0, keepdim=True)

    if sr != 16000:
        wav = torchaudio.transforms.Resample(sr, 16000)(wav)

    # ASR (rnnt)
    transcript = asr_model(wav, "ml", "rnnt")
    print("\n[Malayalam Transcript]")
    print(transcript)

    # Chunk long text
    chunks = chunk_text(transcript)
    
    english_chunks = []
    src_lang = "mal_Mlym"
    tgt_lang = "eng_Latn"

    # Translate each chunk
    for ch in chunks:
        batch = ip.preprocess_batch(
            [ch],
            src_lang=src_lang,
            tgt_lang=tgt_lang
        )

        inputs = tokenizer(
            batch,
            return_tensors="pt",
            padding=True,
            truncation=True  # prevents crash
        ).to(DEVICE)

        with torch.no_grad():
            out = trans_model.generate(
                **inputs,
                max_length=256,
                num_beams=5,
                use_cache=False  # IMPORTANT fix
            )

        decoded = tokenizer.batch_decode(
            out,
            skip_special_tokens=True
        )
        eng = ip.postprocess_batch(decoded, lang=tgt_lang)[0]
        english_chunks.append(eng)

    final_english = " ".join(english_chunks)

    print("\n\n=== FINAL ENGLISH TRANSLATION ===\n")
    print(final_english)
    return final_english


# -----------------------------
# CALL THE FUNCTION
# -----------------------------
transcribe_and_translate("audio.mp3")
