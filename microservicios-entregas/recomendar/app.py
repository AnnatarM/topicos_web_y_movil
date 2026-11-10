from math import isfinite
from flask import Flask, jsonify, request
from entregas.recomendador import CAMPOS, CAMPOS_NUMERICOS, CAMPOS_TEXTO, obtener_recomendador
from entregas.reglas import es_posible

app = Flask(__name__)
recomendador = obtener_recomendador("arbol")

@app.get("/salud")
def salud():
    return jsonify(servicio="recomendar", estado="ok")

@app.post("/sugerir")
def sugerir():
    cuerpo = request.get_json(silent=True)
    if not isinstance(cuerpo, dict):
        return jsonify(error="Se requiere un objeto JSON"), 400
    faltantes = [c for c in CAMPOS if c not in cuerpo]
    if faltantes:
        return jsonify(error="Faltan campos", campos=faltantes), 400
    paquete = {c: cuerpo[c] for c in CAMPOS}
    for campo in CAMPOS_NUMERICOS:
        try:
            paquete[campo] = float(paquete[campo])
            if not isfinite(paquete[campo]) or paquete[campo] < 0:
                raise ValueError()
        except (TypeError, ValueError, OverflowError):
            return jsonify(error=f"{campo} debe ser un número finito no negativo"), 400
    if any(paquete[c] not in (0, 1) for c in ("fragil", "refrigerado")):
        return jsonify(error="fragil y refrigerado deben ser 0 o 1"), 400
    if not 0 <= paquete["hora_salida"] < 24:
        return jsonify(error="hora_salida debe estar entre 0 y menos de 24"), 400
    if any(not isinstance(paquete[c], str) or not paquete[c].strip() for c in CAMPOS_TEXTO):
        return jsonify(error="Los campos de texto deben ser cadenas no vacías"), 400
    try:
        resultado = recomendador.explicar(paquete)
    except (ValueError, TypeError):
        return jsonify(error="Valores incompatibles con el modelo"), 400
    if not es_posible(resultado.medio, paquete):
        return jsonify(error="Ningún medio cumple las reglas"), 422
    # El proceso original menciona una vista y un plan del monolito.
    # Exponemos solo el resultado pertinente a este servicio.
    return jsonify(
        servicio="recomendar", medio=resultado.medio, motivo=resultado.motivo,
        preferido_por_modelo=resultado.preferido_por_modelo,
        corregido_por_reglas=resultado.corregido_por_reglas,
        ranking=resultado.ranking, descartados=resultado.descartados,
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002, debug=False)
