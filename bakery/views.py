from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import LoginRequiredMixin

from decimal import Decimal
from datetime import date
from collections import Counter
from PIL import Image
from os import remove

from bakery.models import Grocery, Ingredient, Component, Recipe, Order, OrderQuantity
from .forms import GroceryForm, ComponentForm, RecipeForm, OrderForm, parse_str_to_decimal

class HomeView(LoginRequiredMixin, generic.ListView):
    model = Order
    template_name = 'bakery/home.html'
    context_object_name = 'orders'
    
    def get_queryset(self):
        return reversed(Order.objects.filter(delivery_date__gte=date.today()))

class GroceryListView(LoginRequiredMixin, generic.ListView):
    model = Grocery
    template_name = 'bakery/grocery_list.html'
    context_object_name = 'grocery_list'
    paginate_by = 20

class GroceryDetailView(LoginRequiredMixin, generic.DetailView):
    model = Grocery
    template_name = 'bakery/grocery_detail.html'
    context_object_name = 'grocery_info'

class ComponentListView(LoginRequiredMixin, generic.ListView):
    model = Component
    template_name = 'bakery/component_list.html'
    context_object_name = 'component_list'
    paginate_by = 10

class ComponentDetailView(LoginRequiredMixin, generic.DetailView):
    model = Component
    template_name = 'bakery/component_detail.html'
    context_object_name = 'component_info'

class RecipeListView(LoginRequiredMixin, generic.ListView):
    model = Recipe
    template_name = 'bakery/recipe_list.html'
    context_object_name = 'recipe_list'
    paginate_by = 6
        
class RecipeDetailView(LoginRequiredMixin, generic.DetailView):
    model = Recipe
    template_name = 'bakery/recipe_detail.html'
    context_object_name = 'recipe_info'

class OrderListView(LoginRequiredMixin, generic.ListView):
    model = Order
    template_name = 'bakery/order_list.html'
    context_object_name = 'order_list'
    paginate_by = 6

class OrderDetailView(LoginRequiredMixin, generic.DetailView):
    model = Order
    template_name = 'bakery/order_detail.html'
    context_object_name = 'order_info'
    
    def get_context_data(self, **kwargs):
        context = super(OrderDetailView, self).get_context_data(**kwargs)
        #add recipe info to context using OrderQuantity
        cost = 0
        recipe_list = []
        for order_quantity in OrderQuantity.objects.filter(for_order=context['order_info']):
            recipe_list.append(order_quantity)
            cost += order_quantity.for_recipe.cost * order_quantity.get_quantity()
        context['recipes'] = recipe_list
        context['cost'] = cost
        return context

@require_http_methods(["GET", "POST"])
@login_required
def create_grocery(request):
    if request.method == 'POST':
        form = GroceryForm(request.POST)
        print(request.POST)
        if form.is_valid():
            item = Grocery(
                    name = form.cleaned_data['name'],
                    cost = form.cleaned_data['cost'],
                    cost_amount = form.cleaned_data['cost_amount'],
                    units = form.cleaned_data['units'],
                    default_units = form.cleaned_data['units'] if form.cleaned_data['units'] == 'ct' else form.cleaned_data['default_units']
                    )
            item.save()
            item.calculate_values()
            return HttpResponseRedirect(reverse('bakery:view-groceries'))
    else:
        form = GroceryForm()
    return render(request, 'bakery/addgrocery.html', {'form': form})

def revert_name(str):
    '''Remove the text 'custom_amount_' or 'custom_units_' from the start of a string
    '''
    if str.startswith('custom_amount_') or str.startswith('custom_units_'):
        str = str.replace('custom_', '')
        if str.startswith('amount_'):
            str = str.replace('amount_', '')
        else:
            str = str.replace('units_', '')
    return str

def component_sort_post_to_dict(post):
    '''Given a QueryDict.dict() object, return a dictionary of list pairs where each
    pair is a property belonging to a related Grocery and in the order: amount, units
    e.g. {Grocery.name:[['custom_amount_foo', 2], ['custom_units_foo', 'tsp']]}
    '''
    dict = {}
    for entry in sorted(post):
        if entry.startswith('custom_'):
            name = Grocery.objects.get(hash=revert_name(entry)).name
            try:
                #units
                dict[name].append([entry, post[entry]])
            except KeyError:
                #amount
                dict[name] = [[entry, post[entry]]]
    return dict

