import os
import google.generativeai as genai
from dotenv import load_dotenv

# Carica la chiave API dal file .env
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Chiave API non trovata. Controllare file .env.")
    exit()

try:
    genai.configure(api_key=GEMINI_API_KEY)

    print("Modelli disponibili")

    # Chiama l'API per elencare i modelli
    for m in genai.list_models():
        # Controlliamo quali modelli supportano 'generateContent'
        # (che è quello che ci serve per il nostro prompt)
        if 'generateContent' in m.supported_generation_methods:
            print(f"    Modello UTILE: {m.name}")
        else:
            print(f"    (Modello non utile: {m.name})")

    print("-------------------------------------------------")

except Exception as e:
    print(f"Errore durante la connessione all'API: {e}")