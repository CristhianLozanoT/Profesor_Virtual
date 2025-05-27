import fitz  # PyMuPDF
import docx
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# --- 1. Extraer texto del archivo (PDF o DOCX) ---
def extraer_texto_de_archivo(archivo_path):
    if archivo_path.endswith('.pdf'):
        doc = fitz.open(archivo_path)
        texto = ""
        for pagina in doc:
            texto += pagina.get_text()
        return texto
    elif archivo_path.endswith('.docx'):
        doc = docx.Document(archivo_path)
        return '\n'.join([p.text for p in doc.paragraphs])
    return ""

# --- 2. Dividir el texto por párrafos ---
def dividir_en_parrafos(texto):
    return [p for p in texto.split('\n') if p.strip()]

# --- 3. Vectorizar los fragmentos ---
modelo = SentenceTransformer('all-MiniLM-L6-v2')

def vectorizar_fragmentos(fragmentos):
    return modelo.encode(fragmentos).tolist()

def buscar_respuesta(pregunta, fragmentos):
    """
    Busca el fragmento más relevante usando similitud coseno entre vectores.
    """
    vector_pregunta = modelo.encode([pregunta])[0]  # Vector de la pregunta
    vectores = [np.array(f.vector) for f in fragmentos]  # Vectores de fragmentos

    similitudes = cosine_similarity([vector_pregunta], vectores)[0]
    indice_mas_similar = np.argmax(similitudes)

    fragmento_mas_similar = fragmentos[indice_mas_similar]
    return fragmento_mas_similar.texto  # Texto más similar

def calcular_similitud_coseno(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
        return 0
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))