from .models import Pedido


def registrar_pedido(datos_formulario):
  """Trámite encargado de dar de alta un pedido en la base de datos."""
  pedido = Pedido.objects.create(
      origen=datos_formulario.get('origen'),
      destino=datos_formulario.get('destino'),
      peso=datos_formulario.get('peso', 0.0),
      estado='Registrado',
      eta='Calculando ruta...',
  )
  return pedido