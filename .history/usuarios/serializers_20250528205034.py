from rest_framework import serializers
from .models import Usuario, Archivo, Tema, Conversacion
from django.contrib.auth import get_user_model

User = get_user_model()

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_profesor', 'is_estudiante']

class RegistroSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'is_profesor', 'is_estudiante']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class ArchivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Archivo
        fields = '__all__'
        read_only_fields = ['profesor', 'fecha_subida']

class TemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tema
        fields = '__all__'

class ConversacionSerializer(serializers.ModelSerializer):
    es_inicio = serializers.BooleanField(required=False, default=False)
    class Meta:
        model = Conversacion
        fields = ['id_conversacion', 'pregunta', 'tema', 'respuesta', 'estudiante', 'es_inicio']
        extra_kwargs = {
            'respuesta': {'read_only': True},
            'estudiante': {'read_only': True},
            'id_conversacion': {'required': False},
        }