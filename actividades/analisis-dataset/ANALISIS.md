# Análisis del dataset de medios de transporte

**Alumno:** Annatar Armando Murillo Rivera
**Matrícula:** 22121283

## Cómo correr las actividades

Desde la raíz del repositorio:

```bash
pip install pandas scikit-learn joblib matplotlib
python dataset-medios/entrenar_arbol.py      # solo si falta modelo_medios.joblib (córrelo dentro de dataset-medios/)
python actividades/analisis-dataset/actividad1.py
python actividades/analisis-dataset/actividad2.py
python actividades/analisis-dataset/actividad3.py
python actividades/analisis-dataset/actividad4.py
python actividades/analisis-dataset/actividad5.py
```

`comun.py` carga el CSV y el modelo desde `dataset-medios/` y separa los datos igual que `entrenar_arbol.py` (`test_size=0.2`, `stratify`, `random_state=42`), así que todas las actividades analizan los mismos 2 000 envíos de prueba.

---

## Actividad 1 — El retrato del dataset

### Predicción

- Con lluvia va a dominar la camioneta, porque es el único medio cerrado.
- En el centro va a dominar la bicicleta, porque son distancias cortas y hay tráfico.
- La bicicleta no va a pasar de unos 7 km.
- Sí habrá algunas etiquetas que rompan las reglas, porque el dataset tiene ruido.

### Resultado

| Clima | Bicicleta | Camioneta | Dron | Moto |
|---|---|---|---|---|
| despejado | 32.84 % | 16.57 % | 13.52 % | 37.07 % |
| lluvia | 8.49 % | 16.68 % | 0.00 % | **74.83 %** |
| viento_fuerte | 31.69 % | 18.41 % | 0.00 % | 49.90 % |

| Zona | Bicicleta | Camioneta | Dron | Moto |
|---|---|---|---|---|
| centro | **58.45 %** | 13.52 % | 0.00 % | 28.03 % |
| periferia | 0.88 % | 13.98 % | 12.61 % | 72.53 % |
| residencial | 26.20 % | 14.62 % | 17.30 % | 41.89 % |
| rural | 0.00 % | 40.80 % | 0.00 % | 59.20 % |

Máximos observados contra la tabla `LIMITES`:

| Medio | Peso máx. (dato / límite) | Volumen máx. | Distancia máx. |
|---|---|---|---|
| bicicleta | 7.99 / 8 | 39.70 / 40 | 7.00 / 7 |
| moto | 24.93 / 25 | 89.99 / 90 | 39.90 / 40 |
| dron | 2.50 / 2.5 | 11.98 / 12 | 14.99 / 15 |
| camioneta | 80.00 / 1000 | 400.57 / 3000 | 59.12 / 1000 |

Etiquetas que rompen las reglas (revisadas con `es_posible`): **0**.

### Comparación

- **Lluvia:** me equivoqué. Con lluvia domina la moto (74.83 %), no la camioneta (16.68 %). No consideré que la lluvia solo penaliza a la moto (+15 y 15 % más lenta), mientras que la camioneta sigue siendo la más cara por tarifa y por kilómetro. Para la mayoría de los paquetes, la moto mojada sigue saliendo más barata.
- **Centro:** acerté, domina la bicicleta con 58.45 %.
- **Distancia de la bici:** acerté, el máximo es exactamente 7.00 km.
- **Reglas rotas:** me equivoqué, hay 0. El ruido del generador solo cambia la etiqueta por *otro medio posible*, así que nunca produce una etiqueta imposible.

### Preguntas

