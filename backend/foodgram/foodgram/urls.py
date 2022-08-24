from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api_foodgram.urls')),
    path(
        'redoc/',
        TemplateView.as_view(template_name='docks/redoc.html'),
        name='redoc'
    ),
]
