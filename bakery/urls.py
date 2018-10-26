from django.conf.urls import url
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'bakery'

urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^groceries/$', views.GroceryListView.as_view(), name='view-groceries'),
    url(r'^components/$', views.ComponentListView.as_view(), name='view-components'),
    url(r'^recipes/$', views.RecipeListView.as_view(), name='view-recipes'),
    url(r'^orders/$', views.OrderListView.as_view(), name='view-orders'),
    url(r'^add/grocery/$', views.create_grocery, name='create-grocery'),
    url(r'^add/component/$', views.create_component, name='create-component'),
    url(r'^add/recipe/$', views.create_recipe, name='create-recipe'),
    url(r'^add/order/$', views.create_order, name='create-order'),
    url(r'^groceries/detail/(?P<pk>[0-9]+)/$', views.GroceryDetailView.as_view(), name='grocery_detail'),
    url(r'^components/detail/(?P<pk>[0-9]+)/$', views.ComponentDetailView.as_view(), name='component_detail'),
    url(r'^recipes/detail/(?P<pk>[0-9]+)/$', views.RecipeDetailView.as_view(), name='recipe_detail'),
    url(r'^orders/detail/(?P<pk>[0-9]+)/$', views.OrderDetailView.as_view(), name='order_detail'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
