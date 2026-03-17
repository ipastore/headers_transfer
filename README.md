# headers_transfer

Extract player data from screenshots and append rows to an Excel file using Gemini Flash vision AI.

## What it does

`extract.py` takes a screenshot of a player profile (e.g. from a scouting platform) and uses Gemini 2.5 Flash to extract 30 predefined fields, then appends a new row to a `.xlsx` file.

## Fields extracted (30)

| Field | Field |
|---|---|
| Name | Shirt Name |
| Birth Date | Height |
| Weight | Preferred Foot |
| Nationality | Second Nationality |
| Market Value | Position |
| Second Position | Club |
| Contract Expiry Date | Notes |
| Profile Link | Transfermarkt Link |
| Address | Phone |
| Studies | League |
| On Loan | Club of Origin of Loan |
| Representative | Representative's Contact |
| Rep Contract Expiry | Representative Link |
| Annual Net Salary | Position Profile |
| Document ID | Document Expiry Date |

---

## Two ways to run

| Method | Best for |
|---|---|
| **Python CLI** | macOS / Linux with Python installed |
| **Docker + `run.sh`** | Windows, or any machine without Python |

---

## Option A — Python CLI

### Installation

**1. Clone the repo**

```bash
git clone https://github.com/ipastore/headers_transfer
cd headers_transfer
```

**2. Create and activate a virtual environment**

**conda (recommended if you have conda installed)**

```bash
conda create -n headers_transfer python=3.12
conda activate headers_transfer
```

**plain venv (no conda)**

```bash
python3.12 -m venv .venv        # use python3 if python3.12 is not available
source .venv/bin/activate
which python                    # confirm it shows .venv/bin/python
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Set your Gemini API key**

Get a free key (no credit card) at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — create it in a new project.

```bash
echo "GEMINI_API_KEY=your_key_here" > .env
```

### Verify installation

```bash
python test_gemini.py                    # test Gemini connection
python -m unittest tests.test_append -v        # test xlsx read/write
```

### Usage

```bash
# Batch — all images in assets/screens/
python extract.py assets/screens/ assets/ScoutDecisionPlayerImport.xlsx

# Single player
python extract.py assets/screens/ assets/ScoutDecisionPlayerImport.xlsx --file 1.jpg

# Dry run — inspect without writing
python extract.py assets/screens/ assets/ScoutDecisionPlayerImport.xlsx --file 1.jpg --dry-run --verbose

# Reset — clear all rows, keep header
python extract.py assets/screens/ assets/ScoutDecisionPlayerImport.xlsx --reset
```

---

## Option B — Docker + run.sh (Windows / no Python)

No Python installation needed. Docker runs everything inside a container and writes the xlsx directly to your local folder via a volume mount.

### Prerequisites

Install **Docker Desktop**:
- **Windows**: [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop) — enable WSL2 when prompted
- **macOS**: same link, pick Apple Silicon or Intel build

### Windows — set up WSL first

WSL (Windows Subsystem for Linux) lets you run bash scripts on Windows. Docker Desktop requires it and installs it automatically, but you need to activate it first.

**1. Enable WSL2 (run in PowerShell as Administrator):**

```powershell
wsl --install
```

Restart your machine when prompted.

**2. Open the repo from WSL:**

```bash
# In the WSL terminal (Ubuntu)
cd /mnt/c/Users/<YourName>/path/to/headers_transfer
```

Your Windows `C:\` drive is mounted at `/mnt/c/` inside WSL.

**3. From here, all commands are identical to macOS.**

### Setup

```bash
# Clone the repo (or navigate to it if already cloned)
git clone https://github.com/ipastore/headers_transfer
cd headers_transfer

# Set your API key
echo "GEMINI_API_KEY=your_key_here" > .env

# Make the script executable (macOS/WSL)
chmod +x scripts/run.sh
```

### Usage

```bash
# Batch — all images in assets/screens/
./scripts/run.sh

# Single player
./scripts/run.sh --file 1.jpg

# Dry run — inspect without writing
./scripts/run.sh --file 1.jpg --dry-run --verbose

# Reset — clear all rows, keep header
./scripts/run.sh --reset

# Force fallback model (if primary quota is exhausted)
./scripts/run.sh --fallback
```

The script auto-builds the Docker image on first run. The xlsx is written to your local `assets/` folder — not inside Docker.

### What run.sh does

```
1. Checks if the Docker image exists → builds it if not
2. Mounts your local assets/ folder into the container
3. Passes your .env API key to the container
4. Runs extract.py inside Docker
5. Removes the container after each run (--rm)
```

---

## Flags

| Flag | Description |
|---|---|
| `--file <name>` | Process a single image inside the screens directory |
| `--dry-run` | Print extracted fields without writing to xlsx |
| `--verbose` | Show the full Gemini prompt and raw model response |
| `--reset` | Delete all data rows below the header, then exit |
| `--fallback` | Skip primary model, use fallback directly |

---

## Safety

- Writes are atomic: data is written to a temp file first, then replaces the original.
- If the xlsx is open in Excel when you run the script, data is saved to a timestamped fallback file (e.g. `ScoutDecisionPlayerImport_20260317_143022.xlsx`) so nothing is lost.

---

## Project structure

```
headers_transfer/
├── assets/
│   ├── screens/              # Input screenshots
│   └── ScoutDecisionPlayerImport.xlsx
├── docs/
│   ├── MVP_PLAN.md
│   └── API_PLAN.md
├── api.py                    # FastAPI wrapper (for n8n / server use)
├── extract.py                # CLI entrypoint
├── gemini_client.py          # Gemini 2.5 Flash vision wrapper
├── xlsx_manager.py           # xlsx read/write helper
├── Dockerfile
├── run.sh                    # Docker runner script
├── tests/
│   ├── test_gemini.py        # API connection test
│   └── test_append.py        # xlsx unit tests
├── scripts/
│   └── run.sh                # Docker runner script
├── requirements.txt
├── .env                      # Your API key (gitignored)
├── .env.example              # Key template
└── .gitignore
```

## Requirements

- A free Gemini API key from [aistudio.google.com](https://aistudio.google.com)
- **CLI**: Python 3.9+, conda or venv
- **Docker**: Docker Desktop (Windows or macOS)
