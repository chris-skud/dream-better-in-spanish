# Dream Better In Spanish

Personal web app for learning Spanish through podcasts. Plays podcast audio with a synchronized two-pane view: Spanish transcript on the left, English translation on the right.

## Tooling

**This project uses [uv](https://docs.astral.sh/uv/) for dependency management and Python execution. Always use uv for Python commands.**

Common commands:

- `uv sync` — install dependencies from `pyproject.toml` into `.venv`
- `uv run python -m pipeline.main list [--limit N]` — list episodes from the Dreaming Spanish RSS feed; `*` marks already-processed episodes
- `uv run python -m pipeline.main process-latest [--force]` — transcribe + translate the most recent episode
- `uv run python -m pipeline.main process-episode <episode_id> [--force]` — process a specific episode (ID is shown by `list`)
- `uv run python -m http.server 8000` — serve the frontend (and `data/`) at <http://localhost:8000/web/player.html>. Run from the project root so both `/web/` and `/data/` are reachable.
- `uv run python -c '...'` — run an ad-hoc Python snippet
- `uv add <package>` — add a runtime dependency
- `uv add --dev <package>` — add a dev-only dependency

Do not invoke `python` / `python3` / `pip` directly — they bypass the project venv.

## Layout

- `pipeline/` — Python pipeline: RSS → audio → Whisper transcription → Claude translation → JSON
  - `rss.py` — Buzzsprout RSS parser; generates stable `ds-YYYYMMDD-slug` episode IDs
  - `transcribe.py` — faster-whisper wrapper (medium model, Spanish)
  - `translate.py` — Anthropic SDK batched translation with strict schema validation
  - `process.py` — orchestrator: download → transcribe → translate → write JSON + update index
  - `main.py` — argparse CLI: `list`, `process-latest`, `process-episode`
- `data/episodes/{id}.json` — per-episode transcripts (Spanish + English aligned by segment)
- `data/index.json` — episode list for the frontend picker
- `web/` — static frontend (HTML/CSS/JS, no framework)
  - `player.html` — two-pane bilingual player; loads a transcript JSON and the audio
  - `app.js` — fetches the transcript JSON, renders the segment rows
  - `styles.css` — layout and typography

## Secrets

`ANTHROPIC_API_KEY` is loaded from `.env` via `python-dotenv`. See `.env.example`.
