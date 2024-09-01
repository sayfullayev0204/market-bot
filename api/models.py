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
        return self.nomi

class Rayon(models.Model):
    mahsulot = models.ForeignKey(Mahsulot, on_delete=models.CASCADE)
    nomi = models.CharField(max_length=300)

    def __str__(self):
        return self.nomi

class Korinish(models.Model):
    rayon = models.ForeignKey(Rayon, on_delete=models.CASCADE)
    nomi = models.CharField(max_length=300)

    def __str__(self):
        return self.nomi


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shaxar = models.ForeignKey(Shaxar, on_delete=models.CASCADE)
    mahsulot = models.ForeignKey(Mahsulot, on_delete=models.CASCADE)
    rayon = models.ForeignKey(Rayon, on_delete=models.CASCADE)
    korinish = models.ForeignKey(Korinish, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=8, unique=True)
    confirmed = models.BooleanField(default=False)
    payment_received = models.BooleanField(default=False)
    admin_confirmed = models.BooleanField(default=False)
    payment_amount = models.IntegerField(null=True, blank=True)
    receipt_photo = models.ImageField('chek/', null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
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
