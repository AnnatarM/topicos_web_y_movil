import json
from unittest.mock import patch

from django.test import TestCase, TransactionTestCase, Client
from django.urls import reverse

from .medios import EntregaCamioneta, EntregaMotocicleta, EntregaBicicleta, EntregaDron, Plan
from .proveedores_ia import ProveedorIAJson, ProveedorIAXml, AdapterJson, AdapterXml, Sugerencia
from .fabrica import crear, MedioDesconocidoError
from .models import Pedido, Pago
from .services import registrar_pedido, _calcular_monto
from . import proveedores_ia


class _PedidoFalso:
    def __init__(self, peso):
        self.peso = peso


_CONTEXTO_VACIO = {}



# Día 3 — Strategy, Adapter y fábrica


class StrategyCamionetaTest(TestCase):

    def test_planear_devuelve_plan(self):
        plan = EntregaCamioneta().planear(_PedidoFalso(50), _CONTEXTO_VACIO)
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


class AdapterJsonTest(TestCase):

    def setUp(self):
        self.adapter = AdapterJson(ProveedorIAJson())

    def test_devuelve_sugerencia(self):
        self.assertIsInstance(self.adapter.obtener_sugerencia(20.0), Sugerencia)

    def test_medio_es_string_no_vacio(self):
        s = self.adapter.obtener_sugerencia(20.0)
        self.assertIsInstance(s.medio, str)
        self.assertTrue(len(s.medio) > 0)

    def test_no_expone_route_hint_en_dominio(self):
        #La Sugerencia NO debe tener atributos propios del proveedor externo.
        s = self.adapter.obtener_sugerencia(20.0)
        self.assertFalse(hasattr(s, 'route_hint'))
        self.assertFalse(hasattr(s, 'score'))

    def test_peso_bajo_sugiere_dron_o_bicicleta(self):
        self.assertIn(self.adapter.obtener_sugerencia(3.0).medio, ('dron', 'bicicleta'))

    def test_peso_alto_sugiere_camioneta(self):
        self.assertEqual(self.adapter.obtener_sugerencia(200.0).medio, 'camioneta')


class AdapterXmlTest(TestCase):

    def setUp(self):
        self.adapter = AdapterXml(ProveedorIAXml())

    def test_devuelve_sugerencia(self):
        self.assertIsInstance(self.adapter.obtener_sugerencia(20.0), Sugerencia)

    def test_medio_es_string_no_vacio(self):
        s = self.adapter.obtener_sugerencia(20.0)
        self.assertIsInstance(s.medio, str)
        self.assertTrue(len(s.medio) > 0)

    def test_no_expone_etiquetas_xml_en_dominio(self):
        #La Sugerencia NO debe tener atributos propios del XML del proveedor.
        s = self.adapter.obtener_sugerencia(20.0)
        self.assertFalse(hasattr(s, 'vehicle'))
        self.assertFalse(hasattr(s, 'suggestion'))

    def test_peso_bajo_sugiere_dron(self):
        self.assertEqual(self.adapter.obtener_sugerencia(2.0).medio, 'dron')

    def test_peso_alto_sugiere_camioneta(self):
        self.assertEqual(self.adapter.obtener_sugerencia(200.0).medio, 'camioneta')


class AdapterEquivalenciaTest(TestCase):
    #Ambos adapters deben producir Sugerencias estructuralmente equivalentes.

    def test_misma_estructura_para_peso_bajo(self):
        sug_json = AdapterJson(ProveedorIAJson()).obtener_sugerencia(2.0)
        sug_xml = AdapterXml(ProveedorIAXml()).obtener_sugerencia(2.0)
        for s in (sug_json, sug_xml):
            self.assertIsInstance(s, Sugerencia)
            self.assertTrue(hasattr(s, 'medio') and hasattr(s, 'motivo'))


