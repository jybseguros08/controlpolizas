"""
Capa: services
Responsabilidad: generar el Excel de resultados con openpyxl y devolverlo en bytes.
"""

from datetime import date
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# variables tipo string con los colores del diseño (sin el #)
ROJO = "AE1800"
NEGRO = "201E1D"
GRIS_CLARO = "F3F2F2"
BLANCO = "FFFFFF"


def _estilo_cabecera(hoja, fila, columnas):
    """
    Pinta una fila de cabecera: fondo rojo, letra blanca y en negrita.
    """
    # variable tipo PatternFill: relleno rojo
    relleno = PatternFill("solid", start_color=ROJO, end_color=ROJO)
    # variable tipo Font: letra blanca en negrita
    fuente = Font(color=BLANCO, bold=True)
    # variable tipo Alignment: centrado
    alineacion = Alignment(horizontal="center", vertical="center")

    # bucle sobre las columnas de la cabecera
    for columna in range(1, columnas + 1):
        celda = hoja.cell(row=fila, column=columna)
        celda.fill = relleno
        celda.font = fuente
        celda.alignment = alineacion


def _ajustar_anchos(hoja):
    """
    Ajusta el ancho de cada columna según el texto más largo.
    """
    # variable tipo diccionario: letra de columna -> ancho máximo
    anchos = {}
    # bucle sobre todas las filas con datos
    for fila in hoja.iter_rows():
        for celda in fila:
            if celda.value is None:
                continue
            # variable tipo int: largo del texto de la celda
            largo = len(str(celda.value))
            letra = get_column_letter(celda.column)
            if letra not in anchos or largo > anchos[letra]:
                anchos[letra] = largo

    # bucle sobre los anchos calculados (máximo 45 para no exagerar)
    for letra, largo in anchos.items():
        hoja.column_dimensions[letra].width = min(largo + 2, 45)


def _fecha_texto(valor):
    """
    Convierte una fecha a texto dd/mm/aaaa. Devuelve "-" si viene vacía.
    """
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    return "-"


