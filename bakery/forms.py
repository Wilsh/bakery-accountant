from django import forms
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

import re
from decimal import Decimal

from bakery.models import Grocery, Component, Recipe, Order

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

TYPES = (
    ('B', 'Baked'),
    ('I', 'Icing'),
    ('D', 'Decoration'),
    ('O', 'Other'),
)

class GroceryForm(forms.Form):
    name = forms.CharField(label='Ingredient name', max_length=120)
    cost = forms.DecimalField(label='Purchase price', max_digits=5, decimal_places=2, 
        validators=[MinValueValidator(0, message="Price must not be negative.")]
        )
    cost_amount = forms.DecimalField(label='Purchase amount', max_digits=7, decimal_places=3, 
        validators=[MinValueValidator(Decimal('0.001'), message="Amount must be greater than zero.")]
        )
    units = forms.ChoiceField(label='Purchase units', choices=UNIT_TYPES)
    default_units = forms.ChoiceField(label='Default units for recipe measurement', choices=UNIT_TYPES)
    
    def clean_name(self):
        name = self.cleaned_data['name']
        try:
            Grocery.objects.get(name__iexact=name)
            raise forms.ValidationError(
                _("An ingredient named \"%(name)s\" already exists."),
                params={'name': name},
                )
        except Grocery.DoesNotExist:
            pass
        return name
    
    def clean_default_units(self):
        if self.cleaned_data['default_units'] == 'ct' and self.cleaned_data['units'] != 'ct':
            raise forms.ValidationError(
                _("Cannot set Default units to 'Count' if Purchase units is not also 'Count'."))
        return self.cleaned_data['default_units']

def parse_str_to_decimal(str):
    '''Converts a string containing a whole number, mixed number, fraction, or decimal to a Decimal.
    Returns (False, "error message") if the given string is in an invalid format.
    Returns (True, Decimal) otherwise.    
    '''
    message = '\"%(str)s\" is not formatted properly. Use a whole number, mixed number, fraction, or decimal (e.g. 2 1/4 or 2.25)'
    str = str.strip()
    number = Decimal(0)
    #match not "/. 0123456789"
    pattern = re.compile(r"[^\/\. \d]")
    if pattern.search(str) is not None:
        message = '\"%(str)s\" contains invalid characters. Use only the character \"/\" or \".\" and numbers.'
        return(False, message)
    #match "0123456789"
    pattern = re.compile(r"[\d]")
    if pattern.search(str) is None:
        message = '\"%(str)s\" contains no numbers.'
        return(False, message)
    #match "."
    pattern = re.compile(r"[\.]")
    if pattern.search(str) is not None:
        #check for excess "."
        if str.count('.') > 1:
            message = '\"%(str)s\" contains too many decimals. Only one is allowed.'
            return(False, message)
        #match " "
        pattern = re.compile(r"[ ]")
        if pattern.search(str) is not None:
            message = '\"%(str)s\" contains invalid characters. Do not combine spaces with a decimal.'
            return(False, message)
        #match "/"
        pattern = re.compile(r"[\/]")
        if pattern.search(str) is not None:
            message = '\"%(str)s\" contains invalid characters. Do not combine a slash with a decimal.'
            return(False, message)
        #check validity as decimal
        try:
            number = Decimal(str)
        except Exception:
            return(False, message)
    else:
        #match "/"
        pattern = re.compile(r"[\/]")
        if pattern.search(str) is not None:
            #check for excess "/"
            if str.count('/') > 1:
                message = '\"%(str)s\" contains too many slashes. Only one is allowed.'
                return(False, message)
            #match " "
            pattern = re.compile(r"[ ]")
            if pattern.search(str) is not None:
                #check for valid mixed number
                #multiple spaces between the whole number and fraction are permitted
                numbers = str.split(' ')
                for char in numbers[1:-1]:
                    if char != '':
                        return(False, message)
                try:
                    whole_num = Decimal(numbers[0])
                except Exception:
                    return(False, message)
                fraction = numbers[-1]
            else:
                whole_num = number #Decimal(0)
                fraction = str
            #check for valid fraction
            numbers = fraction.split('/')
            try:
                numerator = Decimal(numbers[0])
                denominator = Decimal(numbers[1])
            except Exception:
                return(False, message)
            if denominator == 0:
                message = '\"%(str)s\" cannot divide by zero.'
                return(False, message)
            number = whole_num + (numerator / denominator)
        else:
            #check valid whole number
            try:
                number = Decimal(str)
            except Exception:
                return(False, message)
    return (True, number)

def validate_str_as_decimal(str):
    valid, message = parse_str_to_decimal(str)
    if not valid:
        raise ValidationError(
            _(message),
            params={'str': str},
        )

