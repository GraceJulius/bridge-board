"""Bridge Board: turning flyers and scattered ideas into Lincoln x Oxford connections.

Run:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

import ai
import store

st.set_page_config(page_title="Bridge Board", page_icon="🌉", layout="wide")

CATEGORY_COLORS = {
    "Health": "#e5484d",
    "Volunteer": "#30a46c",
    "Social": "#8e4ec6",
    "Education": "#0090ff",
    "Other": "#8b8d98",
}

st.markdown(
    """
    <style>
      .badge {display:inline-block;padding:2px 10px;border-radius:999px;color:white;
              font-size:0.8rem;font-weight:600;margin-right:6px;}
      .sample {background:#f0f0f3;color:#555;}
    </style>
    """,
    unsafe_allow_html=True,
)


def badge(text: str, color: str | None = None, extra_class: str = "") -> str:
    style = f"background:{color};" if color else ""
    return f'<span class="badge {extra_class}" style="{style}">{text}</span>'


def outreach_box(event: dict, plan: dict | None, key: str) -> None:
    if st.button("✉️ Draft outreach message", key=f"draft_{key}"):
        with st.spinner("Drafting..."):
            try:
                st.session_state[f"draft_text_{key}"] = ai.draft_outreach(event, plan)
            except Exception as e:  # keep the demo alive
                st.error(f"Could not draft message: {e}")
    if st.session_state.get(f"draft_text_{key}"):
        st.text_area("Edit before sending", st.session_state[f"draft_text_{key}"],
                     height=220, key=f"draft_area_{key}")
        st.caption("Copy with Ctrl/Cmd + A, then Ctrl/Cmd + C")


def event_card(event: dict, key_prefix: str = "board") -> None:
    with st.container(border=True):
        cat = event.get("category", "Other")
        header = badge(cat, CATEGORY_COLORS.get(cat, "#8b8d98"))
        if event.get("is_sample"):
            header += badge("Sample data", extra_class="sample")
        st.markdown(header, unsafe_allow_html=True)
        st.subheader(event.get("title", "Untitled event"))
        meta = " · ".join(x for x in [event.get("date"), event.get("time"), event.get("location")] if x)
        if meta:
            st.caption(meta)

        lang = st.radio("Language", ["English", "Español"], horizontal=True,
                        key=f"{key_prefix}_lang_{event['id']}", label_visibility="collapsed")
        st.write(event.get("summary_es") if lang == "Español" else event.get("summary_en"))

        if event.get("how_students_can_help"):
            st.markdown(f"**How students can help:** {event['how_students_can_help']}")
        if event.get("organizer") or event.get("contact"):
            st.caption(f"Organizer: {event.get('organizer', '')}  {event.get('contact', '')}")

        with st.expander("Reach out to the organizer"):
            outreach_box(event, None, f"{key_prefix}_{event['id']}")


# ---------------------------------------------------------------------------
st.title("🌉 Bridge Board")
st.write("Snap a flyer, find where you fit, and connect Lincoln and Oxford one step at a time.")

tab_board, tab_scan, tab_plan = st.tabs(["📋 Board", "📸 Scan a flyer", "🧠 I'm overwhelmed"])

# ---------------- Board ----------------
with tab_board:
    events = store.load_events()
    choice = st.segmented_control("Filter", ["All"] + ai.CATEGORIES, default="All")
    shown = [e for e in events if choice in (None, "All") or e.get("category") == choice]
    if not shown:
        st.info("No events in this category yet. Scan a flyer to add one!")
    cols = st.columns(2)
    for i, ev in enumerate(shown):
        with cols[i % 2]:
            event_card(ev)

# ---------------- Scan ----------------
with tab_scan:
    st.write("Upload or take a photo of a community flyer. AI reads it, tags it, and translates it.")
    photo = st.camera_input("Take a photo") if st.toggle("Use camera") else None
    upload = st.file_uploader("...or upload an image", type=["png", "jpg", "jpeg", "webp"])
    image = photo or upload

    if image and st.button("✨ Read this flyer", type="primary"):
        img_bytes = image.getvalue()
        mime = image.type or "image/jpeg"
        try:
            with st.status("Working on it...", expanded=True) as status:
                st.write("👀 Reading the flyer (vision)...")
                event = ai.extract_event(img_bytes, mime)
                st.write("🏷️ Tagging and translating...")
                event.update(ai.tag_and_translate(event))
                event = store.add_event(event)
                status.update(label="Added to the board!", state="complete")
            st.session_state["last_scanned"] = event
        except Exception as e:
            st.error(f"Something went wrong reading the flyer: {e}")

    if st.session_state.get("last_scanned"):
        c1, c2 = st.columns([1, 1])
        with c1:
            if image:
                st.image(image, caption="Your flyer")
        with c2:
            event_card(st.session_state["last_scanned"], key_prefix="scan")

# ---------------- Overwhelmed ----------------
with tab_plan:
    st.write("Dump every idea you have, messy is fine. AI will help you pick one real next step.")
    dump = st.text_area(
        "Your brain dump",
        height=180,
        placeholder="I want Lincoln and Oxford to get along better... maybe events together? "
                    "A volunteer app? There's measles at the high school and I want to help but "
                    "I don't know anyone in Oxford...",
    )
    if st.button("🧭 Help me start", type="primary", disabled=not dump.strip()):
        with st.spinner("Sorting through your ideas..."):
            try:
                st.session_state["plan"] = ai.make_plan(dump, store.load_events())
            except Exception as e:
                st.error(f"Could not make a plan: {e}")

    plan = st.session_state.get("plan")
    if plan:
        st.markdown("#### What I'm hearing")
        st.write(" · ".join(plan.get("themes", [])))

        st.markdown("#### Your ideas, ranked")
        for i, idea in enumerate(plan.get("ranked_ideas", []), 1):
            st.markdown(
                f"**{i}. {idea.get('idea')}**  \n"
                f"Effort: `{idea.get('effort')}` · Impact: `{idea.get('impact')}`  \n"
                f"{idea.get('why', '')}"
            )

        st.markdown("#### ✅ Your step this week")
        st.success(plan.get("this_week", ""))
        if plan.get("encouragement"):
            st.caption(plan["encouragement"])

        linked = store.get_event(plan.get("linked_event_id", ""))
        if linked:
            st.markdown("#### 🔗 Matched event")
            event_card(linked, key_prefix="plan")
            st.markdown("#### ✉️ Your outreach message")
            outreach_box(linked, plan, "plan_main")
