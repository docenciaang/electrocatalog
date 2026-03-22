from typing import Optional

from pydantic import BaseModel, Field


class ResistenciaEnrichment(BaseModel):
    valor_ohm:     Optional[float] = None
    encapsulado:   Optional[str]   = None
    tolerancia:    Optional[float] = Field(None, ge=0, le=100)
    potencia_w:    Optional[float] = Field(None, ge=0)
    voltaje_max_v: Optional[float] = Field(None, ge=0)
    description:   Optional[str]   = None


class CondensadorEnrichment(BaseModel):
    capacitancia_uf: Optional[float] = Field(None, ge=0)
    encapsulado:     Optional[str]   = None
    tolerancia:      Optional[float] = Field(None, ge=0, le=100)
    voltaje_max_v:   Optional[float] = Field(None, ge=0)
    description:     Optional[str]   = None


class InductorEnrichment(BaseModel):
    inductancia_uh: Optional[float] = Field(None, ge=0)
    encapsulado:    Optional[str]   = None
    tolerancia:     Optional[float] = Field(None, ge=0, le=100)
    potencia_w:     Optional[float] = Field(None, ge=0)
    description:    Optional[str]   = None


class ICEnrichment(BaseModel):
    familia_ic:    Optional[str]   = None
    encapsulado:   Optional[str]   = None
    voltaje_max_v: Optional[float] = Field(None, ge=0)
    description:   Optional[str]   = None
    notes:         Optional[str]   = None


class MicrocontroladorEnrichment(BaseModel):
    flash_kb:       Optional[float] = Field(None, ge=0)
    ram_kb:         Optional[float] = Field(None, ge=0)
    rom_kb:         Optional[float] = Field(None, ge=0)
    voltaje_op_v:   Optional[float] = Field(None, ge=0)
    frecuencia_mhz: Optional[float] = Field(None, ge=0)
    wifi:           Optional[bool]  = None
    bt:             Optional[bool]  = None
    zigbee:         Optional[bool]  = None
    lora:           Optional[bool]  = None
    familia_ic:     Optional[str]   = None
    encapsulado:    Optional[str]   = None
    description:    Optional[str]   = None


class GenericoEnrichment(BaseModel):
    encapsulado: Optional[str] = None
    description: Optional[str] = None


_SCHEMA_BY_TIPO = {
    "resistencia":      ResistenciaEnrichment,
    "condensador":      CondensadorEnrichment,
    "inductor":         InductorEnrichment,
    "ic":               ICEnrichment,
    "microcontrolador": MicrocontroladorEnrichment,
}


def get_schema(tipo: str | None):
    return _SCHEMA_BY_TIPO.get(tipo or "", GenericoEnrichment)