class ComponentForm(forms.Form):
    name = forms.CharField(label='Component name', max_length=120)
    component_type = forms.ChoiceField(label='Component type', choices=TYPES)
    groceries = forms.ModelMultipleChoiceField(label='Ingredients', queryset=Grocery.objects.all(), to_field_name="name")
    notes = forms.CharField(label='Notes', required=False, widget=forms.Textarea)
    units = forms.ChoiceField(label='Units', choices=UNIT_TYPES, required=False)
    
    def __init__(self, *args, **kwargs):
        do_more = True
        try:
            amounts = kwargs.pop('extra')
        except KeyError:
            do_more = False
        super(ComponentForm, self).__init__(*args, **kwargs)
        if do_more:
            #add fields for each ingredient amount and unit
            for name in sorted(amounts):
                amount_hash_id = amounts[name][0][0]
                units_hash_id = amounts[name][1][0]
                self.fields[amount_hash_id] = forms.CharField(label=amount_hash_id, max_length=10, validators=[validate_str_as_decimal])
                self.fields[units_hash_id] = forms.ChoiceField(label=units_hash_id, choices=UNIT_TYPES)
    
    def clean(self):
        #validation for units in added fields
        cleaned_data = super().clean()
        for field in cleaned_data:
            if field.startswith('custom_units_'):
                msg = ""
                str = field.replace('custom_units_', '')
                grocery = Grocery.objects.get(hash=str)
                if cleaned_data[field] == 'ct' and grocery.units != 'ct':
                    msg = "Cannot select 'Count' for an ingredient whose default units are not 'Count'"
                    break
                elif cleaned_data[field] != 'ct' and grocery.units == 'ct':
                    msg = "The default units for this ingredient are 'Count'"
                    break
        if msg:
            self.add_error(field, forms.ValidationError(_(msg)))
        return cleaned_data
    
    def clean_name(self):
        name = self.cleaned_data['name']
        try:
            Component.objects.get(name__iexact=name)
            raise forms.ValidationError(
                _("A component named \"%(name)s\" already exists."),
                params={'name': name},
                )
        except Component.DoesNotExist:
            pass
        return name

class RecipeForm(forms.Form):
    name = forms.CharField(label='Recipe name', max_length=140)
    component_baked = forms.ModelMultipleChoiceField(label='Baked components', queryset=Component.objects.filter(component_type='B'), to_field_name="name", required=False)
    component_icing = forms.ModelMultipleChoiceField(label='Icing components', queryset=Component.objects.filter(component_type='I'), to_field_name="name", required=False)
    component_decoration = forms.ModelMultipleChoiceField(label='Decoration components', queryset=Component.objects.filter(component_type='D'), to_field_name="name", required=False)
    component_other = forms.ModelMultipleChoiceField(label='Other components', queryset=Component.objects.filter(component_type='O'), to_field_name="name", required=False)
    time_estimate = forms.CharField(label='Estimated time to complete (hours)', max_length=10, validators=[validate_str_as_decimal])
    image = forms.ImageField(label='Image (optional)', required=False)
    notes = forms.CharField(label='Notes', required=False, widget=forms.Textarea)

    def clean_name(self):
        name = self.cleaned_data['name']
        try:
            Recipe.objects.get(name__iexact=name)
            raise forms.ValidationError(
                _("A recipe named \"%(name)s\" already exists."),
                params={'name': name},
                )
        except Recipe.DoesNotExist:
            pass
        return name

    def clean(self):
        cleaned_data = super(RecipeForm, self).clean()
        component_baked = cleaned_data.get('component_baked')
        component_icing = cleaned_data.get('component_icing')
        component_decoration = cleaned_data.get('component_decoration')
        component_other = cleaned_data.get('component_other')

        if component_baked or component_icing or component_decoration or component_other:
            pass
        else:
            self.add_error('component_baked', "At least one component must be selected.")

class OrderForm(forms.Form):
    customer = forms.CharField(label='Customer name', max_length=120)
    recipes = forms.ModelChoiceField(queryset=Recipe.objects.all(), empty_label="Select a recipe")
    delivery_date = forms.CharField()
    requires_delivery = forms.BooleanField(required=False, widget=forms.CheckboxInput)
    notes = forms.CharField(label='Notes', required=False, widget=forms.Textarea)
    
    def __init__(self, *args, **kwargs):
        do_more = True
        try:
            recipes = kwargs.pop('extra')
        except KeyError:
            do_more = False
        super(OrderForm, self).__init__(*args, **kwargs)
        if do_more:
            #add fields for additional recipes
            for item in recipes:
                if recipes[item] != '':
                    self.fields[item] = forms.ModelChoiceField(queryset=Recipe.objects.all(), empty_label="Select a recipe")
    
    def clean_delivery_date(self):
        date = self.cleaned_data['delivery_date']
        date = date.replace('T', ' ')
        return date

    
