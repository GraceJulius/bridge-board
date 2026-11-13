"""New Bridge Board features: Get Help, fact-check card, Ask Bridge, community map, impact tracker."""

from __future__ import annotations

import html
import io
import json
import textwrap
import uuid
from datetime import datetime
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import ai

DATA = Path(__file__).parent / "data"
INK, FOREST, CREAM, TERRA = "#1E2A22", "#2F4A36", "#FAF8F2", "#B4532A"
RES_COLORS = {"hospital": [192, 86, 63], "clinic": [61, 112, 151], "campus": [47, 74, 54],
              "public_health": [138, 107, 176]}
CAT_RGB = {"Health": [192, 86, 63], "Volunteer": [62, 122, 82], "Social": [138, 107, 176],
           "Education": [61, 112, 151], "Other": [139, 141, 128]}


def esc(v) -> str:
    return html.escape(str(v or ""))


def load_resources() -> list[dict]:
    return json.loads((DATA / "resources.json").read_text(encoding="utf-8"))


def now_local() -> datetime:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        return datetime.now()


def open_status(res: dict, now: datetime) -> tuple[str, str]:
    """Return (label, color) for whether a resource is open right now."""
    if "24/7" in (res.get("hours") or ""):
        return "Open 24/7", "#3E7A52"
    hours = (res.get("open_hours") or {}).get(str(now.weekday()))
    if not res.get("open_hours"):
        return "Call for hours", "#8A9188"
    t = now.hour + now.minute / 60
    if hours and hours[0] <= t < hours[1]:
        return "Open now", "#3E7A52"
    return "Closed now", TERRA