class FabricaTest(TestCase):

    def test_camioneta(self):
        self.assertIsInstance(crear('camioneta'), EntregaCamioneta)

    def test_motocicleta(self):
        self.assertIsInstance(crear('motocicleta'), EntregaMotocicleta)

    def test_bicicleta(self):
        self.assertIsInstance(crear('bicicleta'), EntregaBicicleta)

    def test_dron(self):
        self.assertIsInstance(crear('dron'), EntregaDron)

    def test_medio_desconocido_lanza_error(self):
        with self.assertRaises(MedioDesconocidoError):
            crear('teleportacion')

    def test_case_insensitive(self):
        #La fábrica debe ignorar mayúsculas.
        self.assertIsInstance(crear('DRON'), EntregaDron)


class IntegracionPedidoTest(TestCase):

    def setUp(self):
        self.client = Client()

    def _post_pedido(self, origen='Almacén Central', destino='Sucursal Norte', peso='3.0'):
        return self.client.post(reverse('crear_pedido'), {
            'origen': origen, 'destino': destino, 'peso': peso,
        })

    def test_post_redirige_a_seguimiento(self):
        """PRG: el POST debe redirigir a GET /pedidos/<id>/"""
        r = self._post_pedido()
        self.assertEqual(r.status_code, 302)
        self.assertIn('/pedidos/', r['Location'])

    def test_get_seguimiento_devuelve_200(self):
        r = self._post_pedido()
        self.assertEqual(self.client.get(r['Location']).status_code, 200)

    def test_pedido_guardado_con_medio(self):
        self._post_pedido(peso='3.0')
        pedido = Pedido.objects.last()
        self.assertIsNotNone(pedido)
        self.assertIn(pedido.medio, ('camioneta', 'motocicleta', 'bicicleta', 'dron'))

    def test_pedido_pesado_asigna_camioneta(self):
        self._post_pedido(peso='200.0')
        self.assertEqual(Pedido.objects.last().medio, 'camioneta')

    def test_pedido_liviano_asigna_dron(self):
        self._post_pedido(peso='2.0')
        self.assertEqual(Pedido.objects.last().medio, 'dron')

    def test_eta_no_vacia(self):
        self._post_pedido()
        pedido = Pedido.objects.last()
        self.assertTrue(len(pedido.eta) > 0)
        self.assertNotEqual(pedido.eta, 'Calculando ruta...')

    def test_recargar_get_no_crea_pedido_extra(self):
        #El PRG garantiza que recargar el GET no crea pedidos duplicados.
        self._post_pedido()
        total = Pedido.objects.count()
        self.client.get(f'/pedidos/{Pedido.objects.last().pk}/')
        self.assertEqual(Pedido.objects.count(), total)


# Día 4 — Transacción, fallback de IA, notificación post-commit y pago


class TransaccionAtomicaTest(TestCase):

    def test_pedido_se_guarda_en_flujo_normal(self):
        self.client.post(reverse('crear_pedido'), {'origen': 'A', 'destino': 'B', 'peso': '5.0'})
        self.assertEqual(Pedido.objects.count(), 1)

    def test_rollback_si_create_lanza_excepcion(self):
        #Si Pedido.objects.create() falla dentro del atomic(), no queda ningún registro.
        with patch.object(Pedido.objects, 'create', side_effect=Exception('BD caída')):
            with self.assertRaises(Exception):
                registrar_pedido({'origen': 'X', 'destino': 'Y', 'peso': '5.0'})
        self.assertEqual(Pedido.objects.count(), 0)


