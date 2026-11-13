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

NAVY = "#14213D"
ORANGE = "#F26B1D"
CATEGORY_COLORS = {
    "Health": "#E5484D",
    "Volunteer": "#2F9E6B",
    "Social": "#8E4EC6",
    "Education": "#0B7BD9",
    "Other": "#8B8D98",
}
TRUST_BADGES = {
    "aligned": ("✓ Matches official guidance", "#2F9E6B"),
    "needs_review": ("⚠ Health claims need review", "#D9480F"),
}

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"], .stMarkdown, p, li, label {{ font-family: 'Inter', sans-serif; }}
h1, h2, h3, h4, .bb-title {{ font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.01em; }}
#MainMenu, footer, [data-testid="stDecoration"] {{ visibility: hidden; }}
.block-container {{ padding-top: 1.5rem; max-width: 1200px; }}

.bb-hero {{
  background: radial-gradient(circle at 85% 20%, rgba(242,107,29,0.35), transparent 40%),
              linear-gradient(135deg, {NAVY} 0%, #1F3A6B 100%);
  color: white; border-radius: 22px; padding: 34px 38px; margin-bottom: 18px;
}}
.bb-hero h1 {{ color: white; font-size: 2.6rem; margin: 0 0 6px 0; }}
.bb-hero p {{ color: rgba(255,255,255,0.85); font-size: 1.08rem; margin: 0; max-width: 680px; }}
.bb-stats {{ display: flex; gap: 12px; margin-top: 22px; flex-wrap: wrap; }}
.bb-stat {{ background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.18);
  border-radius: 14px; padding: 10px 16px; min-width: 130px; }}
.bb-stat b {{ display: block; font-size: 1.5rem; font-family: 'Space Grotesk', sans-serif; }}
.bb-stat span {{ font-size: 0.8rem; opacity: 0.8; }}

