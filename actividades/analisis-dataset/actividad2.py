"""Actividad 2: la hora y el dron."""

from pathlib import Path

import pandas as pd

from comun import OBJETIVO, cargar_datos, es_de_noche

datos = cargar_datos()
tabla = pd.crosstab(datos["hora_salida"], datos[OBJETIVO])

print("=== Envíos por hora y medio ===")
print(tabla)

sin_dron = tabla.index[tabla["dron"] == 0].tolist()
print(f"\nHoras sin ningún dron: {sin_dron}")
print(f"Drones a las 3:00: {tabla.loc[3, 'dron']}")

noche = datos["hora_salida"].apply(es_de_noche)
print(f"\nEnvíos de noche: {noche.sum()} ({noche.mean():.2%})")
print(f"Envíos de día:   {(~noche).sum()} ({(~noche).mean():.2%})")

print("\n=== Bicicleta y moto de las 19 a las 22 ===")
print(tabla.loc[19:22, ["bicicleta", "moto"]])

try:
    import matplotlib
    matplotlib.use("Agg")
    grafica = tabla.plot(kind="bar", stacked=True, figsize=(12, 6), title="Medio recomendado por hora de salida")
    destino = Path(__file__).with_name("hora_vs_medio.png")
    grafica.figure.savefig(destino, bbox_inches="tight")
    print(f"\nGráfica guardada en {destino.name}")
except ImportError:
    print("\n(Instala matplotlib para generar la gráfica)")
