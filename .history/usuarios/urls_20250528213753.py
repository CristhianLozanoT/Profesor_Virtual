from django.urls import path
from .views import *

urlpatterns = [
    path('registro/', RegistroView.as_view(), name='registro'),
    path('subir-archivo/', ArchivoUploadView.as_view(), name='subir_archivo'),
    path('temas/', ListadoTemasView.as_view(), name='temas'),
    path('preguntar/', PreguntaView.as_view(), name='preguntar'),
    path('historial/', HistorialPreguntasView.as_view(), name='historial_preguntas'),
    path('user/', UsuarioActualView.as_view(), name='usuario_actual'),
    path('estadisticas/<int:tema_id>/', EstadisticasPreguntasView.as_view(), name='estadisticas-preguntas'),
]


