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