def tel(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    return f"tel:{digits}"


# ---------------------------------------------------------------------------
# Get Help
# ---------------------------------------------------------------------------

def resource_card(r: dict, now: datetime, highlight: bool = False) -> str:
    label, color = open_status(r, now)
    border = f"border:2px solid {FOREST};" if highlight else ""
    src = (f'<a href="{esc(r["source"])}" target="_blank" style="color:#8A9188">source</a>'
           if r.get("source") else "")
    addr = f'<div class="bb-meta" style="margin:4px 0 0 0">📍 {esc(r["address"])}</div>' if r.get("address") else ""
    return f"""
<div class="bb-res" style="{border}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px">
    <div><div class="bb-card-title" style="font-size:1.08rem">{esc(r['name'])}</div>
      <span class="bb-badge" style="background:{color}">{label}</span>
      <span style="font-size:0.78rem;color:#6E776D;margin-left:6px">{esc(r.get('hours'))}</span></div>
    <a class="bb-call" style="color:white !important;text-decoration:none !important" href="{tel(r['phone'])}">📞 {esc(r['phone'])}</a>
  </div>
  <div class="bb-summary" style="font-size:0.88rem;margin-top:8px">{esc(r.get('when'))}</div>
  {addr}
  <div style="font-size:0.72rem;margin-top:6px">{src}</div>
</div>"""


HELP_CSS = f"""
<style>
.bb-sos {{ background: linear-gradient(135deg, #B23A2A, #8E2A1E); color: white; border-radius: 26px;
  padding: 24px 28px; display:flex; justify-content:space-between; align-items:center; gap: 18px; flex-wrap: wrap; }}
.bb-sos h3 {{ color:white; margin:0; font-family:'Inter Tight',sans-serif; font-weight:600; font-size:1.5rem; }}
.bb-sos p {{ margin:4px 0 0 0; opacity:.9; font-size:.92rem; }}
.bb-sos a {{ background:white; color:#8E2A1E !important; text-decoration:none !important; font-weight:700; border-radius:999px;
  padding: 12px 24px; font-size: 1.1rem; white-space:nowrap; }}
.bb-sos-mini {{ display:flex; gap:10px; margin-top: 12px; flex-wrap:wrap; }}
.bb-sos-mini a {{ background: {CREAM}; border:1px solid rgba(30,42,34,0.15); color:{INK} !important; text-decoration:none !important;
  border-radius: 999px; padding: 8px 16px; font-size:.86rem; }}
.bb-res {{ background:{CREAM}; border:1px solid rgba(30,42,34,0.10); border-radius: 22px; padding: 16px 18px;
  margin-bottom: 12px; animation: fadeUp .6s ease both; }}
.bb-call, .bb-call:hover, .bb-call:visited {{ background:{FOREST}; color:white !important; text-decoration:none !important; border-radius:999px; padding:8px 14px;
  font-size:.86rem; white-space:nowrap; font-weight:600; }}
.bb-route {{ border-radius: 22px; padding: 18px 22px; margin: 10px 0; }}
.bb-disclaimer {{ font-size:.78rem; color:#6E776D; margin-top:8px; }}
</style>"""


def render_help() -> None:
    resources = load_resources()
    by_id = {r["id"]: r for r in resources}
    now = now_local()
    st.markdown(HELP_CSS, unsafe_allow_html=True)
    st.markdown(
        """<div class="bb-sos"><div><h3>Life-threatening emergency? Call 911 now.</h3>
<p>Trouble breathing, chest pain, severe bleeding, unconscious, seizure, stroke signs, or overdose.</p></div>
<a href="tel:911" style="text-decoration:none !important">📞 Call 911</a></div>
<div class="bb-sos-mini">
  <a href="tel:988" style="text-decoration:none !important">💬 988 Crisis Lifeline (call or text)</a>
  <a href="tel:18002221222" style="text-decoration:none !important">☎ Poison Control 1-800-222-1222</a>
  <a href="tel:4843657211" style="text-decoration:none !important">🛡 Lincoln Public Safety 484-365-7211 (24/7)</a>
</div>""",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown('<div class="bb-section">Where should I go?</div>', unsafe_allow_html=True)
        st.caption("Describe what's going on. AI points you to the right verified place based on what's "
                   "open right now. It does not diagnose.")
        situation = st.text_area("What's going on?", height=110, label_visibility="collapsed",
                                 placeholder="e.g. My roommate has a fever and a rash and we're not sure "
                                             "if she had the MMR vaccine. It's 9pm.", key="help_text")
        if st.button("Find the right care", type="primary", disabled=not situation.strip()):
            hit = ai.red_flag_hit(situation)
            if hit:
                # Safety first: no AI call needed to say "call 911"
                st.session_state["help_route"] = {
                    "level": "emergency",
                    "recommend": ["988", "911"] if any(w in hit for w in ("suicid", "kill myself", "end my life",
                                                                          "hurt myself", "self")) else ["911"],
                    "why": "What you described can be life-threatening. Get emergency help right now.",
                    "while_you_wait": ["Stay with the person", "Don't drive yourself if you feel faint",
                                       "Call Lincoln Public Safety if you're on campus"],
                    "measles_concern": False, "guard": True,
                }
            else:
                with st.spinner("Finding the right place..."):
                    try:
                        st.session_state["help_route"] = ai.route_help(
                            situation, resources, now.strftime("%A %I:%M %p"))
                    except Exception as e:
                        st.error(f"Couldn't get a recommendation: {e}. If it's serious, call 911.")

        route = st.session_state.get("help_route")
        if route:
            level = route.get("level", "info")
            colors = {"emergency": ("#F7DCD5", "#8E2A1E", "🚨 Emergency: get help now"),
                      "urgent": ("#F7E4D8", "#8A3A1A", "⏱ Get care today"),
                      "soon": ("#EEF3EA", FOREST, "📅 Book a visit soon"),
                      "info": ("#EEF3EA", FOREST, "ℹ️ Information and prevention")}
            bg, fg, title = colors.get(level, colors["info"])
            steps = "".join(f"<li>{esc(s)}</li>" for s in route.get("while_you_wait", []))
            st.markdown(
                f'<div class="bb-route" style="background:{bg};color:{fg}"><b style="font-size:1.1rem">{title}</b>'
                f'<div style="margin-top:6px">{esc(route.get("why"))}</div>'
                + (f'<ul style="margin:8px 0 0 0">{steps}</ul>' if steps else "") + "</div>",
                unsafe_allow_html=True,
            )
            if route.get("measles_concern"):
                st.warning("Possible measles: **call before you go in** so others aren't exposed. The Chester "
                           "County Health Department asks people with symptoms to contact them first: 610-344-6225.")
            for rid in route.get("recommend", []):
                if rid in by_id:
                    st.markdown(resource_card(by_id[rid], now, highlight=True), unsafe_allow_html=True)
            st.markdown('<div class="bb-disclaimer">Bridge Board is not a medical provider and does not give '
                        'medical advice. When in doubt, call 911.</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="bb-section">Verified care near Lincoln & Oxford</div>', unsafe_allow_html=True)
        st.caption(f"Contacts checked against official sources on Nov 13, 2026. Status as of "
                   f"{now.strftime('%a %I:%M %p')}.")
        for r in resources:
            if r["type"] in ("emergency", "crisis"):
                continue
            st.markdown(resource_card(r, now), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Fact-check card
# ---------------------------------------------------------------------------

def _font(size: int, bold: bool = False):
    from PIL import ImageFont
    names = (["Arial Bold.ttf", "Helvetica-Bold.ttf", "DejaVuSans-Bold.ttf"] if bold
             else ["Arial.ttf", "Helvetica.ttf", "DejaVuSans.ttf"])
    dirs = ["/System/Library/Fonts/Supplemental/", "/Library/Fonts/", "/System/Library/Fonts/",
            "/usr/share/fonts/truetype/dejavu/", "C:/Windows/Fonts/", ""]
    for d in dirs:
        for n in names:
            try:
                return ImageFont.truetype(d + n, size)
            except Exception:
                continue
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def factcheck_png(fc: dict, lang: str = "en") -> bytes:
    from PIL import Image, ImageDraw
    W, pad = 1080, 70
    img = Image.new("RGB", (W, 1500), "#FAF8F2")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 210], fill="#2F4A36")
    d.text((pad, 50), "FACT CHECK · BRIDGE BOARD", font=_font(26, True), fill="#DCE8D9")
    y = 95
    for line in textwrap.wrap(fc.get(f"headline_{lang}", ""), 34):
        d.text((pad, y), line, font=_font(46, True), fill="white"); y += 54
    y = max(y, 210) + 40
    for c in fc.get("claims", []):
        d.text((pad, y), "THE FLYER SAYS", font=_font(22, True), fill="#B4532A"); y += 34
        for line in textwrap.wrap(str(c.get("claim", "")), 52):
            d.text((pad, y), line, font=_font(30), fill="#5C655C"); y += 38
        y += 10
        d.text((pad, y), "THE FACTS", font=_font(22, True), fill="#3E7A52"); y += 34
        for line in textwrap.wrap(str(c.get(f"fact_{lang}", "")), 50):
            d.text((pad, y), line, font=_font(32, True), fill="#1E2A22"); y += 42
        d.text((pad, y), f"Source: {c.get('source', '')}", font=_font(22), fill="#8A9188"); y += 60
    tips = fc.get(f"safety_tips_{lang}") or []
    if tips:
        d.text((pad, y), "STAY SAFE", font=_font(22, True), fill="#B4532A"); y += 34
        for t in tips:
            for line in textwrap.wrap("• " + str(t), 52):
                d.text((pad, y), line, font=_font(28), fill="#1E2A22"); y += 36
        y += 24
    d.rounded_rectangle([pad - 20, y, W - pad + 20, y + 170], radius=28, fill="#F5DCC0")
    yy = y + 28
    for line in textwrap.wrap(fc.get(f"bottom_line_{lang}", ""), 48)[:3]:
        d.text((pad, yy), line, font=_font(32, True), fill="#1E2A22"); yy += 42
    y += 210
    d.text((pad, y), "Questions? Chester County Health Department · 610-344-6225", font=_font(24), fill="#5C655C")
    img = img.crop((0, 0, W, min(1500, y + 70)))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def factcheck_section(event: dict, key: str) -> None:
    """Button + card for a flagged event."""
    k = f"fc_{key}"
    if st.button("🛡 Make a fact-check card to share", key=f"btn_{k}", type="primary"):
        with st.spinner("Writing a kind, accurate fact-check..."):
            try:
                st.session_state[k] = ai.make_factcheck(event)
            except Exception as e:
                st.error(f"Could not make the card: {e}")
    fc = st.session_state.get(k)
    if not fc:
        return
    lang = st.segmented_control("Card language", ["English", "Español"], default="English", key=f"lang_{k}")
    lg = "es" if lang == "Español" else "en"
    claims = "".join(
        f'<div style="margin-top:12px"><div class="bb-eyebrow" style="color:{TERRA}">The flyer says</div>'
        f'<div style="color:#5C655C">{esc(c.get("claim"))}</div>'
        f'<div class="bb-eyebrow" style="color:#3E7A52;margin-top:6px">The facts</div>'
        f'<div style="font-weight:600;color:{INK}">{esc(c.get("fact_" + lg))}</div>'
        f'<div style="font-size:.75rem;color:#8A9188">Source: {esc(c.get("source"))}</div></div>'
        for c in fc.get("claims", []))
    tips = fc.get(f"safety_tips_{lg}") or []
    tips_html = ("<div style='margin-top:12px'><div class='bb-eyebrow' style='color:%s'>Stay safe</div>%s</div>"
                 % (TERRA, "".join(f"<div>• {esc(t)}</div>" for t in tips))) if tips else ""
    st.markdown(
        f"""<div style="border-radius:24px;overflow:hidden;border:1px solid rgba(30,42,34,.12);margin-top:10px">
<div style="background:{FOREST};color:white;padding:18px 22px"><div class="bb-eyebrow" style="color:#DCE8D9">Fact check · Bridge Board</div>
<div style="font-family:'Inter Tight',sans-serif;font-size:1.4rem;font-weight:600">{esc(fc.get('headline_' + lg))}</div></div>
<div style="background:{CREAM};padding:6px 22px 20px 22px">{claims}{tips_html}
<div style="background:#F5DCC0;border-radius:18px;padding:14px 16px;margin-top:14px;font-weight:600;color:{INK}">
{esc(fc.get('bottom_line_' + lg))}</div></div></div>""",
        unsafe_allow_html=True,
    )
    try:
        st.download_button("⬇ Download as image", factcheck_png(fc, lg), file_name=f"fact-check-{lg}.png",
                           mime="image/png", key=f"dl_{k}_{lg}")
    except Exception as e:
        st.caption(f"Image export unavailable: {e}")


# ---------------------------------------------------------------------------
# Ask Bridge
# ---------------------------------------------------------------------------

def render_ask(events: list[dict]) -> None:
    resources = load_resources()
    st.markdown('<div class="bb-section">Ask Bridge</div>', unsafe_allow_html=True)
    st.caption("Ask anything about local events, volunteering, or where to get care. English or Español. "
               "Answers come from the board and verified resources.")
    hist = st.session_state.setdefault("ask_history", [])
    if not hist:
        cols = st.columns(3)
        starters = ["Where can I get the MMR vaccine?", "How can I help this weekend?",
                    "¿Dónde puedo vacunar a mis hijos contra el sarampión?"]
        for c, q in zip(cols, starters):
            if c.button(q, use_container_width=True):
                st.session_state["ask_pending"] = q
                st.rerun()
    for m in hist:
        with st.chat_message(m["role"], avatar="🌉" if m["role"] == "assistant" else "🙂"):
            st.markdown(m["content"])
    q = st.chat_input("Ask a question...") or st.session_state.pop("ask_pending", None)
    if q:
        with st.chat_message("user", avatar="🙂"):
            st.markdown(q)
        with st.chat_message("assistant", avatar="🌉"):
            if ai.red_flag_hit(q):
                st.error("If this is happening now, **call 911** (or **988** for a crisis). Then I can help more.")
            with st.spinner("Thinking..."):
                try:
                    a = ai.ask_bridge(q, hist, events, resources)
                except Exception as e:
                    a = f"Sorry, I couldn't answer that right now ({e})."
            st.markdown(a)
        hist += [{"role": "user", "content": q}, {"role": "assistant", "content": a}]


# ---------------------------------------------------------------------------
# Community map
# ---------------------------------------------------------------------------

def render_map(events: list[dict]) -> None:
    import pydeck as pdk
    rows = []
    for i, e in enumerate(events):
        lat, lon = ai.place_coords(e)
        lat += ((i % 3) - 1) * 0.0012  # small offset so stacked events stay visible
        lon += ((i % 2) - 0.5) * 0.0016
        flagged = ai.is_flagged(e)
        rows.append({"lat": lat, "lon": lon, "name": e.get("title", ""),
                     "info": ("⚠ Flagged by trust check" if flagged else e.get("category", "")) + " · " + str(e.get("date", "")),
                     "color": [180, 83, 42] if flagged else CAT_RGB.get(e.get("category"), CAT_RGB["Other"]),
                     "radius": 140})
    for r in load_resources():
        if r.get("lat") is None:
            continue
        rows.append({"lat": r["lat"], "lon": r["lon"], "name": "✚ " + r["name"], "info": r.get("hours", ""),
                     "color": RES_COLORS.get(r["type"], [47, 74, 54]), "radius": 220})
    df = pd.DataFrame(rows)
    layer = pdk.Layer("ScatterplotLayer", df, get_position="[lon, lat]", get_fill_color="color",
                      get_radius="radius", radius_min_pixels=7, radius_max_pixels=22, pickable=True,
                      stroked=True, get_line_color=[250, 248, 242], line_width_min_pixels=2, opacity=0.9)
    view = pdk.ViewState(latitude=39.83, longitude=-75.88, zoom=10.2, pitch=0)
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view, map_provider="carto",
                             map_style=pdk.map_styles.CARTO_LIGHT,
                             tooltip={"html": "<b>{name}</b><br/>{info}"}), use_container_width=True)
    chips = "".join(
        f'<span class="bb-chip"><span style="color:rgb({c[0]},{c[1]},{c[2]})">●</span> {n}</span>'
        for n, c in [("Health", CAT_RGB["Health"]), ("Volunteer", CAT_RGB["Volunteer"]), ("Social", CAT_RGB["Social"]),
                     ("Education", CAT_RGB["Education"]), ("Flagged", [180, 83, 42]),
                     ("Hospital / clinic", RES_COLORS["hospital"]), ("Campus", RES_COLORS["campus"])])
    st.markdown(chips, unsafe_allow_html=True)
    st.caption("Event locations are approximate.")


