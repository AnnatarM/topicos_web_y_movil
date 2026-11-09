"""Actividad 5: el dron es minoría, ¿hay que balancear el dataset?"""

import sys

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier

from comun import CARPETA_DATASET, CATEGORICAS, COLUMNAS, NUMERICAS, OBJETIVO, cargar_datos, es_posible, separar

datos = cargar_datos()
x_entreno, x_prueba, y_entreno, y_prueba = separar(datos)


def nuevo_arbol(class_weight=None):
    return Pipeline([
        ("preparacion", ColumnTransformer([
            ("numericas", "passthrough", NUMERICAS),
            ("categoricas", OneHotEncoder(handle_unknown="ignore"), CATEGORICAS),
        ])),
        ("arbol", DecisionTreeClassifier(max_depth=8, min_samples_leaf=5, random_state=42,
                                         class_weight=class_weight)),
    ])


def evaluar(nombre, x_ent, y_ent, x_pru=x_prueba, y_pru=y_prueba, class_weight=None):
    arbol = nuevo_arbol(class_weight).fit(x_ent, y_ent)
    pred = arbol.predict(x_pru)
    imposibles = sum(not es_posible(m, fila) for m, (_, fila) in zip(pred, x_pru.iterrows()))
    return {
        "Estrategia": nombre,
        "Envíos de entrenamiento": len(y_ent),
        "Exactitud": round((pred == y_pru).mean(), 3),
        "Precision dron": round(precision_score(y_pru, pred, labels=["dron"], average="macro", zero_division=0), 3),
        "Recall dron": round(recall_score(y_pru, pred, labels=["dron"], average="macro", zero_division=0), 3),
        "Veces que predice dron": int((pred == "dron").sum()),
        "Drones reales en la prueba": int((y_pru == "dron").sum()),
        "Sugerencias imposibles": imposibles,
    }


entreno = x_entreno.assign(**{OBJETIVO: y_entreno})
drones = entreno[entreno[OBJETIVO] == "dron"]
otros = entreno[entreno[OBJETIVO] != "dron"]
n_dron = len(drones)

# Parte A: modelos "tontos" de referencia.
print("=== Parte A: referencias ===")
print(f"  Nunca dice dron y acierta todo lo demás: {(y_prueba != 'dron').mean():.1%}")
print(f"  Siempre dice moto: {(y_prueba == 'moto').mean():.1%}\n")

filas = [evaluar("Sin balancear", x_entreno, y_entreno)]

# 1. Submuestreo: cada clase se recorta al número de drones.
sub = pd.concat([
    grupo.sample(n=min(len(grupo), n_dron), random_state=42) for _, grupo in entreno.groupby(OBJETIVO)
])
filas.append(evaluar("Submuestreo (quitar ejemplos)", sub[COLUMNAS], sub[OBJETIVO]))

# 2. Sobremuestreo: se repiten drones hasta igualar a la clase mayoritaria.
mayor = entreno[OBJETIVO].value_counts().max()
sobre = pd.concat([otros, drones.sample(n=mayor, replace=True, random_state=42)])
filas.append(evaluar("Sobremuestreo (repetir drones)", sobre[COLUMNAS], sobre[OBJETIVO]))

# 3. class_weight="balanced": equivocarse con un dron cuesta más.
filas.append(evaluar("class_weight='balanced'", x_entreno, y_entreno, class_weight="balanced"))

# 4. Drones nuevos del generador con otra semilla (sin tocar la prueba).
sys.path.insert(0, str(CARPETA_DATASET))
import random  # noqa: E402

import generar_dataset as g  # noqa: E402

rng = random.Random(2026)
nuevos = []
while len(nuevos) < mayor - n_dron:
    paquete = g.generar_paquete(rng)
    if g.recomendar(paquete, rng, 0.03) == "dron":
        nuevos.append({**paquete, OBJETIVO: "dron"})
extra = pd.concat([entreno, pd.DataFrame(nuevos)])
filas.append(evaluar("Drones nuevos del generador", extra[COLUMNAS], extra[OBJETIVO]))

# Trampa a propósito: repetir drones ANTES de separar.
mayor_total = datos[OBJETIVO].value_counts().max()
todos_drones = datos[datos[OBJETIVO] == "dron"]
trampa = pd.concat([datos[datos[OBJETIVO] != "dron"],
                    todos_drones.sample(n=mayor_total, replace=True, random_state=42)])
xt_ent, xt_pru, yt_ent, yt_pru = separar(trampa)
filas.append(evaluar("TRAMPA: repetir drones antes de separar", xt_ent, yt_ent, xt_pru, yt_pru))

tabla = pd.DataFrame(filas).set_index("Estrategia")
pd.set_option("display.width", 200)
print("=== Parte B: estrategias (prueba: los mismos 2 000 envíos, salvo la trampa) ===")
print(tabla.to_string())

# En la trampa, ¿cuántos drones de la prueba son copias exactas de uno que el modelo vio al entrenar?
claves_entreno = set(map(tuple, xt_ent[yt_ent == "dron"].values.tolist()))
copias = sum(tuple(f) in claves_entreno for f in xt_pru[yt_pru == "dron"].values.tolist())
print(f"\nTrampa: {copias} de {(yt_pru == 'dron').sum()} drones de la prueba son copias exactas de uno del entrenamiento.")
