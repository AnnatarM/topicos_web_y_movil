from django.shortcuts import get_object_or_404, redirect, render
from .models import Pedido
from .services import registrar_pedido


def crear_pedido_view(request):
  if request.method == 'POST':
    # La vista delega el trámite a la capa de servicio
    pedido = registrar_pedido(request.POST)

    # Patrón PRG (Post/Redirect/Get): Redirigimos al GET de seguimiento
    return redirect('seguimiento_pedido', pk=pedido.pk)

  return render(request, 'entregas/crear_pedido.html')


def seguimiento_pedido_view(request, pk):
  pedido = get_object_or_404(Pedido, pk=pk)

  # El contexto llega ya listo a la plantilla (sin SQL ni lógica metida ahí)
  contexto = {
      'folio': pedido.pk,
      'estado': pedido.estado,
      'eta': pedido.eta,
      'origen': pedido.origen,
      'destino': pedido.destino,
  }
  return render(request, 'entregas/seguimiento.html', contexto)