1. **¿Dónde nunca aparece el dron?** En el centro, con lluvia, con viento fuerte y en la zona rural. Los tres primeros los explica directamente la regla del dron en `es_posible`: `clima != "despejado"` o `zona_destino == "centro"` lo descartan. La zona rural no tiene una regla propia: sus distancias empiezan en 15 km (`DISTANCIA_POR_ZONA["rural"] = (15, 60)`) y el dron tiene un límite de 15 km, así que el límite de distancia lo deja fuera.
2. **¿Por qué la bici casi no va a la periferia?** Por `distancia_km`. En la periferia la distancia mínima es de 5.23 km y la mediana de 15.75 km; de 2 046 envíos, solo 46 están a 7 km o menos. Por eso solo hay 18 bicicletas.
3. **¿Qué límites se adivinan con los datos?** Los de bicicleta, moto y dron: sus máximos quedan pegados al límite (por ejemplo, 24.93 contra 25 kg de la moto). El de la camioneta no se puede adivinar: su máximo (80 kg, 400 L) es el tope con el que se generaron los paquetes, no el límite del vehículo (1000 kg). Las reglas que no son de "máximo", como "el dron no vuela de noche" o "solo la camioneta lleva refrigerados", tampoco se ven en un `max`; hay que cruzar columnas.
4. **Camionetas a menos de 2 km:** hay **107**. De ellas, **95** tienen una razón clara: 36 son refrigeradas y 61 no caben en una moto por peso o volumen. Las **12** restantes podrían ir en otro medio. Mi explicación: 6 son frágiles (la fragilidad penaliza +50 a la moto y +30 a la bici, y 0 a la camioneta), 6 tienen lluvia o viento, y además está el ruido del 8 % en el costo y el 3 % de etiquetas cambiadas.

### Para pensar

Solo con el CSV podría reconstruir los límites duros de peso, volumen y distancia, y las prohibiciones claras como "dron nunca con lluvia". No podría reconstruir con seguridad las reglas que dependen de combinar columnas ni las que casi no tienen ejemplos. El caso de la zona rural lo muestra: los datos sugieren "el dron no va a lo rural", pero la regla real es "el dron no pasa de 15 km". Si un modelo "descubre" las reglas, puede aprender una correlación accidental en lugar de la regla real, y fallar en cuanto aparezca un envío rural de 14 km. Por eso las reglas del negocio deben escribirse a mano y el modelo solo debe elegir entre los medios posibles.

---

## Actividad 2 — La hora y el dron

### Predicción

- A las 3:00 van a salir 0 drones, porque la regla prohíbe volar de noche.
- Alrededor del 15 % de los envíos saldrá de noche.

### Resultado

- Horas sin ningún dron: **0, 1, 2, 3, 4, 5, 21, 22 y 23**. Drones a las 3:00: **0**.
- Envíos de noche: **1 053 (10.53 %)**. Envíos de día: **8 947 (89.47 %)**.

| Hora | Bicicleta | Moto |
|---|---|---|
| 19 | 166 | 199 |
| 20 | 115 | 160 |
| 21 | 20 | 240 |
| 22 | 5 | 116 |

La gráfica completa se guarda en `hora_vs_medio.png` al correr `actividad2.py`.

### Comparación

Acerté con los drones. Con la noche me pasé: es el 10.53 % y no el 15 %. Los pesos de horas del generador le dan entre 1 y 2 a las horas de madrugada, contra 9 a las del día.

### Preguntas

1. **¿En qué horas no hay dron?** De las 21:00 a las 5:59. Coincide exactamente con la regla `noche = hora_salida >= 21 or hora_salida < 6`.
2. **Noche contra día:** hay 1 053 envíos de noche contra 8 947 de día, unas 8.5 veces menos. El árbol tiene pocos ejemplos para aprender cómo se decide de noche, así que es más fácil que se equivoque en esas horas. La actividad 3 lo confirma: 26 de los 29 errores de "moto mandada a dron" son de noche.
3. **Bicicletas de las 20 a las 21:** bajan de 115 a 20 y las motos suben de 160 a 240. El `README.md` lo explica en *Riesgos*: "La bicicleta de noche y con lluvia también recibe penalizaciones". A partir de las 21:00 es de noche y la bici recibe +30 de penalización; la moto se queda con esos envíos.
4. **¿Por qué le cuesta al árbol?** La noche no es un solo rango continuo: son dos pedazos en los extremos del día (0 a 5 y 21 a 23). Una pregunta del tipo "hora ≤ X" solo corta en un punto, así que necesita como mínimo **dos preguntas**: `hora ≤ 5` y `hora > 20`.

### Para pensar

Agregaría una columna `es_noche = 1 si hora_salida >= 21 o hora_salida < 6, si no 0`. Con ella, el árbol puede separar la noche con una sola pregunta. Para comprobar que ayudó, volvería a entrenar el árbol con la columna nueva y lo mediría con los mismos 2 000 envíos de prueba. Me fijaría en dos números: que la exactitud total no baje (92.1 % actual) y que bajen los errores "moto → dron" de noche (hoy son 26). También revisaría que `es_noche` aparezca con importancia mayor que cero.

