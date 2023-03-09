import email
from email.mime import image
from operator import truediv
from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, null= True)
    email = models.CharField(max_length=200, null= True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.CharField(max_length=200, primary_key=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    year_public = models.CharField(max_length = 10)
    publisher = models.CharField(max_length=200)
    image_url = models.CharField(max_length=200, default='image/cart.png')
    price = models.FloatField(default= 10)
    def __str__(self):
        return self.title
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete= models.SET_NULL, blank=True, null=True)
    date_order = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False, null=True, blank= False)
    transaction_id = models.CharField(max_length=200, null=True)

    def __str__(self):
        return str(self.transaction_id)
    
    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        return total
    
    @property
    def get_cart_item_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total
    
    @property
    def shipping(self):
        shipping = True
        return shipping
    
class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete= models.SET_NULL, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete= models.SET_NULL, blank=True, null=True )
    quantity = models.IntegerField(default=0, null= True, blank= True)
    date_added = models.DateTimeField(auto_now_add=True)
    @property
    def get_total(self):
        total = self.product.price * self.quantity
        return total

class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete= models.SET_NULL, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete= models.SET_NULL, blank=True, null=True )
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    Phonenumber = models.CharField(max_length=200)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.address)