# ---------------------------------------------------------------------------
# Impact tracker
# ---------------------------------------------------------------------------

def load_impact() -> list[dict]:
    p = DATA / "impact.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def save_impact(rows: list[dict]) -> None:
    (DATA / "impact.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def render_impact(events: list[dict]) -> None:
    rows = load_impact()
    good = [e for e in events if not ai.is_flagged(e)]
    by_title = {e["title"]: e for e in good}

    total_h = sum(float(r.get("hours", 0)) for r in rows)
    people = len({r.get("student", "").strip().lower() for r in rows if r.get("student")})
    evs = len({r.get("event") for r in rows})
    st.markdown(
        f"""<div class="bb-how" style="margin-top:6px">
<div class="bb-how-card peach" style="min-height:120px"><div class="bb-eyebrow">Volunteer hours</div>
<div style="font-family:'Inter Tight',sans-serif;font-size:2.6rem;font-weight:500;color:{INK}">{total_h:g}</div></div>
<div class="bb-how-card" style="min-height:120px"><div class="bb-eyebrow">Students involved</div>
<div style="font-family:'Inter Tight',sans-serif;font-size:2.6rem;font-weight:500;color:{INK}">{people}</div></div>
<div class="bb-how-card" style="min-height:120px"><div class="bb-eyebrow">Community events supported</div>
<div style="font-family:'Inter Tight',sans-serif;font-size:2.6rem;font-weight:500;color:{INK}">{evs}</div></div>
</div>""",
        unsafe_allow_html=True,
    )
    if any(r.get("is_sample") for r in rows):
        st.caption("Includes entries marked as sample data for the demo.")

    left, right = st.columns([1, 1.1], gap="large")
    with left:
        st.markdown('<div class="bb-section">Log your impact</div>', unsafe_allow_html=True)
        with st.form("impact_form", clear_on_submit=True):
            student = st.text_input("Your first name or initials")
            event = st.selectbox("Event", list(by_title) or ["(no events yet)"])
            hours = st.number_input("Hours", min_value=0.5, max_value=24.0, value=2.0, step=0.5)
            note = st.text_input("What did you do? (optional)", placeholder="Helped at the check-in table")
            if st.form_submit_button("Add to our impact", type="primary") and event in by_title:
                rows.insert(0, {"id": uuid.uuid4().hex[:6], "student": student.strip() or "Anonymous",
                                "event": event, "category": by_title[event].get("category", "Other"),
                                "hours": hours, "note": note, "date": now_local().strftime("%Y-%m-%d"),
                                "is_sample": False})
                save_impact(rows)
                st.toast("Thank you! Logged. 🌱")
                st.rerun()
    with right:
        st.markdown('<div class="bb-section">Hours by area</div>', unsafe_allow_html=True)
        if rows:
            df = pd.DataFrame(rows)
            df["hours"] = df["hours"].astype(float)
            agg = df.groupby("category", as_index=False)["hours"].sum().sort_values("hours", ascending=False)
            color = alt.Scale(domain=list(CAT_RGB), range=[f"rgb({c[0]},{c[1]},{c[2]})" for c in CAT_RGB.values()])
            chart = alt.Chart(agg).mark_bar(cornerRadiusEnd=8, height=26).encode(
                x=alt.X("hours:Q", title="Hours"), y=alt.Y("category:N", sort="-x", title=None),
                color=alt.Color("category:N", scale=color, legend=None), tooltip=["category", "hours"])
            text = chart.mark_text(align="left", dx=6, color=INK).encode(text=alt.Text("hours:Q", format="~g"))
            st.altair_chart((chart + text).properties(height=60 + 42 * len(agg)), use_container_width=True)
            st.markdown('<div class="bb-section" style="font-size:1rem">Recent</div>', unsafe_allow_html=True)
            for r in rows[:5]:
                tag = " · <i>sample</i>" if r.get("is_sample") else ""
                st.markdown(f"<div style='font-size:.9rem;padding:6px 0;border-bottom:1px solid rgba(30,42,34,.08)'>"
                            f"<b>{esc(r['student'])}</b> · {float(r['hours']):g}h at {esc(r['event'])}"
                            f"<span style='color:#6E776D'> {esc(r.get('note'))}{tag}</span></div>",
                            unsafe_allow_html=True)
        else:
            st.info("No hours logged yet. Be the first!")
