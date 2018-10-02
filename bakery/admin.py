from django.contrib import admin

# Register your models here.
from .models import Grocery, Ingredient, Component, Recipe, Order, OrderQuantity

admin.site.register(Grocery)
admin.site.register(Ingredient)
admin.site.register(Component)
admin.site.register(Recipe)
admin.site.register(Order)
admin.site.register(OrderQuantity)
