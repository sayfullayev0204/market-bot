# urls.py
from django.urls import path
from .views import *

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
    
    
    path('order/<str:order_id>/', OrderViewSet.as_view({'get': 'retrieve','delete': 'destroy'}), name='order-delete'),
    path('orders/', order_list, name='list'),
    path('orders/<int:pk>/', order_detail, name='detail'),

    path('orders/confirm_payment/<str:order_id>/', confirm_payment, name='confirm_payment'),

    path('order/<str:order_id>/payment/', save_payment, name='save_payment'),
    path('order/<str:order_id>/details/', get_order_details, name='get_order_details'),



    # URLs for Shaxar
    path('shaxarlar/', shaxar_list, name='shaxar_list'),
    path('shaxarlar/<int:pk>/', shaxar_edit_delete, name='shaxar_edit_delete'),

    #card
    path('cards/', card_list, name='card_list'),
    path('cards/<int:pk>/', card_edit_delete, name='card_edit_delete'),

    # URLs for Mahsulot
    path('mahsulotlar/', mahsulot_list, name='mahsulot_list'),
    path('mahsulotlar/<int:pk>/', mahsulot_edit_delete, name='mahsulot_edit_delete'),

    # URLs for Rayon
    path('rayonlar/', rayon_list, name='rayon_list'),
    path('rayonlar/<int:pk>/', rayon_edit_delete, name='rayon_edit_delete'),
    #cards
    path('card/', CardViewSet.as_view({'get': 'list', 'post': 'create'}), name='card'),
    path('card/<int:pk>/', get_card, name='get_card'),
    # URLs for Korinish
    path('korinishlar/', korinish_list, name='korinish_list'),
    path('korinishlar/<int:pk>/', korinish_edit_delete, name='korinish_edit_delete'),


    path('accounts/register', add_admin_view, name='add_admin'),
    path('accounts/login/', login_view, name='login'),
    path('', home, name='home'),


]




