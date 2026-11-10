from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from .reglas import es_posible

CARPETA_MODELOS = Path(__file__).resolve().parent / "modelo"

MODELOS = {
    "arbol": {
        "archivo": "modelo_medios.joblib",
        "nombre": "Árbol de decisión",
        "etiqueta_motivo": "árbol de decisión",
    },
    "bosque": {
        "archivo": "modelo_bosque.joblib",
        "nombre": "Random Forest",
        "etiqueta_motivo": "random forest",
    },
    "red": {
        "archivo": "modelo_red.joblib",
        "nombre": "Red neuronal (MLP)",
        "etiqueta_motivo": "red neuronal",
    },
}

CAMPOS_NUMERICOS = [
    "distancia_km", "peso_kg", "largo_cm", "ancho_cm", "alto_cm", "volumen_l",
    "fragil", "refrigerado", "valor_declarado_mxn", "hora_salida",
]
CAMPOS_TEXTO = ["prioridad", "zona_destino", "clima", "trafico"]
CAMPOS = CAMPOS_NUMERICOS + CAMPOS_TEXTO


@dataclass(frozen=True)
class Sugerencia:
    medio: str
    motivo: str


@dataclass
class ResultadoRecomendacion:
    medio: str
    motivo: str
    modelo: str
    modelo_nombre: str
    preferido_por_modelo: str
    corregido_por_reglas: bool
    ranking: list
    descartados: list
    proceso: list = field(default_factory=list)

    def a_dict(self):
        return asdict(self)


class RecomendadorIA(ABC):
    @abstractmethod
    def sugerir(self, paquete: dict) -> Sugerencia:
        pass

    @abstractmethod
    def explicar(self, paquete: dict) -> ResultadoRecomendacion:
        pass


class RecomendadorSklearn(RecomendadorIA):
    """Cualquier Pipeline de scikit-learn con predict_proba → Sugerencia + proceso."""

    def __init__(self, clave: str):
        if clave not in MODELOS:
            raise ValueError(f"modelo desconocido: {clave}")
        info = MODELOS[clave]
        ruta = CARPETA_MODELOS / info["archivo"]
        if not ruta.exists():
            raise FileNotFoundError(
                f"No encuentro {ruta}. Entrene el modelo y cópielo a entregas/modelo/."
            )
        self.clave = clave
        self.nombre = info["nombre"]
        self.etiqueta_motivo = info["etiqueta_motivo"]
        self._modelo = joblib.load(ruta)

    def sugerir(self, paquete):
        resultado = self.explicar(paquete)
        return Sugerencia(resultado.medio, resultado.motivo)

    def explicar(self, paquete):
        proceso = [
            {
                "paso": 1,
                "titulo": "Paquete recibido",
                "detalle": "La vista valida los 14 campos y se los pasa al adaptador.",
            },
            {
                "paso": 2,
                "titulo": f"El modelo ({self.nombre}) calcula probabilidades",
                "detalle": (
                    "predict_proba responde un porcentaje por cada medio. "
                    "Todavía no se elige nada definitivo."
                ),
            },
        ]

        datos = pd.DataFrame([paquete], columns=CAMPOS)
        probabilidades = self._modelo.predict_proba(datos)[0]
        ranking = sorted(
            [
                {"medio": medio, "confianza": round(float(p), 3)}
                for medio, p in zip(self._modelo.classes_, probabilidades)
            ],
            key=lambda item: -item["confianza"],
        )
        preferido = ranking[0]["medio"]

        proceso.append({
            "paso": 3,
            "titulo": "Ranking del modelo",
            "detalle": (
                f"Prefiere {preferido} "
                f"({ranking[0]['confianza']:.0%}). "
                "Los demás quedan como alternativas."
            ),
            "ranking": ranking,
        })

        descartados = []
        elegido = None
        confianza_elegida = 0.0
        for item in ranking:
            medio = item["medio"]
            if es_posible(medio, paquete):
                elegido = medio
                confianza_elegida = item["confianza"]
                break
            descartados.append({
                "medio": medio,
                "confianza": item["confianza"],
                "razon": "las reglas del negocio lo marcan como imposible",
            })

        proceso.append({
            "paso": 4,
            "titulo": "Las reglas filtran lo imposible",
            "detalle": (
                "Se recorre el ranking de más a menos probable y se descarta "
                "cualquier medio que rompa límites de peso, distancia, clima, "
                "hora o zona."
            ),
            "descartados": descartados,
        })

        if elegido is None:
            elegido = "camioneta"
            motivo = "ningún medio sugerido era posible"
            corregido = True
        else:
            motivo = f"{self.etiqueta_motivo}, confianza {confianza_elegida:.0%}"
            corregido = elegido != preferido
            if corregido:
                motivo += f"; se descartó {preferido} por las reglas del negocio"

        proceso.append({
            "paso": 5,
            "titulo": "Medio sugerido",
            "detalle": motivo,
            "medio": elegido,
            "corregido_por_reglas": corregido,
        })

        proceso.append({
            "paso": 6,
            "titulo": "La estrategia del medio arma el plan",
            "detalle": (
                f'crear_medio("{elegido}").planear(paquete) calcula minutos '
                "e indicación. La vista solo ensambla la respuesta JSON."
            ),
        })

        return ResultadoRecomendacion(
            medio=elegido,
            motivo=motivo,
            modelo=self.clave,
            modelo_nombre=self.nombre,
            preferido_por_modelo=preferido,
            corregido_por_reglas=corregido,
            ranking=ranking,
            descartados=descartados,
            proceso=proceso,
        )


def modelos_disponibles():
    disponibles = []
    for clave, info in MODELOS.items():
        ruta = CARPETA_MODELOS / info["archivo"]
        disponibles.append({
            "id": clave,
            "nombre": info["nombre"],
            "archivo": info["archivo"],
            "listo": ruta.exists(),
        })
    return disponibles


@lru_cache(maxsize=8)
def obtener_recomendador(clave: str = "arbol") -> RecomendadorIA:
    return RecomendadorSklearn(clave or "arbol")
