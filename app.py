"""
Consulting Problem Structurer — Web Interface
Run with: python -m streamlit run app.py
"""

import streamlit as st
import anthropic
import json
from datetime import datetime
from pathlib import Path

# ── Import the core logic from structurer.py ──────────────────
from structurer import SYSTEM_PROMPT, format_brief, save_brief

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Consulting Problem Structurer",
    page_icon="🔍",
    layout="wide"
)

# ── Header ────────────────────────────────────────────────────
st.title("🔍 Consulting Problem Structurer")
st.caption("Paste a client problem statement. Get a structured diagnostic brief in seconds.")
st.divider()

# ── Input ─────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    problem = st.text_area(
        "Client problem statement",
        placeholder='e.g. "Our engineering and product teams are constantly misaligned. '
                    'We ship things customers don\'t want, and by the time we realise it '
                    'we\'ve lost two sprints. The CTO and CPO are barely talking..."',
        height=160,
        label_visibility="collapsed"
    )

with col2:
    st.markdown("**What this tool does:**")
    st.markdown("- Classifies the problem type")
    st.markdown("- Generates 3 leading hypotheses")
    st.markdown("- Builds a MECE issue tree")
    st.markdown("- Produces diagnostic questions")
    st.markdown("- Suggests a first workshop format")
    st.markdown("- Flags red flags for the engagement")

run = st.button("Structure this problem →", type="primary", disabled=not bool(problem.strip()))

# ── Analysis ──────────────────────────────────────────────────
if run and problem.strip():
    with st.spinner("Analyzing with Claude..."):
        try:
            # Works locally (env var) and on Streamlit Cloud (secrets)
            api_key = st.secrets.get("ANTHROPIC_API_KEY", None) if hasattr(st, "secrets") else None
            client = anthropic.Anthropic(api_key=api_key)  # falls back to env var if None
            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": f"Client problem statement:\n\n{problem}"}]
            )

            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            data = json.loads(raw)

        except Exception as e:
            st.error(f"Something went wrong: {e}")
            st.stop()

    st.divider()

    # ── Results layout ────────────────────────────────────────
    st.subheader("📋 Diagnostic Brief")
    st.caption(f"Generated {datetime.now().strftime('%d %B %Y, %H:%M')}  ·  "
               f"{response.usage.input_tokens} tokens in / {response.usage.output_tokens} out")

    # Classification
    pc = data["problem_classification"]
    badge_color = {
        "Delivery/Execution": "🔴",
        "Org/People": "🟡",
        "Strategy/Product": "🔵",
        "Technical Architecture": "🟢"
    }.get(pc["primary_type"], "⚪")

    st.markdown(f"### {badge_color} {pc['primary_type']}  ·  {pc['confidence']} confidence")
    st.info(pc["reasoning"])

    st.divider()

    # Three columns: Hypotheses | Issue Tree | Questions
    h_col, t_col, q_col = st.columns(3)

    with h_col:
        st.markdown("#### 💡 Leading Hypotheses")
        for i, h in enumerate(data["initial_hypotheses"], 1):
            with st.expander(f"Hypothesis {i}", expanded=True):
                st.markdown(f"**{h['hypothesis']}**")
                st.caption(f"Evidence: {h['evidence_in_statement']}")

    with t_col:
        st.markdown("#### 🌳 Issue Tree")
        it = data["issue_tree"]
        st.markdown(f"**Root:** {it['root_problem']}")
        for branch in it["branches"]:
            with st.expander(branch["area"], expanded=False):
                for sub in branch["sub_issues"]:
                    st.markdown(f"- {sub}")

    with q_col:
        st.markdown("#### ❓ Diagnostic Questions")
        for i, q in enumerate(data["diagnostic_questions"], 1):
            with st.expander(f"Q{i}", expanded=True):
                st.markdown(f"**{q['question']}**")
                st.caption(f"Reveals: {q['what_it_reveals']}")

    st.divider()

    # Workshop + Red flags side by side
    w_col, r_col = st.columns(2)

    with w_col:
        ws = data["workshop_suggestion"]
        st.markdown("#### 🗓️ Suggested First Workshop")
        st.markdown(f"**{ws['format']}** · {ws['duration']}")
        for item in ws["agenda"]:
            st.markdown(f"- {item}")
        st.success(f"**Output:** {ws['key_output']}")

    with r_col:
        if data.get("red_flags"):
            st.markdown("#### ⚠️ Red Flags")
            for flag in data["red_flags"]:
                st.warning(flag)

    st.divider()

    # Save + download
    brief_text = format_brief(data, problem)
    filepath = save_brief(brief_text, problem)

    st.download_button(
        label="⬇️ Download brief as .md",
        data=brief_text,
        file_name=filepath.name,
        mime="text/markdown"
    )
    st.caption(f"Also saved to: `{filepath}`")
