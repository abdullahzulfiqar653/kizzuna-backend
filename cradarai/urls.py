# urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from web_app import views

schema_view = get_schema_view(
    openapi.Info(
        title="Cradar API",
        default_version='v1',
        description="API description",
        terms_of_service="https://www.cradarai.com/terms/",
        contact=openapi.Contact(email="contact@cradarai.com"),
        license=openapi.License(name="Your License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),

    # # note
    # path('note/', include('note.urls')),
    # path('note/', include('transcriber.urls')),

    # # workspace
    # path('workspace/', include('workspace.urls')),

    # # project
    # path('project/', include('project.urls')),

    # # tag
    # path('tag/', include('tag.urls')),

    # # takeaway
    # path('takeaway/', include('takeaway.urls')),

    # # user
    # path('user/', include('user.urls')),

    # # auth
    # path('', include('auth.urls')),

    path('home', views.home, name='home'),

    # path('web_app/', include('web_app.urls')),

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
