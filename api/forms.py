from django import forms
from .models import Shaxar, Mahsulot, Rayon, Korinish,Card

class ShaxarForm(forms.ModelForm):
    class Meta:
        model = Shaxar
        fields = ['nomi']

class MahsulotForm(forms.ModelForm):
    class Meta:
        model = Mahsulot
        fields = ['shaxar', 'nomi', 'narxi']

class RayonForm(forms.ModelForm):
    class Meta:
        model = Rayon
        fields = ['mahsulot', 'nomi']

class KorinishForm(forms.ModelForm):
    class Meta:
        model = Korinish
        fields = ['rayon', 'nomi']

class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ['card_name','card_user', 'card_number']