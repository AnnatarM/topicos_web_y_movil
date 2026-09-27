"""
Día 3 — Pruebas
===============
Cubre:  Strategy · Adapter · Fábrica · Integración
"""
from django.test import TestCase, Client
from django.urls import reverse

from .medios import (
    EntregaCamioneta,
    EntregaMotocicleta,
    EntregaBicicleta,
    EntregaDron,
    Plan,
)
from .proveedores_ia import (
    ProveedorIAJson,
    ProveedorIAXml,
    AdapterJson,
    AdapterXml,
    Sugerencia,
)
from .fabrica import crear, MedioDesconocidoError
from .models import Pedido


# ---------------------------------------------------------------------------
# Objeto mínimo que imita un Pedido para los tests de Strategy
# ---------------------------------------------------------------------------
class _PedidoFalso:
    def __init__(self, peso):
        self.peso = peso


_CONTEXTO_VACIO = {}


# ===========================================================================
# 1. PRUEBAS DEL STRATEGY
# ===========================================================================

class StrategyCamionetaTest(TestCase):

    def test_planear_devuelve_plan(self):
        strategy = EntregaCamioneta()
        plan = strategy.planear(_PedidoFalso(50), _CONTEXTO_VACIO)
        self.assertIsInstance(plan, Plan)
        self.assertEqual(plan.medio, 'camioneta')

    def test_eta_carga_normal(self):
        plan = EntregaCamioneta().planear(_PedidoFalso(50), _CONTEXTO_VACIO)
        self.assertIn('24 horas', plan.eta)

    def test_eta_carga_extra_pesada(self):
        plan = EntregaCamioneta().planear(_PedidoFalso(200), _CONTEXTO_VACIO)
        self.assertIn('48 horas', plan.eta)


class StrategyMotocicletaTest(TestCase):

    def test_planear_devuelve_plan(self):
        plan = EntregaMotocicleta().planear(_PedidoFalso(10), _CONTEXTO_VACIO)
        self.assertIsInstance(plan, Plan)
        self.assertEqual(plan.medio, 'motocicleta')

    def test_eta_contiene_horas(self):
        plan = EntregaMotocicleta().planear(_PedidoFalso(10), _CONTEXTO_VACIO)
        self.assertIn('horas', plan.eta)


class StrategyBicicletaTest(TestCase):

    def test_planear_devuelve_plan(self):
        plan = EntregaBicicleta().planear(_PedidoFalso(3), _CONTEXTO_VACIO)
        self.assertIsInstance(plan, Plan)
        self.assertEqual(plan.medio, 'bicicleta')

    def test_eta_es_rapida(self):
        plan = EntregaBicicleta().planear(_PedidoFalso(3), _CONTEXTO_VACIO)
        self.assertIn('2 horas', plan.eta)


class StrategyDronTest(TestCase):

    def test_planear_devuelve_plan(self):
        plan = EntregaDron().planear(_PedidoFalso(2), _CONTEXTO_VACIO)
        self.assertIsInstance(plan, Plan)
        self.assertEqual(plan.medio, 'dron')

    def test_eta_es_muy_rapida(self):
        plan = EntregaDron().planear(_PedidoFalso(2), _CONTEXTO_VACIO)
        self.assertIn('1 hora', plan.eta)


# ===========================================================================
# 2. PRUEBAS DEL ADAPTER
# ===========================================================================

class AdapterJsonTest(TestCase):

    def setUp(self):
        self.adapter = AdapterJson(ProveedorIAJson())

    def test_devuelve_sugerencia(self):
        sugerencia = self.adapter.obtener_sugerencia(20.0)
        self.assertIsInstance(sugerencia, Sugerencia)

    def test_medio_es_string_no_vacio(self):
        sugerencia = self.adapter.obtener_sugerencia(20.0)
        self.assertIsInstance(sugerencia.medio, str)
        self.assertTrue(len(sugerencia.medio) > 0)

    def test_no_expone_route_hint_en_dominio(self):
        """La Sugerencia NO debe tener atributos propios del proveedor externo."""
        sugerencia = self.adapter.obtener_sugerencia(20.0)
        self.assertFalse(hasattr(sugerencia, 'route_hint'))
        self.assertFalse(hasattr(sugerencia, 'score'))

    def test_peso_bajo_sugiere_dron_o_bicicleta(self):
        sugerencia = self.adapter.obtener_sugerencia(3.0)
        self.assertIn(sugerencia.medio, ('dron', 'bicicleta'))

    def test_peso_alto_sugiere_camioneta(self):
        sugerencia = self.adapter.obtener_sugerencia(200.0)
        self.assertEqual(sugerencia.medio, 'camioneta')


