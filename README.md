# apply-jobs-mcp

MCP server + scheduled worker that discovers, filters, and prepares internship
applications from an allowlisted set of sources, using `cv.tex` as the single
source of truth for your profile. Nothing is ever submitted without an
explicit confirmation.

## Quickstart

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev,browser]"     # browser extra is optional
.venv/bin/python -m pytest -q                 # 39 tests
```

### Run the MCP server

```bash
.venv/bin/python -m apply_jobs_mcp.server
```

Or register it in opencode (`opencode.json`, already in this repo - shows up
as tools prefixed `apply-jobs-mcp_`):

```json
{
  "mcp": {
    "apply-jobs-mcp": {
      "type": "local",
      "command": [".venv/bin/python", "-m", "apply_jobs_mcp.server"],
      "environment": { "AJM_CONFIG": "config.example.toml" }
    }
  }
}
```

### Scan for jobs (public, no login)

```bash
.venv/bin/python -m apply_jobs_mcp.worker --source amazon --keywords intern --print
.venv/bin/python -m apply_jobs_mcp.worker --source internshala --keywords software
```

Job data lands in `data/applications.sqlite3`; reports:

```bash
.venv/bin/python -c "from apply_jobs_mcp import reports; reports.export_report(reports.Store('data/applications.sqlite3'), 'output/reports')"
```

or via the MCP tool `export_report`.

## How it works

```text
public scan / add_job_url
      /  |  \
  sources.py (allowlist) -> policy.py (scam+comp+fit) -> storage.py
                                  |                            |
                            compensation.py              reports.py
```

- `sources.py` - only approved domains can ever be scanned or browsed.
- `policy.py` - eligibility, scam gates, stipend-first score.
- `compensation.py` - normalizes `Rs 25k/mo`, `3 LPA`, `$2,000/mo` -> INR/month.
- `profile.py` - parses `cv.tex` into structured data; never writes the source.
- `storage.py` - SQLite (WAL). Jobs, applications, events.
- `reports.py` - Markdown + JSON exports.

## Campaign (changeable without code)

See `campaigns/summer-2027.toml` (stipend thresholds, visa rules, date window,
roles, daily cap, scan interval). Global settings: `config.example.toml`
(copy to `config.toml` to override).

## Safety model

- Submit flows require explicit confirmation and are not wired yet by design.
- Browsing outside approved domains / shorteners / unknown hosts is blocked.
- Credentials are never stored; logins are manual in a dedicated profile.
- Job descriptions are treated as data, never as instructions.

## Application lifecycle (MCP tools)

```text
scan_source / add_job_url      discover + grade (policy.py)
prepare_application(job_id)    package dir under output/applications/:
                                 resume.tex (tailored) + cover-letter.md
                                 + job.json + form-answers.json
review_application(app_id)     inspect package before touching a browser
open_application(app_id)       visible, isolated browser (manual login allowed)
fill_application(app_id)       fills only fields it recognises; reports the rest
confirm_submission(app_id,     submits ONLY with the exact token CONFIRM-<id>;
  token="CONFIRM-1")           records URL + confirmation, status 'submitted'
```

No step is automatic in series: review -> open -> fill -> confirm are four
separate decisions you approve in OpenCode.

## Scheduled scans (systemd user timer)

```bash
bash deploy/install.sh
# --> runs .venv/bin/python -m apply_jobs_mcp.worker --source all
#     every 3 days at 07:00 IST (day 1/4/7/... of each month)
```

Manual run anytime: `.venv/bin/python -m apply_jobs_mcp.worker --source internshala --keywords "software developer" --print`

## LLM (optional)

Set `llm.enabled = true` in `config.toml` to let Ollama
(`gemma4:31b-cloud`, local) write cover letters; the deterministic template
fallback is used otherwise. The model only sees the parsed profile + job text
and is instructed to never invent facts.

## Known notes

- PDF compilation needs TeX: `prepare_application` compiles `resume.pdf` via
  `latexmk` (installed); the PDF is auto-attached by `fill_application`.
- Public scanners (no login): Internshala, Amazon, Greenhouse boards
  (9 live: stripe, vercel, reddit, cloudflare, mozilla, datadog, duolingo,
  discord, netlify), Ashby boards (openai, linear, cursor, perplexity, n8n).
- Browse-mode sources (login/JS, use `open_application`): LinkedIn, Glassdoor,
  Google/Meta/NVIDIA/JPMorgan careers, Naukri, Indeed, Wellfound.
- Policy is conservative: scam-adjacent wording must look like a payment
  demand on you, never a mention (Amazon payment-boilerplate safe); "intern"
  match is word-bounded so "internal tooling" doesn't sneak in.
- Workers default `--source all` = every source with a public scanner.

