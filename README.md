# 🌉 Bridge Board

**An AI tool that turns paper flyers and scattered ideas into real connections between Lincoln University and the Oxford, PA community.**

Built for the Lincoln University CS Club Hackathon 2026, theme: *Best Innovation of an AI Tool*.

## The problem

Alex is a Lincoln student who wants to help improve the relationship between Lincoln and Oxford, but he's overwhelmed and doesn't know where to start. With measles cases confirmed at Oxford High School, health is a moment where both communities have a shared stake. Local information lives on paper flyers, and good intentions get stuck at "where do I even begin?"

## What it does

| Feature | How AI is used |
|---|---|
| 📸 **Flyer scan** | A vision model reads a photo of a flyer and extracts title, date, time, location, organizer and contact |
| 🏷️ **Tag + translate** | The LLM categorizes the event (Health, Volunteer, Social, Education), writes a short summary, and translates it to Spanish |
| 📋 **Bridge Board** | All events in one filterable board with an English/Spanish toggle |
| 🧠 **"I'm overwhelmed" mode** | The LLM groups a student's messy ideas into themes, ranks them by effort vs. impact, and links one action this week to a real board event |
| ✉️ **Outreach drafter** | The LLM drafts a short, human message from the student to the event organizer |

**AI pipeline:** photo ➡️ vision extraction ➡️ tagging + translation ➡️ board ➡️ planning ➡️ outreach draft

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env      # then add your API key
streamlit run app.py
```

Set `AI_PROVIDER` to `anthropic` or `openai` in `.env` and add the matching key. `MODEL` is optional.

## Project structure

```
app.py            Streamlit UI (Board, Scan, Overwhelmed tabs)
ai.py             AI functions: extract_event, tag_and_translate, make_plan, draft_outreach
store.py          JSON file storage for events
data/events.json  Seed events (clearly labeled as sample data)
```

## Responsible AI

- Events marked **Sample data** are placeholders for the demo, not real events
- The flyer scanner only uses what's visible on the flyer and leaves missing fields blank instead of guessing
- No personal data about community members is collected or stored
- For health questions, point people to official sources: Chester County Health Department, PA Department of Health, CDC

## Team

- Grace Julius: AI engine
- _Partner name_: UI, data, demo