@require_http_methods(["GET", "POST"])
@login_required
def create_component(request):
    added_fields_context = {}
    if request.method == 'POST':
        #manage dynamically-added fields
        added_fields_context = component_sort_post_to_dict(request.POST.dict())
        form = ComponentForm(request.POST, extra=added_fields_context)
        if form.is_valid():
            #create new Component
            item = Component(
                    name = form.cleaned_data['name'],
                    component_type = form.cleaned_data['component_type'],
                    notes = form.cleaned_data['notes']
                    )
            item.save()
            #link new Component with each Grocery through an Ingredient
            for entry in added_fields_context:
                grocery = Grocery.objects.get(name=entry)
                success, number = parse_str_to_decimal(form.cleaned_data[added_fields_context[entry][0][0]])
                if success:
                    ingredient = Ingredient(
                        for_grocery = grocery,
                        for_component = item,
                        units = form.cleaned_data[added_fields_context[entry][1][0]],
                        amount = number
                    )
                    ingredient.save()
            item.calculate_cost()
            return HttpResponseRedirect(reverse('bakery:view-components'))
    else:
        form = ComponentForm()
    return render(request, 'bakery/addcomponent.html', {'form': form, 'extra': added_fields_context})
    
@require_http_methods(["GET", "POST"])
@login_required
def edit_component(request, pk):
    component = get_object_or_404(Component, pk=pk)
    added_fields_context = {}
    if request.method == 'POST':
        #manage dynamically-added fields
        added_fields_context = component_sort_post_to_dict(request.POST.dict())
        form = ComponentForm(request.POST, extra=added_fields_context, edit=component.name)
        if form.is_valid():
            #clear existing Ingredient relations
            Ingredient.objects.filter(for_component=component).delete()
            #update Component
            component.name = form.cleaned_data['name']
            component.component_type = form.cleaned_data['component_type']
            component.notes = form.cleaned_data['notes']
            component.save()
            #link Component with each Grocery through an Ingredient
            for entry in added_fields_context:
                grocery = Grocery.objects.get(name=entry)
                success, number = parse_str_to_decimal(form.cleaned_data[added_fields_context[entry][0][0]])
                if success:
                    ingredient = Ingredient(
                        for_grocery = grocery,
                        for_component = component,
                        units = form.cleaned_data[added_fields_context[entry][1][0]],
                        amount = number
                    )
                    ingredient.save()
            component.update()
            return HttpResponseRedirect(reverse('bakery:component-detail', args=(pk,)))
    else:#Grocery.name:[['custom_amount_foo', 2], ['custom_units_foo', 'tsp']]
        ingredients = Ingredient.objects.filter(for_component=component)
        form_info = {
                'name':component.name,
                'component_type':component.component_type,
                'notes':component.notes
        }
        grocery_list = []
        for ingredient in ingredients:
            grocery = ingredient.for_grocery
            grocery_list.append(grocery)
            amount = 'custom_amount_' + grocery.hash
            units = 'custom_units_' + grocery.hash
            added_fields_context[grocery.name] = [[amount, ingredient.amount], [units, ingredient.units]]
            form_info[amount] = ingredient.amount
            form_info[units] = ingredient.units
        form_info['groceries'] = grocery_list
        form = ComponentForm(form_info, extra=added_fields_context, edit=component.name)
    return render(request, 'bakery/addcomponent.html', {'form': form, 'extra': added_fields_context})

