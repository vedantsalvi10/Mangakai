
from django.contrib import admin
from authentication.views import register
from animeImage.views import animeImage,posesGeneration
from panelGeneration.views import generate_story_prompt
from rest_framework.authtoken.views import obtain_auth_token
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/',register),
    path('login/',obtain_auth_token),
    path('animefy/',animeImage),
    path('poses/',posesGeneration),
    path('story/',generate_story_prompt),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)