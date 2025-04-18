import fitz  # PyMuPDF
import docx
from sentence_transformers import SentenceTransformer

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

