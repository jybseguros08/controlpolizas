"""
Capa: models
Responsabilidad: reglas del negocio del proyecto control-polizas.
"""

from datetime import date

from models.datos import cargar_clientes, cargar_polizas

# variable tipo date: fecha de corte para calcular estados
FECHA_CORTE = date(2026, 11, 9)

# variable tipo int: días de aviso para considerar una póliza como "por vencer"
DIAS_AVISO = 30


def estado_poliza(hasta, fecha_corte=FECHA_CORTE):
    """
    Devuelve el estado de una póliza: "Vencida", "Por vencer", "Vigente" o "Sin fecha".
    """
    if hasta is None:
        return "Sin fecha"
    # variable tipo int: diferencia en días entre la fecha hasta y el corte
    dias = (hasta - fecha_corte).days
    if dias < 0:
        return "Vencida"
    elif 0 <= dias <= DIAS_AVISO:
        return "Por vencer"
    else:
        return "Vigente"


def calcular_resultados(fecha_corte=FECHA_CORTE):
    """
    Cruza cada póliza con el maestro por cédula, calcula días hasta vencer y
    estado, y devuelve una lista de diccionarios ordenada de menos a más días
    (lo urgente primero).
    """
    # variable tipo DataFrame: clientes del maestro
    clientes = cargar_clientes()
    # variable tipo lista: pólizas leídas de los PDF
    polizas = cargar_polizas()

    # variable tipo diccionario: cédula -> correo (búsqueda rápida)
    clientes_por_cedula = {}
    for _, fila in clientes.iterrows():
        cedula = str(fila["Cedula"]).strip()
        correo = fila.get("Correo", "")
        clientes_por_cedula[cedula] = correo

    # variable tipo lista: resultados finales
    resultados = []

    for poliza in polizas:
        cedula = poliza.get("cedula")
        # variable tipo string o None
        correo = None
        # variable tipo booleano
        en_maestro = False
        if cedula is not None and cedula in clientes_por_cedula:
            en_maestro = True
            correo = clientes_por_cedula[cedula]

        hasta = poliza.get("hasta")
        # variable tipo int o None
        dias_hasta_vencer = None
        if hasta is not None:
            dias_hasta_vencer = (hasta - fecha_corte).days

        # variable tipo string
        estado = estado_poliza(hasta, fecha_corte)

        # variable tipo diccionario con el resultado de una póliza
        resultado = {
            "archivo": poliza.get("archivo"),
            "aseguradora": poliza.get("aseguradora"),
            "numero": poliza.get("numero"),
            "ramo": poliza.get("ramo"),
            "nombre": poliza.get("nombre"),
            "cedula": poliza.get("cedula"),
            "correo": correo,
            "en_maestro": en_maestro,
            "desde": poliza.get("desde"),
            "hasta": poliza.get("hasta"),
            "prima": poliza.get("prima"),
            "pago": poliza.get("pago"),
            "suma": poliza.get("suma"),
            "asesor": poliza.get("asesor"),
            "dias_hasta_vencer": dias_hasta_vencer,
            "estado": estado,
        }
        resultados.append(resultado)

    # ordenamos de menos a más días; los None (sin fecha) van al final
    resultados.sort(key=lambda r: (r["dias_hasta_vencer"] is None, r["dias_hasta_vencer"] or 0))

    return resultados


def contar_por_estado(resultados):
    """
    Devuelve un diccionario con la cantidad de pólizas de cada estado.
    """
    # variable tipo diccionario: estado -> cantidad
    conteo = {}
    for r in resultados:
        estado = r["estado"]
        if estado in conteo:
            conteo[estado] += 1
        else:
            conteo[estado] = 1
    return conteo


def primas_por_aseguradora(resultados):
    """
    Devuelve un diccionario aseguradora -> suma de primas de pólizas no vencidas,
    ordenado de mayor a menor suma.
    """
    # variable tipo diccionario: aseguradora -> suma acumulada
    primas = {}
    for r in resultados:
        if r["estado"] != "Vencida" and r["prima"] is not None:
            aseguradora = r["aseguradora"]
            prima = r["prima"]
            if aseguradora in primas:
                primas[aseguradora] += prima
            else:
                primas[aseguradora] = prima

    # ordenamos de mayor a menor suma
    ordenada = sorted(primas.items(), key=lambda item: item[1], reverse=True)
    return dict(ordenada)


def buscar_inconsistencias(resultados):
    """
    Devuelve una lista de textos describiendo las inconsistencias encontradas.
    """
    # variable tipo lista de strings
    inconsistencias = []

    # obtenemos las cédulas del maestro para el cruce
    clientes = cargar_clientes()
    # variable tipo conjunto: cédulas del maestro
    cedulas_maestro = set()
    for _, fila in clientes.iterrows():
        cedulas_maestro.add(str(fila["Cedula"]).strip())

    # variable tipo conjunto: cédulas que tienen al menos una póliza
    cedulas_con_poliza = set()
    for r in resultados:
        if r["cedula"] is not None:
            cedulas_con_poliza.add(r["cedula"])

    # Tipo 1: cliente del maestro sin ninguna póliza
    for cedula in cedulas_maestro - cedulas_con_poliza:
        inconsistencias.append(f"Cliente del maestro sin ninguna póliza: cédula {cedula}")

    # recorremos resultados para tipos 2 y 3
    for r in resultados:
        # Tipo 2: póliza cuya cédula no está en el maestro
        if not r["en_maestro"] and r["cedula"] is not None:
            inconsistencias.append(
                f"Póliza con cédula no registrada en el maestro: {r['numero']} (cédula {r['cedula']})"
            )

        # Tipo 3: póliza sin prima
        if r["prima"] is None:
            inconsistencias.append(
                f"Póliza sin prima: {r['numero']} ({r['archivo']})"
            )

        # Tipo 3: póliza con fecha ilegible (hasta no se pudo leer)
        if r["hasta"] is None:
            inconsistencias.append(
                f"Póliza con fecha ilegible (hasta): {r['numero']} ({r['archivo']})"
            )

    return inconsistencias


def buscar_por_numero(numero):
    """
    Busca una póliza por su número en los resultados calculados.
    Devuelve el diccionario de la póliza o None si no existe.
    """
    resultados = calcular_resultados()
    for r in resultados:
        if r["numero"] == numero:
            return r
    return None
