from django.conf.urls import url
from . import views
from django.conf import settings
from django.conf.urls.static import static
#from bakery.models import Grocery

app_name = 'bakery'
urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^orders/$', views.OrderListView.as_view(), name='view-order'),
    url(r'^add/grocery/$', views.create_grocery, name='create-grocery'),
    url(r'^add/component/$', views.create_component, name='create-component'),
    url(r'^add/recipe/$', views.create_recipe, name='create-recipe'),
    url(r'^add/order/$', views.create_order, name='create-order'),
    url(r'^recipes/detail/(?P<pk>[0-9]+)/$', views.RecipeDetailView.as_view(), name='recipe_detail'),
    url(r'^orders/detail/(?P<pk>[0-9]+)/$', views.OrderDetailView.as_view(), name='order_detail'),
    # url(r'^update/grocery/$', views.GroceryUpdate.as_view(), name='grocery-update'),
    # url(r'^items/detail/(?P<pk>[0-9]+)/$', views.ItemDetailView.as_view(), name='item_detail'),
    # url(r'^recipes/$', views.RecipeListView.as_view(), name='recipe_list'),
    # url(r'^recipes/detail/(?P<pk>[0-9]+)/$', views.RecipeDetailView.as_view(), name='recipe_detail'),
    # url(r'^crafting/$', views.CraftingProfitListView.as_view(), name='craftingprofit_list'),
    # url(r'^crafting/max/$', views.CraftingProfitDelayListView.as_view(), name='craftingprofitdelay_list'),
    # url(r'^relist/$', views.RelistListView.as_view(), name='relist_list'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
