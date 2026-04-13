import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).with_name("portaria.db")


def conectar() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def executar(sql: str, params: tuple = ()):
    with conectar() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur


def criar_tabelas() -> None:
    executar("""
        CREATE TABLE IF NOT EXISTS pessoas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            documento TEXT NOT NULL UNIQUE,
            tipo TEXT NOT NULL,
            quadra_lote TEXT,
            status TEXT NOT NULL DEFAULT 'FORA'
        );
    """)

    executar("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            documento TEXT NOT NULL,
            acao TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            destino TEXT,
            porteiro TEXT
        );
    """)

    executar("""
        CREATE TABLE IF NOT EXISTS autorizacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            documento TEXT NOT NULL,
            destino TEXT NOT NULL,
            ativo INTEGER NOT NULL DEFAULT 1,
            autorizado_por TEXT,
            data_hora TEXT NOT NULL
        );
    """)

    executar("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            perfil TEXT NOT NULL DEFAULT 'porteiro',
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TEXT NOT NULL
        );
    """)

    executar("CREATE INDEX IF NOT EXISTS idx_pessoas_status ON pessoas(status);")
    executar("CREATE INDEX IF NOT EXISTS idx_pessoas_tipo ON pessoas(tipo);")
    executar("CREATE INDEX IF NOT EXISTS idx_hist_doc_data ON historico(documento, data_hora);")
    executar("CREATE INDEX IF NOT EXISTS idx_hist_data ON historico(data_hora);")
    executar("CREATE INDEX IF NOT EXISTS idx_aut_doc_dest_ativo ON autorizacoes(documento, destino, ativo);")
    executar("CREATE INDEX IF NOT EXISTS idx_usuarios_usuario ON usuarios(usuario);")


# ------------------ PESSOAS ------------------

def inserir_pessoa(nome: str, documento: str, tipo: str, quadra_lote: str | None) -> None:
    executar("""
        INSERT INTO pessoas (nome, documento, tipo, quadra_lote)
        VALUES (?, ?, ?, ?)
    """, (nome, documento, tipo, quadra_lote))


def listar_pessoas(limit: int | None = None, offset: int | None = None):
    sql = """
        SELECT id, nome, documento, tipo, quadra_lote, status
        FROM pessoas
        ORDER BY id DESC
    """
    params: list = []
    if limit is not None:
        sql += " LIMIT ?"
        params.append(int(limit))
        if offset is not None:
            sql += " OFFSET ?"
            params.append(int(offset))

    cur = executar(sql, tuple(params))
    return cur.fetchall()


def listar_pessoas_por_tipo(tipo: str, limit: int | None = None, offset: int | None = None):
    sql = """
        SELECT id, nome, documento, tipo, quadra_lote, status
        FROM pessoas
        WHERE tipo = ?
        ORDER BY id DESC
    """
    params: list = [tipo]
    if limit is not None:
        sql += " LIMIT ?"
        params.append(int(limit))
        if offset is not None:
            sql += " OFFSET ?"
            params.append(int(offset))

    cur = executar(sql, tuple(params))
    return cur.fetchall()


def listar_dentro():
    cur = executar("""
        SELECT id, nome, documento, tipo, quadra_lote, status
        FROM pessoas
        WHERE status = 'DENTRO'
        ORDER BY id DESC
    """)
    return cur.fetchall()


def buscar_pessoa(documento: str):
    cur = executar("""
        SELECT id, nome, documento, tipo, quadra_lote, status
        FROM pessoas
        WHERE documento = ?
        LIMIT 1
    """, (documento,))
    return cur.fetchone()


def editar_pessoa(documento: str, nome: str, tipo: str, quadra_lote: str | None) -> None:
    executar("""
        UPDATE pessoas
        SET nome = ?, tipo = ?, quadra_lote = ?
        WHERE documento = ?
    """, (nome, tipo, quadra_lote, documento))


def remover_pessoa(documento: str) -> None:
    executar("DELETE FROM pessoas WHERE documento = ?", (documento,))


def atualizar_status(documento: str, status: str) -> None:
    executar("""
        UPDATE pessoas
        SET status = ?
        WHERE documento = ?
    """, (status, documento))


# ------------------ HISTÓRICO / RELATÓRIO ------------------

def registrar_historico(documento: str, acao: str, destino: str | None, porteiro: str) -> None:
    data_hora = datetime.now().isoformat(timespec="seconds")
    executar("""
        INSERT INTO historico (documento, acao, data_hora, destino, porteiro)
        VALUES (?, ?, ?, ?, ?)
    """, (documento, acao, data_hora, destino, porteiro))


def relatorio_por_data(data_iso: str):
    # data_iso no formato "YYYY-MM-DD"
    cur = executar("""
        SELECT h.data_hora, h.acao, p.nome, p.documento, p.tipo, h.porteiro, h.destino
        FROM historico h
        JOIN pessoas p ON p.documento = h.documento
        WHERE h.data_hora LIKE ?
        ORDER BY h.data_hora
    """, (f"{data_iso}%",))
    return cur.fetchall()


# ------------------ AUTORIZAÇÕES (opcional, você já tinha) ------------------

def autorizar_documento(documento: str, destino: str, autorizado_por: str) -> None:
    data_hora = datetime.now().isoformat(timespec="seconds")
    executar("""
        INSERT INTO autorizacoes (documento, destino, ativo, autorizado_por, data_hora)
        VALUES (?, ?, 1, ?, ?)
    """, (documento, destino, autorizado_por, data_hora))


def revogar_documento(documento: str, destino: str) -> None:
    executar("""
        UPDATE autorizacoes
        SET ativo = 0
        WHERE documento = ? AND destino = ? AND ativo = 1
    """, (documento, destino))


def esta_autorizado(documento: str, destino: str) -> bool:
    cur = executar("""
        SELECT 1
        FROM autorizacoes
        WHERE documento = ? AND destino = ? AND ativo = 1
        ORDER BY id DESC
        LIMIT 1
    """, (documento, destino))
    return cur.fetchone() is not None


# ------------------ USUÁRIOS (login CLI, você já tinha) ------------------

def contar_usuarios() -> int:
    cur = executar("SELECT COUNT(*) AS total FROM usuarios")
    row = cur.fetchone()
    return int(row["total"]) if row else 0


def inserir_usuario(usuario: str, senha_hash: str, salt: str, perfil: str = "porteiro") -> None:
    criado_em = datetime.now().isoformat(timespec="seconds")
    executar("""
        INSERT INTO usuarios (usuario, senha_hash, salt, perfil, ativo, criado_em)
        VALUES (?, ?, ?, ?, 1, ?)
    """, (usuario, senha_hash, salt, perfil, criado_em))


def buscar_usuario(usuario: str):
    cur = executar("""
        SELECT usuario, senha_hash, salt, perfil, ativo
        FROM usuarios
        WHERE usuario = ?
        LIMIT 1
    """, (usuario,))
    return cur.fetchone()