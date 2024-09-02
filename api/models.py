from django.db import models
import random

class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    username = models.CharField(max_length=100, unique=True, null=True, blank=True)

    def __str__(self):
        return self.name or "No Name"

class Shaxar(models.Model):
    nomi = models.CharField(max_length=300)

    def __str__(self):
        return self.nomi

class Mahsulot(models.Model):
    shaxar = models.ForeignKey(Shaxar, on_delete=models.CASCADE)
    nomi = models.CharField(max_length=300)
    narxi = models.IntegerField()

    def __str__(self):
        return f"{self.shaxar.nomi}ga {self.nomi}"

class Rayon(models.Model):
    mahsulot = models.ForeignKey(Mahsulot, on_delete=models.CASCADE)
    nomi = models.CharField(max_length=300)

    def __str__(self):
        return f"{self.mahsulot.shaxar.nomi}ga {self.nomi} tumaniga {self.mahsulot.nomi}"

class Korinish(models.Model):
    rayon = models.ForeignKey(Rayon, on_delete=models.CASCADE)
    nomi = models.CharField(max_length=300)

    def __str__(self):
        return self.nomi

class Card(models.Model):
    card_name = models.CharField(max_length=300)
    card_number = models.CharField(max_length=300)
    card_user = models.CharField(max_length=300)

    def __str__(self):
        return self.card_name

class Order(models.Model):
    order_id = models.CharField(max_length=8, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shaxar = models.ForeignKey(Shaxar, on_delete=models.CASCADE)
    mahsulot = models.ForeignKey(Mahsulot, on_delete=models.CASCADE)
    rayon = models.ForeignKey(Rayon, on_delete=models.CASCADE)
    korinish = models.ForeignKey(Korinish, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed = models.BooleanField(default=False)
    
    # New fields for payment
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    receipt_image = models.ImageField(upload_to='receipts/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = self.generate_unique_id()
        super().save(*args, **kwargs)

    def generate_unique_id(self):
        while True:
            new_id = ''.join(random.choices('0123456789', k=8))
            if not Order.objects.filter(order_id=new_id).exists():
                return new_id

    def __str__(self):
        return f"Order {self.order_id} by {self.user.name} {self.created_at}"