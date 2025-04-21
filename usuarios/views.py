from rest_framework import generics, permissions
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView
import uuid
from usuarios.serializers import ArchivoSerializer, ConversacionSerializer, RegistroSerializer, TemaSerializer
from .models import Archivo, Tema, Conversacion, FragmentoVectorizado
from .serializers import *  # Puedes dejarlo si te funciona
from .utils import extraer_texto_de_archivo, dividir_en_parrafos, vectorizar_fragmentos
from .gemini_chat import responder_con_gemini

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
        estudiante = self.request.user
        pregunta = serializer.validated_data['pregunta']
        tema = serializer.validated_data['tema']
        id_conversacion = serializer.validated_data.get('id_conversacion')

        # Si no se proporciona un id_conversacion, generar uno nuevo
        if not id_conversacion:
            id_conversacion = str(uuid.uuid4())

        # Recuperar el historial de la conversación
        historial = Conversacion.objects.filter(
            id_conversacion=id_conversacion,
            estudiante=estudiante,
            tema=tema
        ).order_by('fecha')

        # Construir el historial como texto
        historial_texto = "\n".join([
            f"Estudiante: {msg.pregunta}\nProfesor: {msg.respuesta}"
            for msg in historial
            if msg.respuesta  # Solo incluir mensajes con respuesta
        ])

        # Generar respuesta con Gemini (texto + contexto)
        respuesta_texto, _ = responder_con_gemini(pregunta, tema, historial_texto)

        # Guardar la nueva interacción
        serializer.save(
            estudiante=estudiante,
            respuesta=respuesta_texto,
            id_conversacion=id_conversacion
        )

class ArchivoListView(ListAPIView):
    queryset = Archivo.objects.all()
    serializer_class = ArchivoSerializer

class HistorialPreguntasView(generics.ListAPIView):
    serializer_class = ConversacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversacion.objects.filter(estudiante=self.request.user).order_by('-fecha')
