# Consulting Problem Structurer — Project Context

**Live:** https://clueful-consultant.streamlit.app/
**Repo:** https://github.com/CluefullConsultant/consulting-problem-structurer

## What it does

Paste a raw client problem statement. Returns a MECE issue tree, 3 leading hypotheses, 3 diagnostic questions, and a first-workshop suggestion.

## Key files

- `app.py` — Streamlit UI
- `structurer.py` — SYSTEM_PROMPT and CLI logic

## Key technical patterns

**Anthropic SDK streaming:**
```python
with client.messages.stream(
    model="claude-sonnet-4-5",
    max_tokens=2048,
    system=SYSTEM_PROMPT,
    messages=[{"role": "user", "content": prompt}]
) as stream:
    for text in stream.text_stream:
        raw += text
        stream_box.markdown(...)
    final_message = stream.get_final_message()
stream_box.empty()
```
Use `final_message.usage.input_tokens` / `final_message.usage.output_tokens` for token display.

**Robust JSON parsing:**
```python
import re
match = re.search(r'\{.*\}', raw, re.DOTALL)
if match:
    raw = match.group()
data = json.loads(raw)
```
Claude occasionally wraps JSON output in markdown fences or adds preamble. The regex handles this.

**Streamlit example buttons (on_click pattern):**
```python
def load_example(text):
    st.session_state.problem_input = text
    st.session_state.auto_run = True

col.button(label, on_click=load_example, args=(text,))
```
Never use `st.rerun()` inside button handlers. Never combine `value=` and `key=` on the same widget. The `on_click` callback fires before rerender, guaranteeing session state is set when the widget renders.

**API key on Streamlit Cloud:**
```python
api_key = st.secrets.get("ANTHROPIC_API_KEY", None) if hasattr(st, "secrets") else None
client = anthropic.Anthropic(api_key=api_key)
```
Key is stored in Streamlit Cloud secrets at share.streamlit.io > App settings > Secrets. Identical pattern used in `clueless-consultant`.

## Shared context

This is one of four coding-showcase tools under `~/Projects` (alongside `clueless-consultant`, `excel-ppt`, and `landing-page`). For style rules, who Antony is, and the Haik Spitzer meeting context these tools were built for, see `../CLAUDE.md`.
