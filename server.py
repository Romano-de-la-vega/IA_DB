import os
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import create_engine, text

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - library optional in tests
    OpenAI = None  # type: ignore

app = FastAPI(title="Assistant SQL")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class DBParams(BaseModel):
    driver: str
    host: str
    port: int
    database: str
    username: str
    password: str
    options: Optional[str] = None
    api_key: Optional[str] = None


class QueryRequest(DBParams):
    question: str


def build_url(p: DBParams) -> str:
    url = f"{p.driver}://{p.username}:{p.password}@{p.host}:{p.port}/{p.database}"
    if p.options:
        url += f"?{p.options}"
    return url


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/test-connection")
async def test_connection(params: DBParams):
    engine = create_engine(build_url(params))
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception as e:  # pragma: no cover - depends on DB
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/query")
async def query(data: QueryRequest):
    api_key = data.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="Missing OpenAI API key")
    if OpenAI is None:  # pragma: no cover - library optional
        raise HTTPException(status_code=500, detail="openai library not installed")

    client = OpenAI(api_key=api_key)

    sql_prompt = (
        "Tu es un assistant qui convertit une question en requête SQL. "
        "Ne renvoie que la requête SQL finale sans commentaire.\n"  # FR translation to instruct
        f"Question: {data.question}"
    )
    sql_resp = client.responses.create(model="gpt-4o-mini", input=sql_prompt)
    sql = sql_resp.output_text.strip()

    engine = create_engine(build_url(data))
    rows: List[Dict[str, Any]] = []
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = [dict(r) for r in result]
    except Exception as e:  # pragma: no cover - depends on DB
        raise HTTPException(status_code=400, detail=f"SQL error: {e}")

    interpret_prompt = (
        f"Question: {data.question}\n"
        f"SQL: {sql}\n"
        f"Résultats: {rows}\n"
        "Fournis une réponse concise en français pour l'utilisateur."
    )
    ans_resp = client.responses.create(model="gpt-4o-mini", input=interpret_prompt)
    answer = ans_resp.output_text.strip()

    return {"sql": sql, "answer": answer}


if __name__ == "__main__":  # pragma: no cover - manual run
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
