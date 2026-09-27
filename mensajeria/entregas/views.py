from django.shortcuts import get_object_or_404, redirect, render
from .models import Pedido, Pago
from .services import registrar_pedido


# ---------------------------------------------------------------------------
# Diccionario de coordenadas para ciudades mexicanas de prueba.
# Resolución de presentación: la vista convierte el nombre de ciudad en
# coordenadas para que la plantilla solo renderice datos preparados.
# Si una ciudad no está en el dict, la vista pasa None y la plantilla
# muestra el fallback sin romper la página.
# ---------------------------------------------------------------------------
_COORDENADAS: dict[str, tuple[float, float]] = {
    # Michoacán
    'morelia':          (19.7069, -101.1945),
    'uruapan':          (19.4197, -102.0606),
    'tarimbaro':        (19.7500, -101.0833),
    'tarímbaro':        (19.7500, -101.0833),
    'zamora':           (19.9833, -102.2833),
    'lazaro cardenas':  (17.9583, -102.2000),
    'lázaro cárdenas':  (17.9583, -102.2000),
    'patzcuaro':        (19.5153, -101.6097),
    'pátzcuaro':        (19.5153, -101.6097),
    'apatzingan':       (19.0883, -102.3542),
    'apatzingán':       (19.0883, -102.3542),
    'zitacuaro':        (19.4333, -100.3500),
    'zitácuaro':        (19.4333, -100.3500),
    'sahuayo':          (20.0608, -102.7222),
    'jacona':           (19.9706, -102.7231),
    'jiquilpan':        (19.9833, -102.7167),
    'maravatio':        (19.8997, -100.4500),
    'maravatío':        (19.8997, -100.4500),
    # Ciudad de México y área metro
    'mexico':                (19.4326,  -99.1332),
    'ciudad de mexico':      (19.4326,  -99.1332),
    'ciudad de méxico':      (19.4326,  -99.1332),
    'cdmx':                  (19.4326,  -99.1332),
    'ecatepec':              (19.6013,  -99.0603),
    'tlalnepantla':          (19.5433,  -99.2072),
    'naucalpan':             (19.4806,  -99.2392),
    # Otras ciudades principales
    'guadalajara':      (20.6597, -103.3496),
    'monterrey':        (25.6866, -100.3161),
    'puebla':           (19.0414,  -98.2063),
    'queretaro':        (20.5888, -100.3899),
    'querétaro':        (20.5888, -100.3899),
    'leon':             (21.1221, -101.6800),
    'léon':             (21.1221, -101.6800),
    'tijuana':          (32.5149, -117.0382),
    'cancun':           (21.1619,  -86.8515),
    'cancún':           (21.1619,  -86.8515),
    'merida':           (20.9674,  -89.5926),
    'mérida':           (20.9674,  -89.5926),
    'hermosillo':       (29.0730, -110.9559),
    'chihuahua':        (28.6353, -106.0889),
    'san luis potosi':  (22.1565,  -100.9855),
    'san luis potosí':  (22.1565,  -100.9855),
    'aguascalientes':   (21.8818, -102.2916),
    'culiacan':         (24.8000, -107.3833),
    'culiacán':         (24.8000, -107.3833),
    'torreon':          (25.5429, -103.4068),
    'torreón':          (25.5429, -103.4068),
    'veracruz':         (19.1738,  -96.1342),
    'oaxaca':           (17.0732,  -96.7266),
    'acapulco':         (16.8531,  -99.8237),
    'tuxtla gutierrez': (16.7521,  -93.1152),
    'tuxtla gutiérrez': (16.7521,  -93.1152),
    'saltillo':         (25.4232, -100.9933),
    'toluca':           (19.2826,  -99.6557),
    'xalapa':           (19.5438,  -96.9102),
    'cuernavaca':       (18.9261,  -99.2200),
    'tepic':            (21.5042, -104.8942),
    'colima':           (19.2452, -103.7241),
    'durango':          (24.0277, -104.6531),
    'campeche':         (19.8301,  -90.5349),
    'villahermosa':     (17.9892,  -92.9475),
    'zacatecas':        (22.7709, -102.5832),
    'guanajuato':       (21.0190, -101.2574),
    'celaya':           (20.5234, -100.8153),
    'irapuato':         (20.6769, -101.3495),
}


def _buscar_coordenadas(nombre_ciudad: str) -> tuple[float, float] | None:
    """
    Normaliza el nombre de ciudad y lo busca en el diccionario.
    Devuelve (lat, lon) o None si no se encuentra.
    La plantilla decide qué mostrar con esa información.
    """
    clave = nombre_ciudad.strip().lower()
    return _COORDENADAS.get(clave)


def crear_pedido_view(request):
    if request.method == 'POST':
        # La vista delega el trámite a la capa de servicio
        pedido = registrar_pedido(request.POST)

        # Patrón PRG (Post/Redirect/Get): Redirigimos al GET de seguimiento
        return redirect('seguimiento_pedido', pk=pedido.pk)

    return render(request, 'entregas/crear_pedido.html')


def seguimiento_pedido_view(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)

    # Resolver coordenadas para el mapa interactivo.
    # Si la ciudad no está en el diccionario, se pasa None y la plantilla
    # muestra el fallback. La lógica de BD ya se ejecutó antes de llegar aquí.
    coord_origen  = _buscar_coordenadas(pedido.origen)
    coord_destino = _buscar_coordenadas(pedido.destino)

    # Recuperar pago simulado si existe (pedidos viejos pueden no tenerlo)
    try:
        pago = pedido.pago
        monto_pago     = pago.monto
        id_transaccion = str(pago.id_transaccion)[:8].upper()  # solo primeros 8 chars
    except Pago.DoesNotExist:
        monto_pago     = None
        id_transaccion = None

    # El contexto llega ya listo a la plantilla (sin SQL ni lógica metida ahí)
    contexto = {
        'folio':          pedido.pk,
        'estado':         pedido.estado,
        'eta':            pedido.eta,
        'origen':         pedido.origen,
        'destino':        pedido.destino,
        'medio':          pedido.medio,
        # Pago simulado
        'monto_pago':     monto_pago,
        'id_transaccion': id_transaccion,
        # Coordenadas para Leaflet (None si la ciudad no está en el dict)
        'lat_origen':   coord_origen[0]  if coord_origen  else None,
        'lon_origen':   coord_origen[1]  if coord_origen  else None,
        'lat_destino':  coord_destino[0] if coord_destino else None,
        'lon_destino':  coord_destino[1] if coord_destino else None,
    }
    return render(request, 'entregas/seguimiento.html', contexto)