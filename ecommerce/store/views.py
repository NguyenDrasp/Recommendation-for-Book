from datetime import datetime
from itertools import product
from statistics import quantiles
from urllib.robotparser import RequestRate
from venv import create
from django.shortcuts import render
from .models import *
from django.http import JsonResponse
import json
import datetime
import pandas as pd
from .utils import cartData, cookieCart, guessOrder
from .RecSys.Recomendation import *
# Create your views here.

ratings=pd.read_csv('./Data/Ratings.csv')
users=pd.read_csv("./Data/Users.csv")
books=pd.read_csv("./Data/Books.csv")
books_data=books.merge(ratings,on="ISBN")

df=books_data.copy()
df.dropna(inplace=True)
df.reset_index(drop=True,inplace=True)
df.drop(columns=["Year-Of-Publication","Image-URL-S","Image-URL-M"],axis=1,inplace=True)
df.drop(index=df[df["Book-Rating"]==0].index,inplace=True)
df["Book-Title"]=df["Book-Title"].apply(lambda x: re.sub("[\W_]+"," ",x).strip())

new_df=df[df['User-ID'].map(df['User-ID'].value_counts()) > 200]  # Drop users who vote less than 200 times.
users_pivot=new_df.pivot_table(index=["User-ID"],columns=["ISBN"],values="Book-Rating")
users_pivot.fillna(0,inplace=True)


def store (request):
    data = cartData(request)
    top10_id = popular_book(df, 10)["ISBN"]
    user_id=random.choice(new_df["User-ID"].values)
    user_based_rec=user_based(new_df,users_pivot,df,user_id)
    books_for_user=common(new_df,user_based_rec,user_id)
    cartItems = data['cartItems']
    x = Product.objects.filter(id = top10_id[0])
    for i in top10_id[1:]:
        y = Product.objects.filter(id = i)
        x = x|y
    recuser_item = Product.objects.filter(id = books_for_user[0])
    for i in books_for_user[1:]:
        y = Product.objects.filter(id = i)
        recuser_item = recuser_item|y
    recuser_item = recuser_item|x
    recuser_item = recuser_item[:5]
    
    products = Product.objects.all()
    context = {
        'products': products,
        'cartItems': cartItems,
        'top': x,
        'recu': recuser_item
    }
    return render(request, 'store/store.html', context)

def cart (request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items ,'order': order, 'cartItems':cartItems}
    return render(request, 'store/cart.html', context)

def product_view(request, product_id):
    data = cartData(request)

    product = Product.objects.get(id = product_id)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    
    Rec = item_based(df,product_id)
    x = Product.objects.filter(id = Rec[1])
    for i in Rec[2:]:
        y = Product.objects.filter(id = i)
        x = x|y
    context = {'items': items ,'order': order, 'cartItems':cartItems, 'product':product, 'rec': x}
    return render(request, 'store/product_view.html', context)

def checkout (request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    
    context = {'items': items ,'order': order, 'cartItems':cartItems}
    return render(request, 'store/checkout.html', context)

def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    if request.user.is_authenticated:
        customer = request.user.customer
    else:
        customer, order = guessOrder(request, data)
    
    product = Product.objects.get(id = productId)
    order, created = Order.objects.get_or_create(customer = customer, complete = False)
    orderItem, created = OrderItem.objects.get_or_create(order = order, product = product)

    if action == 'add':
        orderItem.quantity += 1
    elif action == 'remove':
        orderItem.quantity -= 1
    orderItem.save()

    if orderItem.quantity <=0 :
        orderItem.delete()
    return JsonResponse('Item was added',  safe = False)

def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, create = Order.objects.get_or_create(customer = customer, complete= False)

    else:
        customer, order = guessOrder(request, data)
    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == float(order.get_cart_item_total):
        order.complete = True
    order.save()
    if order.shipping == True:
        ShippingAddress.objects.create(
            customer = customer,
            order = order,
            address = data['shipping']['address'],
            city = data['shipping']['City'],
            state = data['shipping']['Distric'],
        )

    return JsonResponse('Payment complete', safe = False)

def addtoDB(request):
    df = pd.read_csv("/home/datnt/Tài liệu học tập/2022.1/ProjectI/ecommerce/Data/popular_10.csv",low_memory=False)
    for i in range(0, len(df)):
        x = Product.objects.update_or_create(id = df['ISBN'][i], title = df['Book-Title'][i], author = df['Book-Author'][i], year_public = df['Year-Of-Publication'][i], publisher = df['Publisher'][i], image_url  = df['Image-URL-L'][i])
        print(x)
    return JsonResponse('Items was saveed',  safe = False)
