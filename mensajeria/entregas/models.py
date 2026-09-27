import uuid
from django.db import models


class Pedido(models.Model):
    origen = models.CharField(max_length=255)
    destino = models.CharField(max_length=255)
    peso = models.DecimalField(max_digits=6, decimal_places=2)
    estado = models.CharField(max_length=50, default='Registrado')
    eta = models.CharField(
        max_length=100, default='24 horas (ETA provisional)'
    )
    # Día 3: medio de entrega asignado por el Strategy.
    # blank=True para mantener compatibilidad con pedidos del Día 2
    # que fueron creados antes de existir este campo.
    medio = models.CharField(max_length=50, blank=True, default='')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Pedido #{self.id} - {self.estado}'


class Pago(models.Model):
    """
    Día 4 — Pago simulado.

    Representa el cobro ficticio asociado a un pedido.
    Queda dentro del mismo transaction.atomic() que el Pedido:
    si la creación del Pago falla, el Pedido también se revierte
    (y viceversa), garantizando consistencia entre ambos registros.

    id_transaccion:
        UUID único generado por el servidor en el momento del pago.
        En producción serviría como identificador idempotente para
        detectar dobles envíos y evitar cobrar dos veces la misma
        operación (actualmente no se implementa esa lógica completa).
    """
    pedido = models.OneToOneField(
        Pedido,
        on_delete=models.CASCADE,
        related_name='pago',
    )
    monto = models.DecimalField(max_digits=8, decimal_places=2)
    estado = models.CharField(max_length=20, default='aprobado')
    id_transaccion = models.UUIDField(default=uuid.uuid4, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Pago #{self.id} — Pedido #{self.pedido_id} — ${self.monto}'