# Lab Tracker

Web-based project tracking for research labs.

## Setup

```bash
# Clone and setup
git clone <repo>
cd lab-tracker
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"

# Run tests
pytest
```

## Development

```bash
# Run the server
uvicorn app.main:app --reload
```

## Status

Currently in development. See implementation progress in commits.