class FallbackIATest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('crear_pedido')

    def tearDown(self):
        proveedores_ia.IA_CAIDA = False

    def test_ia_caida_pedido_se_guarda(self):
        proveedores_ia.IA_CAIDA = True
        self.client.post(self.url, {'origen': 'A', 'destino': 'B', 'peso': '3.0'})
        pedido = Pedido.objects.last()
        self.assertIsNotNone(pedido)
        self.assertEqual(pedido.medio, proveedores_ia.MEDIO_FALLBACK)

    def test_ia_caida_responde_302(self):
        proveedores_ia.IA_CAIDA = True
        r = self.client.post(self.url, {'origen': 'A', 'destino': 'B', 'peso': '3.0'})
        self.assertEqual(r.status_code, 302)

    def test_ia_caida_seguimiento_funciona(self):
        proveedores_ia.IA_CAIDA = True
        r = self.client.post(self.url, {'origen': 'A', 'destino': 'B', 'peso': '3.0'})
        self.assertEqual(self.client.get(r['Location']).status_code, 200)

    def test_ia_caida_no_consulta_ia_en_get(self):
        """El GET de seguimiento usa datos de BD; no debe invocar la IA."""
        self.client.post(self.url, {'origen': 'A', 'destino': 'B', 'peso': '3.0'})
        pk = Pedido.objects.last().pk
        proveedores_ia.IA_CAIDA = True
        with patch.object(proveedores_ia, 'obtener_sugerencia_con_fallback') as mock_ia:
            self.assertEqual(self.client.get(f'/pedidos/{pk}/').status_code, 200)
            mock_ia.assert_not_called()

    def test_ia_funcionando_asigna_medio_real(self):
        proveedores_ia.IA_CAIDA = False
        self.client.post(self.url, {'origen': 'A', 'destino': 'B', 'peso': '3.0'})
        self.assertEqual(Pedido.objects.last().medio, 'dron')


class NotificacionPostCommitTest(TestCase):
    #captureOnCommitCallbacks(execute=True) simula el commit real dentro de TestCase,
    #permitiendo verificar que on_commit() se dispara y que robust=True absorbe fallos.
    

    def test_callback_se_ejecuta_despues_del_commit(self):
        llamadas = []

        def espia(pedido_id, medio):
            llamadas.append((pedido_id, medio))

        with patch('entregas.services._notificar_pedido', side_effect=espia):
            with self.captureOnCommitCallbacks(execute=True):
                pedido = registrar_pedido({'origen': 'A', 'destino': 'B', 'peso': '5.0'})

        self.assertEqual(len(llamadas), 1)
        self.assertEqual(llamadas[0][0], pedido.pk)

    def test_notificacion_fallando_no_deshace_pedido(self):
        #robust=True: la excepción de la notificación no revierte el pedido ya confirmado.
        with patch('entregas.services._notificar_pedido', side_effect=Exception('SMTP caído')):
            with self.captureOnCommitCallbacks(execute=True):
                pedido = registrar_pedido({'origen': 'X', 'destino': 'Y', 'peso': '10.0'})

        recuperado = Pedido.objects.filter(pk=pedido.pk).first()
        self.assertIsNotNone(recuperado)
        self.assertEqual(recuperado.origen, 'X')

    def test_pedido_existe_despues_del_commit(self):
        pedido = registrar_pedido({'origen': 'Origen', 'destino': 'Destino', 'peso': '10.0'})
        recuperado = Pedido.objects.get(pk=pedido.pk)
        self.assertEqual(recuperado.origen, 'Origen')
        self.assertEqual(recuperado.destino, 'Destino')

    def test_sin_notificacion_el_pedido_se_guarda_igual(self):
        pedido = registrar_pedido({'origen': 'P', 'destino': 'Q', 'peso': '7.0'})
        self.assertIsNotNone(Pedido.objects.filter(pk=pedido.pk).first())


class NotificacionTransactionTest(TransactionTestCase):
    #TransactionTestCase usa commits reales, lo que permite verificar on_commit() sin mocks.

    def test_notificacion_real_post_commit(self):
        #La notificación se dispara después del commit; el pedido ya existe en BD cuando ocurre.
        secuencia = []

        def espia(pedido_id, medio):
            secuencia.append(('notificacion', pedido_id, Pedido.objects.filter(pk=pedido_id).exists()))

        with patch('entregas.services._notificar_pedido', side_effect=espia):
            pedido = registrar_pedido({'origen': 'Trans-A', 'destino': 'Trans-B', 'peso': '6.0'})

        self.assertEqual(len(secuencia), 1)
        _, pk_notificado, pedido_existia = secuencia[0]
        self.assertEqual(pk_notificado, pedido.pk)
        self.assertTrue(pedido_existia)

    def test_notificacion_fallando_pedido_persiste_con_commit_real(self):
        #Con commit real y robust=True: la excepción de la notificación no revierte el pedido.
        with patch('entregas.services._notificar_pedido', side_effect=RuntimeError('Correo caído')):
            pedido = registrar_pedido({'origen': 'Trans-X', 'destino': 'Trans-Y', 'peso': '15.0'})
        self.assertTrue(Pedido.objects.filter(pk=pedido.pk).exists())


