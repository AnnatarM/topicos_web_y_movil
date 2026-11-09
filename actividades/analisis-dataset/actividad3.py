"""Actividad 3: anatomía de los errores."""

from comun import LIMITES, OBJETIVO, cargar_datos, cargar_modelo, es_de_noche, es_posible, separar

datos = cargar_datos()
_, x_prueba, _, y_prueba = separar(datos)
modelo = cargar_modelo()

analisis = x_prueba.assign(real=y_prueba, predicho=modelo.predict(x_prueba))
errores = analisis[analisis["real"] != analisis["predicho"]]

print(f"Envíos de prueba: {len(analisis)}")
print(f"Errores: {len(errores)} ({len(errores) / len(analisis):.1%})")

print("\n=== Confusiones más frecuentes ===")
print(errores.groupby(["real", "predicho"]).size().sort_values(ascending=False).head(5).to_string())

bici_camioneta = errores[
    ((errores["real"] == "bicicleta") & (errores["predicho"] == "camioneta"))
    | ((errores["real"] == "camioneta") & (errores["predicho"] == "bicicleta"))
]
print(f"\nConfusiones entre bicicleta y camioneta: {len(bici_camioneta)}")

# Pregunta 2: era moto y el modelo dijo dron.
moto_dron = errores[(errores["real"] == "moto") & (errores["predicho"] == "dron")].copy()
moto_dron["noche"] = moto_dron["hora_salida"].apply(es_de_noche)
moto_dron["dron_posible"] = moto_dron.apply(lambda f: es_posible("dron", f), axis=1)
print("\n=== Moto que el modelo mandó a dron ===")
print(f"  Total: {len(moto_dron)}")
print(f"  De noche: {moto_dron['noche'].sum()}")
print(f"  Las reglas los corrigen (dron imposible): {(~moto_dron['dron_posible']).sum()}")
print(f"  Las reglas NO los corrigen (dron posible): {moto_dron['dron_posible'].sum()}")
no_corregidos = moto_dron[moto_dron["dron_posible"]]
if len(no_corregidos):
    print("  Cómo son los que las reglas no corrigen:")
    print(no_corregidos[["distancia_km", "peso_kg", "volumen_l", "fragil", "valor_declarado_mxn",
                         "prioridad", "zona_destino", "hora_salida", "trafico"]].to_string())

# Pregunta 3: era moto y el modelo dijo bicicleta.
moto_bici = errores[(errores["real"] == "moto") & (errores["predicho"] == "bicicleta")]
bici_bien = analisis[(analisis["real"] == "bicicleta") & (analisis["predicho"] == "bicicleta")]
print("\n=== Moto que el modelo mandó a bicicleta ===")
print(f"  Total: {len(moto_bici)}")
print(f"  A más de 6 km (cerca del límite de {LIMITES['bicicleta']['distancia_km']} km): {(moto_bici['distancia_km'] > 6).sum()}")
columnas = ["distancia_km", "peso_kg", "volumen_l", "fragil", "valor_declarado_mxn", "hora_salida"]
comparacion = {
    "moto→bici (error)": moto_bici[columnas].mean(),
    "bici acertada": bici_bien[columnas].mean(),
}
import pandas as pd  # noqa: E402
print("  Promedios comparados:")
print(pd.DataFrame(comparacion).round(2).to_string())
for col in ["prioridad", "clima", "trafico"]:
    print(f"  {col}:")
    print(pd.DataFrame({
        "moto→bici": moto_bici[col].value_counts(normalize=True),
        "bici acertada": bici_bien[col].value_counts(normalize=True),
    }).fillna(0).round(2).to_string())

# ¿Qué pasa con otro random_state?
print("\n=== Errores con otra separación (random_state=7) ===")
_, x_otra, _, y_otra = separar(datos, semilla=7)
print(f"  Errores: {(modelo.predict(x_otra) != y_otra).sum()} de {len(y_otra)}")
print("  (Ojo: con otra semilla parte de esa prueba la vio el modelo al entrenar.)")
