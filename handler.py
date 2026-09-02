import os
import time
import base64
import torch
import torchaudio
import scipy.io.wavfile
import runpod
from transformers import AutoProcessor, MusicgenForConditionalGeneration

ALL_GENRES = [
    "Trance / Uplifting",
    "Drum & Bass",
    "Dark Techno / Industrial",
    "House / Tech House",
    "Synthwave / Cyberpunk",
    "Hardstyle / Rawstyle",
    "Dubstep / Riddim",
    "Ambient / Cinematic",
    "Psytrance",
    "Progressive House"
]

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Initializing MusicGen on serverless worker device: {device.upper()}...")

processor = AutoProcessor.from_pretrained("facebook/musicgen-medium")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-medium").to(device)
print("Serverless model successfully loaded!")


def handler(event):
    try:
        job_input = event.get("input", {})

        prompt = job_input.get("prompt", "")
        bpm = int(job_input.get("bpm", 175))
        genre = job_input.get("genre", "Drum & Bass")
        duration = int(job_input.get("duration", 60))
        exclude_genres = job_input.get("exclude_genres", "")
        has_vocals = bool(job_input.get("has_vocals", False))
        vocal_gender = job_input.get("vocal_gender", "female")

        if not prompt:
            return {"error": "Missing required field: prompt"}

        target_duration = min(max(duration, 10), 300)
        print(f"[SERVERLESS] Generating {genre} | {bpm} BPM | Vocals: {has_vocals} ({vocal_gender}) | Duration: {target_duration}s")

        vocal_desc = f"with clear {vocal_gender} vocals" if has_vocals else "instrumental track without vocals"
        exclusions_text = f", avoiding elements of {exclude_genres}" if exclude_genres else ""
        full_prompt = f"Full professional mix arrangement, {vocal_desc}, {genre}, {bpm} BPM{exclusions_text}: {prompt}"

        inputs = processor(text=[full_prompt], padding=True, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items() if hasattr(v, "to")}

        max_tokens = int(target_duration * 50)
        print(f"[SERVERLESS] Running model inference (Tokens: {max_tokens})...")

        audio_values = model.generate(**inputs, max_new_tokens=max_tokens)
        audio_np = audio_values[0, 0].cpu().numpy()

        output_filename = f"/tmp/fusionworx_{int(bpm)}bpm_{int(time.time())}.wav"
        scipy.io.wavfile.write(output_filename, model.config.audio_encoder.sampling_rate, audio_np)

        with open(output_filename, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode("utf-8")

        os.remove(output_filename)
        print("[SERVERLESS] Track rendered successfully!")

        return {
            "status": "success",
            "message": f"Track generated for {genre}",
            "audio_base64": audio_base64,
            "genre": genre,
            "bpm": bpm
        }

    except Exception as e:
        print(f"[SERVERLESS ERROR]: {e}")
        return {"error": str(e)}


runpod.serverless.start({"handler": handler})
