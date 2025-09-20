> **Status: One-time open-source drop (AS IS).**  
> This project is provided under the MIT License **without active maintenance, support, or warranties**.  
> **Issues and pull requests are not accepted.** Please fork if you need changes.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Status: As-Is](https://img.shields.io/badge/status-as--is-lightgrey)

# Resume Screener — Setup & Usage (Windows & macOS)

This project screens resumes against a rubric using LLMs. It parses your rubric from `data/rubric.txt`, scores shortlisted resumes, and produces ranked results.

**Pipeline at a glance**
1. Parse resumes (`src/parser.py`) and compute stable IDs.
2. Prefilter & shortlist by JD (`src/prefilter.py`).
3. Parse the rubric with an LLM (cached) (`src/rubric_parser.py`).
4. Score candidates with rubric-driven dimensions (`src/scorer.py`).
5. Rank & export (`src/ranker.py`) via `src/cli.py`.

---

## Prerequisites

- **Python** 3.10–3.12
- **OpenAI API key** in env var `OPENAI_API_KEY`
- A rubric at `data/rubric.txt`
- A folder of resumes (PDF/DOCX/TXT supported by your parser)
- A job description text file (e.g., `jd.txt`)

> The scorer owns caching and treats the rubric as the single source of truth. Changing the rubric or `SCHEMA_VER` naturally creates fresh cache entries.

---

## Quick Start — Windows (PowerShell)

1. Open PowerShell in the project root.
2. Create & activate a virtual environment (example uses Python 3.11):
   ```ps1
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```ps1
   pip install -r requirements.txt
   ```
   If you don't have a requirements file, install the minimum:
   ```ps1
   pip install openai pandas tqdm
   ```
4. Set your OpenAI key (choose one):
   - Current shell only:
     ```ps1
     $Env:OPENAI_API_KEY = "sk-..."
     ```
   - Persist for future shells:
     ```ps1
     setx OPENAI_API_KEY "sk-..."
     ```
5. Ensure your rubric exists at `data\rubric.txt`.
6. Prepare inputs:
   - `resumes\` → PDF/DOCX/TXT files
   - `jd.txt` → job description
7. Run the CLI:
   ```ps1
   python -m src.cli --resumes .\resumes --jd .\jd.txt --k 100 --out .\out
   ```
   OR
   ```ps1
   uv run python -m src.cli --resumes ./data/resumes --jd ./data/jd.txt --k 5 --out ./out
   ```
---

## Quick Start — macOS (Terminal)

1. Open Terminal in the project root.
2. Create & activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Without a requirements file, install the minimum:
   ```bash
   pip install openai pandas tqdm
   ```
4. Set your OpenAI key (current shell):
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```
   (Optionally add to `~/.zshrc` or `~/.bashrc` for persistence.)
5. Ensure your rubric exists at `data/rubric.txt`.
6. Prepare inputs:
   - `resumes/` → PDF/DOCX/TXT files
   - `jd.txt` → job description
7. Run the CLI:
   ```bash
   python -m src.cli --resumes ./resumes --jd ./jd.txt --k 100 --out ./out
   ```

---

## Running the CLI

```bash
python -m src.cli --resumes <RESUMES_DIR> --jd <JD_TXT_PATH> --k 100 --out ./out
```
**Args**
- `--resumes`  : Directory containing resumes
- `--jd`       : Path to the job description text file
- `--k`        : Number of top prefiltered resumes to score with the LLM (default 100)
- `--out`      : Output directory (default `./out`)

**Notes**
- The CLI always calls the scorer; caching is handled inside the scorer itself.
- Ensure `data/rubric.txt` exists; it is the authoritative scoring rubric.
- The scorer appends a `DETECTED_CONTACTS` block to stabilize URL/email/phone extraction.

---

## Environment Variables

**Required**
- `OPENAI_API_KEY` — Your OpenAI API key

**Optional (defaults are sensible)**
- `RUBRIC_PATH`        : Path to rubric (default `data/rubric.txt`)
- `OPENAI_MODEL_PARSE` : Model for rubric parsing (default `gpt-4o`)
- `OPENAI_MODEL_SCORE` : Model for scoring (default `gpt-4o`)
- `RUBRIC_CACHE_ROOT`  : Rubric cache dir (default `out/cache/rubric`)
- `SCORE_CACHE_ROOT`   : Scoring cache dir (default `out/cache/llm`)
- `MAX_RESUME_CHARS`   : Truncation limit for resume text (default `5000`)

**Windows (PowerShell)**
```ps1
$Env:OPENAI_API_KEY = "sk-..."
$Env:RUBRIC_PATH = "data\\rubric.txt"
```

**macOS (zsh/bash)**
```bash
export OPENAI_API_KEY="sk-..."
export RUBRIC_PATH="data/rubric.txt"
```

---

## Outputs & Cache Layout

- `out/details.jsonl` — One JSON record per scored resume (extracted fields + per‑dimension scores)  
- `out/results.csv`   — Ranked results (uses `total_score` by default)

**Cache (managed by scorer)**
```
out/
└── cache/
    ├── rubric/
    │   └── <rubric_sha>.json
    └── llm/
        └── <jd_sha>/
            └── <rubric_sha>/
                └── <SCHEMA_VER>/
                    └── <res_sha>.json
```

You can safely rerun the CLI; cached entries are reused automatically.

---

## Tips & Troubleshooting

- **Missing/invalid API key** → set `OPENAI_API_KEY` as shown above.
- **ModuleNotFoundError** → `pip install -r requirements.txt` (or install `openai pandas tqdm`).
- **macOS SSL** (python.org builds) → run `Install Certificates.command` from your Python folder.
- **Empty outputs** → ensure `data/rubric.txt`, a non-empty `resumes/` folder, and a valid `jd.txt`.
- **PDF extraction issues** → the pipeline normalizes contacts, but make sure your PDFs contain text (not images only).
- **Force fresh runs** → delete `out/cache/`.

---

Happy screening!
