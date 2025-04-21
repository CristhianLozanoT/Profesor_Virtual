import os
from dotenv import load_dotenv
import google.generativeai as genai
import numpy as np
from .models import FragmentoVectorizado
from sentence_transformers import SentenceTransformer

# 1. Cargar .env y configurar Gemini
load_dotenv()

genai.configure(api_key="AIzaSyB13rip9ZrzO1QTomMh-HPjn2FShtjvYb4")  # Mejor usar variable de entorno
modelo_llm = genai.GenerativeModel("gemini-1.5-pro-latest")  # Ruta completa y correcta del modelo

# 2. Cargar modelo de embeddings
modelo_embeddings = SentenceTransformer('all-MiniLM-L6-v2')

# 3. Similitud coseno
def similitud_coseno(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# 4. Recuperar fragmentos más relevantes
def recuperar_fragmentos_relevantes(pregunta, tema, k=3):
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
def responder_con_gemini(pregunta, tema, historial=""):
    contexto = recuperar_fragmentos_relevantes(pregunta, tema)

    prompt = f"""
Eres un profesor virtual. Responde con detalle la siguiente pregunta basada en el contexto proporcionado.

Historial de la conversación:
{historial}

Contexto:
{contexto}

Pregunta del estudiante:
{pregunta}

Recuerda responder de manera clara, pedagógica y basada en el contexto.
"""
    try:
        respuesta = modelo_llm.generate_content(prompt)
        return respuesta.text, contexto  # Devolvemos ambos: texto y contexto
    except Exception as e:
        print(f"Error al generar respuesta con Gemini: {e}")
        return "Lo siento, ocurrió un error al procesar tu solicitud.", ""