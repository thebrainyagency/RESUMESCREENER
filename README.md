> **Status: One-time open-source drop (AS IS).**  
> This project is provided under the MIT License **without active maintenance, support, or warranties**.  
> **Issues and pull requests are not accepted.** Please fork if you need changes.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Status: As-Is](https://img.shields.io/badge/status-as--is-lightgrey)

# Resume Screener — Setup & Usage

This project screens resumes against a rubric using LLMs. It provides both a **Streamlit web UI** for easy team use and a **command-line interface** for programmatic access.

**Pipeline at a glance**
1. Parse resumes (`src/parser.py`) from PDF/DOCX/TXT files.
2. Prefilter & shortlist by job description (`src/prefilter.py`).
3. Parse the rubric with an LLM (`src/rubric_parser.py`).
4. Score candidates with rubric-driven dimensions (`src/scorer.py`).
5. Rank & export results (`src/ranker.py`).

---

## Prerequisites

- **Python** 3.12+
- **OpenAI API key** (can be set as env var `OPENAI_API_KEY` or entered in UI)
- **uv package manager** (recommended) or pip
- Resume files (PDF/DOCX/TXT supported)
- Job description text
- Scoring rubric text

## Two Ways to Use

### 🖥️ **Streamlit Web UI** (Recommended for Teams)
Easy-to-use web interface with drag & drop file uploads, progress tracking, and results visualization.

### ⌨️ **Command Line Interface**
Direct CLI access for automation and scripting.

---

## 🖥️ Streamlit Web UI Setup

### Installation
```bash
# Clone or download the repository
# Navigate to project directory

# Install dependencies with uv (recommended)
uv sync

# OR install with pip
pip install -r requirements.txt
```

### Running the Web UI
```bash
# Start the Streamlit app
uv run streamlit run app.py

# OR with pip
streamlit run app.py
```

### Using the Web Interface
1. **Setup**: Enter OpenAI API key and select model (gpt-4o or gpt-4o-mini)
2. **Upload**: Drag & drop resumes, paste job description and rubric
3. **Configure**: Set percentage of resumes to score (25% recommended)
4. **Process**: Click "Start Screening" and watch real-time progress
5. **Results**: View rankings, individual scores, and download CSV

---

## ⌨️ Command Line Interface

### Basic Usage
```bash
# Using uv (recommended)
uv run python -m src.cli --resumes ./resumes --jd ./jd.txt --k 50 --out ./out

# Using pip
python -m src.cli --resumes ./resumes --jd ./jd.txt --k 50 --out ./out
```

### Arguments
- `--resumes`: Directory containing resume files
- `--jd`: Path to job description text file
- `--k`: Number of top resumes to score (default: 100)
- `--out`: Output directory (default: ./out)

### Environment Setup for CLI
```bash
# Set OpenAI API key
export OPENAI_API_KEY="sk-..."

# Optional: Override model (default: gpt-4o)
export OPENAI_MODEL_PARSE="gpt-4o"
export OPENAI_MODEL_SCORE="gpt-4o"
```
---

## File Organization

### Sample Files (Included)
- `data/jd_sample.txt` - Example job description
- `data/rubric_sample.txt` - Example scoring rubric
- `data/resumes/` - Sample resume files

### Working Files (Create These)
- `resumes/` - Your actual resume files
- `jd.txt` - Your job description
- `rubric.txt` - Your scoring rubric

> **Note**: Working files are in `.gitignore` to keep your actual screening data private.

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
