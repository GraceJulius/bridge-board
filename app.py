"""Bridge Board: turning flyers and scattered ideas into Lincoln x Oxford connections.

Run:  streamlit run app.py
"""

from __future__ import annotations

import html
import time

import altair as alt
import pandas as pd
import streamlit as st

import ai
import store

st.set_page_config(page_title="Bridge Board", page_icon="🌉", layout="wide")

INK = "#1E2A22"
FOREST = "#2F4A36"
SAGE = "#7FA287"
STONE = "#E9E5DA"
CREAM = "#FAF8F2"
PEACH = "#F5DCC0"
TERRA = "#B4532A"
# aliases used further down
NAVY = INK
ORANGE = FOREST
CATEGORY_COLORS = {
    "Health": "#C0563F",
    "Volunteer": "#3E7A52",
    "Social": "#8A6BB0",
    "Education": "#3D7097",
    "Other": "#8B8D80",
}
CATEGORY_ICONS = {"Health": "✚", "Volunteer": "♥", "Social": "☺", "Education": "✎", "Other": "✳"}
TRUST_BADGES = {
    "aligned": ("✓ Matches official guidance", "#3E7A52"),
    "needs_review": ("⚠ Health claims need review", TERRA),
}

# ---------------------------------------------------------------------------
# Styles: calm, editorial, nature-inspired
# ---------------------------------------------------------------------------
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600&family=Inter:wght@400;500;600&display=swap');
html, body, .stMarkdown, p, li, label, input, textarea, button {{ font-family: 'Inter', sans-serif; }}
h1, h2, h3, h4 {{ font-family: 'Inter Tight', sans-serif !important; }}
#MainMenu, footer, [data-testid="stDecoration"], header[data-testid="stHeader"] {{ display: none !important; }}
.block-container {{ padding-top: 1.2rem; max-width: 1220px; }}

@keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(14px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes drift {{ 0% {{ transform: scale(1) rotate(0deg); }} 100% {{ transform: scale(1.12) rotate(4deg); }} }}
@keyframes pulse {{ 0%,100% {{ box-shadow: 0 0 0 0 rgba(250,248,242,0.6); }} 50% {{ box-shadow: 0 0 0 6px rgba(250,248,242,0); }} }}

/* top bar */
.bb-nav {{ display:flex; align-items:center; justify-content:space-between; padding: 6px 4px 16px 4px;
  border-bottom: 1px solid rgba(30,42,34,0.12); margin-bottom: 18px; font-size: 0.82rem; color: {INK}; }}
.bb-logo {{ font-weight: 600; letter-spacing: 0.08em; font-size: 0.82rem; }}
.bb-navlinks span {{ margin: 0 16px; opacity: 0.7; }}
.bb-pill {{ display:inline-block; border: 1px solid rgba(30,42,34,0.18); border-radius: 999px; padding: 5px 12px;
  font-size: 0.76rem; background: {CREAM}; }}
.bb-pill.green {{ background: #DCE8D9; border-color: transparent; color: {FOREST}; font-weight: 600; }}

/* hero: split panel */
.bb-hero {{ display:grid; grid-template-columns: 1fr 1fr; border-radius: 28px; overflow:hidden; min-height: 430px;
  animation: fadeUp .8s ease both; box-shadow: 0 20px 50px rgba(30,42,34,0.10); }}
.bb-hero-left {{ background: {CREAM}; padding: 46px 44px; display:flex; flex-direction:column; justify-content:space-between; }}
.bb-hero-left h1 {{ font-family:'Inter Tight',sans-serif; font-weight:500; font-size: 3.4rem; line-height:1.02;
  letter-spacing:-0.035em; color:{INK}; margin: 14px 0 14px 0; }}
.bb-hero-left p {{ color:#5C655C; font-size:1.02rem; max-width: 430px; margin:0; line-height:1.55; }}
.bb-stats {{ display:flex; gap: 0; margin-top: 30px; border-top: 1px solid rgba(30,42,34,0.12); }}
.bb-stat {{ flex:1; padding: 14px 14px 0 0; }}
.bb-stat + .bb-stat {{ border-left: 1px solid rgba(30,42,34,0.12); padding-left: 14px; }}
.bb-stat b {{ display:block; font-family:'Inter Tight',sans-serif; font-weight:500; font-size:1.9rem; color:{INK}; letter-spacing:-0.02em; }}
.bb-stat span {{ font-size:0.76rem; color:#6E776D; }}
.bb-hero-right {{ position:relative; overflow:hidden; color:{CREAM};
  background: linear-gradient(160deg, #3B5B42 0%, {FOREST} 45%, #1C2E21 100%); }}
.bb-leaf {{ position:absolute; inset:-20%; animation: drift 14s ease-in-out infinite alternate;
  background:
    radial-gradient(ellipse 40% 12% at 30% 30%, rgba(160,200,150,0.22), transparent 70%),
    radial-gradient(ellipse 50% 10% at 70% 55%, rgba(160,200,150,0.18), transparent 70%),
    radial-gradient(ellipse 35% 9% at 40% 78%, rgba(200,230,180,0.14), transparent 70%),
    repeating-linear-gradient(115deg, rgba(255,255,255,0.035) 0 2px, transparent 2px 38px); }}
.bb-wordmark {{ position:absolute; left:34px; top:34px; font-family:'Inter Tight',sans-serif; font-size:2.1rem;
  font-weight:500; letter-spacing:-0.02em; display:flex; align-items:center; gap:10px; }}
.bb-orb {{ width:46px; height:46px; border-radius:50%; background: radial-gradient(circle at 35% 30%, #F8E6CF, #D9A877);
  display:inline-flex; align-items:center; justify-content:center; font-size:1.3rem; }}
.bb-anno {{ position:absolute; font-size:0.8rem; letter-spacing:0.01em; display:flex; align-items:center; gap:8px; opacity:0.95; }}
.bb-anno i {{ width:8px; height:8px; border-radius:50%; background:{CREAM}; display:inline-block; animation: pulse 2.6s infinite; }}
.bb-line {{ position:absolute; background: rgba(250,248,242,0.55); width:1px; transform-origin: top left; }}
.bb-tagline {{ position:absolute; left:34px; bottom:30px; font-size:0.74rem; opacity:0.75; max-width: 260px; line-height:1.5; }}

/* how-it-works cards */
.bb-how {{ display:grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 26px 0 8px 0; }}
.bb-how-card {{ background:{CREAM}; border: 1px solid rgba(30,42,34,0.10); border-radius: 26px; padding: 22px;
  display:flex; flex-direction:column; justify-content:space-between; min-height: 190px;
  animation: fadeUp .8s ease both; transition: transform .25s ease, box-shadow .25s ease; }}
.bb-how-card:hover {{ transform: translateY(-4px); box-shadow: 0 16px 34px rgba(30,42,34,0.10); }}
.bb-how-card.peach {{ background: linear-gradient(150deg, #FBEBD8 0%, {PEACH} 100%); border-color: transparent; }}
.bb-how-card h4 {{ font-family:'Inter Tight',sans-serif; font-weight:600; font-size:1.08rem; color:{INK}; margin: 12px 0 6px 0; }}
.bb-how-card p {{ font-size:0.86rem; color:#5C655C; margin:0; line-height:1.5; }}
.bb-icon {{ width:38px; height:38px; border-radius:50%; background:white; display:flex; align-items:center;
  justify-content:center; font-size:1rem; color:{INK}; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
.bb-arrow {{ width:38px; height:38px; border-radius:50%; border:1px solid rgba(30,42,34,0.2); display:flex;
  align-items:center; justify-content:center; color:{INK}; font-size:0.95rem; }}
.bb-arrow.fill {{ background:{FOREST}; color:white; border-color:{FOREST}; }}
.bb-row {{ display:flex; align-items:center; justify-content:space-between; margin-top: 14px; }}
.bb-tags span {{ font-size:0.72rem; color:#6E776D; margin-right:8px; }}
.bb-avatars {{ display:flex; align-items:center; gap:8px; font-size:0.78rem; color:{INK}; }}
.bb-avatars b {{ width:28px; height:28px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center;
  font-size:0.68rem; color:white; border:2px solid {CREAM}; margin-left:-10px; }}
.bb-avatars b:first-child {{ margin-left:0; }}

/* tabs as pills */
.stTabs [data-baseweb="tab-list"] {{ gap: 8px; background: transparent; border-bottom: none; margin-top: 18px; }}
.stTabs [data-baseweb="tab"] {{ background:{CREAM}; border: 1px solid rgba(30,42,34,0.12); border-radius: 999px;
  padding: 8px 20px; height:auto; }}
.stTabs [aria-selected="true"] {{ background:{INK}; color:{CREAM} !important; border-color:{INK}; }}
.stTabs [aria-selected="true"] p {{ color:{CREAM} !important; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display:none; }}

/* event cards */
[data-testid="stVerticalBlockBorderWrapper"]:has(.bb-card-head),
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .bb-card-head) {{
  border-radius: 26px !important; background:{CREAM} !important;
  border: 1px solid rgba(30,42,34,0.10) !important; animation: fadeUp .7s ease both;
  transition: transform .25s ease, box-shadow .25s ease; }}
[data-testid="stVerticalBlockBorderWrapper"]:has(.bb-card-head):hover,
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .bb-card-head):hover {{
  transform: translateY(-3px); box-shadow: 0 14px 30px rgba(30,42,34,0.09); }}
.bb-card-head {{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 10px; }}
.bb-badges {{ display:flex; gap:6px; flex-wrap:wrap; margin: 10px 0 6px 0; }}
.bb-badge {{ padding: 3px 10px; border-radius: 999px; font-size: 0.72rem; font-weight: 600; color: white; }}
.bb-badge.light {{ background: #ECE8DD; color: #5C655C; }}
.bb-card-title {{ font-family:'Inter Tight',sans-serif; font-size:1.32rem; font-weight:600; letter-spacing:-0.015em;
  color:{INK}; margin: 2px 0 4px 0; }}
.bb-meta {{ color:#6E776D; font-size:0.84rem; margin-bottom:10px; }}
.bb-summary {{ color:#3A443B; font-size:0.95rem; line-height:1.55; }}
.bb-help {{ background: #EEF3EA; border-radius: 14px; padding: 10px 14px; margin-top: 12px; font-size: 0.86rem; color:{FOREST}; }}
.bb-trust {{ border-radius: 14px; padding: 10px 14px; margin-top: 10px; font-size: 0.83rem; line-height:1.5; }}
.bb-trust.ok {{ background: #E3EEDF; color: #2E5E3C; }}
.bb-trust.warn {{ background: #F7E4D8; color: #8A3A1A; border: 1px solid #E9B99C; }}
.bb-org {{ color:#8A9188; font-size:0.78rem; margin-top: 12px; }}

/* pipeline trace */
.bb-step {{ display:flex; gap:14px; align-items:flex-start; padding: 12px 0; border-bottom: 1px solid rgba(30,42,34,0.10);
  animation: fadeUp .5s ease both; }}
.bb-step:last-child {{ border-bottom:none; }}
.bb-dot {{ width:30px; height:30px; border-radius:50%; border: 1px solid rgba(30,42,34,0.25); color:{INK};
  display:flex; align-items:center; justify-content:center; font-size:0.78rem; flex-shrink:0; background:{CREAM}; }}
.bb-step b {{ color:{INK}; font-weight:600; }}
.bb-step small {{ color:#6E776D; display:block; margin-top:2px; }}

/* planner */
.bb-chip {{ display:inline-block; background:{CREAM}; border:1px solid rgba(30,42,34,0.14); color:{INK};
  border-radius:999px; padding:6px 14px; margin:0 6px 6px 0; font-size:0.85rem; }}
.bb-action {{ background: linear-gradient(150deg, #FBEBD8 0%, {PEACH} 100%); color:{INK}; border-radius: 26px;
  padding: 26px 28px; font-family:'Inter Tight',sans-serif; font-size: 1.45rem; font-weight:500; letter-spacing:-0.02em;
  line-height:1.3; animation: fadeUp .7s ease both; }}
.bb-action small {{ display:block; font-family:'Inter',sans-serif; font-size:0.72rem; font-weight:600; letter-spacing:0.1em;
  text-transform:uppercase; color:#8A5A2E; margin-bottom:8px; }}
.bb-fit {{ height:6px; border-radius:6px; background:#E2DED2; overflow:hidden; margin:8px 0 6px 0; }}
.bb-fit > div {{ height:100%; background:{FOREST}; border-radius:6px; }}
.bb-section {{ font-family:'Inter Tight',sans-serif; font-size:1.25rem; font-weight:500; letter-spacing:-0.02em;
  color:{INK}; margin: 22px 0 10px 0; }}
.bb-eyebrow {{ font-size:0.72rem; letter-spacing:0.12em; text-transform:uppercase; color:#7A8379; }}

/* inputs & buttons */
.stButton button, .stDownloadButton button {{ border-radius: 999px !important; padding: 0.55rem 1.3rem !important; }}
textarea, [data-testid="stFileUploaderDropzone"] {{ border-radius: 18px !important; background:{CREAM} !important; }}

@media (max-width: 900px) {{
  .bb-hero, .bb-how {{ grid-template-columns: 1fr; }}
  .bb-hero-right {{ min-height: 300px; }}
  .bb-navlinks {{ display:none; }}
}}
</style>
""",
    unsafe_allow_html=True,
)


def esc(value) -> str:
    """Escape model or flyer text before it goes into HTML (flyers are untrusted input)."""
    return html.escape(str(value or ""))


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

def outreach_box(event: dict, plan: dict | None, key: str) -> None:
    if st.button("✉️ Draft my message", key=f"draft_{key}", type="primary"):
        with st.spinner("Writing a message that sounds like you..."):
            try:
                st.session_state[f"draft_text_{key}"] = ai.draft_outreach(event, plan)
            except Exception as e:  # keep the demo alive
                st.error(f"Could not draft message: {e}")
    if st.session_state.get(f"draft_text_{key}"):
        st.text_area("Edit before sending", st.session_state[f"draft_text_{key}"],
                     height=230, key=f"draft_area_{key}")
        st.caption("Tip: click in the box, then Cmd + A and Cmd + C to copy")


def trust_html(event: dict) -> str:
    trust = event.get("trust") or {}
    status = trust.get("status")
    if status not in TRUST_BADGES:
        return ""
    cls = "ok" if status == "aligned" else "warn"
    src = f" · Check: {esc(trust.get('official_source'))}" if trust.get("official_source") else ""
    return f'<div class="bb-trust {cls}"><b>{TRUST_BADGES[status][0]}</b><br>{esc(trust.get("note"))}{src}</div>'


def event_card(event: dict, lang: str = "English", key_prefix: str = "board",
               show_outreach: bool = True) -> None:
    cat = event.get("category", "Other")
    color = CATEGORY_COLORS.get(cat, CATEGORY_COLORS["Other"])
    icon = CATEGORY_ICONS.get(cat, "✳")
    status = (event.get("trust") or {}).get("status")

    badges = f'<span class="bb-badge" style="background:{color}">{esc(cat)}</span>'
    if status in TRUST_BADGES:
        label, bcolor = TRUST_BADGES[status]
        badges += f'<span class="bb-badge" style="background:{bcolor}">{label}</span>'
    badges += ('<span class="bb-badge light">Sample data</span>' if event.get("is_sample")
               else '<span class="bb-badge light">📸 Scanned</span>')

    meta = " · ".join(esc(x) for x in [event.get("date"), event.get("time"), event.get("location")] if x)
    summary = event.get("summary_es") if lang == "Español" else event.get("summary_en")
    helps = (f'<div class="bb-help"><b>How students can help</b> · {esc(event["how_students_can_help"])}</div>'
             if event.get("how_students_can_help") and status != "needs_review" else "")
    org = " ".join(esc(x) for x in [event.get("organizer"), event.get("contact")] if x)
    arrow = ('<div class="bb-arrow" style="border-color:#E9B99C;color:#8A3A1A">!</div>' if status == "needs_review"
             else '<div class="bb-arrow">↗</div>')

    with st.container(border=True):
        st.markdown(
            f"""<div class="bb-card-head"><div class="bb-icon" style="color:{color}">{icon}</div>{arrow}</div>
<div class="bb-badges">{badges}</div>
<div class="bb-card-title">{esc(event.get("title") or "Untitled event")}</div>
<div class="bb-meta">{meta}</div>
<div class="bb-summary">{esc(summary)}</div>
{helps}{trust_html(event)}
<div class="bb-org">{org}</div>""",
            unsafe_allow_html=True,
        )
        if show_outreach and status != "needs_review":
            with st.expander("Reach out to the organizer"):
                outreach_box(event, None, f"{key_prefix}_{event['id']}")


def pipeline_html(steps: list[tuple[str, str, str]]) -> str:
    rows = "".join(
        f'<div class="bb-step" style="animation-delay:{i * 0.06:.2f}s"><div class="bb-dot">{icon}</div>'
        f'<div><b>{esc(t)}</b><small>{esc(d)}</small></div></div>'
        for i, (icon, t, d) in enumerate(steps)
    )
    return f"<div>{rows}</div>"


# ---------------------------------------------------------------------------
# Top bar + hero + how it works
# ---------------------------------------------------------------------------
events = store.load_events()
n_health = sum(1 for e in events if e.get("category") == "Health")
n_flagged = sum(1 for e in events if (e.get("trust") or {}).get("status") == "needs_review")

st.markdown(
    f"""
<div class="bb-nav">
  <div class="bb-logo">✳ BRIDGE BOARD</div>
  <div class="bb-navlinks"><span>Board</span><span>Scan</span><span>Plan</span><span>Trust check</span></div>
  <div class="bb-pill">Lincoln University × Oxford, PA</div>
</div>

<div class="bb-hero">
  <div class="bb-hero-left">
    <div>
      <span class="bb-pill green">Community, made simple</span>
      <h1>Small steps.<br>Stronger neighbors.</h1>
      <p>Snap a local flyer and AI turns it into a verified, translated event. Feeling overwhelmed?
      Tell us your ideas and we'll find your first step.</p>
    </div>
    <div class="bb-stats">
      <div class="bb-stat"><b>{len(events)}</b><span>events on the board</span></div>
      <div class="bb-stat"><b>{n_health}</b><span>health events</span></div>
      <div class="bb-stat"><b>{n_flagged}</b><span>flagged as misleading</span></div>
    </div>
  </div>
  <div class="bb-hero-right">
    <div class="bb-leaf"></div>
    <div class="bb-wordmark">BRIDGE <span class="bb-orb">🌉</span> BOARD</div>
    <div class="bb-anno" style="left:46%; top:142px;"><i></i>Read by AI vision</div>
    <div class="bb-line" style="left:58%; top:172px; height:58px;"></div>
    <div class="bb-anno" style="left:58%; top:232px;"><i></i>Fact-checked vs. CDC guidance</div>
    <div class="bb-line" style="left:58%; top:262px; height:50px;"></div>
    <div class="bb-anno" style="left:58%; top:314px;"><i></i>Translated EN · ES</div>
    <div class="bb-line" style="left:58%; top:344px; height:30px;"></div>
    <div class="bb-anno" style="left:58%; top:376px;"><i></i>Matched to you</div>
    <div class="bb-tagline">From a paper flyer to a real connection, every step verified by AI and guided by people.</div>
  </div>
</div>

<div class="bb-how">
  <div class="bb-how-card peach" style="animation-delay:.1s">
    <div><div class="bb-icon">📸</div><h4>Scan a flyer</h4>
    <p>Photograph any flyer in town. AI reads it, translates it, and checks its health claims.</p></div>
    <div class="bb-row"><div class="bb-tags"><span># Vision</span><span># Trust check</span></div><div class="bb-arrow fill">↗</div></div>
  </div>
  <div class="bb-how-card" style="animation-delay:.2s">
    <div><div class="bb-icon">🧭</div><h4>Find your first step</h4>
    <p>Dump your messy ideas. AI ranks them by effort and impact and matches you to verified events.</p></div>
    <div class="bb-row"><div class="bb-tags"><span># Planning</span><span># Matching</span></div><div class="bb-arrow">↗</div></div>
  </div>
  <div class="bb-how-card" style="animation-delay:.3s">
    <div><div class="bb-icon">✉️</div><h4>Reach out</h4>
    <p>Get a warm, human first message to the organizer, ready to edit and send.</p></div>
    <div class="bb-row"><div class="bb-avatars"><b style="background:#3E7A52">L</b><b style="background:#C0563F">O</b><b style="background:#D9A877">✳</b>&nbsp;Lincoln × Oxford</div><div class="bb-arrow">↗</div></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

tab_board, tab_scan, tab_plan = st.tabs(["Community Board", "Scan a Flyer", "I'm Overwhelmed"])

# ---------------------------------------------------------------------------
# Board
# ---------------------------------------------------------------------------
with tab_board:
    c1, c2 = st.columns([3, 1])
    with c1:
        choice = st.segmented_control("Filter by category", ["All"] + ai.CATEGORIES, default="All")
    with c2:
        lang = st.segmented_control("Language", ["English", "Español"], default="English", key="board_lang")
    shown = [e for e in events if choice in (None, "All") or e.get("category") == choice]
    if not shown:
        st.info("Nothing here yet. Scan a flyer to add the first one!")
    cols = st.columns(2, gap="medium")
    for i, ev in enumerate(shown):
        with cols[i % 2]:
            event_card(ev, lang or "English")

# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------
with tab_scan:
    left, right = st.columns([1, 1.15], gap="large")
    with left:
        st.markdown('<div class="bb-section">1. Add a flyer</div>', unsafe_allow_html=True)
        use_cam = st.toggle("Use my camera")
        photo = st.camera_input("Take a photo") if use_cam else None
        upload = st.file_uploader("Upload a flyer photo", type=["png", "jpg", "jpeg", "webp"])
        image = photo or upload
        if image:
            st.image(image, use_container_width=True)
        run = st.button("✨ Read this flyer with AI", type="primary", disabled=image is None,
                        use_container_width=True)

    with right:
        st.markdown('<div class="bb-section">2. What the AI is doing</div>', unsafe_allow_html=True)
        trace = st.empty()
        if not run and not st.session_state.get("last_trace"):
            trace.markdown(pipeline_html([
                ("1", "Read the flyer", "Vision model pulls out title, date, place, organizer, contact"),
                ("2", "Understand it", "Classifies the event and writes a plain-language summary"),
                ("3", "Translate it", "English and Spanish, so every neighbor can read it"),
                ("4", "Check health claims", "Compares claims with CDC and PA Department of Health guidance"),
                ("5", "Post to the board", "Ready for students to find and act on"),
            ]), unsafe_allow_html=True)

        if run and image:
            steps = []
            try:
                t0 = time.time()
                steps.append(("…", "Reading the flyer", "Vision model at work"))
                trace.markdown(pipeline_html(steps), unsafe_allow_html=True)
                event = ai.extract_event(image.getvalue(), image.type or "image/jpeg")
                conf = event.get("confidence")
                missing = event.get("missing") or []
                legible = ""
                try:
                    legible = f" · {int(float(conf) * 100)}% legible" if conf not in (None, "") else ""
                except (TypeError, ValueError):
                    pass
                steps[-1] = ("✓", "Read the flyer",
                             f"Found \"{event.get('title', '')}\"" + legible
                             + (f" · missing: {', '.join(map(str, missing))}" if missing else "")
                             + f" · {time.time() - t0:.1f}s")

                t1 = time.time()
                steps.append(("…", "Classifying, translating, fact-checking", "One reasoning pass"))
                trace.markdown(pipeline_html(steps), unsafe_allow_html=True)
                event.update(ai.tag_and_translate(event))
                status = (event.get("trust") or {}).get("status", "")
                steps[-1] = ("✓", "Classified and translated",
                             f"{event.get('category')} · EN + ES · {time.time() - t1:.1f}s")
                steps.append(("⚠" if status == "needs_review" else "✓", "Health claim check",
                              {"aligned": "Matches official guidance",
                               "needs_review": "Flagged: claims conflict with official guidance",
                               "no_health_claims": "No health claims found"}.get(status, "Checked")))
                for k in ("confidence", "missing"):
                    event.pop(k, None)
                event = store.add_event(event)
                steps.append(("✓", "Posted to the board", "Live for every student and neighbor"))
                trace.markdown(pipeline_html(steps), unsafe_allow_html=True)
                st.session_state["last_trace"] = steps
                st.session_state["last_scanned"] = event
                if status == "needs_review":
                    st.toast("Heads up: this flyer has health claims that need review", icon="⚠️")
                else:
                    st.toast("Added to the board!", icon="✅")
            except Exception as e:
                st.error(f"Something went wrong reading the flyer: {e}")
        elif st.session_state.get("last_trace"):
            trace.markdown(pipeline_html(st.session_state["last_trace"]), unsafe_allow_html=True)

        if st.session_state.get("last_scanned"):
            st.markdown('<div class="bb-section">3. Result</div>', unsafe_allow_html=True)
            lang_scan = st.segmented_control("Language", ["English", "Español"], default="English",
                                             key="scan_lang")
            event_card(st.session_state["last_scanned"], lang_scan or "English", key_prefix="scan")

# ---------------------------------------------------------------------------
# Overwhelmed
# ---------------------------------------------------------------------------
with tab_plan:
    st.markdown('<div class="bb-section">Dump every idea you have. Messy is fine.</div>',
                unsafe_allow_html=True)
    st.caption("The AI finds the themes, ranks your ideas by effort and impact, and matches you "
               "with verified events. Flagged events are never recommended.")
    dump = st.text_area(
        "Your brain dump",
        height=150,
        label_visibility="collapsed",
        placeholder="I want Lincoln and Oxford to actually know each other... maybe joint events? "
                    "A volunteer app? There's measles at the high school and I want to help but I "
                    "don't know anyone in Oxford. I'm good at math and I play basketball...",
    )
    if st.button("🧭 Help me start", type="primary", disabled=not dump.strip()):
        with st.spinner("Listening to your ideas and checking the board..."):
            try:
                st.session_state["plan"] = ai.make_plan(dump, store.load_events())
            except Exception as e:
                st.error(f"Could not make a plan: {e}")

    plan = st.session_state.get("plan")
    if plan:
        st.markdown('<div class="bb-section">What I\'m hearing</div>', unsafe_allow_html=True)
        st.markdown("".join(f'<span class="bb-chip">{esc(t)}</span>' for t in plan.get("themes", [])),
                    unsafe_allow_html=True)

        st.markdown(
            f'<div class="bb-action" style="margin-top:14px"><small>Your step this week</small>'
            f'{esc(plan.get("this_week"))}</div>',
            unsafe_allow_html=True,
        )
        if plan.get("encouragement"):
            st.caption(plan["encouragement"])

        left, right = st.columns([1.1, 1], gap="large")
        with left:
            st.markdown('<div class="bb-section">Your ideas: effort vs. impact</div>', unsafe_allow_html=True)
            rows = []
            for i, idea in enumerate(plan.get("ranked_ideas", []), 1):
                try:
                    rows.append({"#": str(i), "idea": str(idea.get("idea", "")),
                                 "effort": float(idea.get("effort", 3)),
                                 "impact": float(idea.get("impact", 3)),
                                 "why": str(idea.get("why", ""))})
                except (TypeError, ValueError, AttributeError):
                    continue
            if rows:
                df = pd.DataFrame(rows)
                base = alt.Chart(df).encode(
                    x=alt.X("effort:Q", scale=alt.Scale(domain=[0.5, 5.5]), title="Effort →",
                            axis=alt.Axis(values=[1, 2, 3, 4, 5], grid=False, format="d")),
                    y=alt.Y("impact:Q", scale=alt.Scale(domain=[0.5, 5.5]), title="Impact →",
                            axis=alt.Axis(values=[1, 2, 3, 4, 5], grid=False, format="d")),
                    tooltip=["idea", "effort", "impact", "why"],
                )
                quad = alt.Chart(pd.DataFrame({"x": [0.5], "x2": [3], "y": [3], "y2": [5.5]})).mark_rect(
                    color="#7FA287", opacity=0.14).encode(x="x:Q", x2="x2:Q", y="y:Q", y2="y2:Q")
                quad_label = alt.Chart(pd.DataFrame({"x": [0.7], "y": [5.25], "t": ["Quick wins"]})).mark_text(
                    align="left", color="#2F4A36", fontWeight="bold").encode(x="x:Q", y="y:Q", text="t:N")
                pts = base.mark_circle(size=900, color=ORANGE, opacity=0.92)
                nums = base.mark_text(color="white", fontWeight="bold", fontSize=14).encode(text="#:N")
                st.altair_chart((quad + quad_label + pts + nums).properties(height=320),
                                use_container_width=True)
                for r in rows:
                    st.markdown(f"**{r['#']}. {esc(r['idea'])}**  \n<span style='color:#6E776D'>"
                                f"{esc(r['why'])}</span>", unsafe_allow_html=True)

        with right:
            st.markdown('<div class="bb-section">Your best matches</div>', unsafe_allow_html=True)
            matches = plan.get("matches", [])
            if not matches:
                st.info("No strong matches on the board yet. Scan a flyer to add more options.")
            first = True
            for m in matches:
                ev = store.get_event(m.get("event_id", ""))
                if not ev:
                    continue
                try:
                    fit = max(0, min(100, int(float(m.get("fit", 0)))))
                except (TypeError, ValueError):
                    fit = 0
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;margin-top:6px">'
                    f'<b>{esc(ev.get("title"))}</b><span style="color:{ORANGE};font-weight:700">{fit}% fit</span></div>'
                    f'<div class="bb-fit"><div style="width:{fit}%"></div></div>'
                    f'<div style="color:#6E776D;font-size:0.88rem;margin-bottom:6px">{esc(m.get("reason"))}</div>',
                    unsafe_allow_html=True,
                )
                if first:
                    event_card(ev, key_prefix="plan", show_outreach=False)
                    st.markdown('<div class="bb-section">✉️ Reach out</div>', unsafe_allow_html=True)
                    outreach_box(ev, plan, "plan_main")
                    first = False
