"""AI engine for Bridge Board.

Four functions, each one LLM call:
    extract_event(image_bytes, mime)  -> dict   (vision: flyer photo to structured event)
    tag_and_translate(event)          -> dict   (category, summaries in English + Spanish)
    make_plan(brain_dump, events)     -> dict   (rank ideas, pick one action linked to a board event)
    draft_outreach(event, plan)       -> str    (message from the student to the organizer)

Set AI_PROVIDER to "anthropic" or "openai" in .env, plus the matching API key.
"""

from __future__ import annotations

import base64
import json
import os
import re

from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
DEFAULT_MODELS = {
    "gemini": "gemini-flash-latest",
    "anthropic": "claude-sonnet-5-5",
    "openai": "gpt-4o-mini",
}
MODEL = os.getenv("MODEL") or DEFAULT_MODELS.get(PROVIDER, "")

CATEGORIES = ["Health", "Volunteer", "Social", "Education", "Other"]


# ---------------------------------------------------------------------------
# Low level: one function that talks to whichever provider is configured
# ---------------------------------------------------------------------------

def _call_llm(prompt: str, image_bytes: bytes | None = None, mime: str = "image/jpeg",
              max_tokens: int = 1200) -> str:
    if PROVIDER == "gemini":
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        contents = []
        if image_bytes:
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime))
        contents.append(prompt)
        resp = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(max_output_tokens=max_tokens * 2),
        )
        return resp.text or ""

    if PROVIDER == "anthropic":
        import anthropic

        client = anthropic.Anthropic()
        content = []
        if image_bytes:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime,
                    "data": base64.b64encode(image_bytes).decode(),
                },
            })
        content.append({"type": "text", "text": prompt})
        resp = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": content}],
        )
        return "".join(b.text for b in resp.content if b.type == "text")

    if PROVIDER == "openai":
        from openai import OpenAI

        client = OpenAI()
        content = [{"type": "text", "text": prompt}]
        if image_bytes:
            data_url = f"data:{mime};base64,{base64.b64encode(image_bytes).decode()}"
            content.append({"type": "image_url", "image_url": {"url": data_url}})
        resp = client.chat.completions.create(
            model=MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": content}],
        )
        return resp.choices[0].message.content or ""

    raise ValueError(f"Unknown AI_PROVIDER: {PROVIDER}")


def _parse_json(text: str) -> dict:
    """Pull the first JSON object out of a model reply, even if wrapped in ``` fences."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"Model did not return JSON:\n{text[:500]}")
    return json.loads(match.group(0))


# ---------------------------------------------------------------------------
# Feature 1: flyer photo -> event
# ---------------------------------------------------------------------------

def extract_event(image_bytes: bytes, mime: str = "image/jpeg") -> dict:
    prompt = """You are reading a photo of a community flyer.
Extract the event details. Return ONLY a JSON object with these keys:
{
  "title": string,
  "date": "YYYY-MM-DD" or "" if unknown,
  "time": string or "",
  "location": string or "",
  "organizer": string or "",
  "contact": email, phone, or website shown on the flyer, or "",
  "raw_text": the main text of the flyer in one short paragraph
}
Only use information visible on the flyer. Use "" for anything missing. Do not guess."""
    return _parse_json(_call_llm(prompt, image_bytes, mime))


# ---------------------------------------------------------------------------
# Feature 2: tag + translate
# ---------------------------------------------------------------------------

def tag_and_translate(event: dict) -> dict:
    prompt = f"""Here is a community event near Lincoln University in Oxford, Pennsylvania:
{json.dumps(event, ensure_ascii=False)}

Return ONLY a JSON object:
{{
  "category": one of {CATEGORIES},
  "summary_en": a friendly 2 sentence summary in English,
  "summary_es": the same summary in natural Spanish,
  "how_students_can_help": one sentence on how a college student could help or join
}}"""
    return _parse_json(_call_llm(prompt))


# ---------------------------------------------------------------------------
# Feature 4: "I'm overwhelmed" mode
# ---------------------------------------------------------------------------

def make_plan(brain_dump: str, events: list[dict]) -> dict:
    board = [
        {k: e.get(k, "") for k in ("id", "title", "date", "category", "organizer", "summary_en")}
        for e in events
    ]
    prompt = f"""A Lincoln University student wants to improve the relationship between
Lincoln and the Oxford, PA community but feels overwhelmed. Here is their brain dump:

\"\"\"{brain_dump}\"\"\"

Here are real events currently on the community board:
{json.dumps(board, ensure_ascii=False)}

Help them get unstuck. Return ONLY a JSON object:
{{
  "themes": [list of 2 to 4 short themes you see in their ideas],
  "ranked_ideas": [
    {{"idea": short text, "effort": "low"|"medium"|"high", "impact": "low"|"medium"|"high", "why": one sentence}}
  ],
  "this_week": one concrete action they can take in the next 7 days,
  "linked_event_id": the id of the board event that best fits this_week, or "" if none fit,
  "encouragement": one short, warm, genuine sentence (no cliches)
}}
Rank ideas with the best impact for the least effort first. Keep the plan small and doable."""
    return _parse_json(_call_llm(prompt, max_tokens=1500))


# ---------------------------------------------------------------------------
# Feature 5: outreach drafter
# ---------------------------------------------------------------------------

def draft_outreach(event: dict, plan: dict | None = None, student_name: str = "Alex") -> str:
    action = (plan or {}).get("this_week", "volunteer at or support this event")
    prompt = f"""Write a short message from {student_name}, a student at Lincoln University,
to the organizer of this event:
{json.dumps(event, ensure_ascii=False)}

Goal: {action}
- Introduce yourself in one line
- Offer Lincoln students as volunteers or partners
- Ask one clear question about next steps
- Under 120 words, warm and human, no buzzwords, no em dashes
Return only the message text with a subject line at the top."""
    return _call_llm(prompt, max_tokens=500).strip()
