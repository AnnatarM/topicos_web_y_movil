import uuid
from django.db import models


class Pedido(models.Model):
    origen = models.CharField(max_length=255)
    destino = models.CharField(max_length=255)
    peso = models.DecimalField(max_digits=6, decimal_places=2)
    estado = models.CharField(max_length=50, default='Registrado')
    eta = models.CharField(max_length=100, default='24 horas (ETA provisional)')
    # Resultado del Strategy; queda persistido para reutilizar la asignación al consultar el pedido.
    medio = models.CharField(max_length=50, blank=True, default='')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Pedido #{self.id} - {self.estado}'


class Pago(models.Model):
    """
    Pago simulado asociado uno a uno con un Pedido.
    Participa en el mismo transaction.atomic() que el Pedido: si uno falla,
    el otro también se revierte.
    id_transaccion: UUID que serviría como identificador idempotente en producción.
    """
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='pago')
    monto = models.DecimalField(max_digits=8, decimal_places=2)
    estado = models.CharField(max_length=20, default='aprobado')
    id_transaccion = models.UUIDField(default=uuid.uuid4, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Pago #{self.id} — Pedido #{self.pedido_id} — ${self.monto}'