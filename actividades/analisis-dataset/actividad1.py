"""Actividad 1: el retrato del dataset."""

import pandas as pd

from comun import LIMITES, OBJETIVO, cargar_datos, es_posible

datos = cargar_datos()

print("=== Medio por clima (% de cada fila) ===")
print((pd.crosstab(datos["clima"], datos[OBJETIVO], normalize="index") * 100).round(2))

print("\n=== Medio por zona de destino (% de cada fila) ===")
print((pd.crosstab(datos["zona_destino"], datos[OBJETIVO], normalize="index") * 100).round(2))

print("\n=== Distancia, peso y volumen por medio ===")
print(datos.groupby(OBJETIVO)[["distancia_km", "peso_kg", "volumen_l"]].agg(["min", "median", "max"]))

print("\n=== Máximo observado contra la tabla LIMITES ===")
for medio, limite in LIMITES.items():
    maximos = datos.loc[datos[OBJETIVO] == medio, list(limite)].max()
    partes = [f"{col}: {maximos[col]:.2f} / {tope}" for col, tope in limite.items()]
    print(f"  {medio:<10} " + " | ".join(partes))

# ¿Alguna etiqueta rompe las reglas del negocio?
rompen = datos.apply(lambda fila: not es_posible(fila[OBJETIVO], fila), axis=1)
print(f"\nEtiquetas que rompen las reglas: {rompen.sum()}")

# Pregunta 2: bicicleta y periferia. La distancia lo explica.
periferia = datos[datos["zona_destino"] == "periferia"]
print("\n=== Periferia ===")
print(f"  Envíos: {len(periferia)}")
print(f"  Distancia mínima: {periferia['distancia_km'].min():.2f} km, mediana: {periferia['distancia_km'].median():.2f} km")
print(f"  Envíos a 7 km o menos (alcance de la bici): {(periferia['distancia_km'] <= 7).sum()}")
print(f"  Bicicletas a la periferia: {(periferia[OBJETIVO] == 'bicicleta').sum()}")

# Pregunta 4: camionetas en viajes de menos de 2 km.
cortas = datos[(datos[OBJETIVO] == "camioneta") & (datos["distancia_km"] < 2)].copy()
cortas["refrigerado_si"] = cortas["refrigerado"] == 1
cortas["no_cabe_en_moto"] = (cortas["peso_kg"] > LIMITES["moto"]["peso_kg"]) | (cortas["volumen_l"] > LIMITES["moto"]["volumen_l"])
cortas["razon_clara"] = cortas["refrigerado_si"] | cortas["no_cabe_en_moto"]
print("\n=== Camionetas a menos de 2 km ===")
print(f"  Total: {len(cortas)}")
print(f"  Refrigerados: {cortas['refrigerado_si'].sum()}")
print(f"  No caben en moto (peso o volumen): {cortas['no_cabe_en_moto'].sum()}")
print(f"  Con razón clara (cualquiera de las dos): {cortas['razon_clara'].sum()}")
sin_razon = cortas[~cortas["razon_clara"]]
print(f"  Sin razón clara: {len(sin_razon)}")
if len(sin_razon):
    print("  Cómo son las que no tienen razón clara:")
    print("   clima:", sin_razon["clima"].value_counts().to_dict())
    print("   fragil:", sin_razon["fragil"].value_counts().to_dict())
    print("   prioridad:", sin_razon["prioridad"].value_counts().to_dict())
    print("   valor > 20 000:", int((sin_razon["valor_declarado_mxn"] > 20000).sum()))
