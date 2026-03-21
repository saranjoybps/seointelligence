# SEO Intelligence Backend

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Endpoints

- `POST /api/analyze/stream`
- `GET /api/analysis/{id}`
- `GET /api/health`