class PlantillaLimpiaTest(TestCase):

    def _crear_y_obtener_seguimiento(self, peso='5.0'):
        client = Client()
        r = client.post(reverse('crear_pedido'), {'origen': 'Orig', 'destino': 'Dest', 'peso': peso})
        return client.get(r['Location'])

    def test_seguimiento_contiene_folio(self):
        self.assertContains(self._crear_y_obtener_seguimiento(), 'Pedido #')

    def test_seguimiento_contiene_medio(self):
        self.assertContains(self._crear_y_obtener_seguimiento(), 'Medio de entrega')

    def test_seguimiento_contiene_eta(self):
        self.assertContains(self._crear_y_obtener_seguimiento(), 'ETA')

    def test_seguimiento_contiene_origen_y_destino(self):
        r = self._crear_y_obtener_seguimiento()
        self.assertContains(r, 'Orig')
        self.assertContains(r, 'Dest')

    def test_plantilla_no_tiene_orm_ni_sql(self):
        #La plantilla no debe contener accesos a ORM, SQL ni llamadas a la IA.
        import os
        ruta = os.path.join(os.path.dirname(__file__), 'templates', 'entregas', 'seguimiento.html')
        with open(ruta, encoding='utf-8') as f:
            contenido = f.read()
        for patron in (
            'objects.', '.filter(', '.get(', 'SELECT ', 'INSERT ', 'UPDATE ',
            'ProveedorIA', 'AdapterJson', 'AdapterXml', 'fabrica.crear', 'obtener_sugerencia',
        ):
            self.assertNotIn(patron, contenido, msg=f'La plantilla NO debe contener "{patron}"')


class PagoSimuladoTest(TestCase):
    #Pago simulado dentro de transaction.atomic(): atomicidad y persistencia.

    def _datos(self, origen='A', destino='B', peso='5.0'):
        return {'origen': origen, 'destino': destino, 'peso': peso}

    def test_crear_pedido_crea_pago(self):
        pedido = registrar_pedido(self._datos())
        self.assertTrue(Pago.objects.filter(pedido=pedido).exists())

    def test_pago_queda_aprobado(self):
        pedido = registrar_pedido(self._datos())
        self.assertEqual(Pago.objects.get(pedido=pedido).estado, 'aprobado')

    def test_pedido_y_pago_persisten(self):
        pedido = registrar_pedido(self._datos(peso='8.0'))
        self.assertIsNotNone(Pedido.objects.filter(pk=pedido.pk).first())
        self.assertIsNotNone(Pago.objects.filter(pedido=pedido).first())

    def test_fallo_pago_hace_rollback_del_pedido(self):
        #Si Pago.objects.create() falla, el Pedido también se revierte.
        with patch.object(Pago.objects, 'create', side_effect=Exception('Pasarela caída')):
            with self.assertRaises(Exception):
                registrar_pedido(self._datos())
        self.assertEqual(Pedido.objects.count(), 0)
        self.assertEqual(Pago.objects.count(), 0)

    def test_notificacion_ocurre_despues_del_commit_con_pago(self):
        llamadas = []

        def espia(pedido_id, medio):
            llamadas.append(pedido_id)

        with patch('entregas.services._notificar_pedido', side_effect=espia):
            with self.captureOnCommitCallbacks(execute=True):
                pedido = registrar_pedido(self._datos())

        self.assertEqual(len(llamadas), 1)
        self.assertEqual(llamadas[0], pedido.pk)

    def test_notificacion_falla_pedido_y_pago_persisten(self):
        #robust=True: la excepción de la notificación no revierte Pedido ni Pago.
        with patch('entregas.services._notificar_pedido', side_effect=RuntimeError('SMTP caído')):
            with self.captureOnCommitCallbacks(execute=True):
                pedido = registrar_pedido(self._datos(peso='12.0'))
        self.assertTrue(Pedido.objects.filter(pk=pedido.pk).exists())
        self.assertTrue(Pago.objects.filter(pedido=pedido).exists())

    def test_ia_funcionando_flujo_normal_con_pago(self):
        proveedores_ia.IA_CAIDA = False
        try:
            pedido = registrar_pedido(self._datos(peso='3.0'))
            self.assertIsNotNone(pedido.pk)
            self.assertTrue(Pago.objects.filter(pedido=pedido).exists())
        finally:
            proveedores_ia.IA_CAIDA = False

    def test_ia_caida_fallback_con_pago(self):
        proveedores_ia.IA_CAIDA = True
        try:
            pedido = registrar_pedido(self._datos(peso='5.0'))
            self.assertEqual(pedido.medio, proveedores_ia.MEDIO_FALLBACK)
            self.assertTrue(Pago.objects.filter(pedido=pedido).exists())
        finally:
            proveedores_ia.IA_CAIDA = False

    def test_get_seguimiento_no_llama_ia_con_pago(self):
        #GET /pedidos/<id>/ recupera datos de BD sin invocar la IA.
        client = Client()
        client.post(reverse('crear_pedido'), {'origen': 'A', 'destino': 'B', 'peso': '3.0'})
        pk = Pedido.objects.last().pk
        proveedores_ia.IA_CAIDA = True
        try:
            with patch.object(proveedores_ia, 'obtener_sugerencia_con_fallback') as mock_ia:
                r = client.get(f'/pedidos/{pk}/')
                self.assertEqual(r.status_code, 200)
                mock_ia.assert_not_called()
        finally:
            proveedores_ia.IA_CAIDA = False



