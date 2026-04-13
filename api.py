from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from database import criar_tabelas
from models import PessoaCreate, PessoaUpdate, EntradaRequest, SaidaRequest
from services import *

app = FastAPI(title="Sistema Portaria API")

# CORS (ESSENCIAL)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    criar_tabelas()


@app.get("/health")
def health():
    return {"status": "ok"}


# ------------------ PESSOAS ------------------

@app.get("/pessoas")
def listar_pessoas():
    return listar_pessoas_service()


@app.get("/pessoas/dentro")
def dentro():
    return listar_dentro_service()


@app.post("/pessoas")
def criar_pessoa(payload: PessoaCreate):
    ok, msg = inserir_pessoa_service(
        payload.nome,
        payload.documento,
        payload.tipo,
        payload.quadra,
        payload.lote
    )
    if not ok:
        raise HTTPException(400, msg)
    return {"message": msg}


@app.delete("/pessoas/{documento}")
def deletar(documento: str):
    ok, msg = remover_pessoa_service(documento)
    if not ok:
        raise HTTPException(400, msg)
    return {"message": msg}


# ------------------ MOVIMENTAÇÃO ------------------

@app.post("/entrada")
def entrada(payload: EntradaRequest):
    ok, msg = registrar_entrada_service(
        payload.documento,
        payload.quadra,
        payload.lote,
        payload.porteiro
    )
    if not ok:
        raise HTTPException(400, msg)
    return {"message": msg}


@app.post("/saida")
def saida(payload: SaidaRequest):
    ok, msg = registrar_saida_service(
        payload.documento,
        payload.porteiro
    )
    if not ok:
        raise HTTPException(400, msg)
    return {"message": msg}