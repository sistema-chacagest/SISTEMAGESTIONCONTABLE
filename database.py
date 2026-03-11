import json
import os
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

FILES = {
    "clientes": DATA_DIR / "clientes.json",
    "proveedores": DATA_DIR / "proveedores.json",
    "facturas_venta": DATA_DIR / "facturas_venta.json",
    "facturas_compra": DATA_DIR / "facturas_compra.json",
    "cobranzas": DATA_DIR / "cobranzas.json",
    "pagos": DATA_DIR / "pagos.json",
    "movimientos_bancarios": DATA_DIR / "movimientos_bancarios.json",
    "cheques_cartera": DATA_DIR / "cheques_cartera.json",
    "cheques_emitidos": DATA_DIR / "cheques_emitidos.json",
    "config": DATA_DIR / "config.json",
}

def load_data(key: str) -> list | dict:
    path = FILES[key]
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    default = {} if key == "config" else []
    save_data(key, default)
    return default

def save_data(key: str, data: list | dict):
    path = FILES[key]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def get_next_id(key: str) -> int:
    data = load_data(key)
    if not data:
        return 1
    return max(item.get("id", 0) for item in data) + 1

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def date_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")

CONDICIONES_IVA = [
    "Responsable Inscripto",
    "Monotributista",
    "Exento en IVA",
    "Consumidor Final",
]

BANCOS = [
    "Galicia",
    "Provincia",
    "Santander",
    "Supervielle",
    "Nación",
    "Comafi",
    "Mercado Pago",
]

ALICUOTAS_IVA = {
    "21%": 0.21,
    "10.5%": 0.105,
    "27%": 0.27,
    "Exento": 0.0,
}

CUENTAS_GASTOS = [
    "Sueldos y Jornales",
    "Alquileres",
    "Servicios (Luz/Gas/Agua)",
    "Telefonía e Internet",
    "Honorarios Profesionales",
    "Materiales y Suministros",
    "Mantenimiento y Reparaciones",
    "Publicidad y Marketing",
    "Seguros",
    "Fletes y Transporte",
    "Gastos Bancarios",
    "Impuestos y Tasas",
    "Otros Gastos",
]
