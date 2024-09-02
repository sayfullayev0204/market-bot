from rest_framework import serializers
from .models import User, Shaxar, Mahsulot, Rayon, Korinish, Order,Card


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['telegram_id', 'name', 'username']

class ShaxarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shaxar
        fields = ['id', 'nomi']

class MahsulotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mahsulot
        fields = ['id', 'shaxar', 'nomi', 'narxi']

class RayonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rayon
        fields = ['id', 'mahsulot', 'nomi']

class KorinishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Korinish
        fields = ['id', 'rayon', 'nomi']

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['id', 'card_name', 'card_number', 'card_user']

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['user', 'shaxar', 'mahsulot', 'rayon', 'korinish', 'order_id','created_at', 'confirmed']