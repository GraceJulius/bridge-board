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

# Approximate coordinates of known places, used to put scanned events on the map
PLACES = {
    "lincoln_university": ("Lincoln University campus", 39.8087, -75.9277),
    "oxford_center": ("Downtown Oxford", 39.7851, -75.9788),
    "oxford_library": ("Oxford Public Library", 39.7843, -75.9800),
    "oxford_high_school": ("Oxford Area High School", 39.7795, -75.9720),
    "west_grove": ("West Grove", 39.8220, -75.8277),
    "kennett_square": ("Kennett Square", 39.8468, -75.7116),
    "west_chester": ("West Chester", 39.9607, -75.6055),
}


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


def is_flagged(event: dict) -> bool:
    """True if the trust check flagged health misinformation or scam warning signs."""
    trust = event.get("trust") or {}
    return trust.get("status") == "needs_review" or trust.get("safety") == "caution"


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
# Step 2: classify, translate, and run the trust check (health claims + scam signals)
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
  "place": the closest match for the event location from {list(PLACES)}, or "oxford_center" if unclear,
  "trust": {{
    "status": "aligned" | "needs_review" | "no_health_claims",
    "note": one sentence explaining the health judgment,
    "official_source": the most relevant official source to check, e.g. "CDC: Measles vaccination" or "",
    "safety": "ok" | "caution",
    "safety_flags": [short phrases naming each warning sign found, or empty list]
  }}
}}

Rules for the health check ("status"), which protects the community from health misinformation:
- "no_health_claims" if the flyer makes no medical or health claims.
- "aligned" only if every health claim matches established guidance from the CDC, the
  Pennsylvania Department of Health, or the Chester County Health Department.
- "needs_review" if any claim contradicts that guidance (for example discouraging vaccines,
  or promoting unproven cures), is exaggerated, or you are not sure. When in doubt, choose needs_review.

Rules for the safety check ("safety"), which protects people from scams and social engineering:
- Look for warning signs such as: asking for payment, gift cards, or wire transfers to attend or "reserve";
  asking for SSNs, bank details, or other sensitive personal info; location hidden until you RSVP or pay;
  pressure or urgency ("today only", "act now"); selling products alongside health or charity claims;
  contact details that cannot be verified (no organizer name, personal email only, shortened links or QR codes
  with no explanation); promises that sound too good to be true.
- "caution" if one or more clear warning signs are present; otherwise "ok".
- Never invent claims or warning signs that are not on the flyer."""
    return _parse_json(_call_llm(prompt))


# ---------------------------------------------------------------------------
# Step 3: "I'm overwhelmed" planner + matcher
# ---------------------------------------------------------------------------

def make_plan(brain_dump: str, events: list[dict]) -> dict:
    board = [
        {k: e.get(k, "") for k in ("id", "title", "date", "category", "organizer",
                                    "summary_en", "how_students_can_help")}
        for e in events
        if not is_flagged(e)  # never route students to flagged events
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


def place_coords(event: dict) -> tuple:
    """Return (lat, lon) for an event: explicit coords first, then the AI-picked place."""
    if event.get("lat") is not None and event.get("lon") is not None:
        return float(event["lat"]), float(event["lon"])
    _, lat, lon = PLACES.get(event.get("place") or "", PLACES["oxford_center"])
    return lat, lon


# ---------------------------------------------------------------------------
# Feature: fact-check card for flagged flyers
# ---------------------------------------------------------------------------

def make_factcheck(event: dict) -> dict:
    prompt = f"""A community flyer near Oxford, Pennsylvania was flagged by a trust check:
{json.dumps(event, ensure_ascii=False)}

Write a short, kind, shareable fact-check card for neighbors. Do not mock anyone. Return ONLY JSON:
{{
  "headline_en": a calm headline (max 8 words),
  "headline_es": the same headline in Spanish,
  "claims": [
    {{"claim": what the flyer says (short), "fact_en": what official guidance says (one sentence),
      "fact_es": the same in Spanish, "source": "CDC" | "PA Department of Health" | "Chester County Health Department"}}
  ],
  "safety_tips_en": [0 to 2 short tips if scam warning signs were found],
  "safety_tips_es": [the same tips in Spanish],
  "bottom_line_en": one sentence on what to do instead (e.g. where to get the MMR vaccine),
  "bottom_line_es": the same in Spanish
}}
Use only well-established public health facts. 1 to 3 claims."""
    return _parse_json(_call_llm(prompt, max_tokens=1500))


# ---------------------------------------------------------------------------
# Feature: Ask Bridge (grounded Q&A)
# ---------------------------------------------------------------------------

def ask_bridge(question: str, history: list[dict], events: list[dict], resources: list[dict]) -> str:
    board = [{k: e.get(k) for k in ("title", "date", "time", "location", "organizer", "contact",
                                    "category", "summary_en", "how_students_can_help")} for e in events]
    for b, e in zip(board, events):
        b["flagged_by_trust_check"] = is_flagged(e)
    care = [{k: r.get(k) for k in ("name", "phone", "hours", "address", "when")} for r in resources]
    convo = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in history[-6:])
    prompt = f"""You are Ask Bridge, a helpful assistant for Lincoln University students and Oxford, PA residents.

