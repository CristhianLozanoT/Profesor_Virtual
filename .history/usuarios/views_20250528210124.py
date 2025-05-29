from grpc import Status
from rest_framework import generics, permissions
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView
import uuid
from usuarios.serializers import ArchivoSerializer, ConversacionSerializer, RegistroSerializer, TemaSerializer
from .models import Archivo, Tema, Conversacion, FragmentoVectorizado
from .serializers import *  # Puedes dejarlo si te funciona
from .utils import extraer_texto_de_archivo, dividir_en_parrafos, vectorizar_fragmentos
from .models import FragmentoVectorizado
import os
from .utils import extraer_texto_de_archivo, dividir_en_parrafos, vectorizar_fragmentos
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .gemini_chat import  responder_con_gemini



User = get_user_model()

class UsuarioActualView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "username": user.username,
            "is_profesor": user.is_profesor,
            "is_estudiante": user.is_estudiante,
        })

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
        es_inicio = serializer.validated_data.get('es_inicio', False)
        id_conversacion = serializer.validated_data.get('id_conversacion')

        # Si es el inicio o no hay id_conversacion, generar uno nuevo
    if es_inicio or not id_conversacion:
        id_conversacion = str(uuid.uuid4())
        # Recuperar el historial solo si no es el inicio
        historial_texto = ""
        if not es_inicio:
            historial = Conversacion.objects.filter(
                id_conversacion=id_conversacion,
                estudiante=estudiante,
                tema=tema
            ).order_by('fecha')

            historial_texto = "\n".join([
                f"Estudiante: {msg.pregunta}\nProfesor: {msg.respuesta}"
                for msg in historial
                if msg.respuesta
            ])

        # Generar respuesta con Gemini
        respuesta_texto, _ = responder_con_gemini(
            pregunta=pregunta,
            tema=tema,
            historial=historial_texto,
            es_inicio=es_inicio,
            nombre_estudiante=estudiante.first_name or estudiante.username
        )

        # Guardar la nueva interacción
        serializer.save(
            estudiante=estudiante,
            respuesta=respuesta_texto,
            id_conversacion=id_conversacion
        )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        data = response.data
        id_conversacion = self.get_serializer().instance.id_conversacion
        data['id_conversacion'] = id_conversacion
        return Response(data, status=Status.HTTP_201_CREATED)

class ArchivoListView(ListAPIView):
    queryset = Archivo.objects.all()
    serializer_class = ArchivoSerializer

class HistorialPreguntasView(generics.ListAPIView):
    serializer_class = ConversacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversacion.objects.filter(estudiante=self.request.user).order_by('-fecha')
    
class GenerarPreguntasView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tema = request.data.get("tema")
        cantidad = int(request.data.get("cantidad", 5))

        if not tema:
            return Response({"error": "El tema es obligatorio"}, status=400)

        try:
            preguntas_texto, _ = generar_preguntas_con_gemini(tema, cantidad)
            preguntas = [
                p.lstrip("0123456789. )-•").strip() 
                for p in preguntas_texto.split("\n") 
                if p.strip()
            ]
            return Response({"preguntas": preguntas})
        except Exception as e:
             print(f"Error interno al generar preguntas: {e}")
             return Response({"error": str(e)}, status=500)
