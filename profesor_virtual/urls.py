# profesor_virtual/urls.py
from django.contrib import admin
from django.urls import path, include
from usuarios.views import ArchivoListView, PreguntaView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('usuarios.urls')),  # Incluye las URLs de la aplicación `usuarios`
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('archivos/', ArchivoListView.as_view(), name='listar_archivos'),
    path('preguntar/', PreguntaView.as_view(), name='preguntar'),
]