---

## Actividad 3 — Anatomía de los errores

### Predicción

- La confusión más frecuente será entre bicicleta y moto, porque se traslapan en distancias cortas.
- No creo que confunda una bicicleta con una camioneta, porque son medios muy distintos.

### Resultado

- Errores: **158 de 2 000 (7.9 %)**.

| Real | Predicho | Veces |
|---|---|---|
| moto | bicicleta | 46 |
| camioneta | moto | 32 |
| moto | dron | 29 |
| bicicleta | moto | 20 |
| dron | bicicleta | 18 |

- Confusiones entre bicicleta y camioneta: **9**.

### Comparación

Acerté en que la confusión principal es moto–bicicleta, pero me equivoqué con bicicleta–camioneta: sí pasa, 9 veces (todas de camioneta real que el modelo mandó a bici). Revisando, son paquetes ligeros (0.6 a 4.9 kg), cortos (1.7 a 5.1 km), casi todos al centro y con clima despejado; solo 3 son frágiles. Para el modelo son bicicletas típicas. Lo más probable es que la etiqueta "camioneta" venga del ruido del generador (el 3 % de etiquetas cambiadas por otro medio posible).

### Preguntas

1. **Errores más frecuentes:** las tres confusiones principales son moto → bicicleta (46), camioneta → moto (32) y moto → dron (29). Casi todas son entre medios "vecinos", que pueden llevar el mismo paquete. El modelo sí aprendió bien los límites duros; donde falla es en elegir entre dos medios que ambos son posibles, que es justo donde el generador mete ruido.
2. **Moto mandada a dron:** son **29**. **26 son de noche** y las reglas del negocio las corrigen todas, porque el dron no puede volar de noche. Las **3** que las reglas no corrigen tienen esto en común: son de zona residencial, en la tarde (13, 17 y 18 h), con **tráfico alto**, paquetes ligeros (0.9 a 1.7 kg) y distancias de 7 a 12 km. Son casos donde el dron sí es posible y probablemente conviene, pero la etiqueta dice moto por el ruido del costo.
3. **Moto mandada a bicicleta:** son **46** y solo **5** están a más de 6 km, así que la distancia no lo explica. Lo que los distingue de las bicicletas que el modelo sí acertó es la **prioridad** y el **clima**: el 48 % son `mismo_dia` (contra 12 % en las bicis acertadas) y el 24 % son con lluvia (contra 2 %). Con urgencia alta, la moto gana por velocidad, y con lluvia la bici se penaliza.

**¿Qué pasa con otro `random_state`?** Con `random_state=7` salen 140 errores en lugar de 158, pero ese número es engañoso: el modelo se entrenó con la separación de `random_state=42`, así que parte de esa "prueba" ya la vio al entrenar. Para analizar errores reales hay que usar exactamente la misma separación que en el entrenamiento.

### Para pensar

Arreglaría **moto → bicicleta**: es el error más frecuente (46) y las reglas del negocio no lo corrigen, porque la bicicleta sí es posible. Además, mandar una bici con lluvia y prioridad `mismo_dia` significa entregar tarde y en peores condiciones. Lo arreglaría en el **modelo**: el árbol de profundidad 8 no alcanza a combinar bien prioridad + clima + distancia. Probaría un árbol más profundo o el Random Forest de `entrenar_modelo.py`. Los errores "moto → dron" de noche no los tocaría, porque las reglas ya los corrigen.

---

## Actividad 4 — ¿Qué columnas usa de verdad el modelo?

### Predicción

Orden que esperaba, de más a menos importante: `distancia_km`, `peso_kg`, `volumen_l`, `refrigerado`, `clima`, `hora_salida`, `prioridad`, `fragil`, `zona_destino`, `trafico`, `valor_declarado_mxn`, `largo_cm`, `ancho_cm` y `alto_cm`. Creía que las tres medidas no se usarían, porque el volumen ya las resume.

### Resultado

