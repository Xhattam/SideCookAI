import os

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from scipy._lib.pyprima.common import message
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
import pandas as pd
import numpy as np
import logging
import faiss
from sentence_transformers import SentenceTransformer
import json
from dotenv import load_dotenv

logger = logging.getLogger("Main")
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
INDEX_DIR = BASE_DIR / "index"
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
RECIPES_CSV = DATA_DIR / "recipes.csv"
INDEX_FILE = INDEX_DIR / "recipes.faiss"
META_FILE = INDEX_DIR / "recipes_meta.json"
MODEL_NAME = "all-MiniLM-L6-v2"

app = FastAPI(title="Recipe Finder Mock App")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("HF_TOKEN"))
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

model = SentenceTransformer(MODEL_NAME)
index = None
meta = []

USERS = {"demo": "demo123"}


def ensure_index():
    global index, meta
    if INDEX_FILE.exists() and META_FILE.exists():
        index = faiss.read_index(str(INDEX_FILE))
        meta = json.loads(META_FILE.read_text())
        return

    df = pd.read_csv(filepath_or_buffer=RECIPES_CSV, sep="|")
    docs = (df["title"].fillna("") + ". " + df["contents"].fillna("")).tolist()
    emb = model.encode(docs, normalize_embeddings=True).astype(np.float32)
    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb)
    meta = df.to_dict(orient="records")
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_FILE))
    META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2))


def logged_in(request: Request):
    return request.session.get("user") is not None


@app.on_event("startup")
def startup_event():
    ensure_index()


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    if logged_in(request):
        return RedirectResponse("/search", status_code=302)
    return RedirectResponse("/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request,"login.html", {"request": request, "error": None})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if USERS.get(username) != password:
        return templates.TemplateResponse(request,"login.html", {"request": request, "error": "Invalid username or password."}, status_code=401)
    request.session["user"] = username
    return RedirectResponse("/search", status_code=302)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


@app.get("/search", response_class=HTMLResponse)
def search_page(request: Request):
    if not logged_in(request):
        request.session["flash"] = "Please log in first to search!"
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(request,"search.html", {"request": request, "user": request.session.get("user"), "query": "", "results": None})


@app.post("/search", response_class=HTMLResponse)
def do_search(request: Request, query: str = Form(...)):
    if not logged_in(request):
        return RedirectResponse("/login", status_code=302)
    q = query.strip()
    if not q:
        return templates.TemplateResponse(request, "search.html", {"request": request, "user": request.session.get("user"), "query": query, "results": [], "message": "Enter a search query."})
    q_emb = model.encode([q], normalize_embeddings=True).astype(np.float32)
    scores, ids = index.search(q_emb, k=min(5, index.ntotal))
    results = []
    for score, idx in zip(scores[0], ids[0]):
        row = meta[idx]
        results.append({
            "title": row["title"],
            "contents": row["contents"],
            "score": float(score)
        })
    return templates.TemplateResponse(request,"search.html", {"request": request, "user": request.session.get("user"), "query": query, "results": results, "message": None})
