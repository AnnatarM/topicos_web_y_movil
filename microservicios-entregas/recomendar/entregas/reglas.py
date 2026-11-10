# Límites que ningún modelo puede saltarse. El modelo aprende de ejemplos y
# a veces se equivoca; estas reglas vienen del negocio y no se negocian.
LIMITES = {
    "bicicleta": {"peso_kg": 8, "volumen_l": 40, "distancia_km": 7},
    "moto": {"peso_kg": 25, "volumen_l": 90, "distancia_km": 40},
    "camioneta": {"peso_kg": 1000, "volumen_l": 3000, "distancia_km": 1000},
    "dron": {"peso_kg": 2.5, "volumen_l": 12, "distancia_km": 15},
}


def es_posible(medio, paquete):
    limite = LIMITES[medio]
    if paquete["peso_kg"] > limite["peso_kg"]:
        return False
    if paquete["volumen_l"] > limite["volumen_l"]:
        return False
    if paquete["distancia_km"] > limite["distancia_km"]:
        return False
    if paquete["refrigerado"] and medio != "camioneta":
        return False
    noche = paquete["hora_salida"] >= 21 or paquete["hora_salida"] < 6
    if medio == "dron" and (
        paquete["clima"] != "despejado"
        or noche
        or paquete["zona_destino"] == "centro"
    ):
        return False
    if medio == "bicicleta" and paquete["zona_destino"] == "rural":
        return False
    return True
