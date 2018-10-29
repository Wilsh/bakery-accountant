from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from bakery.models import Grocery, Ingredient, Recipe
from datetime import datetime, date

register = template.Library()

@register.simple_tag
def get_grocery_unit_dict():
    '''Return a dictionary containing a list of the default units and a 
    hash for each Grocery name
    '''
    groceries = Grocery.objects.all()
    dict = {}
    for item in groceries:
        dict[item.name] = [item.default_units, item.hash]
    return mark_safe(dict)

@register.simple_tag
def get_recipes():
    '''Return a dictionary of Recipe names using their database ids as keys
    '''
    recipes = Recipe.objects.all()
    dict = {}
    for item in recipes:
        dict[item.id] = item.name
    return mark_safe(dict)

@register.filter
def dict_to_list(dict):
    '''Convert a dictionary into a list of key-value pairs sorted by key
    '''
    list = []
    for entry in sorted(dict):
        list.append([entry, dict[entry]])
    return list

@register.filter
@stringfilter
def get_option_tag(str):
    '''Return a string formatted for use as an option of a select element.
    The returned string is not marked safe because this tag is intended to
    produce a string that is used in a comparison and not as actual html.
    str must be a key in the units dictionary.
    '''
    units = {
        'ct': 'Count',
        'p': 'Pinch',
        'tsp': 'Teaspoon',
        'tbsp': 'Tablespoon',
        'floz': 'Fluid Ounce',
        'C': 'Cup',
        'pt': 'Pint',
        'qt': 'Quart',
    }
    return f'<option value="{str}">{units[str]}</option>'

@register.filter
@stringfilter
def get_option_tag_selected(str):
    '''Return a string formatted for use as an option of a select element.
    str must be a key in the units dictionary.
    '''
    units = {
        'ct': 'Count',
        'p': 'Pinch',
        'tsp': 'Teaspoon',
        'tbsp': 'Tablespoon',
        'floz': 'Fluid Ounce',
        'C': 'Cup',
        'pt': 'Pint',
        'qt': 'Quart',
    }
    return mark_safe(f'<option value="{str}" selected>{units[str]}</option>')

@register.filter
@stringfilter
def as_string(str):
    return str

@register.filter
def is_custom(str):
    return str.startswith('custom_')

@register.filter
def is_custom_amount(str):
    return str.startswith('custom_amount')

@register.filter
@stringfilter
def get_grocery_name(custom_amount_hash):
    '''Return the name attribute of the Grocery object corresponding 
    to the given hash value
    '''
    return Grocery.objects.get(hash=revert_name(custom_amount_hash)).name

@register.filter
@stringfilter
def revert_name(str):
    '''Remove the text 'custom_amount_' or 'custom_units_' from the start 
    of a string
    '''
    if str.startswith('custom_amount_') or str.startswith('custom_units_'):
        str = str.replace('custom_', '')
        if str.startswith('amount_'):
            str = str.replace('amount_', '')
        else:
            str = str.replace('units_', '')
    return str

@register.simple_tag
def get_datetime_now():
    '''Return current datetime in the format YYYY-MM-DDTHH:MM:SS
    '''
    date = datetime.now().replace(microsecond=0)
    return date.isoformat()

@register.simple_tag
def get_date():
    '''Return current date in the format YYYY-MM-DD
    '''
    return date.today().isoformat()

@register.simple_tag
def get_ingredient(grocery, component):
    '''Return the Ingredient object corresponding to the given Grocery 
    and Component objects
    '''
    return Ingredient.objects.get(for_grocery=grocery, for_component=component)

@register.filter
@stringfilter
def get_common_fraction(num):
    '''Given the Decimal 'num' with three decimal places, return its 
    representation as a fraction or mixed number if the decimal component 
    has a common fraction as seen in recipes. A num in the form 'x.000' is 
    returned without the decimal component
    '''
    dict = {
        '875': '7/8',
        '750': '3/4',
        '667': '2/3',
        '625': '5/8',
        '500': '1/2',
        '375': '3/8',
        '333': '1/3',
        '250': '1/4',
        '125': '1/8',
        '000': ''
    }
    string = str(num)
    out = ''
    wholenum = int(string[:len(string)-4])
    if wholenum > 0:
        out += str(wholenum) + ' '
    if string[len(string)-3:] in dict:
        out += dict[string[len(string)-3:]]
    else:
        return string
    return out.strip()
