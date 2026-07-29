# Daybook X launch post

Attach the four PNGs in filename order. They are 1440×1440, use only the
repository's deterministic fictional dataset, and are intentionally free of
marketing overlays so the product can speak for itself.

## Post copy

```text
I didn’t want another SaaS holding my financial history. So I built Daybook: local-first + open source.

CSV/OFX/QFX → SQLite. Auditable numbers. Useful patterns. Optional read-only LLM advisor.

No account. No telemetry. Your data stays yours.

github.com/hr23232323/daybook
```

## Optional first reply

```text
Early, useful, and MIT.

Built with FastAPI + vanilla JS + SQLite; no frontend build step. Manual import and deterministic discoveries work without an API key. The advisor is model-agnostic and supports local Ollama.

Feedback, issues, and PRs welcome.
```

## Image order and alt text

1. `01-statement.png`

   Daybook Statement page with fictional data. A dark sidebar sits beside a
   $1,774.93 net-position summary, an outflow-category donut chart, and a Sankey
   diagram tracing income into spending categories.

2. `02-discoveries.png`

   Daybook Discoveries page with fictional data. Locally computed findings show
   a 67% needs and 33% discretionary split, seven subscriptions costing $146 per
   month, eating out costing $615 per month, and a shopping-frequency pattern.

3. `03-advisor.png`

   Daybook's read-only Advisor page with fictional data. In Balanced mode it
   answers “Where is my money quietly leaking?” with grounded findings about
   eating out, subscriptions, and small purchases, followed by query and research
   counts.

4. `04-import.png`

   Daybook Import & sync page showing two explicit data paths: fully local
   CSV/OFX/QFX statement import and optional third-party SimpleFIN synchronization.

## Posting notes

- Use the four images in one post, not a thread; X will show them as a two-by-two
  gallery.
- Do not add hashtags. The copy already includes the relevant nouns and the
  images provide the visual hook.
- Paste the alt text above into X's image-description editor before posting.
- If the link preview competes with the four images in the composer, keep the
  images and the plain repository URL.

## Re-rendering

Run from the repository root:

```bash
marketing/social/x-launch/render_images.sh
```

The script requires `ffmpeg` and regenerates the public assets from the
fictional-data captures in `marketing/video/source/`.