def crear_excel_resultados(resultados, conteo, primas, inconsistencias, fecha_corte=None):
    """
    Crea un libro de Excel con 3 hojas: Resumen, Pólizas e Inconsistencias.
    Devuelve el archivo en bytes.
    """
    # variable tipo Workbook: el libro de Excel
    libro = Workbook()

    # ---------- Hoja 1: Resumen ----------
    # la primera hoja viene creada por defecto
    hoja_resumen = libro.active
    hoja_resumen.title = "Resumen"

    hoja_resumen["A1"] = "Corredora de Seguros Horizonte"
    hoja_resumen["A1"].font = Font(size=16, bold=True, color=ROJO)
    hoja_resumen["A2"] = "Control de pólizas · Reporte generado"
    hoja_resumen["A2"].font = Font(size=11, color=NEGRO)
    hoja_resumen["A3"] = f"Fecha de corte: {_fecha_texto(fecha_corte)}"
    hoja_resumen["A3"].font = Font(bold=True)

    # tabla de contadores por estado
    hoja_resumen["A5"] = "Estado"
    hoja_resumen["B5"] = "Cantidad"
    _estilo_cabecera(hoja_resumen, 5, 2)

    # variable tipo int: número de fila actual
    fila = 6
    # bucle sobre los estados conocidos
    for estado in ("Vigente", "Por vencer", "Vencida", "Sin fecha"):
        hoja_resumen.cell(row=fila, column=1, value=estado)
        hoja_resumen.cell(row=fila, column=2, value=conteo.get(estado, 0))
        fila += 1

    # tabla de primas por aseguradora
    fila += 1
    hoja_resumen.cell(row=fila, column=1, value="Aseguradora")
    hoja_resumen.cell(row=fila, column=2, value="Primas no vencidas (CRC)")
    _estilo_cabecera(hoja_resumen, fila, 2)
    fila += 1

    # bucle sobre el diccionario aseguradora -> monto
    for aseguradora, monto in primas.items():
        hoja_resumen.cell(row=fila, column=1, value=aseguradora)
        # variable tipo celda: la usamos para dar formato de número
        celda_monto = hoja_resumen.cell(row=fila, column=2, value=monto)
        celda_monto.number_format = "#,##0.00"
        fila += 1

    # total de inconsistencias
    fila += 1
    hoja_resumen.cell(row=fila, column=1, value="Inconsistencias encontradas").font = Font(bold=True)
    hoja_resumen.cell(row=fila, column=2, value=len(inconsistencias)).font = Font(bold=True)

    _ajustar_anchos(hoja_resumen)

    # ---------- Hoja 2: Pólizas ----------
    hoja_polizas = libro.create_sheet("Pólizas")

    # variable tipo lista con los títulos de las columnas
    columnas = [
        "Póliza", "Asegurado", "Cédula", "Correo", "Aseguradora", "Ramo",
        "Vigencia desde", "Vigencia hasta", "Días para vencer",
        "Prima anual (CRC)", "Forma de pago", "Suma asegurada (CRC)",
        "Asesor", "Estado", "En maestro",
    ]

    # escribimos la cabecera
    for indice, titulo in enumerate(columnas, start=1):
        hoja_polizas.cell(row=1, column=indice, value=titulo)
    _estilo_cabecera(hoja_polizas, 1, len(columnas))
    hoja_polizas.freeze_panes = "A2"

    # variable tipo int: fila donde empezamos a escribir datos
    fila = 2
    # bucle sobre cada póliza ya calculada
    for r in resultados:
        hoja_polizas.cell(row=fila, column=1, value=r.get("numero"))
        hoja_polizas.cell(row=fila, column=2, value=r.get("nombre"))
        hoja_polizas.cell(row=fila, column=3, value=r.get("cedula"))
        hoja_polizas.cell(row=fila, column=4, value=r.get("correo"))
        hoja_polizas.cell(row=fila, column=5, value=r.get("aseguradora"))
        hoja_polizas.cell(row=fila, column=6, value=r.get("ramo"))
        hoja_polizas.cell(row=fila, column=7, value=_fecha_texto(r.get("desde")))
        hoja_polizas.cell(row=fila, column=8, value=_fecha_texto(r.get("hasta")))
        hoja_polizas.cell(row=fila, column=9, value=r.get("dias_hasta_vencer"))
        hoja_polizas.cell(row=fila, column=10, value=r.get("prima"))
        hoja_polizas.cell(row=fila, column=11, value=r.get("pago"))
        hoja_polizas.cell(row=fila, column=12, value=r.get("suma"))
        hoja_polizas.cell(row=fila, column=13, value=r.get("asesor"))
        hoja_polizas.cell(row=fila, column=14, value=r.get("estado"))
        hoja_polizas.cell(row=fila, column=15, value="Sí" if r.get("en_maestro") else "No")
        fila += 1

    # formato de número para las columnas de dinero
    for numero_fila in range(2, fila):
        hoja_polizas.cell(row=numero_fila, column=10).number_format = "#,##0.00"
        hoja_polizas.cell(row=numero_fila, column=12).number_format = "#,##0.00"

    _ajustar_anchos(hoja_polizas)

    # ---------- Hoja 3: Inconsistencias ----------
    hoja_inc = libro.create_sheet("Inconsistencias")
    hoja_inc.cell(row=1, column=1, value="Detalle de la inconsistencia")
    _estilo_cabecera(hoja_inc, 1, 1)

    # variable tipo int: fila de escritura
    fila = 2
    # bucle sobre la lista de textos de inconsistencias
    for texto in inconsistencias:
        hoja_inc.cell(row=fila, column=1, value=texto)
        fila += 1

    # si no hay ninguna, lo dejamos escrito
    if not inconsistencias:
        hoja_inc.cell(row=2, column=1, value="Sin inconsistencias")

    _ajustar_anchos(hoja_inc)

    # ---------- Devolver bytes ----------
    # variable tipo BytesIO: archivo en memoria
    memoria = BytesIO()
    libro.save(memoria)
    memoria.seek(0)
    return memoria.getvalue()
