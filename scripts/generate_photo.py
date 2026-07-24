#!/usr/bin/env python3
"""Vygeneruje fotku jedla cez Gemini (nanobanana) z foto_prompt receptu.

Použitie:
    GEMINI_API_KEY=... python3 scripts/generate_photo.py "<prompt>" output.png [--aspect 9:16] [--model gemini-3.1-flash-image]

Vyžaduje GEMINI_API_KEY v prostredí (Google AI Studio -> API key) a balík google-genai
(pip install google-genai). Fotky sa negenerujú do repa (CLAUDE.md) - ulož mimo verzovania
a odkaz (foto_url) dopln do receptu ručne po nahratí niekam, kde je prístupný.
"""
import argparse
import os
import sys

from google import genai
from google.genai import types


def generate_photo(prompt: str, output_path: str, aspect: str = "9:16", model: str = "gemini-3.1-flash-image") -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("Chýba GEMINI_API_KEY v prostredí.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=aspect),
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            with open(output_path, "wb") as f:
                f.write(part.inline_data.data)
            print(f"Uložené: {output_path} ({len(part.inline_data.data)} bajtov)")
            return

    sys.exit("Odpoveď neobsahovala obrázok.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", help="Foto prompt (z receptu)")
    parser.add_argument("output", help="Cesta k výstupnému PNG súboru")
    parser.add_argument("--aspect", default="9:16", help="Pomer strán (default 9:16)")
    parser.add_argument("--model", default="gemini-3.1-flash-image", help="Model (default gemini-3.1-flash-image = Nano Banana 2, near-pro kvalita)")
    args = parser.parse_args()

    generate_photo(args.prompt, args.output, args.aspect, args.model)
