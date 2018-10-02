from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from bakery.models import Grocery, Recipe
from datetime import datetime
register = template.Library()

@register.simple_tag
def get_grocery_unit_dict():
    '''Return a dictionary containing a list of the default units and a hash for each Grocery name
    '''
    groceries = Grocery.objects.all()
    dict = {}
    for item in groceries:
        dict[item.name] = [item.default_units, item.hash]
    return mark_safe(dict)

@register.simple_tag
def get_recipes():
    '''Return a dictionary of recipes using their database ids as keys
    '''
    recipes = Recipe.objects.all()
    dict = {}
    for item in recipes:
        dict[item.id] = item.name
    return mark_safe(dict)

@register.filter
def dict_to_list(dict):
    '''Convert a dictionary into a sorted list
    '''
    list = []
    for entry in sorted(dict):
        list.append([entry, dict[entry]])
    return list

@register.filter
@stringfilter
def get_option_tag(str):
    '''
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
    #return '<option value="'+str+'">'+units[str]+'</option>'
    return '<option value="{str}">{units[str]}</option>'

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
    return Grocery.objects.get(hash=revert_name(custom_amount_hash)).name

@register.filter
@stringfilter
def get_option_tag_selected(str):
    '''
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
    #return mark_safe('<option value="'+str+'" selected>'+units[str]+'</option>')
    return mark_safe(f'<option value="{str}" selected>{units[str]}</option>')

@register.filter
@stringfilter
def revert_name(str):
    '''Remove the text 'custom_amount_' or 'custom_units_' from a string
    '''
    if str.startswith('custom_'):
        str = str.replace('custom_', '')
        if str.startswith('amount_'):
            str = str.replace('amount_', '')
        else:
            str = str.replace('units_', '')
    return str

@register.simple_tag
def get_datetime_now():
    '''return current datetime in the format YYYY-MM-DDTHH:MM:SS
    '''
    date = datetime.now().replace(microsecond=0)
    return date.isoformat()

@register.tag
def resolve_str(parser, token):
    try:
        tag_name, str = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0]
        )
    return ResolveStrNode(str)

class ResolveStrNode(template.Node):
    def __init__(self, str):
        self.str = template.Variable(str)

    def render(self, context):
        try:
            context[str] = self.str.resolve(context)
        except template.VariableDoesNotExist:
            pass
        return ''