[data-testid="stVerticalBlockBorderWrapper"] {{
  border-radius: 18px !important; background: white;
  box-shadow: 0 1px 2px rgba(20,33,61,0.04), 0 8px 24px rgba(20,33,61,0.06);
}}
.bb-card-top {{ height: 5px; border-radius: 6px; margin: -4px 0 12px 0; }}
.bb-badges {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }}
.bb-badge {{ padding: 3px 10px; border-radius: 999px; font-size: 0.74rem; font-weight: 600; color: white; }}
.bb-badge.light {{ background: #EEF0F4; color: #5B6275; }}
.bb-card-title {{ font-family: 'Space Grotesk', sans-serif; font-size: 1.25rem; font-weight: 700;
  color: {NAVY}; margin: 2px 0 4px 0; }}
.bb-meta {{ color: #6B7186; font-size: 0.86rem; margin-bottom: 10px; }}
.bb-summary {{ color: #2A3350; font-size: 0.96rem; line-height: 1.5; }}
.bb-help {{ background: #FFF4EC; border-left: 3px solid {ORANGE}; border-radius: 8px;
  padding: 8px 12px; margin-top: 10px; font-size: 0.88rem; color: #6A3410; }}
.bb-trust {{ border-radius: 10px; padding: 8px 12px; margin-top: 10px; font-size: 0.84rem; }}
.bb-trust.ok {{ background: #EAF7F0; color: #1D6B47; }}
.bb-trust.warn {{ background: #FFF0E6; color: #9A3412; border: 1px solid #FDBA8C; }}
.bb-org {{ color: #8A8FA3; font-size: 0.8rem; margin-top: 10px; }}

.bb-step {{ display: flex; gap: 12px; align-items: flex-start; padding: 10px 0;
  border-bottom: 1px dashed #E3E5EB; }}
.bb-step:last-child {{ border-bottom: none; }}
.bb-dot {{ width: 28px; height: 28px; border-radius: 50%; background: {NAVY}; color: white;
  display: flex; align-items: center; justify-content: center; font-size: 0.8rem; flex-shrink: 0; }}
.bb-step b {{ color: {NAVY}; }}
.bb-step small {{ color: #6B7186; display: block; }}

.bb-chip {{ display: inline-block; background: #EEF2FA; color: {NAVY}; border-radius: 999px;
  padding: 5px 12px; margin: 0 6px 6px 0; font-size: 0.86rem; font-weight: 500; }}
.bb-action {{ background: linear-gradient(135deg, {ORANGE}, #F59E0B); color: white;
  border-radius: 18px; padding: 20px 24px; font-size: 1.1rem; }}
.bb-action small {{ display: block; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.08em;
  font-size: 0.72rem; margin-bottom: 4px; }}
.bb-fit {{ height: 8px; border-radius: 6px; background: #EEF0F4; overflow: hidden; margin: 6px 0 4px 0; }}
.bb-fit > div {{ height: 100%; background: linear-gradient(90deg, {ORANGE}, #F59E0B); }}
.bb-section {{ font-family: 'Space Grotesk', sans-serif; font-size: 1.15rem; font-weight: 700;
  color: {NAVY}; margin: 18px 0 8px 0; }}

.stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
.stTabs [data-baseweb="tab"] {{ background: white; border-radius: 12px 12px 0 0; padding: 8px 18px; }}
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
    status = (event.get("trust") or {}).get("status")

    badges = f'<span class="bb-badge" style="background:{color}">{esc(cat)}</span>'
    if status in TRUST_BADGES:
        label, bcolor = TRUST_BADGES[status]
        badges += f'<span class="bb-badge" style="background:{bcolor}">{label}</span>'
    if event.get("is_sample"):
        badges += '<span class="bb-badge light">Sample data</span>'
    else:
        badges += '<span class="bb-badge light">📸 Scanned</span>'

    meta = " · ".join(esc(x) for x in [event.get("date"), event.get("time"), event.get("location")] if x)
    summary = event.get("summary_es") if lang == "Español" else event.get("summary_en")
    helps = (f'<div class="bb-help">🤝 <b>How students can help:</b> {esc(event["how_students_can_help"])}</div>'
             if event.get("how_students_can_help") and status != "needs_review" else "")
    org = " ".join(esc(x) for x in [event.get("organizer"), event.get("contact")] if x)

    with st.container(border=True):
        st.markdown(
            f"""<div class="bb-card-top" style="background:{color}"></div>
<div class="bb-badges">{badges}</div>
<div class="bb-card-title">{esc(event.get("title") or "Untitled event")}</div>
<div class="bb-meta">🗓 {meta}</div>
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
        f'<div class="bb-step"><div class="bb-dot">{icon}</div><div><b>{esc(t)}</b><small>{esc(d)}</small></div></div>'
        for icon, t, d in steps
    )
    return f"<div>{rows}</div>"


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
events = store.load_events()
n_health = sum(1 for e in events if e.get("category") == "Health")
n_flagged = sum(1 for e in events if (e.get("trust") or {}).get("status") == "needs_review")

st.markdown(
    f"""
<div class="bb-hero">
  <h1>🌉 Bridge Board</h1>
  <p>Snap a flyer, find where you fit, and build real connections between Lincoln University
  and the Oxford community, one small step at a time.</p>
  <div class="bb-stats">
    <div class="bb-stat"><b>{len(events)}</b><span>events on the board</span></div>
    <div class="bb-stat"><b>{n_health}</b><span>health events</span></div>
    <div class="bb-stat"><b>{n_flagged}</b><span>flagged for misinformation</span></div>
    <div class="bb-stat"><b>EN · ES</b><span>every event translated</span></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

tab_board, tab_scan, tab_plan = st.tabs(["📋  Community Board", "📸  Scan a Flyer", "🧭  I'm Overwhelmed"])

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
                    color="#2F9E6B", opacity=0.08).encode(x="x:Q", x2="x2:Q", y="y:Q", y2="y2:Q")
                quad_label = alt.Chart(pd.DataFrame({"x": [0.7], "y": [5.25], "t": ["Quick wins"]})).mark_text(
                    align="left", color="#2F9E6B", fontWeight="bold").encode(x="x:Q", y="y:Q", text="t:N")
                pts = base.mark_circle(size=900, color=ORANGE, opacity=0.92)
                nums = base.mark_text(color="white", fontWeight="bold", fontSize=14).encode(text="#:N")
                st.altair_chart((quad + quad_label + pts + nums).properties(height=320),
                                use_container_width=True)
                for r in rows:
                    st.markdown(f"**{r['#']}. {esc(r['idea'])}**  \n<span style='color:#6B7186'>"
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
                    f'<div style="color:#6B7186;font-size:0.88rem;margin-bottom:6px">{esc(m.get("reason"))}</div>',
                    unsafe_allow_html=True,
                )
                if first:
                    event_card(ev, key_prefix="plan", show_outreach=False)
                    st.markdown('<div class="bb-section">✉️ Reach out</div>', unsafe_allow_html=True)
                    outreach_box(ev, plan, "plan_main")
                    first = False
