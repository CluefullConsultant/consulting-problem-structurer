"""
Consulting Problem Structurer
------------------------------
Takes a vague client problem statement (the kind a CTO or founder gives you
in the first 5 minutes of a call) and produces a structured diagnostic brief:
problem classification, hypotheses, MECE issue tree, diagnostic questions,
and a suggested first workshop format.

Built with Claude. Inspired by Tekkr's approach to tech consulting.
"""

import anthropic
import json
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# The system prompt is the brain of the tool.
# It defines how Claude reasons about the problem.
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior consultant at a tech-focused consulting firm (think Tekkr, McKinsey Digital, BCG Platinion). You work primarily with CTOs, CPOs, and founders at scaling startups (Series A through C).

Your job: when a client gives you a vague, emotional, or incomplete problem statement, you structure it into a precise diagnostic brief that a junior consultant can use to prepare for and run a first client meeting.

Your thinking style:
- Lead with a hypothesis, not an open question
- MECE: every issue tree is Mutually Exclusive, Collectively Exhaustive
- Be decisive. No hedging, no "it depends" without a follow-on
- Executive-ready: every sentence could go on a steering committee slide
- Startup-aware: speed and pragmatism matter; perfect is the enemy of done

STRICT OUTPUT RULES:
- diagnostic_questions: EXACTLY 3 items. Not 4, not 6. Exactly 3.
- workshop agenda: EXACTLY 4 bullet points.
- initial_hypotheses: EXACTLY 3 items.
- Return ONLY valid JSON. No preamble, no explanation, no markdown fences.
{
  "problem_classification": {
    "primary_type": "one of: Delivery/Execution | Org/People | Strategy/Product | Technical Architecture",
    "confidence": "High | Medium | Low",
    "reasoning": "one sentence max"
  },
  "initial_hypotheses": [
    {"hypothesis": "...", "evidence_in_statement": "..."},
    {"hypothesis": "...", "evidence_in_statement": "..."},
    {"hypothesis": "...", "evidence_in_statement": "..."}
  ],
  "issue_tree": {
    "root_problem": "...",
    "branches": [
      {"area": "...", "sub_issues": ["...", "...", "..."]},
      {"area": "...", "sub_issues": ["...", "...", "..."]},
      {"area": "...", "sub_issues": ["...", "...", "..."]}
    ]
  },
  "diagnostic_questions": [
    {"question": "...", "what_it_reveals": "..."},
    {"question": "...", "what_it_reveals": "..."},
    {"question": "...", "what_it_reveals": "..."}
  ],
  "workshop_suggestion": {
    "format": "...",
    "duration": "...",
    "agenda": ["...", "...", "...", "..."],
    "key_output": "..."
  },
  "red_flags": ["...", "..."]
}"""


# ─────────────────────────────────────────────────────────────
# Formatting: turn the JSON into something you'd show a client
# ─────────────────────────────────────────────────────────────

def format_brief(data: dict, problem_statement: str) -> str:
    lines = []

    lines.append("=" * 64)
    lines.append("  CONSULTING DIAGNOSTIC BRIEF")
    lines.append(f"  {datetime.now().strftime('%d %B %Y, %H:%M')}")
    lines.append("=" * 64)

    lines.append("\nCLIENT PROBLEM STATEMENT")
    lines.append(f'  "{problem_statement}"')

    # Classification
    pc = data["problem_classification"]
    lines.append(f"\nPROBLEM CLASSIFICATION")
    lines.append(f"  {pc['primary_type']}  [{pc['confidence']} confidence]")
    lines.append(f"  {pc['reasoning']}")

    # Hypotheses
    lines.append(f"\nLEADING HYPOTHESES")
    for i, h in enumerate(data["initial_hypotheses"], 1):
        lines.append(f"\n  {i}. {h['hypothesis']}")
        lines.append(f"     Evidence in statement: {h['evidence_in_statement']}")

    # Issue tree
    it = data["issue_tree"]
    lines.append(f"\nISSUE TREE")
    lines.append(f"  Root: {it['root_problem']}")
    for branch in it["branches"]:
        lines.append(f"\n  +-- {branch['area']}")
        for sub in branch["sub_issues"]:
            lines.append(f"  |     - {sub}")

    # Diagnostic questions
    lines.append(f"\nDIAGNOSTIC QUESTIONS  (first client meeting)")
    for i, q in enumerate(data["diagnostic_questions"], 1):
        lines.append(f"\n  Q{i}: {q['question']}")
        lines.append(f"       Reveals: {q['what_it_reveals']}")

    # Workshop
    ws = data["workshop_suggestion"]
    lines.append(f"\nSUGGESTED FIRST WORKSHOP")
    lines.append(f"  Format: {ws['format']}   Duration: {ws['duration']}")
    lines.append(f"  Agenda:")
    for item in ws["agenda"]:
        lines.append(f"    - {item}")
    lines.append(f"  Output: {ws['key_output']}")

    # Red flags
    if data.get("red_flags"):
        lines.append(f"\nRED FLAGS")
        for flag in data["red_flags"]:
            lines.append(f"  ! {flag}")

    lines.append("\n" + "=" * 64)
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Save: every brief gets its own timestamped markdown file
# ─────────────────────────────────────────────────────────────

def save_brief(content: str, problem_statement: str) -> Path:
    output_dir = Path(__file__).parent / "briefs"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = problem_statement[:40].lower().replace(" ", "_")
    slug = "".join(c for c in slug if c.isalnum() or c == "_")
    filepath = output_dir / f"{timestamp}_{slug}.md"
    filepath.write_text(content, encoding="utf-8")
    return filepath


# ─────────────────────────────────────────────────────────────
# Core: call Claude, parse, format, save
# ─────────────────────────────────────────────────────────────

def analyze(problem_statement: str) -> None:
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment

    print("\n  Analyzing...\n")

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Client problem statement:\n\n{problem_statement}"
            }
        ]
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if Claude wraps the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)
    brief = format_brief(data, problem_statement)

    print(brief)

    filepath = save_brief(brief, problem_statement)
    print(f"\n  Saved: {filepath}")
    print(f"  Tokens: {response.usage.input_tokens} in / {response.usage.output_tokens} out\n")


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 64)
    print("  CONSULTING PROBLEM STRUCTURER")
    print("  Built with Claude  |  Tekkr-style tech consulting")
    print("=" * 64)
    print("\nPaste the client's problem statement below.")
    print("This is what a CTO or founder says in the first call.")
    print("Press Enter twice when done.\n")

    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)

    problem = "\n".join(lines).strip()

    if not problem:
        print("Nothing entered. Exiting.")
        return

    analyze(problem)


if __name__ == "__main__":
    main()
