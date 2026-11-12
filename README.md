# Aspersores LOGO! S7

Aplicación gráfica para probar y activar entradas VM en un LOGO! por comunicación S7.

## Características

- Conexión a PLC LOGO! por red TCP/IP.
- Validación de IP y TSAP.
- Activación/desactivación de bits VM.
- Control de exclusividad entre entradas.
- Envío de valor analógico a una dirección `VW`.
- Interfaz con visualización del aspersor y animación visual.

## Requisitos

- Python 3.10 o superior.
- `python-snap7`.
- `tkinter` (incluido con Python para Windows/macOS y normalmente con paquetes de Python para Linux).

## Instalación

1. Clona o descarga este proyecto.
2. Crea un entorno virtual (opcional, pero recomendado):

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate    # Windows
```

3. Instala dependencias:

```bash
pip install -r requirements.txt
```

4. Ejecuta la aplicación:

```bash
python main.py
```

## Estructura del proyecto

```text
aspersores-logo/
├── aspersores_logo/
│   ├── __init__.py
│   ├── app.py
│   ├── animation.py
│   ├── config.py
│   ├── plc.py
│   └── ui.py
├── .gitignore
├── main.py
├── pyproject.toml
├── README.md
├── requirements.txt
└── comunicacionS7VM.py
```

## Configuración

Puedes ajustar los valores por defecto en `aspersores_logo/config.py`:

- IP del LOGO!
- TSAP cliente
- TSAP del LOGO!
- Dirección de entrada analógica
- Rango permitido del valor analógico

## Uso

- Pulsa `Conectar`.
- Marca `habilitar botones` para permitir cambios.
- Usa los botones por cada bit VM.
- En la sección analógica, ajusta el valor y presiona `Enviar`.

## Importante

Esta aplicación requiere que el LOGO! esté configurado correctamente con comunicación S7 y que los TSAP coincidan con la configuración del PLC.

## Licencia

Este proyecto está pensado como una herramienta interna para control y pruebas de equipos de aspersión.
