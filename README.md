# 🌉 Bridge Board

**Small steps. Stronger neighbors.**

Bridge Board is an AI tool that turns paper flyers and scattered ideas into real, safe connections between Lincoln University and the Oxford, PA community.

Built for the Lincoln University CS Club Hackathon 2026. Theme: *Best Innovation of an AI Tool*.

---

## The problem

Meet Alex, a Lincoln student. He loves connecting with his community, but the relationship between Lincoln and Oxford is strained, and he doesn't always feel welcome or safe in town. He has considered transferring. Before he does, he wants to try one more time and actually help.

Then measles cases are confirmed at Oxford Area High School. Health affects everyone, so this is a moment when both communities have a shared stake. But Alex is overwhelmed:

- Local information lives on **paper flyers** taped to walls, in English only
- Some flyers spread **health misinformation** or look like **scams**
- He has a dozen ideas and **no idea where to start**
- In an emergency, students often **don't know where the nearest care is**. Southern Chester County went years without a nearby ER after Jennersville Hospital closed in 2021

## What Bridge Board does

| | Feature | What the AI does |
|---|---|---|
| 📸 | **Scan a flyer** | A vision model reads a photo of any flyer and pulls out the title, date, time, location, organizer and contact, with a legibility score and a list of missing fields |
| 🏷️ | **Tag + translate** | Sorts the event (Health, Volunteer, Social, Education), writes a plain-language summary, and translates it to Spanish |
| 🛡️ | **Trust check** | Runs on every flyer. Health claims are checked against CDC and PA Department of Health guidance, and the flyer is checked for scam warning signs: payment requests, requests for personal info, hidden locations, pressure tactics, product sales. Flagged flyers are never recommended to students |
| 📄 | **Fact-check card** | For a flagged flyer, writes a kind, bilingual "what's actually true" card with official sources, downloadable as an image to share with neighbors |
| 📋 | **Community board** | Every event in one place, filterable by category, with an English/Español toggle and a map view |
| 🧭 | **I'm Overwhelmed** | Takes a messy brain dump, finds the themes, plots ideas on an effort vs. impact chart, picks one action for this week, and scores the best-matching verified events |
| ✉️ | **Outreach drafter** | Writes a short, warm first message from the student to the event organizer |
| 💬 | **Ask Bridge** | Answers questions in English or Spanish using only the board and verified resources |
| 🗺️ | **Community map** | Events and care locations on one map, color-coded, with flagged flyers marked |
| 🌱 | **Our Impact** | Students log volunteer hours; a live dashboard shows hours, students and events supported |
| ✚ | **Get Help** | 911 first, always. Points students to the right verified local care based on what's open right now. Never diagnoses |

### The AI pipeline

```
Flyer photo
   ➡️ Vision extraction (fields, legibility, missing info)
   ➡️ Classify + translate EN/ES
   ➡️ Trust check (health claims + scam signals)
   ➡️ Community board + map
   ➡️ Planner + matcher (effort vs. impact, fit scores)
   ➡️ Outreach draft
```

Every step shows up live on the Scan tab, so you can watch what the AI is doing.

## Safety and responsible AI

**Get Help is built to be safe first:**
- A **keyword safety guard runs before any AI call.** Phrases like "chest pain," "can't breathe," "overdose" or "suicide" (plus common Spanish phrases) show the 911 / 988 screen immediately
- The AI router **never diagnoses** and never names medications or doses. It only suggests *where* to go
- When in doubt, it picks the more cautious option
- Possible measles? It tells people to **call ahead** before going in, following Chester County Health Department guidance
- Every contact in `data/resources.json` comes from an official source, with a link shown on each card

**Across the app:**
- Flyers are untrusted input, so all flyer and model text is **HTML-escaped** before display
- The scanner only uses what's on the flyer and leaves fields blank instead of guessing
- Flagged events are never recommended by the planner or Ask Bridge
- Fact-check cards are written to inform, not shame
- No personal data about community members is collected
- Anything labeled **Sample data** is a demo placeholder, not a real event or real volunteer

## Run it

**Requirements:** Python 3.9 or newer, and an API key from one of: Anthropic (Claude), Google Gemini (free tier), or OpenAI.

```bash
git clone https://github.com/GraceJulius/bridge-board.git
cd bridge-board

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then add your API key
streamlit run app.py
```

In `.env`:

```
AI_PROVIDER=anthropic            # or gemini, or openai
ANTHROPIC_API_KEY=sk-ant-...     # the key for the provider you picked
MODEL=                           # optional, leave blank for the default
```

Free Gemini key: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

**Tips**
- Reset the board to the sample events before a demo or a `git pull`: `git checkout -- data/events.json data/impact.json`
- On a Mac, use `pip` inside the virtual environment (or `pip3` outside it)

## Demo script (3 minutes)

1. **Problem (30s):** Alex's story, the measles cases, the strained relationship
2. **Scan (45s):** Upload `demo_flyers/misleading_flyer.png`. Watch the pipeline run live; the trust check flags both the health claims and the scam signals
3. **Fact-check (20s):** Open "Help neighbors with the facts" and generate the bilingual card
4. **I'm Overwhelmed (40s):** Paste a messy brain dump. Show the effort vs. impact chart, the step for this week, the matched clinic, and the drafted message
5. **Get Help (25s):** Type a symptom question, then "chest pain" to show the safety guard
6. **Impact + close (20s):** Log hours live, show the dashboard, and end on "small steps, stronger neighbors"

`demo_flyers/` has two fictional flyers for a reliable demo:
- `clinic_flyer.png`: a vaccine clinic that should pass the trust check
- `misleading_flyer.png`: a "natural immunity" flyer that should be flagged

## Verified care contacts

`data/resources.json` holds every care and crisis contact shown in the app:

- 911, 988 Suicide & Crisis Lifeline, Poison Control
- Lincoln University Public Safety, Health Services, and Counseling Services
- LCH Health Center, Oxford
- ChristianaCare Hospital, West Grove (nearest ER, 24/7)
- Chester County Hospital (ER, 24/7)
- Chester County Health Department

Contacts were checked against official pages on **Nov 13, 2026**. Phone numbers and hours change, so re-check them before relying on the app in real life.

## Project structure

```
app.py                Main UI: hero, community board, scan, I'm Overwhelmed
extras.py             Get Help, fact-check card, Ask Bridge, map, impact tracker
ai.py                 All AI calls: extraction, tagging + trust check, planner,
                      outreach, fact-check, Ask Bridge, Get Help router, safety guard
store.py              JSON storage for events
data/events.json      Sample events (labeled as sample data)
data/resources.json   Verified care and crisis contacts with sources
data/impact.json      Volunteer hour log (starts with labeled sample entries)
demo_flyers/          Fictional flyers for the live demo
.streamlit/config.toml  Theme colors
```

## Built with

Python, Streamlit, Claude / Gemini / OpenAI (switchable), Altair, pydeck, Pillow

## What's next

- Partner with Lincoln Health Services and Oxford community groups to post real events
- SMS version so residents without smartphones can text a flyer photo or a question
- Human review queue so community moderators confirm trust-check flags
- Real-time vaccine clinic listings from the Chester County Health Department

## Team

- **Grace Julius:** AI engine and trust check
- **_Partner name_:** UI, data and demo
