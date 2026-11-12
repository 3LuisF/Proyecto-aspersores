"""Interfaz gráfica principal."""

from __future__ import annotations

import ipaddress
import tkinter as tk
from tkinter import messagebox, ttk

from snap7.error import S7Error

from .animation import AspersorAnimation
from .config import (
    APP_TITLE,
    DIRECCION_ANALOGICA,
    DIRECCIONES_VM,
    IP_PREDETERMINADA,
    MS_POR_CUADRO_ASPERSOR,
    TEXTOS_BOTONES_VM,
    TSAP_CLIENTE_PREDETERMINADO,
    TSAP_LOGO_PREDETERMINADO,
    VALOR_ANALOGICO_MAX,
    VALOR_ANALOGICO_MIN,
)
from .plc import LogoVM, interpretar_tsap


class ControladorVMLogo:
    def __init__(self, raiz: tk.Tk) -> None:
        self.raiz = raiz
        self.logo: LogoVM | None = None
        self.estados_vm: dict[str, bool | None] = {
            direccion: None for direccion in DIRECCIONES_VM
        }

        self.var_ip = tk.StringVar(value=IP_PREDETERMINADA)
        self.var_tsap_cliente = tk.StringVar(value=TSAP_CLIENTE_PREDETERMINADO)
        self.var_tsap_logo = tk.StringVar(value=TSAP_LOGO_PREDETERMINADO)
        self.seguridad_confirmada = tk.BooleanVar(value=False)
        self.var_estado = tk.StringVar(value="Desconectado")
        self.var_analogica = tk.IntVar(value=VALOR_ANALOGICO_MIN)
        self.var_analogica_plc = tk.StringVar(value="Valor en el LOGO!: --")

        raiz.title(APP_TITLE)
        raiz.protocol("WM_DELETE_WINDOW", self.cerrar)
        self._construir_interfaz()
        self._actualizar_controles()
        self.var_estado.set("Conectando...")
        raiz.after(200, self.alternar_conexion)

    def _construir_interfaz(self) -> None:
        marco = ttk.Frame(self.raiz, padding=12)
        marco.grid(sticky="nsew")
        self.raiz.columnconfigure(0, weight=1)
        self.raiz.rowconfigure(0, weight=1)
        marco.columnconfigure(1, weight=1)

        ttk.Label(
            marco,
            text="Aspersion de Procesos",
            anchor="center",
            font=("Arial", 14, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.boton_conexion = ttk.Button(
            marco, text="Conectar", command=self.alternar_conexion
        )
        self.boton_conexion.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.etiqueta_estado = tk.Label(marco, textvariable=self.var_estado, anchor="center")
        self.etiqueta_estado.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        ttk.Separator(marco).grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Checkbutton(
            marco,
            text="habilitar botones",
            variable=self.seguridad_confirmada,
            command=self._actualizar_controles,
        ).grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.botones_vm: dict[str, ttk.Button] = {}
        for fila, direccion in enumerate(DIRECCIONES_VM, start=9):
            boton = ttk.Button(
                marco,
                text=TEXTOS_BOTONES_VM[direccion][0],
                command=lambda dir_vm=direccion: self._alternar_bit_vm(dir_vm),
            )
            boton.grid(row=fila, column=0, columnspan=2, sticky="ew", pady=(6, 0))
            self.botones_vm[direccion] = boton

        fila_analogica = 9 + len(DIRECCIONES_VM)
        marco_analogico = ttk.LabelFrame(
            marco,
            text=f"Entrada analógica 0 ({DIRECCION_ANALOGICA})",
            padding=8,
        )
        marco_analogico.grid(
            row=fila_analogica,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(12, 0),
        )
        marco_analogico.columnconfigure(0, weight=1)
        self.deslizador_analogico = tk.Scale(
            marco_analogico,
            from_=VALOR_ANALOGICO_MIN,
            to=VALOR_ANALOGICO_MAX,
            orient="horizontal",
            resolution=1,
            variable=self.var_analogica,
            showvalue=False,
        )
        self.deslizador_analogico.grid(row=0, column=0, sticky="ew")
        self.campo_analogico = ttk.Spinbox(
            marco_analogico,
            from_=VALOR_ANALOGICO_MIN,
            to=VALOR_ANALOGICO_MAX,
            increment=1,
            width=5,
            textvariable=self.var_analogica,
        )
        self.campo_analogico.grid(row=0, column=1, padx=(8, 0))
        self.boton_analogico = ttk.Button(
            marco_analogico, text="Enviar", command=self._enviar_analogica
        )
        self.boton_analogico.grid(row=0, column=2, padx=(8, 0))
        ttk.Label(marco_analogico, textvariable=self.var_analogica_plc).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(4, 0)
        )

        self.aspersor = tk.Canvas(marco, width=160, height=130, highlightthickness=0)
        self.aspersor.grid(row=fila_analogica + 1, column=0, columnspan=2, pady=(12, 0))
        self.animador = AspersorAnimation(self.aspersor, self.raiz)

    @staticmethod
    def _normalizar_estado_bit(valor: object) -> bool:
        return LogoVM.normalizar_estado_bit(valor)

    def _leer_bit_vm(self, direccion: str) -> bool:
        if self.logo is None:
            raise ValueError(f"No hay conexión activa para leer {direccion}")
        return self.logo.read_bit(direccion)

    def alternar_conexion(self) -> None:
        if self.logo is not None and self.logo.is_connected():
            self._desconectar()
            return

        try:
            ip = str(ipaddress.IPv4Address(self.var_ip.get().strip()))
            tsap_cliente = interpretar_tsap(self.var_tsap_cliente.get(), "TSAP cliente")
            tsap_logo = interpretar_tsap(self.var_tsap_logo.get(), "TSAP LOGO!")
        except ValueError as exc:
            messagebox.showerror("Configuracion no valida", str(exc), parent=self.raiz)
            return

        cliente = LogoVM()
        try:
            cliente.connect(ip, tsap_cliente, tsap_logo)
        except (S7Error, OSError) as exc:
            self.var_estado.set(f"Error de conexion: {exc}")
            messagebox.showerror("No se pudo conectar", str(exc), parent=self.raiz)
            return

        try:
            estados = {direccion: cliente.read_bit(direccion) for direccion in DIRECCIONES_VM}
            valor_analogico = cliente.read_analog_value()
        except (S7Error, OSError, ValueError) as exc:
            try:
                cliente.disconnect()
            except (S7Error, OSError) as exc_desconexion:
                detalle = (
                    f"No se pudieron leer los bits VM: {exc}\n"
                    f"Tambien fallo la desconexion: {exc_desconexion}"
                )
            else:
                detalle = f"No se pudieron leer los bits VM: {exc}"
            self.var_estado.set("Error al leer bits VM")
            messagebox.showerror("Error de lectura", detalle, parent=self.raiz)
            return

        self.logo = cliente
        self.estados_vm = estados
        self.var_analogica_plc.set(f"Valor en el LOGO!: {valor_analogico}")
        if VALOR_ANALOGICO_MIN <= valor_analogico <= VALOR_ANALOGICO_MAX:
            self.var_analogica.set(valor_analogico)
        self.var_estado.set(f"Conectado a {ip}")
        self.boton_conexion.configure(text="Desconectar")
        self._actualizar_controles()
        activas = [d for d in DIRECCIONES_VM if estados[d]]
        if len(activas) > 1:
            messagebox.showwarning(
                "Entradas excluyentes",
                f"El PLC tiene varias entradas activas a la vez: {', '.join(activas)}. Detén las que sobran.",
                parent=self.raiz,
            )

    def _detener_todo(self) -> list[str]:
        errores: list[str] = []
        if self.logo is None or not self.logo.is_connected():
            return errores
        for direccion in DIRECCIONES_VM:
            try:
                self.logo.write_bit(direccion, False)
            except (S7Error, OSError, ValueError) as exc:
                errores.append(f"{direccion}: {exc}")
            else:
                self.estados_vm[direccion] = False
        return errores

    def _desconectar(self) -> None:
        if self.logo is None:
            return
        errores = self._detener_todo()
        if errores:
            messagebox.showwarning(
                "No se detuvieron todas las entradas",
                "No se pudieron poner en 0 antes de desconectar:\n" + "\n".join(errores),
                parent=self.raiz,
            )
        try:
            self.logo.disconnect()
        except (S7Error, OSError) as exc:
            self.var_estado.set(f"Error al desconectar: {exc}")
            messagebox.showerror("Error al desconectar", str(exc), parent=self.raiz)
            return

        self.logo = None
        self.seguridad_confirmada.set(False)
        self.var_estado.set("Desconectado")
        self.boton_conexion.configure(text="Conectar")
        self._actualizar_controles()

    def _alternar_bit_vm(self, direccion: str) -> None:
        if self.logo is None or not self.logo.is_connected():
            messagebox.showwarning(
                "Sin conexion", "Conecta con el LOGO! antes de cambiar un bit.", parent=self.raiz
            )
            return
        if not self.seguridad_confirmada.get():
            return

        estado_actual = self.estados_vm[direccion]
        if estado_actual is None:
            messagebox.showerror(
                "Estado desconocido",
                f"No se conoce el estado actual de {direccion}. Desconecta y vuelve a conectar para leer el estado del PLC.",
                parent=self.raiz,
            )
            return

        estado_nuevo = not estado_actual
        if estado_nuevo and not self._verificar_exclusion(direccion):
            return
        try:
            self.logo.write_bit(direccion, estado_nuevo)
        except (S7Error, OSError, ValueError) as exc:
            try:
                self.estados_vm[direccion] = self._leer_bit_vm(direccion)
            except (S7Error, OSError, ValueError) as exc_lectura:
                self.estados_vm[direccion] = None
                detalle = (
                    f"No se pudo cambiar {direccion}: {exc}\n"
                    f"Tampoco se pudo confirmar su estado: {exc_lectura}\n"
                    "Desconecta y vuelve a conectar para sincronizarlo."
                )
            else:
                estado_leido = self.estados_vm[direccion]
                detalle = (
                    f"No se pudo confirmar el cambio de {direccion}: {exc}\n"
                    f"El estado leido del PLC es {'activado' if estado_leido else 'desactivado'}."
                )
            self.var_estado.set(f"Error al cambiar {direccion}")
            self._actualizar_controles()
            messagebox.showerror("Error de escritura", detalle, parent=self.raiz)
            return

        self.estados_vm[direccion] = estado_nuevo
        self.var_estado.set(f"  {'activado' if estado_nuevo else 'desactivado'}")
        self._actualizar_controles()

    def _enviar_analogica(self) -> None:
        if self.logo is None or not self.logo.is_connected():
            messagebox.showwarning(
                "Sin conexion", "Conecta con el LOGO! antes de enviar el valor.", parent=self.raiz
            )
            return
        if not self.seguridad_confirmada.get():
            return

        try:
            valor = int(self.var_analogica.get())
        except (tk.TclError, ValueError):
            valor = None
        if valor is None or not VALOR_ANALOGICO_MIN <= valor <= VALOR_ANALOGICO_MAX:
            messagebox.showerror(
                "Valor no valido",
                f"La entrada analógica debe ser un número entero entre {VALOR_ANALOGICO_MIN} y {VALOR_ANALOGICO_MAX}.",
                parent=self.raiz,
            )
            return

        try:
            leido = self.logo.write_analog_value(valor)
        except (S7Error, OSError, ValueError) as exc:
            self.var_estado.set(f"Error al escribir {DIRECCION_ANALOGICA}")
            messagebox.showerror(
                "Error de escritura",
                f"No se pudo enviar {valor} a {DIRECCION_ANALOGICA}: {exc}",
                parent=self.raiz,
            )
            return

        self.var_analogica_plc.set(f"Valor en el LOGO!: {leido}")
        self.var_estado.set(f"{DIRECCION_ANALOGICA} = {leido}")

    def _verificar_exclusion(self, direccion: str) -> bool:
        assert self.logo is not None
        otras = [d for d in DIRECCIONES_VM if d != direccion]
        try:
            for otra in otras:
                self.estados_vm[otra] = self._leer_bit_vm(otra)
        except (S7Error, OSError, ValueError) as exc:
            self.var_estado.set("Error al verificar entradas")
            messagebox.showerror(
                "Error de lectura",
                f"No se pudo confirmar que las otras entradas esten detenidas, asi que no se activa {direccion}: {exc}",
                parent=self.raiz,
            )
            return False
        activas = [otra for otra in otras if self.estados_vm[otra]]
        if activas:
            self._actualizar_controles()
            messagebox.showwarning(
                "Entradas excluyentes",
                f"No se puede activar {direccion} mientras {', '.join(activas)} este activa. Detenla primero.",
                parent=self.raiz,
            )
            return False
        return True

    def _actualizar_controles(self) -> None:
        conectado = self.logo is not None and self.logo.is_connected()
        self.etiqueta_estado.configure(background="#CCFF99" if conectado else "#FF9999")
        puede_alternar = conectado and self.seguridad_confirmada.get()
        hay_activa = any(self.estados_vm[d] for d in DIRECCIONES_VM)
        for direccion, boton in self.botones_vm.items():
            estado = self.estados_vm[direccion]
            habilitado = (
                puede_alternar
                and estado is not None
                and (estado or not hay_activa)
            )
            boton.configure(
                text=TEXTOS_BOTONES_VM[direccion][1 if estado else 0],
                state="normal" if habilitado else "disabled",
            )
        self.boton_conexion.configure(state="normal")
        estado_analogico = "normal" if puede_alternar else "disabled"
        self.deslizador_analogico.configure(state=estado_analogico)
        self.campo_analogico.configure(state=estado_analogico)
        self.boton_analogico.configure(state=estado_analogico)
        if not conectado:
            self.var_analogica_plc.set("Valor en el LOGO!: --")
        self.animador.actualizar(conectado and any(self.estados_vm[d] for d in DIRECCIONES_VM))

    def liberar(self) -> None:
        """Desconecta del LOGO! sin mostrar diálogos; se usa al salir."""
        if self.logo is not None:
            self._detener_todo()
            try:
                self.logo.disconnect()
            except (S7Error, OSError):
                pass
            self.logo = None
        self.animador.detener()

    def cerrar(self) -> None:
        self.liberar()
        self.raiz.destroy()


def main() -> None:
    raiz = tk.Tk()
    controlador = ControladorVMLogo(raiz)
    try:
        raiz.mainloop()
    finally:
        controlador.liberar()
