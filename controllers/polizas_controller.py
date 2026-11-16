"""
Capa: controllers
Responsabilidad: rutas de Flask (Blueprint). No calcula: llama al modelo y al servicio.
"""

import zipfile
from io import BytesIO

from flask import Blueprint, render_template, send_file, abort

from models.polizas import (
    calcular_resultados,
    contar_por_estado,
    primas_por_aseguradora,
    buscar_inconsistencias,
    buscar_por_numero,
    FECHA_CORTE,
)
from services.generador_aviso import crear_aviso_pdf
from services.generador_excel import crear_excel_resultados

# variable tipo Blueprint de Flask
polizas_bp = Blueprint("polizas", __name__)


def _datos_tablero():
    """
    Pide al modelo todos los datos que necesita el tablero.
    Devuelve una tupla con resultados, conteo, primas e inconsistencias.
    """
    # variable tipo lista: resultados del modelo
    resultados = calcular_resultados()
    # variable tipo diccionario: conteo por estado
    conteo = contar_por_estado(resultados)
    # variable tipo diccionario: primas por aseguradora
    primas = primas_por_aseguradora(resultados)
    # variable tipo lista: inconsistencias
    inconsistencias = buscar_inconsistencias(resultados)
    return resultados, conteo, primas, inconsistencias


@polizas_bp.route("/")
def inicio():
    """
    Ruta "/" tablero: muestra resultados, conteo, primas por aseguradora,
    inconsistencias y fecha de corte.
    """
    resultados, conteo, primas, inconsistencias = _datos_tablero()

    return render_template(
        "inicio.html",
        resultados=resultados,
        conteo=conteo,
        primas=primas,
        inconsistencias=inconsistencias,
        fecha_corte=FECHA_CORTE,
        mensaje=None,
    )


@polizas_bp.route("/generar-proceso")
def generar_proceso():
    """
    Ruta "/generar-proceso": vuelve a leer el Excel y los PDF, recalcula todo
    y muestra el tablero con un mensaje de resumen del proceso.
    """
    resultados, conteo, primas, inconsistencias = _datos_tablero()

    # variable tipo string: resumen que se muestra arriba del tablero
    mensaje = (
        f"Proceso ejecutado: {len(resultados)} pólizas leídas · "
        f"{conteo.get('Vigente', 0)} vigentes · "
        f"{conteo.get('Por vencer', 0)} por vencer · "
        f"{conteo.get('Vencida', 0)} vencidas · "
        f"{len(inconsistencias)} inconsistencias."
    )

    return render_template(
        "inicio.html",
        resultados=resultados,
        conteo=conteo,
        primas=primas,
        inconsistencias=inconsistencias,
        fecha_corte=FECHA_CORTE,
        mensaje=mensaje,
    )


@polizas_bp.route("/exportar-excel")
def exportar_excel():
    """
    Ruta "/exportar-excel": genera un Excel nuevo con 3 hojas
    (Resumen, Pólizas, Inconsistencias) y lo descarga.
    """
    resultados, conteo, primas, inconsistencias = _datos_tablero()

    # variable tipo bytes: archivo Excel generado por el servicio
    excel_bytes = crear_excel_resultados(
        resultados, conteo, primas, inconsistencias, FECHA_CORTE
    )

    return send_file(
        BytesIO(excel_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        download_name="control_polizas.xlsx",
        as_attachment=True,
    )



@polizas_bp.route("/aviso/<numero>")
def aviso(numero):
    """
    Ruta "/aviso/<numero>": devuelve el PDF del aviso para ver en el navegador.
    404 si la póliza no existe o está Vigente.
    """
    # variable tipo diccionario o None
    poliza = buscar_por_numero(numero)

    if poliza is None:
        abort(404)

    # condicional: si está vigente, no se genera aviso
    if poliza["estado"] == "Vigente":
        abort(404)

    # variable tipo bytes: PDF generado por el servicio
    pdf_bytes = crear_aviso_pdf(poliza)

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        download_name=f"aviso_{numero}.pdf",
    )


@polizas_bp.route("/descargar-avisos")
def descargar_avisos():
    """
    Ruta "/descargar-avisos": arma en memoria un .zip con los avisos de todas
    las pólizas Por vencer y Vencidas.
    """
    # variable tipo lista: resultados del modelo
    resultados = calcular_resultados()

    # variable tipo BytesIO: archivo zip en memoria
    memoria = BytesIO()

    with zipfile.ZipFile(memoria, "w") as archivo_zip:
        for r in resultados:
            # condicional: solo pólizas Por vencer o Vencidas
            if r["estado"] in ("Por vencer", "Vencida"):
                # variable tipo bytes: PDF del aviso
                pdf_bytes = crear_aviso_pdf(r)
                # variable tipo string: nombre del archivo dentro del zip
                nombre_archivo = f"aviso_{r['numero']}.pdf"
                archivo_zip.writestr(nombre_archivo, pdf_bytes)

    # volver al inicio del buffer para poder leerlo
    memoria.seek(0)

    return send_file(
        memoria,
        mimetype="application/zip",
        download_name="avisos.zip",
        as_attachment=True,
    )


@polizas_bp.app_errorhandler(404)
def pagina_no_encontrada(error):
    return render_template("error_404.html"), 404
