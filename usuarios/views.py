from rest_framework import generics, permissions
from rest_framework.response import Response

from usuarios.serializers import ArchivoSerializer, ConversacionSerializer, RegistroSerializer, TemaSerializer
from .models import Archivo, Tema, Conversacion
from .serializers import *  # Importar todas las serializadores desde serializers.py
from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView
from .utils import extraer_texto_de_archivo, dividir_en_parrafos, vectorizar_fragmentos
from .models import FragmentoVectorizado
import os
from .utils import extraer_texto_de_archivo, dividir_en_parrafos, vectorizar_fragmentos




User = get_user_model()

class RegistroView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistroSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        serializer.save()

class ArchivoUploadView(generics.CreateAPIView):
    queryset = Archivo.objects.all()
    serializer_class = ArchivoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        archivo = serializer.save(profesor=self.request.user)
        tema = Tema.objects.create(archivo=archivo, titulo=f"Tema para {archivo.titulo}")

        ruta = archivo.archivo.path
        texto = extraer_texto_de_archivo(ruta)
        fragmentos = dividir_en_parrafos(texto)
        vectores = vectorizar_fragmentos(fragmentos)

        for texto, vector in zip(fragmentos, vectores):
            FragmentoVectorizado.objects.create(
                archivo=archivo,
                tema=tema,
                texto=texto,
                vector=vector
            )

class ListadoTemasView(generics.ListAPIView):
    queryset = Tema.objects.all()
    serializer_class = TemaSerializer
    permission_classes = [permissions.IsAuthenticated]

class PreguntaView(generics.CreateAPIView):
    queryset = Conversacion.objects.all()
    serializer_class = ConversacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(estudiante=self.request.user)

class ArchivoListView(ListAPIView):
    queryset = Archivo.objects.all()
    serializer_class = ArchivoSerializer

class HistorialPreguntasView(generics.ListAPIView):
    serializer_class = ConversacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversacion.objects.filter(estudiante=self.request.user).order_by('-fecha')