@require_http_methods(["GET", "POST"])
@login_required
def create_recipe(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            #create new Recipe
            item = Recipe(
                    name = form.cleaned_data['name'],
                    time_estimate = form.cleaned_data['time_estimate'],
                    time_actual = form.cleaned_data['time_estimate'] if request.POST['hasBeenMadeBefore'] == 'yes' else 0,
                    notes = form.cleaned_data['notes']
                    )
            if request.FILES:
                item.image = request.FILES['file']
                item.user_uploaded_image = True
            item.save()
            #create image thumbnail
            if request.FILES:
                file = item.image.name.rsplit('/', 1)[1]
                img = Image.open(settings.MEDIA_ROOT + item.image.name)
                img.thumbnail((500,500))
                img.save(settings.MEDIA_ROOT + 'thumbnails/' + file)
                item.image_thumb = settings.MEDIA_URL + 'thumbnails/' + file
                item.save()
            #link Recipe to Components
            for component in form.cleaned_data.get('component_baked'):
                item.components.add(component)
            for component in form.cleaned_data.get('component_icing'):
                item.components.add(component)
            for component in form.cleaned_data.get('component_decoration'):
                item.components.add(component)
            for component in form.cleaned_data.get('component_other'):
                item.components.add(component)
            item.calculate_values()
            return HttpResponseRedirect(reverse('bakery:view-recipes'))
    else:
        form = RecipeForm()
    return render(request, 'bakery/addrecipe.html', {'form': form})
    
@require_http_methods(["GET", "POST"])
@login_required
def edit_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    context = {}
    context['made_before'] = True if recipe.time_actual else False
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, edit=recipe.name)
        if form.is_valid():
            #update Recipe
            recipe.name = form.cleaned_data['name']
            recipe.time_estimate = form.cleaned_data['time_estimate']
            recipe.time_actual = form.cleaned_data['time_estimate'] if request.POST['hasBeenMadeBefore'] == 'yes' else 0
            recipe.notes = form.cleaned_data['notes']
            if request.FILES:
                if recipe.user_uploaded_image:
                    #delete old images
                    try:
                        remove(recipe.image.path)
                    except FileNotFoundError:
                        pass
                    try:
                        remove(settings.MEDIA_ROOT.rsplit('/', 2)[0]+recipe.image_thumb)
                    except FileNotFoundError:
                        pass
                recipe.image = request.FILES['file']
                recipe.user_uploaded_image = True
            recipe.save()
            #create image thumbnail
            if request.FILES:
                file = recipe.image.name.rsplit('/', 1)[1]
                img = Image.open(settings.MEDIA_ROOT + recipe.image.name)
                img.thumbnail((500,500))
                img.save(settings.MEDIA_ROOT + 'thumbnails/' + file)
                recipe.image_thumb = settings.MEDIA_URL + 'thumbnails/' + file
                recipe.save()
            #remove old Components
            recipe.components.clear()
            #link Recipe to new Components
            for component in form.cleaned_data.get('component_baked'):
                recipe.components.add(component)
            for component in form.cleaned_data.get('component_icing'):
                recipe.components.add(component)
            for component in form.cleaned_data.get('component_decoration'):
                recipe.components.add(component)
            for component in form.cleaned_data.get('component_other'):
                recipe.components.add(component)
            recipe.update()
            return HttpResponseRedirect(reverse('bakery:recipe-detail', args=(pk,)))
    else:
        form_info = {
                'name':recipe.name,
                'component_baked': recipe.components.filter(component_type='B'),
                'component_icing': recipe.components.filter(component_type='I'),
                'component_decoration': recipe.components.filter(component_type='D'),
                'component_other': recipe.components.filter(component_type='O'),
                'time_estimate':recipe.time_estimate,
                'image':recipe.image,
                'notes':recipe.notes,
        }
        form = RecipeForm(form_info, edit=recipe.name)
    return render(request, 'bakery/editrecipe.html', {'form': form, 'context':context})

@require_http_methods(["POST"])
@login_required
def delete_recipe(request):
    pk=request.POST['pk']
    recipe = get_object_or_404(Recipe, pk=pk)
    if recipe.can_be_deleted():
        if recipe.user_uploaded_image:
            #delete related images
            try:
                remove(recipe.image.path)
            except FileNotFoundError:
                pass
            try:
                remove(settings.MEDIA_ROOT.rsplit('/', 2)[0]+recipe.image_thumb)
            except FileNotFoundError:
                pass
        recipe.delete()
        return HttpResponseRedirect(reverse('bakery:view-recipes'))
    return HttpResponseRedirect(reverse('bakery:recipe-detail', args=(pk,)))

def order_sort_post_to_dict(post):
    '''Given a QueryDict.dict() object, return a dictionary of Recipe model ids.
    '''
    dict = {}
    for key in post:
        if key.startswith('addedRecipe'):
            dict[key] = post[key]
    return dict

