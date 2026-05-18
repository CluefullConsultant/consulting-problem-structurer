"""
Consulting Problem Structurer - Web Interface
Run with: python -m streamlit run app.py
"""

import streamlit as st
import anthropic
import json
from datetime import datetime
from pathlib import Path
from structurer import SYSTEM_PROMPT, format_brief, save_brief

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Clueful Consultant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Clean up default Streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    /* Hero section */
    .hero {
        padding: 2.5rem 0 1.5rem 0;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 2rem;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #111827;
        letter-spacing: -0.03em;
        margin: 0;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #6b7280;
        margin-top: 0.4rem;
        max-width: 560px;
    }
    .hero-tag {
        display: inline-block;
        background: #f0fdf4;
        color: #166534;
        border: 1px solid #bbf7d0;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.2rem 0.75rem;
        margin-bottom: 0.75rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* Cards */
    .card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
    }
    .card-title {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #9ca3af;
        margin-bottom: 0.5rem;
    }

    /* Classification badge */
    .badge {
        display: inline-block;
        border-radius: 8px;
        padding: 0.5rem 1.1rem;
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    .badge-org      { background: #fef9c3; color: #854d0e; }
    .badge-delivery { background: #fee2e2; color: #991b1b; }
    .badge-strategy { background: #dbeafe; color: #1e40af; }
    .badge-tech     { background: #d1fae5; color: #065f46; }

    /* Section headers */
    .section-label {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        color: #9ca3af;
        margin: 1.5rem 0 0.6rem 0;
    }

    /* Hypothesis item */
    .hyp-item {
        background: #f9fafb;
        border-left: 3px solid #6366f1;
        border-radius: 0 8px 8px 0;
        padding: 0.75rem 1rem;
        margin-bottom: 0.6rem;
    }
    .hyp-title { font-weight: 600; color: #111827; font-size: 0.92rem; }
    .hyp-evidence { color: #6b7280; font-size: 0.82rem; margin-top: 0.3rem; }

    /* Question item */
    .q-item {
        background: #f9fafb;
        border-left: 3px solid #f59e0b;
        border-radius: 0 8px 8px 0;
        padding: 0.75rem 1rem;
        margin-bottom: 0.6rem;
    }
    .q-title { font-weight: 600; color: #111827; font-size: 0.92rem; }
    .q-reveals { color: #6b7280; font-size: 0.82rem; margin-top: 0.3rem; }

    /* Red flag item */
    .flag-item {
        background: #fff7ed;
        border-left: 3px solid #f97316;
        border-radius: 0 8px 8px 0;
        padding: 0.65rem 1rem;
        margin-bottom: 0.5rem;
        color: #7c2d12;
        font-size: 0.88rem;
    }

    /* Issue tree branch */
    .branch-title {
        font-weight: 600;
        color: #374151;
        font-size: 0.9rem;
        margin-top: 0.6rem;
    }
    .branch-item {
        color: #6b7280;
        font-size: 0.85rem;
        padding-left: 1rem;
        margin-top: 0.25rem;
    }

    /* Example buttons row */
    .example-label {
        font-size: 0.78rem;
        color: #9ca3af;
        margin-bottom: 0.4rem;
        font-weight: 500;
    }

    /* Divider */
    .thin-divider {
        border: none;
        border-top: 1px solid #f3f4f6;
        margin: 1.5rem 0;
    }

    /* Token counter */
    .token-info {
        font-size: 0.75rem;
        color: #d1d5db;
        text-align: right;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-tag">Powered by Claude</div>
    <div class="hero-title">Consulting Problem Structurer</div>
    <div class="hero-subtitle">
        Paste what a client says in the first five minutes of a call.
        Get a structured diagnostic brief: hypothesis tree, MECE issue breakdown,
        and first-meeting questions, in seconds.
    </div>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────
if "problem_text" not in st.session_state:
    st.session_state.problem_text = ""
if "auto_run" not in st.session_state:
    st.session_state.auto_run = False

# ── Example problems ──────────────────────────────────────────
EXAMPLES = {
    "CTO/CPO conflict": "Our engineering and product teams are constantly misaligned. We ship things the customers don't want, and by the time we realise it, we've lost two sprints. The CTO and CPO are barely talking. I need someone to fix this before our Series B due diligence.",
    "Scaling crisis": "We've grown from 15 to 80 engineers in 18 months. Deployment frequency dropped from 5x a day to once a week. Senior engineers are spending 60% of their time in meetings. We're about to miss our product roadmap commitment to our Series B investors.",
    "Revenue plateau": "We hit €2M ARR last year and haven't moved since. Sales says the product is missing features. Product says sales is targeting the wrong customers. Meanwhile we're burning €180k a month and have 9 months of runway.",
}

st.markdown('<div class="example-label">Try an example (auto-runs):</div>', unsafe_allow_html=True)
ex_cols = st.columns(len(EXAMPLES))
for col, (label, text) in zip(ex_cols, EXAMPLES.items()):
    if col.button(label, use_container_width=True):
        st.session_state.problem_text = text
        st.session_state.auto_run = True

# ── Input ─────────────────────────────────────────────────────
problem = st.text_area(
    "Client problem statement",
    value=st.session_state.problem_text,
    placeholder='Type or paste what the client says. Messy, emotional, incomplete is fine. That\'s what this tool is for.',
    height=130,
    label_visibility="collapsed",
    key="problem_input"
)
# Keep session state in sync when user types manually
st.session_state.problem_text = problem

col_btn, col_tip = st.columns([1, 4])
run_clicked = col_btn.button("Structure →", type="primary", disabled=not bool(problem.strip()))
col_tip.markdown(
    '<span style="color:#9ca3af;font-size:0.82rem;line-height:3rem;">'
    'Works best with real, unfiltered language from the client.</span>',
    unsafe_allow_html=True
)

# Fire if button clicked OR if an example was just selected
run = run_clicked or st.session_state.auto_run
if st.session_state.auto_run:
    st.session_state.auto_run = False  # reset so it doesn't loop

# ── Analysis ──────────────────────────────────────────────────
if run and problem.strip():
    with st.spinner("Analyzing with Claude..."):
        try:
            api_key = st.secrets.get("ANTHROPIC_API_KEY", None) if hasattr(st, "secrets") else None
            client = anthropic.Anthropic(api_key=api_key)

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

        except json.JSONDecodeError as e:
            st.error(f"Claude returned unexpected output. Try again. ({e})")
            st.stop()
        except Exception as e:
            st.error(f"Something went wrong: {e}")
            st.stop()

    # ── Classification ────────────────────────────────────────
    st.markdown('<hr class="thin-divider">', unsafe_allow_html=True)

    pc = data["problem_classification"]
    badge_class = {
        "Delivery/Execution":    "badge-delivery",
        "Org/People":            "badge-org",
        "Strategy/Product":      "badge-strategy",
        "Technical Architecture":"badge-tech",
    }.get(pc["primary_type"], "badge-org")

    confidence_color = {"High": "#16a34a", "Medium": "#d97706", "Low": "#dc2626"}.get(pc["confidence"], "#6b7280")

    st.markdown(f"""
    <div class="card">
        <div class="card-title">Problem Classification</div>
        <span class="badge {badge_class}">{pc['primary_type']}</span>
        <span style="margin-left:0.75rem;font-size:0.82rem;font-weight:600;color:{confidence_color};">
            {pc['confidence']} confidence
        </span>
        <div style="color:#6b7280;font-size:0.88rem;margin-top:0.5rem;">{pc['reasoning']}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Three columns ─────────────────────────────────────────
    h_col, q_col, t_col = st.columns([1, 1, 1])

    with h_col:
        st.markdown('<div class="section-label">Leading Hypotheses</div>', unsafe_allow_html=True)
        for i, h in enumerate(data["initial_hypotheses"], 1):
            st.markdown(f"""
            <div class="hyp-item">
                <div class="hyp-title">{i}. {h['hypothesis']}</div>
                <div class="hyp-evidence">Evidence: {h['evidence_in_statement']}</div>
            </div>
            """, unsafe_allow_html=True)

    with q_col:
        st.markdown('<div class="section-label">Diagnostic Questions</div>', unsafe_allow_html=True)
        for i, q in enumerate(data["diagnostic_questions"], 1):
            st.markdown(f"""
            <div class="q-item">
                <div class="q-title">Q{i}: {q['question']}</div>
                <div class="q-reveals">Reveals: {q['what_it_reveals']}</div>
            </div>
            """, unsafe_allow_html=True)

    with t_col:
        st.markdown('<div class="section-label">Issue Tree</div>', unsafe_allow_html=True)
        it = data["issue_tree"]
        st.markdown(f'<div style="font-size:0.85rem;color:#374151;font-weight:600;margin-bottom:0.5rem;">Root: {it["root_problem"]}</div>', unsafe_allow_html=True)
        for branch in it["branches"]:
            st.markdown(f'<div class="branch-title">↳ {branch["area"]}</div>', unsafe_allow_html=True)
            for sub in branch["sub_issues"]:
                st.markdown(f'<div class="branch-item">· {sub}</div>', unsafe_allow_html=True)

    # ── Workshop + Red flags ───────────────────────────────────
    st.markdown('<hr class="thin-divider">', unsafe_allow_html=True)
    w_col, r_col = st.columns([1, 1])

    with w_col:
        ws = data["workshop_suggestion"]
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Suggested First Workshop</div>
            <div style="font-weight:600;color:#111827;">{ws['format']}</div>
            <div style="font-size:0.82rem;color:#6b7280;margin-bottom:0.75rem;">{ws['duration']}</div>
            {''.join(f'<div class="branch-item" style="margin-bottom:0.3rem;">· {item}</div>' for item in ws['agenda'])}
            <div style="margin-top:0.75rem;font-size:0.85rem;background:#f0fdf4;border-radius:6px;padding:0.5rem 0.75rem;color:#166534;">
                <strong>Output:</strong> {ws['key_output']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with r_col:
        if data.get("red_flags"):
            st.markdown('<div class="section-label">Red Flags</div>', unsafe_allow_html=True)
            for flag in data["red_flags"]:
                st.markdown(f'<div class="flag-item">⚠ {flag}</div>', unsafe_allow_html=True)

    # ── Download ──────────────────────────────────────────────
    st.markdown('<hr class="thin-divider">', unsafe_allow_html=True)
    brief_text = format_brief(data, problem)
    filepath = save_brief(brief_text, problem)

    dl_col, token_col = st.columns([1, 3])
    dl_col.download_button("⬇ Download brief", data=brief_text, file_name=filepath.name, mime="text/markdown")
    token_col.markdown(
        f'<div class="token-info">{response.usage.input_tokens} tokens in · {response.usage.output_tokens} out · '
        f'{datetime.now().strftime("%d %b %Y, %H:%M")}</div>',
        unsafe_allow_html=True
    )
