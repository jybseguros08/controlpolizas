"""
Capa: models
Responsabilidad: único lugar que abre archivos (Excel y PDF) del proyecto control-polizas.
"""

import os
from datetime import datetime

import pandas as pd
import pdfplumber

# variable tipo diccionario: mapea etiquetas del PDF a nombres de campo internos
CAMPOS = {
    "Numero de poliza": "numero",
    "Ramo": "ramo",
    "Tomador / Asegurado": "nombre",
    "Cedula": "cedula",
    "Vigencia desde": "desde",
    "Vigencia hasta": "hasta",
    "Prima anual": "prima",
    "Forma de pago": "pago",
    "Suma asegurada": "suma",
    "Asesor": "asesor",
}

# variables tipo string con las rutas de los archivos (están en la raíz del proyecto)
RUTA_CLIENTES = "Maestro_Clientes.xlsx"
CARPETA_POLIZAS = "polizas"


def cargar_clientes():
    """
    Lee el Excel de clientes y devuelve un DataFrame de pandas.
    La columna Cedula se guarda como texto sin espacios.
    """
    # variable tipo DataFrame (pandas)
    df = pd.read_excel(RUTA_CLIENTES, sheet_name="Clientes")
    # variable tipo Serie: cedulas como texto sin espacios
    df["Cedula"] = df["Cedula"].astype(str).str.strip()
    return df


def _texto_a_fecha(texto):
    """
    Convierte un string dd/mm/aaaa a objeto date.
    Devuelve None si está vacío o no se puede convertir.
    """
    if texto is None or str(texto).strip() == "":
        return None
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def _texto_a_numero(texto):
    """
    Convierte un monto como "CRC 228,000.00" a número (float).
    Devuelve None si está vacío o no se puede convertir.
    """
    if texto is None or str(texto).strip() == "":
        return None
    try:
        limpio = str(texto).replace("CRC", "").replace(",", "").strip()
        return float(limpio)
    except ValueError:
        return None


def leer_poliza(ruta_pdf):
    """
    Abre un PDF de póliza con pdfplumber y devuelve un diccionario con sus datos.
    """
    # variable tipo string con el nombre del archivo
    archivo = os.path.basename(ruta_pdf)

    # abrimos el PDF con pdfplumber
    with pdfplumber.open(ruta_pdf) as pdf:
        # variable tipo objeto de página
        pagina = pdf.pages[0]
        # variable tipo string con todo el texto de la primera página
        texto = pagina.extract_text() or ""
        # variable tipo lista de líneas
        lineas = texto.splitlines()

    # primera línea es el nombre de la aseguradora
    # variable tipo string
    aseguradora = lineas[0].strip() if lineas else ""

    # variable tipo diccionario con los datos de la póliza
    datos = {
        "archivo": archivo,
        "aseguradora": aseguradora,
        "numero": None,
        "ramo": None,
        "nombre": None,
        "cedula": None,
        "desde": None,
        "hasta": None,
        "prima": None,
        "pago": None,
        "suma": None,
        "asesor": None,
    }

    # bucle sobre las líneas restantes (salteamos la primera que es la aseguradora)
    for linea in lineas[1:]:
        # condicional: solo procesamos líneas que contengan ":"
        if ":" in linea:
            # dividimos en etiqueta y valor
            etiqueta, valor = linea.split(":", 1)
            etiqueta = etiqueta.strip()
            valor = valor.strip()
            # condicional: si la etiqueta está en nuestro diccionario CAMPOS
            if etiqueta in CAMPOS:
                campo = CAMPOS[etiqueta]
                # condicionales especiales para fechas y montos
                if campo in ("desde", "hasta"):
                    datos[campo] = _texto_a_fecha(valor)
                elif campo in ("prima", "suma"):
                    datos[campo] = _texto_a_numero(valor)
                else:
                    # variable tipo string simple
                    datos[campo] = valor

    return datos


def cargar_polizas():
    """
    Recorre la carpeta data/polizas en orden alfabético y devuelve una lista
    con el diccionario de cada PDF.
    """
    # variable tipo lista de nombres de archivo (filtramos solo .pdf)
    archivos = sorted(
        [f for f in os.listdir(CARPETA_POLIZAS) if f.lower().endswith(".pdf")]
    )

    # variable tipo lista de diccionarios
    resultado = []
    for nombre_archivo in archivos:
        # variable tipo string con la ruta completa
        ruta = os.path.join(CARPETA_POLIZAS, nombre_archivo)
        resultado.append(leer_poliza(ruta))

    return resultado
