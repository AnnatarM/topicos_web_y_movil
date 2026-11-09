"""Actividad 4: ¿qué columnas usa de verdad el modelo?"""

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier

from comun import CATEGORICAS, NUMERICAS, cargar_datos, cargar_modelo, separar

modelo = cargar_modelo()
nombres = modelo.named_steps["preparacion"].get_feature_names_out()
importancias = pd.Series(modelo.named_steps["arbol"].feature_importances_, index=nombres)

# El one-hot parte las categóricas en varias columnas; se suman para tener una por columna original.
original = importancias.groupby(lambda n: next(c for c in NUMERICAS + CATEGORICAS if n.split("__", 1)[1].startswith(c))).sum()
print("=== Importancia por columna original ===")
print(original.sort_values(ascending=False).round(4).to_string())


def entrenar_sin(columna, x_entreno, y_entreno, x_prueba, y_prueba):
    numericas = [c for c in NUMERICAS if c != columna]
    categoricas = [c for c in CATEGORICAS if c != columna]
    arbol = Pipeline([
        ("preparacion", ColumnTransformer([
            ("numericas", "passthrough", numericas),
            ("categoricas", OneHotEncoder(handle_unknown="ignore"), categoricas),
        ])),
        ("arbol", DecisionTreeClassifier(max_depth=8, min_samples_leaf=5, random_state=42)),
    ])
    arbol.fit(x_entreno[numericas + categoricas], y_entreno)
    return (arbol.predict(x_prueba[numericas + categoricas]) == y_prueba).mean()


x_entreno, x_prueba, y_entreno, y_prueba = separar(cargar_datos())
base = (modelo.predict(x_prueba) == y_prueba).mean()
print(f"\nExactitud con las 14 columnas: {base:.4f}")

print("\n=== Exactitud al quitar cada columna ===")
resultados = {c: entrenar_sin(c, x_entreno, y_entreno, x_prueba, y_prueba) for c in NUMERICAS + CATEGORICAS}
tabla = pd.DataFrame({"exactitud": resultados})
tabla["cambio"] = tabla["exactitud"] - base
print(tabla.sort_values("cambio").round(4).to_string())
