"""Piezas compartidas por las cinco actividades.

Carga el dataset y el modelo desde la carpeta dataset-medios/ y separa los
datos igual que entrenar_arbol.py, para analizar siempre los mismos 2 000
envíos de prueba.
"""

import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split

CARPETA_DATASET = Path(__file__).resolve().parents[2] / "dataset-medios"
sys.path.insert(0, str(CARPETA_DATASET))

from entrenar_arbol import CATEGORICAS, NUMERICAS, OBJETIVO  # noqa: E402
from usar_modelo import LIMITES, es_posible  # noqa: E402

COLUMNAS = NUMERICAS + CATEGORICAS


def cargar_datos():
    return pd.read_csv(CARPETA_DATASET / "envios_medios.csv")


def separar(datos, semilla=42):
    """Misma separación que entrenar_arbol.py: 20 % de prueba, estratificada."""
    return train_test_split(
        datos[COLUMNAS], datos[OBJETIVO], test_size=0.2, stratify=datos[OBJETIVO], random_state=semilla
    )


def cargar_modelo():
    ruta = CARPETA_DATASET / "modelo_medios.joblib"
    if not ruta.exists():
        sys.exit("Falta modelo_medios.joblib. Entrénalo con: python dataset-medios/entrenar_arbol.py")
    return joblib.load(ruta)


def es_de_noche(hora):
    return hora >= 21 or hora < 6
