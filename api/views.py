from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render,redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status,viewsets
from .models import User, Shaxar, Mahsulot, Rayon, Korinish, Order,Card
from .serializers import UserSerializer, ShaxarSerializer, MahsulotSerializer, RayonSerializer, KorinishSerializer, OrderSerializer,CardSerializer
import threading
import time
from .forms import ShaxarForm, MahsulotForm, RayonForm, KorinishForm,CardForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login

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
        queryset = super().get_queryset()
        shaxar_id = self.request.query_params.get('shaxar_id', None)
        if shaxar_id:
            queryset = queryset.filter(shaxar_id=shaxar_id)
        return queryset

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

class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
@api_view(['GET'])
def get_card(request, pk):
    try:
        card = Card.objects.get(pk=pk)
        serializer = CardSerializer(card)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Card.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
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


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Order
from .serializers import OrderSerializer

@api_view(['PATCH'])
def confirm_payment(request, order_id):
    try:
        order = Order.objects.get(order_id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = OrderSerializer(order, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def order_list(request):
    orders = Order.objects.filter(receipt_image__isnull=False).order_by('-created_at')
    return render(request, 'list.html', {'orders': orders})

# Order Detail View
@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == "POST":
        if 'confirm' in request.POST:
            order.confirmed = True
            order.save()
            send_confirmation_message(order.user.telegram_id, order.order_id, confirmed=True)
            messages.success(request, f"Order {order.order_id} has been confirmed.")
        elif 'reject' in request.POST:
            send_confirmation_message(order.user.telegram_id, order.order_id, confirmed=False)
            order.delete()
            messages.error(request, f"Order {order.order_id} has been rejected and removed from the system.")
        return redirect('list')  
    
    return render(request, 'detail.html', {'order': order})

def send_confirmation_message(telegram_id, order_id, confirmed):
    import requests

    bot_token = '6804578580:AAFgkIvNyRzzLRhaouWCzyBRJ-87jUk6OAs'
    if confirmed:
        text = f"Ваш заказ с идентификатором {order_id} подтвержден!\n Доставка через 29 дней."
    else:
        text = f"Ваш заказ с идентификатором {order_id} отклонен и удален из системы."

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    data = {
        'chat_id': telegram_id,
        'text': text
    }
    
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print(f"Message sent to {telegram_id}")
    else:
        print(f"Failed to send message to {telegram_id}")

# CRUD Views for Shaxar
@login_required
def shaxar_list(request):
    shaxarlar = Shaxar.objects.all()
    if request.method == 'POST':
        form = ShaxarForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('shaxar_list')
    else:
        form = ShaxarForm()
    return render(request, 'shaxar_list.html', {'shaxarlar': shaxarlar, 'form': form})

@login_required
def shaxar_edit_delete(request, pk):
    shaxar = get_object_or_404(Shaxar, pk=pk)
    if request.method == 'POST':
        if 'edit' in request.POST:
            form = ShaxarForm(request.POST, instance=shaxar)
            if form.is_valid():
                form.save()
                return redirect('shaxar_list')
        elif 'delete' in request.POST:
            shaxar.delete()
            return redirect('shaxar_list')
    else:
        form = ShaxarForm(instance=shaxar)
    return render(request, 'form.html', {'form': form, 'shaxar': shaxar})

# CRUD Views for Mahsulot
@login_required
def mahsulot_list(request):
    mahsulotlar = Mahsulot.objects.all()
    if request.method == 'POST':
        form = MahsulotForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('mahsulot_list')
    else:
        form = MahsulotForm()
    return render(request, 'mahsulots.html', {'mahsulotlar': mahsulotlar, 'form': form})

@login_required
def mahsulot_edit_delete(request, pk):
    mahsulot = get_object_or_404(Mahsulot, pk=pk)
    if request.method == 'POST':
        if 'edit' in request.POST:
            form = MahsulotForm(request.POST, instance=mahsulot)
            if form.is_valid():
                form.save()
                return redirect('mahsulot_list')
        elif 'delete' in request.POST:
            mahsulot.delete()
            return redirect('mahsulot_list')
    else:
        form = MahsulotForm(instance=mahsulot)
    return render(request, 'form.html', {'form': form, 'mahsulot': mahsulot})

# CRUD Views for Rayon
@login_required
def rayon_list(request):
    rayonlar = Rayon.objects.all()
    if request.method == 'POST':
        form = RayonForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rayon_list')
    else:
        form = RayonForm()
    return render(request, 'rayon_list.html', {'rayonlar': rayonlar, 'form': form})

@login_required
def rayon_edit_delete(request, pk):
    rayon = get_object_or_404(Rayon, pk=pk)
    if request.method == 'POST':
        if 'edit' in request.POST:
            form = RayonForm(request.POST, instance=rayon)
            if form.is_valid():
                form.save()
                return redirect('rayon_list')
        elif 'delete' in request.POST:
            rayon.delete()
            return redirect('rayon_list')
    else:
        form = RayonForm(instance=rayon)
    return render(request, 'form.html', {'form': form, 'rayon': rayon})

# CRUD Views for Korinish
@login_required
def korinish_list(request):
    rayons = Rayon.objects.all()
    korinishlar = Korinish.objects.all()
    if request.method == 'POST':
        form = KorinishForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('korinish_list')
    else:
        form = KorinishForm()
    return render(request, 'korinishs.html', {'korinishlar': korinishlar,'rayons':rayons, 'form': form})

@login_required
def korinish_edit_delete(request, pk):
    korinish = get_object_or_404(Korinish, pk=pk)
    if request.method == 'POST':
        if 'edit' in request.POST:
            form = KorinishForm(request.POST, instance=korinish)
            if form.is_valid():
                form.save()
                return redirect('korinish_list')
        elif 'delete' in request.POST:
            korinish.delete()
            return redirect('korinish_list')
    else:
        form = KorinishForm(instance=korinish)
    return render(request, 'form.html', {'form': form, 'korinish': korinish})

# Add Admin View
@login_required
def add_admin_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_superuser = True
            user.is_staff = True
            user.save()
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'add_admin.html', {'form': form})

# Login View
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


@login_required
def card_list(request):
    cards = Card.objects.all()
    if request.method == 'POST':
        form = CardForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('card_list')
    else:
        form = CardForm()
    return render(request, 'card_list.html', {'cards': cards, 'form': form})

@login_required
def card_edit_delete(request, pk):
    cards = get_object_or_404(Card, pk=pk)
    if request.method == 'POST':
        if 'edit' in request.POST:
            form = CardForm(request.POST, instance=cards)
            if form.is_valid():
                form.save()
                return redirect('card_list')
        elif 'delete' in request.POST:
            cards.delete()
            return redirect('card_list')
    else:
        form = CardForm(instance=cards)
    return render(request, 'form.html', {'form': form, 'shaxar': cards})



from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Order

@csrf_exempt
@require_POST
def save_payment(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    
    # Extract payment amount and receipt image from the request
    payment_amount = request.POST.get('payment_amount')
    receipt_image = request.FILES.get('receipt_image')
    
    if payment_amount:
        try:
            order.payment_amount = float(payment_amount)
        except ValueError:
            return JsonResponse({'error': 'Invalid payment amount'}, status=400)
    
    if receipt_image:
        order.receipt_image = receipt_image

    order.save()
    
    return JsonResponse({'status': 'Payment details saved successfully'})

# Optionally, you can create a view to get order details for debugging
def get_order_details(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    data = {
        'order_id': order.order_id,
        'user': order.user.id,
        'shaxar': order.shaxar.id,
        'mahsulot': order.mahsulot.id,
        'rayon': order.rayon.id,
        'korinish': order.korinish.id,
        'created_at': order.created_at.isoformat(),
        'confirmed': order.confirmed,
        'payment_amount': order.payment_amount,
        'receipt_image': order.receipt_image.url if order.receipt_image else None,
    }
    return JsonResponse(data)