class AdapterXmlTest(TestCase):

    def setUp(self):
        self.adapter = AdapterXml(ProveedorIAXml())

    def test_devuelve_sugerencia(self):
        sugerencia = self.adapter.obtener_sugerencia(20.0)
        self.assertIsInstance(sugerencia, Sugerencia)

    def test_medio_es_string_no_vacio(self):
        sugerencia = self.adapter.obtener_sugerencia(20.0)
        self.assertIsInstance(sugerencia.medio, str)
        self.assertTrue(len(sugerencia.medio) > 0)

    def test_no_expone_etiquetas_xml_en_dominio(self):
        """La Sugerencia NO debe tener atributos propios del XML del proveedor."""
        sugerencia = self.adapter.obtener_sugerencia(20.0)
        self.assertFalse(hasattr(sugerencia, 'vehicle'))
        self.assertFalse(hasattr(sugerencia, 'suggestion'))

    def test_peso_bajo_sugiere_dron(self):
        sugerencia = self.adapter.obtener_sugerencia(2.0)
        self.assertEqual(sugerencia.medio, 'dron')

    def test_peso_alto_sugiere_camioneta(self):
        sugerencia = self.adapter.obtener_sugerencia(200.0)
        self.assertEqual(sugerencia.medio, 'camioneta')


class AdapterEquivalenciaTest(TestCase):
    """Ambos adapters deben producir Sugerencias estructuralmente equivalentes."""

    def test_misma_estructura_para_peso_bajo(self):
        sug_json = AdapterJson(ProveedorIAJson()).obtener_sugerencia(2.0)
        sug_xml = AdapterXml(ProveedorIAXml()).obtener_sugerencia(2.0)
        # Ambas deben ser Sugerencia con atributos 'medio' y 'motivo'
        self.assertIsInstance(sug_json, Sugerencia)
        self.assertIsInstance(sug_xml, Sugerencia)
        self.assertTrue(hasattr(sug_json, 'medio') and hasattr(sug_json, 'motivo'))
        self.assertTrue(hasattr(sug_xml, 'medio') and hasattr(sug_xml, 'motivo'))


# ===========================================================================
# 3. PRUEBAS DE LA FÁBRICA
# ===========================================================================

class FabricaTest(TestCase):

    def test_camioneta(self):
        strategy = crear('camioneta')
        self.assertIsInstance(strategy, EntregaCamioneta)

    def test_motocicleta(self):
        strategy = crear('motocicleta')
        self.assertIsInstance(strategy, EntregaMotocicleta)

    def test_bicicleta(self):
        strategy = crear('bicicleta')
        self.assertIsInstance(strategy, EntregaBicicleta)

    def test_dron(self):
        strategy = crear('dron')
        self.assertIsInstance(strategy, EntregaDron)

    def test_medio_desconocido_lanza_error(self):
        with self.assertRaises(MedioDesconocidoError):
            crear('teleportacion')

    def test_case_insensitive(self):
        """La fábrica debe ignorar mayúsculas."""
        strategy = crear('DRON')
        self.assertIsInstance(strategy, EntregaDron)


# ===========================================================================
# 4. PRUEBA DE INTEGRACIÓN — POST /pedidos/
# ===========================================================================

class IntegracionPedidoTest(TestCase):

    def setUp(self):
        self.client = Client()

    def _post_pedido(self, origen='Almacén Central', destino='Sucursal Norte', peso='3.0'):
        url = reverse('crear_pedido')
        return self.client.post(url, {
            'origen': origen,
            'destino': destino,
            'peso': peso,
        })

    def test_post_redirige_a_seguimiento(self):
        """PRG: el POST debe redirigir a GET /pedidos/<id>/"""
        response = self._post_pedido()
        self.assertEqual(response.status_code, 302)
        self.assertIn('/pedidos/', response['Location'])

    def test_get_seguimiento_devuelve_200(self):
        """Después del redirect, el GET devuelve 200."""
        response = self._post_pedido()
        seguimiento_url = response['Location']
        response2 = self.client.get(seguimiento_url)
        self.assertEqual(response2.status_code, 200)

    def test_pedido_guardado_con_medio(self):
        """El pedido debe quedar guardado con un campo 'medio' no vacío."""
        self._post_pedido(peso='3.0')
        pedido = Pedido.objects.last()
        self.assertIsNotNone(pedido)
        self.assertIn(pedido.medio, ('camioneta', 'motocicleta', 'bicicleta', 'dron'))

    def test_pedido_pesado_asigna_camioneta(self):
        """Un pedido de 200 kg debe quedar con medio='camioneta'."""
        self._post_pedido(peso='200.0')
        pedido = Pedido.objects.last()
        self.assertEqual(pedido.medio, 'camioneta')

    def test_pedido_liviano_asigna_dron(self):
        """Un pedido de 2 kg debe quedar con medio='dron'."""
        self._post_pedido(peso='2.0')
        pedido = Pedido.objects.last()
        self.assertEqual(pedido.medio, 'dron')

    def test_eta_no_vacia(self):
        """El campo eta debe quedar con un valor real, no 'Calculando ruta...'"""
        self._post_pedido()
        pedido = Pedido.objects.last()
        self.assertTrue(len(pedido.eta) > 0)
        self.assertNotEqual(pedido.eta, 'Calculando ruta...')

    def test_recargar_get_no_crea_pedido_extra(self):
        """El PRG garantiza que recargar el GET no crea pedidos duplicados."""
        self._post_pedido()
        total_antes = Pedido.objects.count()
        seguimiento_url = f'/pedidos/{Pedido.objects.last().pk}/'
        self.client.get(seguimiento_url)
        self.assertEqual(Pedido.objects.count(), total_antes)