| Columna | Importancia | Exactitud sin ella | Cambio |
|---|---|---|---|
| distancia_km | 0.3220 | 0.7930 | −0.1280 |
| volumen_l | 0.1929 | 0.9060 | −0.0150 |
| clima | 0.1438 | 0.8445 | −0.0765 |
| refrigerado | 0.1313 | 0.8785 | −0.0425 |
| peso_kg | 0.1263 | 0.9040 | −0.0170 |
| hora_salida | 0.0587 | 0.8910 | −0.0300 |
| fragil | 0.0199 | 0.9155 | −0.0055 |
| prioridad | 0.0031 | 0.9215 | +0.0005 |
| valor_declarado_mxn | 0.0007 | 0.9210 | 0.0000 |
| ancho_cm | 0.0007 | 0.9205 | −0.0005 |
| largo_cm | 0.0003 | 0.9205 | −0.0005 |
| alto_cm | 0.0003 | 0.9205 | −0.0005 |
| trafico | 0.0002 | 0.9210 | 0.0000 |
| zona_destino | 0.0000 | 0.9210 | 0.0000 |

Exactitud con las 14 columnas: **0.9210**. En `clima`, `prioridad`, `zona_destino` y `trafico` sumé la importancia de sus columnas one-hot.

### Comparación

Acerté con la distancia en primer lugar y con que las medidas casi no se usan. Subestimé el clima: es la tercera columna más importante y quitarla baja 7.65 puntos. También sobreestimé la prioridad: casi no se usa (0.0031), aunque en la actividad 3 vi que explica parte de los errores. Eso indica que el árbol de profundidad 8 no la está aprovechando.

### Preguntas

1. **Las cuatro más importantes:** `distancia_km`, `volumen_l`, `clima` y `refrigerado`. Coinciden con las primeras preguntas del árbol de `entrenar_arbol.py`: la raíz es `distancia_km <= 7.01`, luego `volumen_l <= 90.10`, después `clima_lluvia` y `refrigerado`. Con mi predicción coinciden tres de cuatro (no esperaba el clima tan arriba).
2. **¿Cuál baja más la exactitud?** `distancia_km`: sin ella, la exactitud cae de 92.1 % a 79.3 %. No la cambian nada `zona_destino`, `trafico` ni `valor_declarado_mxn`; las medidas y la prioridad la mueven ±0.05 puntos, que es ruido.
3. **¿Cómo nunca sale un dron al centro si el modelo no usa la zona?** Porque la decisión final no es solo del modelo. Después de predecir, `usar_modelo.py` pasa la sugerencia por `es_posible`, que descarta el dron en el centro y elige el siguiente medio posible. La regla vive en el código del negocio, no en el árbol. Además, la zona está muy ligada a la distancia (el centro va de 0.3 a 6 km), así que el árbol obtiene casi toda esa información de `distancia_km`.

### Para pensar

No dejaría de pedir los datos solo porque el modelo no los usa. La zona la necesitan las reglas del negocio (`es_posible`) y la ruta del repartidor. El valor declarado sirve para el seguro y para penalizar envíos de valor alto. Las medidas son necesarias para calcular el volumen. El tráfico sí lo quitaría del formulario: se puede obtener automáticamente de un servicio de mapas según la hora, en lugar de pedírselo a la persona.

---

## Actividad 5 — El dron es minoría: ¿hay que balancear el dataset?

### Parte A — Pensar antes de tocar los datos

1. Un modelo que nunca dice dron y acierta todo lo demás tendría **90.5 %** de exactitud. Uno que siempre dice moto tendría **45.8 %**. Con un dataset desbalanceado, la exactitud puede verse alta aunque el modelo ignore por completo la clase minoritaria. En su lugar usaría la **precision**, el **recall** y el **F1 por clase**, en especial los del dron.
2. Hay pocos drones porque el dron tiene muchas restricciones: solo vuela con clima despejado, de día, fuera del centro y con paquetes pequeños. No es un error de los datos, refleja cómo opera la empresa. Por eso no hace falta "corregirlo" a la fuerza: el modelo debe predecir dron en la misma proporción que la realidad.
3. Se balancea **después** de separar, y **solo** el entrenamiento. Si se balancea antes, las copias de un mismo dron pueden caer tanto en el entrenamiento como en la prueba, y el modelo "acierta" porque ya los vio. La prueba nunca se balancea, porque debe parecerse a lo que el modelo va a recibir en producción.

### Parte B — Estrategias

Todas se evalúan con los mismos 2 000 envíos de prueba (190 drones reales), salvo la trampa.

