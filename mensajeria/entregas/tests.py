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


# ===========================================================================
# 5. PRUEBAS DEL DÍA 4
# ===========================================================================
# Importaciones adicionales para Día 4
from unittest.mock import patch
from django.test import TransactionTestCase
from . import proveedores_ia


class TransaccionAtomicaTest(TestCase):
    """Día 4 — transaction.atomic(): si falla la persistencia, nada se guarda."""

    def test_pedido_se_guarda_en_flujo_normal(self):
        """En flujo normal, el pedido queda en BD."""
        client = Client()
        url = reverse('crear_pedido')
        client.post(url, {'origen': 'A', 'destino': 'B', 'peso': '5.0'})
        self.assertEqual(Pedido.objects.count(), 1)

    def test_rollback_si_create_lanza_excepcion(self):
        """
        Si Pedido.objects.create() lanza una excepción dentro del atomic(),
        la transacción se revierte y no queda ningún pedido huérfano.
        """
        from django.db import transaction as tx
        from .services import registrar_pedido

        datos = {'origen': 'X', 'destino': 'Y', 'peso': '5.0'}

        with patch.object(Pedido.objects, 'create', side_effect=Exception('BD caída')):
            with self.assertRaises(Exception):
                registrar_pedido(datos)

        # No debe haber quedado ningún pedido
        self.assertEqual(Pedido.objects.count(), 0)


