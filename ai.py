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
# Step 1: flyer photo -> structured event (vision)
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
  "raw_text": all the meaningful text on the flyer, including any health or medical claims, in one paragraph,
  "confidence": a number from 0 to 1 for how clearly you could read the flyer,
  "missing": list of field names you could not find on the flyer
}
Only use information visible on the flyer. Use "" for anything missing. Do not guess."""
    return _parse_json(_call_llm(prompt, image_bytes, mime))


# ---------------------------------------------------------------------------
# Step 2: classify, translate, and run the health trust check
# ---------------------------------------------------------------------------

def tag_and_translate(event: dict) -> dict:
    prompt = f"""Here is a community event near Lincoln University in Oxford, Pennsylvania:
{json.dumps(event, ensure_ascii=False)}

Do three things and return ONLY a JSON object:
{{
  "category": one of {CATEGORIES},
  "summary_en": a friendly 2 sentence summary in English,
  "summary_es": the same summary in natural Spanish,
  "how_students_can_help": one sentence on how a college student could help or join,
  "trust": {{
    "status": "aligned" | "needs_review" | "no_health_claims",
    "note": one sentence explaining your judgment,
    "official_source": the most relevant official source to check, e.g. "CDC: Measles vaccination" or ""
  }}
}}

Rules for "trust" (this protects the community from health misinformation):
- "no_health_claims" if the flyer makes no medical or health claims.
- "aligned" only if every health claim matches established guidance from the CDC, the
  Pennsylvania Department of Health, or the Chester County Health Department.
- "needs_review" if any claim contradicts that guidance (for example discouraging vaccines,
  or promoting unproven cures), is exaggerated, or you are not sure. When in doubt, choose needs_review.
- Never invent claims that are not on the flyer."""
    return _parse_json(_call_llm(prompt))


# ---------------------------------------------------------------------------
# Step 3: "I'm overwhelmed" planner + matcher
# ---------------------------------------------------------------------------

def make_plan(brain_dump: str, events: list[dict]) -> dict:
    board = [
        {k: e.get(k, "") for k in ("id", "title", "date", "category", "organizer",
                                    "summary_en", "how_students_can_help")}
        for e in events
        if (e.get("trust") or {}).get("status") != "needs_review"  # never route students to flagged events
    ]
    prompt = f"""A Lincoln University student wants to improve the relationship between
Lincoln and the Oxford, PA community but feels overwhelmed. Here is their brain dump:

\"\"\"{brain_dump}\"\"\"

Here are verified events currently on the community board:
{json.dumps(board, ensure_ascii=False)}

Help them get unstuck. Return ONLY a JSON object:
{{
  "themes": [2 to 4 short themes you hear in their ideas],
  "ranked_ideas": [
    {{"idea": short label (max 6 words), "effort": 1-5, "impact": 1-5, "why": one sentence}}
  ],
  "this_week": one concrete action they can take in the next 7 days,
  "matches": [
    {{"event_id": id from the board, "fit": 0-100, "reason": one sentence tying the event to their ideas}}
  ],
  "encouragement": one short, warm, genuine sentence (no cliches)
}}
- ranked_ideas: every distinct idea from the brain dump (3 to 6), best impact for least effort first.
- matches: the top 3 board events for this student, best first. Only use ids that exist.
- Keep the plan small and doable."""
    plan = _parse_json(_call_llm(prompt, max_tokens=1800))
    valid = {e["id"] for e in board}
    plan["matches"] = [m for m in plan.get("matches", []) if m.get("event_id") in valid]
    return plan


# ---------------------------------------------------------------------------
# Step 4: outreach drafter
# ---------------------------------------------------------------------------

def draft_outreach(event: dict, plan: dict | None = None, student_name: str = "Alex") -> str:
    action = (plan or {}).get("this_week", "volunteer at or support this event")
    prompt = f"""Write a short message from {student_name}, a student at Lincoln University,
to the organizer of this event:
{json.dumps({k: v for k, v in event.items() if k != "trust"}, ensure_ascii=False)}

Goal: {action}
- Introduce yourself in one line
- Offer Lincoln students as volunteers or partners
- Ask one clear question about next steps
- Under 120 words, warm and human, no buzzwords, no em dashes
Return only the message text with a subject line at the top."""
    return _call_llm(prompt, max_tokens=500).strip()
