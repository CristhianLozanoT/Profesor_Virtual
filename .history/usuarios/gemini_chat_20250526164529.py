import os
from dotenv import load_dotenv
import google.generativeai as genai
import numpy as np
from .models import FragmentoVectorizado
from sentence_transformers import SentenceTransformer

# 1. Cargar .env y configurar Gemini
load_dotenv()

genai.configure(api_key="AIzaSyBO1lxw9lHEIkUwAhdAuJldcNv4djowHuw")  # Mejor usar variable de entorno
modelo_llm = genai.GenerativeModel("gemini-1.5-pro-latest")  # Ruta completa y correcta del modelo

# 2. Cargar modelo de embeddings
modelo_embeddings = SentenceTransformer('all-MiniLM-L6-v2')

# 3. Similitud coseno
def similitud_coseno(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# 4. Recuperar fragmentos más relevantes
def recuperar_fragmentos_relevantes(pregunta, tema, k=2):
    pregunta_vector = modelo_embeddings.encode([pregunta])[0].tolist()
    fragmentos = FragmentoVectorizado.objects.filter(tema=tema)

    fragmentos_con_similitud = []
    for frag in fragmentos:
        sim = similitud_coseno(frag.vector, pregunta_vector)
        fragmentos_con_similitud.append((sim, frag.texto))

    fragmentos_con_similitud.sort(reverse=True)
    fragmentos_relevantes = [texto for _, texto in fragmentos_con_similitud[:k]]

    return "\n\n".join(fragmentos_relevantes)

# 5. Generar respuesta con Gemini
def responder_con_gemini(pregunta, tema, historial="" , nombre_estudiante="", es_inicio=False):
    contexto = recuperar_fragmentos_relevantes(pregunta, tema)
    
    if es_inicio:
        saludo = f"""
         ¡Hola {nombre_estudiante}! 👋
        
        Soy tu profesor virtual y te ayudaré a comprender el tema: "{tema}".
        Trabajaremos con el material que has seleccionado y estaré aquí para responder tus preguntas
        y guiarte en el proceso de aprendizaje.
        
        ¿Qué te gustaría saber sobre este tema?
        """
        

    prompt = f"""
    Eres un profesor virtual cuyo objetivo es guiar al estudiante en la comprensión profunda de un documento que ha compartido. Debes seguir este flujo:

    1. Lee completamente el documento proporcionado en el campo 'contexto'.
    2. Divide el contenido en secciones clave (por capítulos, temas o apartados).
    3. Si el estudiante hace una pregunta, respóndela usando únicamente el contenido del documento.
    4. Si el estudiante no pregunta pero espera una interacción, formula una pregunta pedagógica relacionada con la siguiente sección importante. Solo haz una pregunta a la vez.
    5. Espera la respuesta del estudiante (vía campo 'historial') antes de continuar.
    6. Evalúa su respuesta y decide si necesitas:
       - profundizar,
       - aclarar conceptos,
       - retroceder o
       - avanzar a la siguiente sección.
    7. Finaliza cuando se haya cubierto todo el contenido o el estudiante lo indique.

    Responde de manera clara, paciente y pedagógica. Adáptate al nivel del estudiante según sus respuestas. Usa ejemplos y lenguaje accesible si es necesario.
    === CONTEXTO DEL ARCHIVO ===
    {contexto}

    === HISTORIAL DE CONVERSACIÓN ===
    {historial}

    === PREGUNTA ===
    {pregunta}

    Responde de forma clara, didáctica y detallada.
    """
    try:
        respuesta = modelo_llm.generate_content(prompt)
        return respuesta.text, contexto  # Devolvemos ambos: texto y contexto
    except Exception as e:
        print(f"Error al generar respuesta con Gemini: {e}")
        return "Lo siento, ocurrió un error al procesar tu solicitud.", ""