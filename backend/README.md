# Backend

The production FastAPI app lives in `backend/app`.

The top-level `app/main.py` file is a small compatibility shim so the local
demo can be started with:

```bash
uvicorn app.main:app --reload
```