| Estrategia | Envíos de entrenamiento | Exactitud | Precision dron | Recall dron | Veces que predice dron | Sugerencias imposibles |
|---|---|---|---|---|---|---|
| Sin balancear | 8 000 | 0.921 | 0.839 | 0.905 | 205 | 31 |
| Submuestreo (quitar ejemplos) | 3 032 | 0.898 | 0.889 | 0.932 | 199 | 29 |
| Sobremuestreo (repetir drones) | 10 905 | 0.900 | 0.728 | 1.000 | 261 | 54 |
| `class_weight="balanced"` | 8 000 | 0.902 | 0.766 | 1.000 | 248 | 35 |
| Drones nuevos del generador | 10 905 | 0.900 | 0.722 | 1.000 | 263 | 56 |

**Trampa a propósito:** repetí drones *antes* de separar, así que la prueba quedó con 916 drones.

| Estrategia | Envíos de entrenamiento | Exactitud | Precision dron | Recall dron | Veces que predice dron | Sugerencias imposibles |
|---|---|---|---|---|---|---|
| TRAMPA: repetir drones antes de separar | 10 904 | 0.918 | 0.924 | 0.989 | 981 | 68 |

La precision del dron sube a 0.924 y el recall casi llega a 1, pero es falso: **895 de los 916 drones de la prueba son copias exactas de uno que el modelo vio al entrenar**. No está generalizando, está reconociendo envíos que ya conoce. Además, la prueba ya no se parece a la realidad (46 % de drones en lugar de 9.5 %).

### Parte C — Interpretar

1. **Recall contra precision:** con sobremuestreo, `class_weight` o drones nuevos, el recall sube de 0.905 a **1.000** (encuentra todos los drones), pero la precision baja de 0.839 a **0.72–0.77**. El modelo aprendió que equivocarse con un dron cuesta mucho, así que dice "dron" más seguido (de 205 a 248–263 veces) y agarra drones verdaderos junto con varios que no lo eran.
2. **Menos datos:** el submuestreo entrenó con **3 032** envíos en lugar de 8 000, porque recorta cada clase al número de drones. Se pierde el 62 % de los ejemplos, sobre todo de moto y bicicleta, y la exactitud total baja a 0.898. Curiosamente fue la única estrategia que subió precision y recall a la vez, pero lo pagó con más errores en las otras clases.
3. **Estrategias casi iguales:** el sobremuestreo, `class_weight="balanced"` y los drones nuevos dieron casi los mismos números (recall 1.000, precision entre 0.72 y 0.77). En el fondo hacen lo mismo: aumentan el peso total de los drones al entrenar. Repetir un dron dos veces equivale a decirle al árbol que ese dron vale el doble, que es justo lo que hace `class_weight`. Los drones nuevos se generan con las mismas reglas, así que aportan muy poca información que el árbol no tuviera ya.
4. **La "confianza 84 %":** después de balancear ya no significa lo mismo. El modelo entrenó viendo drones en una proporción mucho mayor que el 9.5 % real, así que sus probabilidades de dron salen infladas. Un "84 %" de un modelo balanceado no equivale a "84 de cada 100 veces es dron" en la vida real.

### Parte D — Decidir

**Recomendación: no usar el modelo balanceado.** Me quedo con el modelo sin balancear y las reglas del negocio encima.

- **Qué cuesta más:** mandar un dron cuando no convenía cuesta más que no usarlo cuando sí convenía. Un dron mal mandado es un riesgo para el equipo y para el paquete. Un dron no usado solo significa que el envío se va en moto, un poco más caro o más lento.
- **Qué corrigen las reglas:** las reglas atrapan las sugerencias imposibles (el dron de noche o con lluvia), pero no las que sí son posibles y aun así no convenían. Con balanceo, las sugerencias imposibles suben de 31 a 35–56, y las predicciones de dron de 205 a hasta 263. Más trabajo para las reglas y más drones dudosos que pasan el filtro.
- **Si la empresa compra el doble de drones:** cambiaría la operación real, así que lo correcto sería generar o juntar datos nuevos con esa proporción y volver a entrenar, no balancear artificialmente los datos de hoy.
- El submuestreo fue el único que mejoró al dron sin inflar las predicciones (199 contra 190 reales), pero perdió exactitud general (0.898). No vale la pena tirar el 62 % de los datos.
