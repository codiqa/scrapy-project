# scrapy-project

## Setup Instructions

### 1) Create a Python virtual environment

```bash
# From the project root
python3 -m venv env
# Activate it
source env/bin/activate
```

### 2) Install required packages

```bash
pip install -r requirements.txt
```

> If `requirements.txt` does not exist yet, see step 4 below.

### 3) Run the scraper

```bash
python scraper.py
```

### 4) Create `requirements.txt` from installed packages

After installing all dependencies (for example with `pip install scrapy requests pandas`), export all currently installed packages in the venv:

```bash
pip freeze > requirements.txt
```

### 5) Add new packages

When you add a new package:

1. Install it in the activated virtualenv, e.g. `pip install beautifulsoup4`
2. Update `requirements.txt`:

```bash
pip freeze > requirements.txt
```

### 6) Tips

- Always activate the venv before running scripts.
- Use `python -m pip` for consistency.
- If your environment uses Python 3.10+ and `python3` points to Python 3, use `python3 -m venv env`.

