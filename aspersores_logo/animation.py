"""Animación del aspersor para la interfaz gráfica."""

from __future__ import annotations

import random
import tkinter as tk

from .config import GOTAS_ASPERSOR, MS_POR_CUADRO_ASPERSOR


class AspersorAnimation:
    def __init__(self, lienzo: tk.Canvas, raiz: tk.Misc) -> None:
        self.lienzo = lienzo
        self.raiz = raiz
        self.gotas: list[list[float]] = []
        self._desfase_chorro = 0
        self._tarea_animacion: str | None = None
        self._dibujar()

    def _dibujar(self) -> None:
        for x0, x1 in ((10, 150), (30, 130), (50, 110)):
            self.lienzo.create_arc(
                x0,
                20,
                x1,
                112,
                start=200,
                extent=140,
                style="arc",
                width=2,
                dash=(4, 3),
                tags=("agua", "chorro"),
            )
        for _ in range(GOTAS_ASPERSOR):
            elemento = self.lienzo.create_oval(0, 0, 0, 0, tags=("agua", "gota"))
            gota = [elemento, 0.0, 0.0, 0.0, 0.0]
            self._generar_gota(gota)
            for _ in range(random.randint(0, 25)):
                self._mover_gota(gota)
            self.gotas.append(gota)
        self.lienzo.create_rectangle(0, 0, 160, 10, fill="#757575", outline="")
        self.lienzo.create_rectangle(74, 10, 86, 50, tags=("cuerpo",))
        self.lienzo.create_rectangle(64, 48, 96, 62, tags=("cuerpo",))
        self.lienzo.create_rectangle(70, 62, 90, 70, tags=("cuerpo",))
        self.lienzo.create_rectangle(77, 70, 83, 76, tags=("cuerpo",))

    def _generar_gota(self, gota: list[float]) -> None:
        gota[1], gota[2] = 80.0, 76.0
        gota[3] = random.uniform(-4.0, 4.0)
        gota[4] = random.uniform(-1.0, 1.5)

    def _mover_gota(self, gota: list[float]) -> None:
        gota[1] += gota[3]
        gota[2] += gota[4]
        gota[4] += 0.35
        if gota[2] > 130 or not -5 < gota[1] < 165:
            self._generar_gota(gota)
        x, y = gota[1], gota[2]
        self.lienzo.coords(int(gota[0]), x - 2, y - 3, x + 2, y + 3)

    def _animar(self) -> None:
        for gota in self.gotas:
            self._mover_gota(gota)
        self._desfase_chorro = (self._desfase_chorro + 1) % 7
        self.lienzo.itemconfigure("chorro", dashoffset=self._desfase_chorro)
        self._tarea_animacion = self.raiz.after(
            MS_POR_CUADRO_ASPERSOR, self._animar
        )

    def detener(self) -> None:
        if self._tarea_animacion is not None:
            self.raiz.after_cancel(self._tarea_animacion)
            self._tarea_animacion = None

    def actualizar(self, activo: bool) -> None:
        color_cuerpo = "#1565C0" if activo else "#9E9E9E"
        self.lienzo.itemconfigure("cuerpo", fill=color_cuerpo, outline="#424242")
        self.lienzo.itemconfigure("agua", outline="#29B6F6")
        self.lienzo.itemconfigure("gota", fill="#29B6F6")
        self.lienzo.itemconfigure("agua", state="normal" if activo else "hidden")
        if activo and self._tarea_animacion is None:
            self._animar()
        elif not activo:
            self.detener()
