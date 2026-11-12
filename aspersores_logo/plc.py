"""Abstracción de la comunicación con el LOGO!."""

from __future__ import annotations

import ipaddress
from typing import Any

import snap7
from snap7.error import S7Error

from .config import (
    DIRECCION_ANALOGICA,
    DIRECCIONES_VM,
    VALOR_ANALOGICO_MAX,
    VALOR_ANALOGICO_MIN,
)


def interpretar_tsap(valor: str, etiqueta: str) -> int:
    """Valida y transforma un TSAP en formato hexadecimal o decimal."""
    valor = valor.strip()
    try:
        if "." in valor:
            partes = valor.split(".")
            if len(partes) != 2 or any(len(parte) != 2 for parte in partes):
                raise ValueError
            tsap = int(partes[0], 16) << 8 | int(partes[1], 16)
        else:
            tsap = int(valor, 0)
    except ValueError as exc:
        raise ValueError(f"{etiqueta} debe tener formato 01.00 o 0x0100.") from exc

    if not 0 <= tsap <= 0xFFFF:
        raise ValueError(f"{etiqueta} debe estar entre 0 y 0xFFFF.")
    return tsap


class LogoVM:
    """Encapsula la conexión y las lecturas/escrituras del PLC."""

    def __init__(self) -> None:
        self.cliente: snap7.Logo | None = None

    @property
    def conectado(self) -> bool:
        return self.cliente is not None and self.cliente.get_connected()

    def connect(self, ip: str, tsap_cliente: int, tsap_logo: int) -> None:
        cliente = snap7.Logo()
        cliente.connect(ip, tsap_cliente, tsap_logo)
        self.cliente = cliente

    def disconnect(self) -> None:
        if self.cliente is None:
            return
        try:
            self.cliente.disconnect()
        except (S7Error, OSError):
            pass
        finally:
            self.cliente = None

    def is_connected(self) -> bool:
        return self.conectado

    @staticmethod
    def normalizar_estado_bit(valor: Any) -> bool:
        """Convierte valores leídos del PLC a un booleano seguro."""
        if isinstance(valor, bool):
            return valor
        if isinstance(valor, int):
            return bool(valor)
        if isinstance(valor, float):
            return bool(int(valor))
        if isinstance(valor, bytes):
            if not valor:
                return False
            if len(valor) == 1:
                return bool(valor[0])
            return bool(int.from_bytes(valor, byteorder="big", signed=False))
        if isinstance(valor, str):
            texto = valor.strip().lower()
            if texto in {"", "0", "false", "off"}:
                return False
            if texto in {"1", "true", "on"}:
                return True
            try:
                return bool(int(texto, 0))
            except ValueError:
                return bool(texto)
        return bool(valor)

    def read_bit(self, direccion: str) -> bool:
        if self.cliente is None:
            raise S7Error("No hay conexión activa con el LOGO!")
        return self.normalizar_estado_bit(self.cliente.read(direccion))

    def write_bit(self, direccion: str, estado: bool) -> None:
        if self.cliente is None:
            raise S7Error("No hay conexión activa con el LOGO!")
        self.cliente.write(direccion, int(bool(estado)))

    def read_analog_value(self) -> int:
        if self.cliente is None:
            raise S7Error("No hay conexión activa con el LOGO!")
        return int(self.cliente.read(DIRECCION_ANALOGICA))

    def write_analog_value(self, valor: int) -> int:
        if self.cliente is None:
            raise S7Error("No hay conexión activa con el LOGO!")
        if not VALOR_ANALOGICO_MIN <= valor <= VALOR_ANALOGICO_MAX:
            raise ValueError(
                f"La entrada analógica debe estar entre {VALOR_ANALOGICO_MIN} y {VALOR_ANALOGICO_MAX}."
            )
        self.cliente.write(DIRECCION_ANALOGICA, valor)
        return int(self.cliente.read(DIRECCION_ANALOGICA))

    def leer_estado_vm(self) -> dict[str, bool]:
        return {direccion: self.read_bit(direccion) for direccion in DIRECCIONES_VM}
