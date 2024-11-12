from django.db import models
from django.core.exceptions import ValidationError
from users.models import Users
from product.models import Product, ProductVarient


# Create your models here.


class Cart(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='carts', null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_charge = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email

    def calculate_total(self):
        self.total_price = sum(item.total_price for item in self.items.all() if item.quantity > 0)
        self.delivery_charge = 0 if self.total_price > 4999 else 99
        self.total_price += self.delivery_charge
        self.save()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVarient, on_delete=models.SET_NULL, null=True, blank=True, related_name='cart_items')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.quantity <= 0 or self.product.quantity < self.quantity:
            raise ValidationError(f"Insufficient quantity for {self.product.name}. Available: {self.product.quantity}")

    def save(self, *args, **kwargs):
        self.clean()

        # Set total_price, ensuring it's 0 if quantity is 0
        if self.quantity > 0:
            self.total_price = (self.price - self.discount) * self.quantity
        else:
            self.total_price = 0

        # Save CartItem, then update cart total
        super().save(*args, **kwargs)
        self.cart.calculate_total()

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in cart ID {self.cart.id}"
