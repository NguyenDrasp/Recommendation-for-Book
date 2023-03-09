from django.urls import path
from . import views

urlpatterns = [
    path('', views.store, name="store"),
    path('cart/', views.cart, name="cart"),
    path('checkout/', views.checkout, name="checkout"),
    path('createdatabase/', views.addtoDB, name='addtoDB'),
    path('update_item/', views.updateItem, name="update_item"),
    path('processOrder/', views.processOrder, name="processOrder"),
    path('product/<product_id>',views.product_view, name="product_view")
]