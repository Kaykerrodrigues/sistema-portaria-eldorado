from __future__ import annotations

import os
import hashlib
import binascii

from database import (
    inserir_pessoa,
    listar_pessoas,
    listar_pessoas_por_tipo,
    listar_dentro,
    buscar_pessoa,
    editar_pessoa,
    remover_pessoa,
    atualizar_status,
    registrar_historico,
    relatorio_por_data,
    # opcionais (já existiam)
    esta_autorizado,
    autorizar_documento,
    revogar_documento,
    contar_usuarios,
    inserir_usuario,
    buscar_usuario,
)

TIPOS_VALIDOS = {"morador", "visitante", "prestador", "entregador"}


def montar_destino(quadra: str | None, lote: str | None) -> str | None:
    if quadra and lote:
        return f"{quadra.strip().upper()}|{lote.strip().upper()}"
    return None


# ------------------ PESSOAS ------------------

def inserir_pessoa_service(
    nome: str,
    documento: str,
    tipo: str,
    quadra: str | None,
    lote: str | None
) -> tuple[bool, str]:
    nome = (nome or "").strip()
    documento = (documento or "").strip()
    tipo = (tipo or "").strip().lower()

    if not nome or not documento:
        return False, "Nome e documento são obrigatórios."

    if tipo not in TIPOS_VALIDOS:
        return False, "Tipo inválido. Use: morador, visitante, prestador, entregador."

    destino = montar_destino(quadra, lote)

    if tipo == "morador" and not destino:
        return False, "Morador precisa de quadra e lote."

    if buscar_pessoa(documento):
        return False, "Já existe uma pessoa com esse documento."

    inserir_pessoa(nome, documento, tipo, destino)
    return True, "Pessoa cadastrada com sucesso."


def listar_pessoas_service(limit: int | None = None, offset: int | None = None):
    rows = listar_pessoas(limit=limit, offset=offset)
    return [dict(r) for r in rows]


def listar_por_tipo_service(tipo: str, limit: int | None = None, offset: int | None = None):
    tipo = (tipo or "").strip().lower()
    if tipo not in TIPOS_VALIDOS:
        return False, "Tipo inválido.", []

    rows = listar_pessoas_por_tipo(tipo, limit=limit, offset=offset)
    return True, "OK", [dict(r) for r in rows]


def listar_dentro_service():
    rows = listar_dentro()
    return [dict(r) for r in rows]


def buscar_pessoa_service(documento: str):
    documento = (documento or "").strip()
    row = buscar_pessoa(documento)
    return dict(row) if row else None


def editar_pessoa_service(
    documento: str,
    nome: str,
    tipo: str,
    quadra_lote: str | None
) -> tuple[bool, str]:
    documento = (documento or "").strip()
    nome = (nome or "").strip()
    tipo = (tipo or "").strip().lower()

    if not documento:
        return False, "Documento é obrigatório."

    p = buscar_pessoa(documento)
    if not p:
        return False, "Pessoa não encontrada."

    if tipo and tipo not in TIPOS_VALIDOS:
        return False, "Tipo inválido."

    # se vier vazio "", remove
    if quadra_lote is not None:
        quadra_lote = quadra_lote.strip()
        if quadra_lote == "":
            quadra_lote = None

    # aplica defaults se vier vazio
    nome_final = nome if nome else p["nome"]
    tipo_final = tipo if tipo else p["tipo"]
    quadra_lote_final = quadra_lote if quadra_lote is not None else p["quadra_lote"]

    editar_pessoa(documento, nome_final, tipo_final, quadra_lote_final)
    return True, "Pessoa atualizada com sucesso."


def remover_pessoa_service(documento: str) -> tuple[bool, str]:
    documento = (documento or "").strip()
    if not documento:
        return False, "Documento inválido."

    p = buscar_pessoa(documento)
    if not p:
        return False, "Pessoa não encontrada."

    if p["status"] == "DENTRO":
        return False, "Não pode remover: a pessoa está DENTRO. Registre a SAÍDA primeiro."

    remover_pessoa(documento)
    return True, "Pessoa removida com sucesso."


# ------------------ ENTRADA / SAÍDA ------------------

def registrar_entrada_service(
    documento: str,
    quadra: str | None,
    lote: str | None,
    porteiro: str
) -> tuple[bool, str]:
    documento = (documento or "").strip()
    porteiro = (porteiro or "").strip()

    if not documento:
        return False, "Documento inválido."
    if not porteiro:
        return False, "Porteiro inválido."

    pessoa = buscar_pessoa(documento)
    if not pessoa:
        return False, "Pessoa não encontrada."

    if pessoa["status"] == "DENTRO":
        return False, "Essa pessoa já está DENTRO."

    destino = montar_destino(quadra, lote)

    # Regra que você já tinha: não morador precisa estar autorizado se informar destino
    if destino and pessoa["tipo"] != "morador":
        if not esta_autorizado(documento, destino):
            return False, "Documento NÃO autorizado para esse destino."

    atualizar_status(documento, "DENTRO")
    registrar_historico(documento, "entrada", destino, porteiro)
    return True, "Entrada registrada."


