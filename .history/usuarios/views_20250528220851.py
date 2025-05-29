from itertools import count
from grpc import Status
from rest_framework import generics, permissions, status
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
from django.db.models import Count




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
        pregunta = serializer.validated_data.get('pregunta', '')  # puede ser vacío para saludo inicial
        tema = serializer.validated_data['tema']
        es_inicio = serializer.validated_data.get('es_inicio', False)
        id_conversacion = serializer.validated_data.get('id_conversacion')

        if es_inicio or not id_conversacion:
            id_conversacion = str(uuid.uuid4())

        historial_texto = ""
        if not es_inicio:
            historial = Conversacion.objects.filter(
                id_conversacion=id_conversacion,
                estudiante=estudiante,
                tema=tema
            ).order_by('fecha')

            historial_texto = "\n".join([
                f"Estudiante: {msg.pregunta}\nProfesor: {msg.respuesta}"
                for msg in historial if msg.respuesta
            ])

        respuesta_texto, contexto = responder_con_gemini(
            pregunta=pregunta,
            tema=tema,
            historial=historial_texto,
            es_inicio=es_inicio,
            nombre_estudiante=estudiante.first_name or estudiante.username
        )

        # Guardar la conversación
        serializer.save(
            estudiante=estudiante,
            respuesta=respuesta_texto,
            id_conversacion=id_conversacion
        )

        # Guardar la pregunta para estadísticas (si no es saludo inicial)
        if not es_inicio and pregunta.strip():
            PreguntaEstudiante.objects.create(
                estudiante=estudiante,
                tema=tema,
                texto=pregunta
            )

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)

            # Obtener id_conversacion desde la respuesta ya creada
            id_conversacion = response.data.get('id_conversacion')
            if not id_conversacion:
                id_conversacion = str(uuid.uuid4())

            # Añadir id_conversacion a la data de respuesta (por si no estaba)
            data = response.data
            data['id_conversacion'] = id_conversacion

            return Response(data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Error in create: {str(e)}")
            return Response(
                {'error': 'Error al procesar la solicitud'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
class ArchivoListView(ListAPIView):
    queryset = Archivo.objects.all()
    serializer_class = ArchivoSerializer

class HistorialPreguntasView(generics.ListAPIView):
    serializer_class = ConversacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversacion.objects.filter(estudiante=self.request.user).order_by('-fecha')

         
class PreguntaEstudianteCreateView(generics.CreateAPIView):
    queryset = PreguntaEstudiante.objects.all()
    serializer_class = PreguntaEstudianteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(estudiante=self.request.user)
         
class EstadisticasPreguntasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, tema_id):
        # Solo profesores pueden acceder
        if not request.user.is_profesor:
            return Response({"detail": "No autorizado"}, status=403)

        data = (
            PreguntaEstudiante.objects
            .filter(tema_id=tema_id)
            .values('texto')
            .annotate(cantidad=Count('id'))
            .order_by('-cantidad')
        )
        serializer = PreguntaFrecuenteSerializer(data, many=True)
        return Response(serializer.data)