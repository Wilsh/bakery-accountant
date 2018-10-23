from django.db import models
from django.forms import ModelForm
from django.utils import timezone

from decimal import Decimal
from math import ceil
import hashlib
from datetime import datetime

# Create your models here.
UNIT_TYPES = (
    ('ct', 'Count'),
    ('p', 'Pinch'),
    ('tsp', 'Teaspoon'),
    ('tbsp', 'Tablespoon'),
    ('floz', 'Fluid Ounce'),
    ('C', 'Cup'),
    ('pt', 'Pint'),
    ('qt', 'Quart'),
)

ONE = Decimal(1)
CONVERSIONS = {
    "p":    {"p": ONE, "tsp": ONE/Decimal(8), "tbsp": ONE/Decimal(24), "floz": ONE/Decimal(48), "C": ONE/Decimal(384), "pt": ONE/Decimal(768), "qt": ONE/Decimal(1536)},
    "tsp":  {"p": Decimal(8), "tsp": ONE, "tbsp": ONE/Decimal(3), "floz": ONE/Decimal(6), "C": ONE/Decimal(48), "pt": ONE/Decimal(96), "qt": ONE/Decimal(192)},
    "tbsp": {"p": Decimal(24), "tsp": Decimal(3), "tbsp": ONE, "floz": ONE/Decimal(2), "C": ONE/Decimal(16), "pt": ONE/Decimal(32), "qt": ONE/Decimal(64)},
    "floz": {"p": Decimal(48), "tsp": Decimal(6), "tbsp": Decimal(2), "floz": ONE, "C": ONE/Decimal(8), "pt": ONE/Decimal(16), "qt": ONE/Decimal(32)},
    "C": {"p": Decimal(384), "tsp": Decimal(48), "tbsp": Decimal(16), "floz": Decimal(8), "C": ONE, "pt": ONE/Decimal(2), "qt": ONE/Decimal(4)},
    "pt": {"p": Decimal(768), "tsp": Decimal(96), "tbsp": Decimal(32), "floz": Decimal(16), "C": Decimal(2), "pt": ONE, "qt": ONE/Decimal(2)},
    "qt": {"p": Decimal(1536), "tsp": Decimal(192), "tbsp": Decimal(64), "floz": Decimal(32), "C": Decimal(4), "pt": Decimal(2), "qt": ONE},
}

class Grocery(models.Model):
    '''An item used in a Component. The unit cost is calculated in terms of
    dollars per cup unless the base unit is Count.
    '''
    name = models.CharField(max_length=120, unique=True)
    cost = models.DecimalField(max_digits=5, decimal_places=2)
    cost_amount = models.DecimalField(max_digits=7, decimal_places=3)
    units = models.CharField(max_length=4, choices=UNIT_TYPES)
    default_units = models.CharField(max_length=4, choices=UNIT_TYPES)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    hash = models.CharField(max_length=33, default='a')

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "groceries"

    def __str__(self):
        return self.name

    def calculate_values(self):
        if self.cost_amount == 0:
            raise ValueError('Grocery.calculate_unit_cost() called with cost_amount assigned as zero')
        elif self.units == 'ct':
            self.unit_cost = self.cost / self.cost_amount
        else:
            self.unit_cost = (self.cost / self.cost_amount) / CONVERSIONS[self.units]["C"]
        #hash will be used as a CSS class, so ensure it begins with a letter
        self.hash = 'a' + hashlib.md5(self.name.encode('utf-8')).hexdigest()
        self.save()

class Ingredient(models.Model):
    '''Ingredient links a Grocery and Component with information about a
    particular instance of a Grocery.
    '''
    for_grocery = models.ForeignKey('Grocery', on_delete=models.CASCADE)
    for_component = models.ForeignKey('Component', on_delete=models.CASCADE)
    units = models.CharField(max_length=4, choices=UNIT_TYPES)
    amount = models.DecimalField(max_digits=7, decimal_places=3)

    def __str__(self):
        return f"Ingredient: {self.for_grocery.name} {self.amount} {self.units} Component: {self.for_component.name}"

    def get_cost(self):
        if self.units == 'ct':
            return self.amount * self.for_grocery.unit_cost
        return self.amount * (self.for_grocery.unit_cost / CONVERSIONS["C"][self.units])

class Component(models.Model):
    '''An item used in a Recipe.
    '''
    groceries = models.ManyToManyField(Grocery, through='Ingredient')
    name = models.CharField(max_length=120, unique=True)
    TYPES = (
        ('B', 'Baked'),
        ('I', 'Icing'),
        ('D', 'Decoration'),
        ('O', 'Other'),
    )
    component_type = models.CharField(max_length=1, choices=TYPES) #.get_component_type_display()
    cost = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(default='', blank=True)

    class Meta:
        ordering = ["component_type"]

    def __str__(self):
        return self.name

    def calculate_cost(self):
        total = Decimal(0)
        for item in self.groceries.all():
            total += item.ingredient_set.get(for_component=self).get_cost()
        self.cost = total
        self.save()
    
    def get_cost(self):
        return self.cost

class Recipe(models.Model):
    '''An item used in an Order.
    '''
    name = models.CharField(max_length=140, unique=True)
    components = models.ManyToManyField(Component)
    time_estimate = models.DecimalField(max_digits=5, decimal_places=3)
    time_actual = models.DecimalField(max_digits=5, decimal_places=3, default=0)
    cost = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    price = models.PositiveSmallIntegerField(default=0)
    image = models.ImageField(default='default.jpg')
    notes = models.TextField(default='', blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name 

    def _calculate_cost(self):
        total = 0
        for item in self.components.all():
            total += item.get_cost()
        self.cost = total

    def _calculate_price(self):
        hourly_rate = 10
        if self.time_actual:
            subtotal = self.cost + (self.time_estimate * Decimal(hourly_rate))
        else:
            #new recipe; assume time_estimate is low
            subtotal = self.cost + (self.time_estimate * Decimal(1.3 * hourly_rate))
        self.price = ceil(subtotal)

    def calculate_values(self):
        self._calculate_cost()
        self._calculate_price()
        self.save()
    
    def get_price(self):
        return self.price

class Order(models.Model):
    '''The top-level organizational model. An Order contains one or more Recipes,
    a Recipe contains one or more Components, and a Component contains one or more
    Ingredients.
    '''
    recipes = models.ManyToManyField(Recipe, through='OrderQuantity')
    customer = models.CharField(max_length=120)
    created_date = models.DateTimeField(default=timezone.now)
    delivery_date = models.DateTimeField()
    requires_delivery = models.BooleanField(default=False)
    quoted_price = models.PositiveSmallIntegerField(default=0)
    price_paid = models.PositiveSmallIntegerField(default=0)
    postmortem_complete = models.BooleanField(default=False)
    notes = models.TextField(default='', blank=True)

    class Meta:
        ordering = ["-delivery_date"]

    def __str__(self): 
        return f"Order for {self.customer}"

    def calculate_quoted_price(self):
        total = 0
        for item in self.recipes.all():
            multiplier = item.orderquantity_set.get(for_order=self).get_quantity()
            total += item.get_price() * multiplier
        if self.requires_delivery:
            total += 15
        total = int(total)
        while total % 5 != 0:
            total += 1
        self.quoted_price = total
        self.save()

class OrderQuantity(models.Model):
    '''Allows for multiple quantities of the same Recipe to exist in the same Order.
    '''
    for_recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    for_order = models.ForeignKey('Order', on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(default=1)
    
    def __str__(self):
        return f"Order for: {self.for_order.customer} {self.quantity} {self.for_recipe.name}"
    
    def get_quantity(self):
        return self.quantity
