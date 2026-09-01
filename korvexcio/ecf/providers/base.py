"""La interfaz que cualquier proveedor de e-CF tiene que implementar
(D3, revisada 31/08: el proveedor se decide en S2.7, todavia bloqueado
por S0.9/S0.3 - esta interfaz existe justo para que el resto del modulo
`ecf` no dependa de cual gane).

Result/Ok/Err en vez de excepciones: los tres metodos (emitir, consultar,
anular) NO propagan excepciones desde un job en background (S2.10) --
capturan sus propios errores y devuelven Err. Quien llama decide si
reintenta, sin que un fallo del proveedor tumbe el worker de la cola.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T

    def is_ok(self) -> bool:
        return True


@dataclass(frozen=True)
class Err:
    message: str
    code: str | None = None
    retryable: bool = True

    def is_ok(self) -> bool:
        return False


Result = Ok[T] | Err


@dataclass(frozen=True)
class EmisionResult:
    track_id: str
    codigo_seguridad: str | None = None
    qr_url: str | None = None


@dataclass(frozen=True)
class ConsultaResult:
    estado: str
    validation_messages: str | None = None


class FiscalProvider(ABC):
    """Cada proveedor real (Alanube, ECF SSD) implementa esto en su
    propio archivo bajo providers/<nombre>.py cuando S2.7 lo desbloquee.
    El constructor de cada implementacion resuelve sus credenciales
    DESDE la Company del documento que se esta procesando -- nunca una
    vez al arrancar (CLAUDE.md regla 10, critica por D19)."""

    @abstractmethod
    def emitir(self, company: str, signed_xml: str) -> Result[EmisionResult]:
        """Envia un e-CF firmado. Devuelve Ok(EmisionResult) con el
        track_id, o Err si el proveedor lo rechazo o hubo un problema
        de red -- nunca levanta una excepcion sin capturar."""
        raise NotImplementedError

    @abstractmethod
    def consultar(self, company: str, track_id: str) -> Result[ConsultaResult]:
        """Pregunta el estado de un e-CF ya enviado por su track_id."""
        raise NotImplementedError

    @abstractmethod
    def anular(self, company: str, encf: str, motivo: str) -> Result[None]:
        """Anula un e-CF ya aceptado. No es cancelar (ECF.before_cancel
        ya bloquea eso para documentos Aceptados) -- es el flujo legal
        de anulacion ante la DGII."""
        raise NotImplementedError
