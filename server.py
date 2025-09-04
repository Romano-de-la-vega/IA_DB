import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore


def get_base_dir() -> Path:
    """Return base directory compatible with PyInstaller bundles."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
app = FastAPI(title="Assistant SQL")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static"), check_dir=False), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ---------------------- Configuration base de données ----------------------
class DBSettings(BaseModel):
    driver: str
    host: str
    port: int
    database: str
    username: str
    password: str


db_settings: Optional[DBSettings] = None
engine: Optional[Engine] = None


def _dsn(cfg: DBSettings) -> str:
    return f"{cfg.driver}://{cfg.username}:{cfg.password}@{cfg.host}:{cfg.port}/{cfg.database}"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/config")
async def save_config(cfg: DBSettings):
    """Save configuration and create engine."""
    global db_settings, engine
    try:
        engine = create_engine(_dsn(cfg))
        # simple test
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        engine = None
        raise HTTPException(status_code=400, detail=str(exc))
    db_settings = cfg
    return {"ok": True}


@app.post("/api/config/test")
async def test_config(cfg: DBSettings):
    try:
        test_engine = create_engine(_dsn(cfg))
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"ok": True}


class Question(BaseModel):
    question: str
    direct: bool = False


@app.post("/api/query")
async def ask_question(payload: Question):
    if engine is None:
        raise HTTPException(status_code=400, detail="Base de données non configurée")

    if payload.direct:
        try:
            with engine.connect() as conn:
                result = conn.execute(text(payload.question))
                rows = [dict(r) for r in result]
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Erreur SQL: {exc}")
        return {"rows": rows}

    if OpenAI is None:
        raise HTTPException(status_code=500, detail="Bibliothèque OpenAI indisponible")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Étape 1 : transformer en SQL
    prompt_sql = (
        "Tu es un assistant qui convertit des questions en requêtes SQL. "
        "Donne uniquement la requête SQL sans explication. Question: "
        f"{payload.question}"
    )
    sql_resp = client.responses.create(
        model="gpt-4o-mini",
        input=[{"role": "user", "content": prompt_sql}],
    )
    sql_query = sql_resp.output_text.strip()

    # Étape 2 : exécuter la requête
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            rows = [dict(r) for r in result]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Erreur SQL: {exc}")

    # Étape 3 : interpréter le résultat
    prompt_interpret = (
        "Question originale: "
        f"{payload.question}\n" "Résultats SQL: "
        f"{rows}\n" "Fournis une réponse concise en français sans données brutes."
    )
    interp_resp = client.responses.create(
        model="gpt-4o-mini",
        input=[{"role": "user", "content": prompt_interpret}],
    )

    return {"answer": interp_resp.output_text, "sql": sql_query}


# --------- Point d'entrée de développement ---------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