@require_http_methods(["GET", "POST"])
@login_required
def create_order(request):
    added_fields_context = {}
    if request.method == 'POST':
        #manage dynamically-added fields
        added_fields_context = order_sort_post_to_dict(request.POST.dict())
        form = OrderForm(request.POST, extra=added_fields_context)
        if form.is_valid():
            #print(request.POST)
            order = Order(
                    customer = form.cleaned_data['customer'],
                    delivery_date = form.cleaned_data['delivery_date'],
                    requires_delivery = form.cleaned_data['requires_delivery'],
                    notes = form.cleaned_data['notes']
                    )
            order.save()
            #use a dictionary to count number of occurences of each recipe
            recipeDict = Counter()
            recipeDict[form.cleaned_data['recipes']] += 1
            for key in form.cleaned_data:
                if key.startswith('addedRecipe'):
                    recipeDict[form.cleaned_data[key]] += 1
            #use count info to link new Order to each Recipe through an OrderQuantity
            for recipe in recipeDict:
                #print(f"recipe: {recipe} order: {order} quantity: {recipeDict[recipe]}")
                order_quantity = OrderQuantity(for_recipe = recipe,
                        for_order = order,
                        quantity = recipeDict[recipe]
                        )
                order_quantity.save()
            #print('############################################')
            #for key in form.cleaned_data.items():
                #print(key)
            order.calculate_prices()
            return HttpResponseRedirect(reverse('bakery:view-orders'))
        #print(request.POST)
    else:
        form = OrderForm()
    return render(request, 'bakery/addorder.html', {'form': form, 'extra': added_fields_context})

@require_http_methods(["GET", "POST"])
@login_required
def edit_order(request, pk):
    order = get_object_or_404(Order, pk=pk)
    added_fields_context = {}
    if request.method == 'POST':
        #manage dynamically-added fields
        added_fields_context = order_sort_post_to_dict(request.POST.dict())
        form = OrderForm(request.POST, extra=added_fields_context)
        if form.is_valid():
            #clear existing OrderQuantity relations
            OrderQuantity.objects.filter(for_order=order).delete()
            #update Order
            order.customer = form.cleaned_data['customer']
            order.delivery_date = form.cleaned_data['delivery_date']
            order.requires_delivery = form.cleaned_data['requires_delivery']
            order.deposit_paid = form.cleaned_data['deposit_paid']
            order.notes = form.cleaned_data['notes']
            order.save()
            #use a dictionary to count number of occurences of each recipe
            recipeDict = Counter()
            recipeDict[form.cleaned_data['recipes']] += 1
            for key in form.cleaned_data:
                if key.startswith('addedRecipe'):
                    recipeDict[form.cleaned_data[key]] += 1
            #use count info to link Order to each Recipe through an OrderQuantity
            for recipe in recipeDict:
                order_quantity = OrderQuantity(
                        for_recipe = recipe,
                        for_order = order,
                        quantity = recipeDict[recipe]
                        )
                order_quantity.save()
            order.calculate_prices()
            return HttpResponseRedirect(reverse('bakery:order-detail', args=(pk,))) 
    else:
        oqs = OrderQuantity.objects.filter(for_order=order)
        form_info = {
                'customer':order.customer,
                'delivery_date':order.delivery_date,
                'requires_delivery':order.requires_delivery,
                'deposit':order.deposit,
                'deposit_paid':order.deposit_paid,
                'notes':order.notes,
                'recipes':oqs[0].for_recipe.pk,
                'recipe_counter':1
        }
        skipped = False
        add = 1
        for count, oq in enumerate(oqs):
            qty = oq.quantity
            add -= 1
            while qty > 0:
                #ignore first recipe; its details are sent in form_info
                if skipped:
                    added_fields_context['addedRecipe'+str(count + add)] = oq.for_recipe.pk
                    form_info['addedRecipe'+str(count + add)] = oq.for_recipe.pk
                    form_info['recipe_counter'] = count + add + 1
                else:
                    skipped = True
                add += 1
                qty -= 1
        form = OrderForm(form_info, extra=added_fields_context)
    return render(request, 'bakery/editorder.html', {'form': form, 'extra': added_fields_context})
    
@require_http_methods(["POST"])
@login_required
def delete_order(request):
    order = get_object_or_404(Order, pk=request.POST['pk'])
    order.delete()
    return HttpResponseRedirect(reverse('bakery:home'))
