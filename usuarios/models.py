from django.db import models
from django.contrib.auth.models import AbstractUser

# Modelo personalizado de usuario
class Usuario(AbstractUser):
    is_profesor = models.BooleanField(default=False)
    is_estudiante = models.BooleanField(default=True)

class Archivo(models.Model):
    profesor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to='archivos/')
    titulo = models.CharField(max_length=255)
    fecha_subida = models.DateTimeField(auto_now_add=True)

class Tema(models.Model):
    archivo = models.ForeignKey(Archivo, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=255)

class Conversacion(models.Model):
    estudiante = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE)
    pregunta = models.TextField()
    respuesta = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.estudiante.username} - {self.pregunta[:30]}"