Community board events:
{json.dumps(board, ensure_ascii=False)}

Verified care and help resources:
{json.dumps(care, ensure_ascii=False)}

Conversation so far:
{convo}

New question: {question}

Rules:
- Answer in the same language the question is written in (English or Spanish).
- Use the board events and resources above for anything local. Name the event or resource and its phone number.
  If something is not on the board or in the resources, say so instead of guessing.
- Never recommend events flagged by the trust check; if asked about one, explain it was flagged and why it matters.
- For health questions, give general information from established public health guidance (CDC, PA Department of Health).
  Do not diagnose or recommend medications or doses. Suggest the right resource instead.
- If the person describes a possible emergency, tell them to call 911 first, in the first sentence.
- If someone mentions thoughts of suicide or self-harm, warmly point them to 988 (call or text) first.
- If someone may have measles symptoms, tell them to call the Chester County Health Department or a doctor
  BEFORE going in, so others are not exposed.
- Keep answers short: 2 to 5 sentences or a few bullets. Warm, plain language."""
    return _call_llm(prompt, max_tokens=700).strip()


# ---------------------------------------------------------------------------
# Feature: Get Help router (never diagnoses)
# ---------------------------------------------------------------------------

RED_FLAGS = [
    "chest pain", "can't breathe", "cant breathe", "cannot breathe", "not breathing", "trouble breathing",
    "unconscious", "passed out", "unresponsive", "seizure", "overdose", "overdosed", "bleeding a lot",
    "severe bleeding", "won't stop bleeding", "stroke", "face drooping", "slurred", "suicide", "kill myself",
    "end my life", "hurt myself", "self harm", "self-harm", "poison", "swallowed", "anaphyla", "allergic reaction",
    "throat closing", "head injury", "gun", "stabbed", "car accident", "no puedo respirar", "dolor de pecho",
    "suicid", "sangrado",
]


def red_flag_hit(text: str) -> str | None:
    low = text.lower()
    return next((f for f in RED_FLAGS if f in low), None)


def route_help(situation: str, resources: list[dict], now_desc: str) -> dict:
    care = [{k: r.get(k) for k in ("id", "name", "type", "hours", "when")} for r in resources]
    prompt = f"""You help Lincoln University students and Oxford, PA residents find the RIGHT place to get care.
You are NOT a doctor. Never diagnose, never name medications or doses.

Current local time: {now_desc}
Verified resources (use only these ids):
{json.dumps(care, ensure_ascii=False)}

What the person says:
<<<{situation}>>>

Return ONLY JSON:
{{
  "level": "emergency" | "urgent" | "soon" | "info",
  "recommend": [1 to 3 resource ids from the list, best first, considering what is open right now],
  "why": one or two plain sentences explaining why these places fit (no diagnosis),
  "while_you_wait": [1 to 3 short, general, safe steps like "Stay with someone" or "Bring your student ID"],
  "measles_concern": true if they mention rash with fever, measles, or measles exposure, else false
}}
- "emergency" if anything could be life-threatening; then recommend "911" first.
- "urgent": needs care today (use the ER if nothing else is open). "soon": a clinic visit in the next days.
  "info": questions, vaccines, or prevention.
- If thoughts of suicide or self-harm are mentioned, level "emergency" and recommend "988" and "911".
- When in doubt, choose the more cautious level."""
    out = _parse_json(_call_llm(prompt, max_tokens=700))
    valid = {r["id"] for r in resources}
    out["recommend"] = [r for r in out.get("recommend", []) if r in valid] or ["lu_health"]
    if out.get("level") == "emergency" and "911" not in out["recommend"]:
        out["recommend"].insert(0, "911")
    return out