def registrar_saida_service(documento: str, porteiro: str) -> tuple[bool, str]:
    documento = (documento or "").strip()
    porteiro = (porteiro or "").strip()

    if not documento:
        return False, "Documento inválido."
    if not porteiro:
        return False, "Porteiro inválido."

    pessoa = buscar_pessoa(documento)
    if not pessoa:
        return False, "Pessoa não encontrada."

    if pessoa["status"] != "DENTRO":
        return False, "Essa pessoa já está FORA."

    atualizar_status(documento, "FORA")
    registrar_historico(documento, "saida", None, porteiro)
    return True, "Saída registrada."


# ------------------ HISTÓRICO / RELATÓRIO ------------------

def relatorio_por_dia_service(data_iso: str):
    data_iso = (data_iso or "").strip()
    if not data_iso:
        return False, "Data é obrigatória no formato AAAA-MM-DD.", []

    rows = relatorio_por_data(data_iso)
    return True, "OK", [dict(r) for r in rows]


# ------------------ USUÁRIOS (CLI) ------------------

def _hash_senha(senha: str, salt_bytes: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt_bytes, 120_000)
    return binascii.hexlify(dk).decode("ascii")


def criar_porteiro_service(usuario: str, senha: str, perfil: str = "porteiro") -> tuple[bool, str]:
    usuario = (usuario or "").strip()
    senha = (senha or "").strip()

    if not usuario or not senha:
        return False, "Usuário e senha são obrigatórios."

    if buscar_usuario(usuario):
        return False, "Esse usuário já existe."

    salt = os.urandom(16)
    senha_hash = _hash_senha(senha, salt)

    inserir_usuario(
        usuario=usuario,
        senha_hash=senha_hash,
        salt=binascii.hexlify(salt).decode("ascii"),
        perfil=perfil,
    )
    return True, "✅ Porteiro criado com sucesso."


def autenticar_service() -> tuple[bool, str, str | None]:
    usuario = input("Usuário: ").strip()
    senha = input("Senha: ").strip()

    row = buscar_usuario(usuario)
    if not row:
        return False, "❌ Usuário ou senha inválidos.", None

    if int(row["ativo"]) != 1:
        return False, "❌ Usuário desativado.", None

    salt = binascii.unhexlify(row["salt"])
    senha_hash = _hash_senha(senha, salt)

    if senha_hash != row["senha_hash"]:
        return False, "❌ Usuário ou senha inválidos.", None

    return True, f"✅ Bem-vindo, {usuario}", usuario


def garantir_primeiro_porteiro() -> None:
    if contar_usuarios() > 0:
        return

    print("\n⚠️ Nenhum porteiro cadastrado ainda.")
    print("Vamos criar o PRIMEIRO PORTEIRO agora.\n")

    while True:
        usuario = input("Criar usuário: ").strip()
        senha = input("Criar senha: ").strip()
        confirma = input("Confirmar senha: ").strip()

        if senha != confirma:
            print("❌ As senhas não conferem.\n")
            continue

        ok, msg = criar_porteiro_service(usuario, senha, perfil="porteiro")
        print(msg)
        if ok:
            break


# ------------------ AUTORIZAÇÕES (opcional) ------------------

def autorizar_service(documento: str, destino: str, porteiro: str) -> tuple[bool, str]:
    documento = (documento or "").strip()
    destino = (destino or "").strip().upper()
    porteiro = (porteiro or "").strip()

    if not documento or not destino:
        return False, "Documento e destino são obrigatórios."
    if not porteiro:
        return False, "Porteiro inválido."

    pessoa = buscar_pessoa(documento)
    if not pessoa:
        return False, "Pessoa não encontrada."
    if pessoa["tipo"] == "morador":
        return False, "Morador não precisa de autorização."

    autorizar_documento(documento, destino, porteiro)
    return True, "✅ Autorizado!"


def revogar_service(documento: str, destino: str) -> tuple[bool, str]:
    documento = (documento or "").strip()
    destino = (destino or "").strip().upper()

    if not documento or not destino:
        return False, "Documento e destino são obrigatórios."

    revogar_documento(documento, destino)
    return True, "✅ Revogado (se existia)."