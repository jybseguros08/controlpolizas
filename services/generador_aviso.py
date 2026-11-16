"""
Capa: services
Responsabilidad: generar avisos de renovación en PDF con fpdf2.
"""

from datetime import date

from fpdf import FPDF


def _to_latin1(texto):
    """
    Convierte texto a latin-1 para que las tildes y eñes no fallen con Helvetica.
    """
    return str(texto).encode("latin-1", errors="replace").decode("latin-1")


def crear_aviso_pdf(poliza):
    """
    Crea un aviso de renovación en PDF (A4 vertical) y lo devuelve en bytes.

    Recibe un diccionario de póliza con claves: nombre, estado, hasta,
    dias_hasta_vencer, numero, aseguradora, ramo, cedula, desde, prima, pago.
    """
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    # -------- Banda superior roja (#AE1800) --------
    pdf.set_fill_color(174, 24, 0)  # rojo #AE1800
    pdf.set_text_color(255, 255, 255)  # blanco
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, _to_latin1("Corredora de Seguros Horizonte"), ln=True, align="C", fill=True)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, _to_latin1("Aviso de renovación de póliza"), ln=True, align="C", fill=True)
    pdf.ln(10)

    # -------- Saludo --------
    pdf.set_text_color(0, 0, 0)  # negro #201E1D
    pdf.set_font("Helvetica", size=12)
    nombre = poliza.get("nombre") or "Cliente"
    pdf.cell(0, 8, _to_latin1(f"Estimado(a) {nombre}:"), ln=True)
    pdf.ln(5)

    # -------- Párrafo según estado --------
    estado = poliza.get("estado", "Vigente")
    hasta = poliza.get("hasta")
    dias = poliza.get("dias_hasta_vencer")

    if estado == "Vencida":
        fecha_str = hasta.strftime("%d/%m/%Y") if isinstance(hasta, date) else "fecha desconocida"
        pdf.multi_cell(0, 8, _to_latin1(f"Su póliza venció el {fecha_str}. Por favor, renueve lo antes posible."))
    elif estado == "Por vencer":
        fecha_str = hasta.strftime("%d/%m/%Y") if isinstance(hasta, date) else "fecha desconocida"
        pdf.multi_cell(0, 8, _to_latin1(
            f"Su póliza vence el {fecha_str} (en {dias} días). Su asesor se comunicará con usted."
        ))
    else:
        pdf.multi_cell(0, 8, _to_latin1("Su póliza está vigente. Este aviso es solo informativo."))

    pdf.ln(8)

    # -------- Tabla de datos --------
    col_etiqueta = 45
    col_valor = 105

    def _fecha_str(fecha):
        if isinstance(fecha, date):
            return fecha.strftime("%d/%m/%Y")
        return "-"

    def _prima_str(prima):
        if prima is None:
            return "No registrada"
        return f"CRC {prima:,.2f}"

    filas = [
        ("Número de póliza", poliza.get("numero", "-")),
        ("Aseguradora", poliza.get("aseguradora", "-")),
        ("Ramo", poliza.get("ramo", "-")),
        ("Cédula", poliza.get("cedula", "-")),
        ("Vigencia", f"{_fecha_str(poliza.get('desde'))} al {_fecha_str(poliza.get('hasta'))}"),
        ("Prima anual", _prima_str(poliza.get("prima"))),
        ("Forma de pago", poliza.get("pago", "-")),
    ]

    pdf.set_font("Helvetica", "B", 10)
    for etiqueta, valor in filas:
        pdf.set_fill_color(243, 242, 242)  # gris claro #F3F2F2
        pdf.cell(col_etiqueta, 8, _to_latin1(etiqueta), border=1, fill=True)
        pdf.set_fill_color(255, 255, 255)  # blanco
        pdf.cell(col_valor, 8, _to_latin1(str(valor)), border=1, fill=True)
        pdf.ln()

    pdf.ln(10)

    # -------- Pie de página gris --------
    pdf.set_y(-20)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(128, 128, 128)  # gris
    pdf.cell(0, 6, _to_latin1("Documento ficticio con fines académicos. No tiene validez legal."), align="C")

    # -------- Devolver bytes --------
    salida = pdf.output(dest="S")
    if isinstance(salida, str):
        return salida.encode("latin-1")
    return salida
