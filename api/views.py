from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from .models import User, Shaxar, Mahsulot, Rayon, Korinish, Order
from .serializers import UserSerializer, ShaxarSerializer, MahsulotSerializer, RayonSerializer, KorinishSerializer, OrderSerializer
import threading
import time

@api_view(['POST'])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def check_user(request, telegram_id):
    try:
        user = User.objects.get(telegram_id=telegram_id)
        serializer = UserSerializer(user)
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

class ShaxarViewSet(viewsets.ModelViewSet):
    queryset = Shaxar.objects.all()
    serializer_class = ShaxarSerializer

class MahsulotViewSet(viewsets.ModelViewSet):
    queryset = Mahsulot.objects.all()
    serializer_class = MahsulotSerializer

    def get_queryset(self):
        shaxar_id = self.request.query_params.get('shaxar_id')
        if shaxar_id:
            return self.queryset.filter(shaxar_id=shaxar_id)
        return self.queryset

class RayonViewSet(viewsets.ModelViewSet):
    queryset = Rayon.objects.all()
    serializer_class = RayonSerializer

    def get_queryset(self):
        mahsulot_id = self.request.query_params.get('mahsulot_id')
        if mahsulot_id:
            return self.queryset.filter(mahsulot_id=mahsulot_id)
        return self.queryset

class KorinishViewSet(viewsets.ModelViewSet):
    queryset = Korinish.objects.all()
    serializer_class = KorinishSerializer

    def get_queryset(self):
        rayon_id = self.request.query_params.get('rayon_id')
        if rayon_id:
            return self.queryset.filter(rayon_id=rayon_id)
        return self.queryset

@api_view(['POST'])
def create_order(request):
    data = request.data

    user = get_object_or_404(User, telegram_id=data['telegram_id'])
    shaxar = get_object_or_404(Shaxar, pk=data['shaxar_id'])
    mahsulot = get_object_or_404(Mahsulot, pk=data['mahsulot_id'])
    rayon = get_object_or_404(Rayon, pk=data['rayon_id'])
    korinish = get_object_or_404(Korinish, pk=data['korinish_id'])

    order = Order.objects.create(
        user=user,
        shaxar=shaxar,
        mahsulot=mahsulot,
        rayon=rayon,
        korinish=korinish
    )

    threading.Thread(target=cancel_order_after_timeout, args=(order,)).start()

    serializer = OrderSerializer(order)

    response_data = serializer.data
    response_data['user_name'] = user.name  
    response_data['created_at'] = order.created_at.strftime('%Y-%m-%d %H:%M:%S')  

    return Response(response_data, status=status.HTTP_201_CREATED)

def cancel_order_after_timeout(order):
    time.sleep(172800) 
    order = Order.objects.get(pk=order.pk)
    if not order.confirmed:
        notify_user_about_payment(order)
        time.sleep(300) 
        order = Order.objects.get(pk=order.pk)
        if not order.confirmed:
            order.delete()

def notify_user_about_payment(order):
    
    pass

# Confirm payment

TELEGRAM_BOT_TOKEN = 'your_telegram_bot_token_here'

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    requests.post(url, data=payload)

def confirm_payment(request):
    data = request.data
    order = get_object_or_404(Order, order_id=data['order_id'])
    order.confirmed = True
    order.save()

    # Get the user associated with the order
    user = order.user  # Assuming there's a ForeignKey to User in the Order model
    telegram_id = user.telegram_id

    # Send a confirmation message to the user's Telegram
    message = f"Your payment for Order #{order.order_id} has been confirmed. Thank you!"
    send_telegram_message(telegram_id, message)

    return Response({"status": "Payment confirmed"}, status=status.HTTP_200_OK)


@api_view(['GET'])
def check_order_id(request):
    order_id = request.GET.get('order_id')
    if not order_id:
        return JsonResponse({'error': 'Order ID not provided'}, status=400)

    exists = Order.objects.filter(order_id=order_id).exists()
    return JsonResponse({'exists': exists})

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    lookup_field = 'order_id'  

    def destroy(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id')
        try:
            order = self.get_queryset().get(order_id=order_id)
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def order_list(request):
    orders = Order.objects.all()
    return render(request, 'list.html', {'orders': orders})