class FallbackIATest(TestCase):
    """Día 4 — Tolerancia a caída de IA: el pedido se guarda con fallback."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('crear_pedido')

    def tearDown(self):
        # Asegurarse de restaurar el flag después de cada test
        proveedores_ia.IA_CAIDA = False

    def test_ia_caida_pedido_se_guarda(self):
        """Con IA_CAIDA=True, el pedido debe guardarse con el medio fallback."""
        proveedores_ia.IA_CAIDA = True
        self.client.post(self.url, {'origen': 'A', 'destino': 'B', 'peso': '3.0'})
        pedido = Pedido.objects.last()
        self.assertIsNotNone(pedido)
        self.assertEqual(pedido.medio, proveedores_ia.MEDIO_FALLBACK)

    def test_ia_caida_responde_302(self):
        """Con IA caída, el POST debe redirigir normalmente (sin 500)."""
        proveedores_ia.IA_CAIDA = True
        response = self.client.post(
            self.url, {'origen': 'A', 'destino': 'B', 'peso': '3.0'}
        )
        self.assertEqual(response.status_code, 302)

    def test_ia_caida_seguimiento_funciona(self):
        """Con IA caída, el GET /pedidos/<id>/ funciona sin llamar a la IA."""
        proveedores_ia.IA_CAIDA = True
        response = self.client.post(
            self.url, {'origen': 'A', 'destino': 'B', 'peso': '3.0'}
        )
        seguimiento_url = response['Location']
        # Dejamos la IA caída para comprobar que el GET no la consulta
        response2 = self.client.get(seguimiento_url)
        self.assertEqual(response2.status_code, 200)

    def test_ia_caida_no_consulta_ia_en_get(self):
        """
        El GET del seguimiento usa solo datos de BD; no debe invocar
        el proveedor de IA aunque esté caído.
        """
        # Primero creamos el pedido con IA funcionando
        self.client.post(self.url, {'origen': 'A', 'destino': 'B', 'peso': '3.0'})
        pk = Pedido.objects.last().pk

        # Ahora "apagamos" la IA
        proveedores_ia.IA_CAIDA = True

        # El GET no debe intentar llamar a la IA
        with patch.object(proveedores_ia, 'obtener_sugerencia_con_fallback') as mock_ia:
            response = self.client.get(f'/pedidos/{pk}/')
            self.assertEqual(response.status_code, 200)
            mock_ia.assert_not_called()  # La vista NO llama a la IA

    def test_ia_funcionando_asigna_medio_real(self):
        """Con IA funcionando, el pedido recibe un medio calculado (no el fallback)."""
        proveedores_ia.IA_CAIDA = False
        self.client.post(self.url, {'origen': 'A', 'destino': 'B', 'peso': '3.0'})
        pedido = Pedido.objects.last()
        # Con peso 3 kg, el proveedor JSON sugiere 'dron'
        self.assertEqual(pedido.medio, 'dron')


class NotificacionPostCommitTest(TestCase):
    """
    Día 4 — transaction.on_commit() con captureOnCommitCallbacks().

    PROBLEMA CON TestCase NORMAL:
    Django envuelve cada test en una transacción que nunca hace commit real,
    por lo que los callbacks de on_commit() nunca se disparan en el test.

    SOLUCIÓN — captureOnCommitCallbacks(execute=True):
    Disponible desde Django 4.1. Captura los callbacks registrados con
    on_commit() dentro del bloque y los ejecuta al salir del bloque,
    simulando el commit real sin necesitar TransactionTestCase.

    Esto permite verificar exactamente la secuencia:
        1. Pedido confirmado (create)
        2. Callback registrado (on_commit)
        3. Callback ejecutado después del bloque atomic
        4. Si el callback falla → el pedido sigue en BD (robust=True)
    """

    def test_callback_se_ejecuta_despues_del_commit(self):
        """
        captureOnCommitCallbacks(execute=True) ejecuta el callback real.
        Verifica que la notificación se dispara exactamente UNA vez.
        """
        from .services import registrar_pedido
        datos = {'origen': 'A', 'destino': 'B', 'peso': '5.0'}

        llamadas = []

        def notificacion_espía(pedido_id, medio):
            llamadas.append((pedido_id, medio))

        with patch('entregas.services._notificar_pedido', side_effect=notificacion_espía):
            with self.captureOnCommitCallbacks(execute=True):
                pedido = registrar_pedido(datos)

        # El callback se ejecutó exactamente una vez después del commit
        self.assertEqual(len(llamadas), 1)
        self.assertEqual(llamadas[0][0], pedido.pk)

    def test_notificacion_fallando_no_deshace_pedido(self):
        """
        Si la notificación lanza una excepción después del commit,
        el pedido debe seguir existiendo en la BD.

        Con robust=True, Django captura la excepción del callback y la
        registra en el log sin propagarla; el pedido ya está confirmado.
        """
        from .services import registrar_pedido
        datos = {'origen': 'X', 'destino': 'Y', 'peso': '10.0'}

        with patch(
            'entregas.services._notificar_pedido',
            side_effect=Exception('SMTP caído'),
        ):
            with self.captureOnCommitCallbacks(execute=True):
                # registrar_pedido hace commit y registra el callback
                pedido = registrar_pedido(datos)
            # Al salir del bloque, captureOnCommitCallbacks ejecuta el callback.
            # Con robust=True, la excepción NO se propaga aquí.

        # El pedido sigue existiendo aunque la notificación haya fallado
        recuperado = Pedido.objects.filter(pk=pedido.pk).first()
        self.assertIsNotNone(recuperado, 'El pedido debe seguir en BD tras fallo de notificación')
        self.assertEqual(recuperado.origen, 'X')

    def test_pedido_existe_despues_del_commit(self):
        """
        Verificación directa: después de registrar_pedido(),
        el objeto Pedido es recuperable desde la BD.
        """
        from .services import registrar_pedido
        datos = {'origen': 'Origen', 'destino': 'Destino', 'peso': '10.0'}
        pedido = registrar_pedido(datos)
        recuperado = Pedido.objects.get(pk=pedido.pk)
        self.assertEqual(recuperado.origen, 'Origen')
        self.assertEqual(recuperado.destino, 'Destino')

    def test_sin_notificacion_el_pedido_se_guarda_igual(self):
        """
        Si el callback nunca se registra (escenario alternativo),
        el pedido igual debe persistir — el commit no depende de on_commit.
        """
        from .services import registrar_pedido
        datos = {'origen': 'P', 'destino': 'Q', 'peso': '7.0'}
        pedido = registrar_pedido(datos)
        self.assertIsNotNone(Pedido.objects.filter(pk=pedido.pk).first())


class NotificacionTransactionTest(TransactionTestCase):
    """
    Día 4 — Verificación con commits REALES usando TransactionTestCase.

    A diferencia de TestCase, TransactionTestCase no envuelve los tests en
    una transacción; cada operación de BD se confirma realmente, lo que
    permite que on_commit() se dispare de verdad.

    Desventaja: más lento (limpia la BD tras cada test con TRUNCATE).
    Ventaja: comportamiento idéntico a producción.
    """

    def test_notificacion_real_post_commit(self):
        """
        En un commit real, la notificación se ejecuta DESPUÉS del commit.
        Verifica el orden: create → commit → notificación.
        """
        from .services import registrar_pedido

        secuencia = []

        def notificacion_espía(pedido_id, medio):
            # En este punto el commit ya ocurrió; comprobamos que el
            # pedido existe en BD antes de que la notificación termine.
            existe = Pedido.objects.filter(pk=pedido_id).exists()
            secuencia.append(('notificacion', pedido_id, existe))

        datos = {'origen': 'Trans-A', 'destino': 'Trans-B', 'peso': '6.0'}

        with patch('entregas.services._notificar_pedido', side_effect=notificacion_espía):
            pedido = registrar_pedido(datos)
            # En TransactionTestCase el commit ocurre aquí mismo (no hay
            # transacción de test envolvente), así que on_commit se dispara
            # al salir del bloque atomic() dentro de registrar_pedido().

        self.assertEqual(len(secuencia), 1, 'La notificación debe ejecutarse exactamente una vez')
        _, pk_notificado, pedido_existia = secuencia[0]
        self.assertEqual(pk_notificado, pedido.pk)
        self.assertTrue(pedido_existia, 'El pedido debe existir en BD cuando se ejecuta la notificación')

    def test_notificacion_fallando_pedido_persiste_con_commit_real(self):
        """
        Con commit real y robust=True: aunque la notificación lance
        una excepción, el pedido ya confirmado sigue en la BD.
        """
        from .services import registrar_pedido

        datos = {'origen': 'Trans-X', 'destino': 'Trans-Y', 'peso': '15.0'}

        with patch(
            'entregas.services._notificar_pedido',
            side_effect=RuntimeError('Servidor de correo caído'),
        ):
            # robust=True hace que la RuntimeError sea absorbida por Django
            pedido = registrar_pedido(datos)

        # El pedido sigue en BD pese al fallo de la notificación
        self.assertTrue(Pedido.objects.filter(pk=pedido.pk).exists())


class PlantillaLimpiaTest(TestCase):
    """
    Día 4 — Plantilla limpia: la vista de seguimiento recibe datos
    preparados y la plantilla solo los presenta.
    """

    def _crear_y_obtener_seguimiento(self, peso='5.0'):
        client = Client()
        url = reverse('crear_pedido')
        response = client.post(url, {'origen': 'Orig', 'destino': 'Dest', 'peso': peso})
        return client.get(response['Location'])

    def test_seguimiento_contiene_folio(self):
        response = self._crear_y_obtener_seguimiento()
        self.assertContains(response, 'Pedido #')

    def test_seguimiento_contiene_medio(self):
        response = self._crear_y_obtener_seguimiento()
        self.assertContains(response, 'Medio de entrega')

    def test_seguimiento_contiene_eta(self):
        response = self._crear_y_obtener_seguimiento()
        self.assertContains(response, 'ETA')

    def test_seguimiento_contiene_origen_y_destino(self):
        response = self._crear_y_obtener_seguimiento()
        self.assertContains(response, 'Orig')
        self.assertContains(response, 'Dest')

    def test_plantilla_no_tiene_orm_ni_sql(self):
        """
        Verificación estructural: el archivo de plantilla no debe
        contener llamadas ORM ni SQL directos.
        """
        import os
        ruta = os.path.join(
            os.path.dirname(__file__),
            'templates', 'entregas', 'seguimiento.html'
        )
        with open(ruta, encoding='utf-8') as f:
            contenido = f.read()
        for patron_prohibido in (
            'objects.', '.filter(', '.get(', 'SELECT ', 'INSERT ', 'UPDATE ',
            'ProveedorIA', 'AdapterJson', 'AdapterXml', 'fabrica.crear',
            'obtener_sugerencia',
        ):
            self.assertNotIn(
                patron_prohibido, contenido,
                msg=f'La plantilla NO debe contener "{patron_prohibido}"'
            )


# ===========================================================================
# 6. PRUEBAS DEL PAGO SIMULADO (Día 4 — parte opcional)
# ===========================================================================
from .models import Pago
from .services import registrar_pedido, _calcular_monto


class PagoSimuladoTest(TestCase):
    """
    Día 4 — Pago simulado dentro de transaction.atomic().

    Verifica que:
    - Crear un pedido también crea un pago aprobado.
    - El monto se calcula a partir del peso.
    - Si el pago falla → rollback del pedido completo.
    - Pedido + pago persisten juntos tras el commit.
    - La notificación post-commit sigue funcionando con el pago.
    """

    def _datos(self, origen='A', destino='B', peso='5.0'):
        return {'origen': origen, 'destino': destino, 'peso': peso}

    # ------------------------------------------------------------------
    # 1. Crear pedido → crea también pago simulado
    # ------------------------------------------------------------------
    def test_crear_pedido_crea_pago(self):
        """Crear pedido también crea un Pago relacionado."""
        pedido = registrar_pedido(self._datos())
        self.assertTrue(
            Pago.objects.filter(pedido=pedido).exists(),
            'Debe existir un Pago asociado al Pedido.'
        )

    # ------------------------------------------------------------------
    # 2. Pago queda aprobado
    # ------------------------------------------------------------------
    def test_pago_queda_aprobado(self):
        """El estado del pago debe ser 'aprobado'."""
        pedido = registrar_pedido(self._datos())
        pago = Pago.objects.get(pedido=pedido)
        self.assertEqual(pago.estado, 'aprobado')

    # ------------------------------------------------------------------
    # 3. Pedido y pago existen después del commit
    # ------------------------------------------------------------------
    def test_pedido_y_pago_persisten(self):
        """Ambos registros deben ser recuperables desde la BD."""
        pedido = registrar_pedido(self._datos(peso='8.0'))
        self.assertIsNotNone(Pedido.objects.filter(pk=pedido.pk).first())
        self.assertIsNotNone(Pago.objects.filter(pedido=pedido).first())

    # ------------------------------------------------------------------
    # 4 & 5. Si la creación del pago falla → rollback (pedido también)
    # ------------------------------------------------------------------
    def test_fallo_pago_hace_rollback_del_pedido(self):
        """
        Si Pago.objects.create() lanza excepción dentro del atomic(),
        el Pedido también se revierte. No debe quedar ningún registro.
        """
        datos = self._datos()
        with patch.object(Pago.objects, 'create', side_effect=Exception('Pasarela caída')):
            with self.assertRaises(Exception):
                registrar_pedido(datos)

        self.assertEqual(Pedido.objects.count(), 0, 'El Pedido debe revertirse cuando falla el Pago.')
        self.assertEqual(Pago.objects.count(), 0, 'No debe quedar ningún Pago huérfano.')

    # ------------------------------------------------------------------
    # 6. Notificación continúa después del commit (con pago)
    # ------------------------------------------------------------------
    def test_notificacion_ocurre_despues_del_commit_con_pago(self):
        """La notificación post-commit se dispara normalmente incluso con el Pago."""
        llamadas = []

        def espia(pedido_id, medio):
            llamadas.append(pedido_id)

        with patch('entregas.services._notificar_pedido', side_effect=espia):
            with self.captureOnCommitCallbacks(execute=True):
                pedido = registrar_pedido(self._datos())

        self.assertEqual(len(llamadas), 1)
        self.assertEqual(llamadas[0], pedido.pk)

    # ------------------------------------------------------------------
    # 7. Notificación falla → pedido y pago siguen existiendo
    # ------------------------------------------------------------------
    def test_notificacion_falla_pedido_y_pago_persisten(self):
        """
        Si la notificación lanza excepción (robust=True la absorbe),
        el Pedido y el Pago deben seguir en la BD.
        """
        with patch(
            'entregas.services._notificar_pedido',
            side_effect=RuntimeError('SMTP caído'),
        ):
            with self.captureOnCommitCallbacks(execute=True):
                pedido = registrar_pedido(self._datos(peso='12.0'))

        self.assertTrue(Pedido.objects.filter(pk=pedido.pk).exists())
        self.assertTrue(Pago.objects.filter(pedido=pedido).exists())

    # ------------------------------------------------------------------
    # 8. IA funcionando → flujo normal con pago
    # ------------------------------------------------------------------
    def test_ia_funcionando_flujo_normal_con_pago(self):
        """Con IA activa, el pedido y el pago se crean correctamente."""
        proveedores_ia.IA_CAIDA = False
        try:
            pedido = registrar_pedido(self._datos(peso='3.0'))
            self.assertIsNotNone(pedido.pk)
            self.assertTrue(Pago.objects.filter(pedido=pedido).exists())
        finally:
            proveedores_ia.IA_CAIDA = False

    # ------------------------------------------------------------------
    # 9. IA caída → fallback + pago igualmente creado
    # ------------------------------------------------------------------
    def test_ia_caida_fallback_con_pago(self):
        """Con IA caída, el fallback actúa y el pago sigue creándose."""
        proveedores_ia.IA_CAIDA = True
        try:
            pedido = registrar_pedido(self._datos(peso='5.0'))
            self.assertEqual(pedido.medio, proveedores_ia.MEDIO_FALLBACK)
            self.assertTrue(Pago.objects.filter(pedido=pedido).exists())
        finally:
            proveedores_ia.IA_CAIDA = False

    # ------------------------------------------------------------------
    # 10. GET del pedido funciona con IA caída (vista no llama a la IA)
    # ------------------------------------------------------------------
    def test_get_seguimiento_no_llama_ia_con_pago(self):
        """
        El GET /pedidos/<id>/ recupera datos de BD (incluido el pago)
        sin invocar la IA, aunque esté caída.
        """
        # Crear pedido con IA activa
        client = Client()
        url = reverse('crear_pedido')
        response = client.post(url, {'origen': 'A', 'destino': 'B', 'peso': '3.0'})
        pk = Pedido.objects.last().pk

        # Apagar la IA y verificar que el GET no la consulta
        proveedores_ia.IA_CAIDA = True
        try:
            with patch.object(proveedores_ia, 'obtener_sugerencia_con_fallback') as mock_ia:
                r = client.get(f'/pedidos/{pk}/')
                self.assertEqual(r.status_code, 200)
                mock_ia.assert_not_called()
        finally:
            proveedores_ia.IA_CAIDA = False

