# urls.py
from django.urls import path
from .views import register_user,order_list, check_user,OrderViewSet,ShaxarViewSet, MahsulotViewSet, RayonViewSet, KorinishViewSet, check_user, create_order, confirm_payment, check_order_id

urlpatterns = [
    path('users/', register_user, name='user-register'),
    path('users/<int:telegram_id>/', check_user, name='user-check'),
    
    path('shaxar/', ShaxarViewSet.as_view({'get': 'list', 'post': 'create'}), name='shaxar_list'),
    path('shaxar/<int:pk>/', ShaxarViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='shaxar_detail'),
    
    path('mahsulot/', MahsulotViewSet.as_view({'get': 'list', 'post': 'create'}), name='mahsulot_list'),
    path('mahsulot/<int:pk>/', MahsulotViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='mahsulot_detail'),
    
    path('rayon/', RayonViewSet.as_view({'get': 'list', 'post': 'create'}), name='rayon_list'),
    path('rayon/<int:pk>/', RayonViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='rayon_detail'),
    
    path('korinish/', KorinishViewSet.as_view({'get': 'list', 'post': 'create'}), name='korinish_list'),
    path('korinish/<int:pk>/', KorinishViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='korinish_detail'),
    
    path('orders/create_order/', create_order, name='create_order'),
    path('orders/confirm_payment/', confirm_payment, name='confirm_payment'),
    path('orders/check_id/', check_order_id, name='check_order_id'),
    
    
    path('order/<str:order_id>/', OrderViewSet.as_view({'get': 'retrieve','delete': 'destroy'}), name='order-delete'),
    path('orders/', order_list, name='order-list'),

    path('orders/confirm_payment/<str:order_id>/', confirm_payment, name='confirm_payment'),
]

