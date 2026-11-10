import os
from uuid import uuid4
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
RECOMENDAR_URL = os.environ.get("RECOMENDAR_URL", "http://recomendar:8002").rstrip("/")
pedidos = []

@app.get("/salud")
def salud():
    return jsonify(servicio="pedidos", estado="ok", recomendar_url=RECOMENDAR_URL)

@app.post("/pedidos")
def crear_pedido():
    paquete = request.get_json(silent=True)
    if not isinstance(paquete, dict) or not paquete:
        return jsonify(error="Se requiere un objeto JSON no vacío"), 400
    try:
        respuesta = requests.post(f"{RECOMENDAR_URL}/sugerir", json=paquete, timeout=(2, 5))
        if respuesta.status_code in (400, 422):
            return jsonify(respuesta.json()), respuesta.status_code
        respuesta.raise_for_status()
        sugerencia = respuesta.json()
        if not isinstance(sugerencia, dict):
            raise ValueError("Respuesta inválida")
        medio, motivo = sugerencia["medio"], sugerencia["motivo"]
        if not isinstance(medio, str) or not isinstance(motivo, str):
            raise ValueError("Respuesta inválida")
    except (requests.RequestException, ValueError, KeyError):
        return jsonify(
            servicio="pedidos", error="Recomendar no está disponible",
            pedido_creado=False,
            medio="camioneta",
            motivo="Alternativa por defecto pendiente de validación; no despachar automáticamente",
            plan_b="Reintentar cuando Recomendar se recupere; no se creó un pedido",
        ), 503
    pedido = dict(folio=uuid4().hex, medio=medio, motivo=motivo, paquete=paquete)
    pedidos.append(pedido)
    return jsonify(servicio="pedidos", folio=pedido["folio"], medio=medio, motivo=motivo), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=False)
