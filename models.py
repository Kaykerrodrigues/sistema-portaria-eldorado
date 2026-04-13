from pydantic import BaseModel, Field


class PessoaCreate(BaseModel):
    nome: str = Field(min_length=1)
    documento: str = Field(min_length=1)
    tipo: str = Field(min_length=1)
    quadra: str | None = None
    lote: str | None = None


class PessoaUpdate(BaseModel):
    nome: str | None = None
    tipo: str | None = None
    quadra_lote: str | None = None


class EntradaRequest(BaseModel):
    documento: str = Field(min_length=1)
    quadra: str | None = None
    lote: str | None = None
    porteiro: str = Field(min_length=1)


class SaidaRequest(BaseModel):
    documento: str = Field(min_length=1)
    porteiro: str = Field(min_length=1)