# Día 5 — Contrato JSON  GET /api/pedidos/<id>/

class EndpointJsonTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.client.post(
            reverse('crear_pedido'),
            {'origen': 'Morelia', 'destino': 'Tarimbaro', 'peso': '5.0'},
        )
        self.pedido = Pedido.objects.last()
        self.url_json = reverse('pedido_json', kwargs={'pk': self.pedido.pk})
        self.url_html = reverse('seguimiento_pedido', kwargs={'pk': self.pedido.pk})

    def test_json_devuelve_200(self):
        self.assertEqual(self.client.get(self.url_json).status_code, 200)

    def test_json_content_type(self):
        self.assertIn('application/json', self.client.get(self.url_json)['Content-Type'])

    def test_json_contiene_campos_minimos(self):
        datos = json.loads(self.client.get(self.url_json).content)
        for campo in ('folio', 'estado', 'eta'):
            self.assertIn(campo, datos)

    def test_json_folio_correcto(self):
        datos = json.loads(self.client.get(self.url_json).content)
        self.assertEqual(datos['folio'], self.pedido.pk)

    def test_json_estado_coincide(self):
        datos = json.loads(self.client.get(self.url_json).content)
        self.assertEqual(datos['estado'], self.pedido.estado)

    def test_json_eta_coincide(self):
        datos = json.loads(self.client.get(self.url_json).content)
        self.assertEqual(datos['eta'], self.pedido.eta)

    def test_html_y_json_mismos_datos(self):
        #HTML y JSON representan el mismo pedido de BD.
        datos = json.loads(self.client.get(self.url_json).content)
        self.assertContains(self.client.get(self.url_html), str(datos['folio']))
        self.assertEqual(datos['eta'], Pedido.objects.get(pk=datos['folio']).eta)

    def test_json_404_pedido_inexistente(self):
        self.assertEqual(self.client.get(reverse('pedido_json', kwargs={'pk': 999999})).status_code, 404)

    def test_json_no_rompe_post(self):
        r = self.client.post(reverse('crear_pedido'), {'origen': 'A', 'destino': 'B', 'peso': '3.0'})
        self.assertEqual(r.status_code, 302)
        self.assertIn('/pedidos/', r['Location'])

    def test_json_no_rompe_get_html(self):
        r = self.client.get(self.url_html)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Pedido #')
