from django.urls import path
from . import views

urlpatterns = [
    path('pedidos/', views.crear_pedido_view, name='crear_pedido'),
    path('pedidos/<int:pk>/', views.seguimiento_pedido_view, name='seguimiento_pedido'),
    # Día 5: el mismo pedido expuesto en JSON para clientes que no consumen HTML.
    path('api/pedidos/<int:pk>/', views.pedido_json_view, name='pedido_json'),
]