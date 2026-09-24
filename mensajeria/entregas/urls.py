from django.urls import path
from . import views

urlpatterns = [
    path('pedidos/', views.crear_pedido_view, name='crear_pedido'),
    path(
        'pedidos/<int:pk>/',
        views.seguimiento_pedido_view,
        name='seguimiento_pedido',
    ),
]