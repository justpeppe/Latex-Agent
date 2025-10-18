import subprocess                   #per eseguire comandi esterni
import os                           #per operazioni sul filesystem
import json                         # lavora con i dati json ottenuti dall'LLM

from dotenv import load_dotenv
import google.generativeai as genai

# Carichiamo le variabili d'ambiente (le nostre chiavi API)
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
     # Se la chiave non eiste stampiamo errore e chiudiamo il programma
     print(f"Non è stata trovata la chiave API per Gemini")
     exit()

try:
     genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
     print(f"Configurazione chiave fallita, errore: {e}")
     exit()
          
# --- Agente 01 : Convertitore da .docx a .tex ---
def agente_convertitore(file_input_docx, file_output_tex):
    
    """
        Usa Pandoc per convertire un file .docx in .tex
        Restituisce true se la conversione ha successo, false altrimenti
    """
    print(f"Agente 01: Avvio conversione di '{file_input_docx}' ---")

    #Verifichiamo che l'input esista
    if not os.path.exists(file_input_docx):
        print(f"Il file '{file_input_docx}' non è stato trovato nella directory")
        return False
    
    try:
        subprocess.run(
            ['pandoc', file_input_docx, '-o', file_output_tex],
            check = True,               #Se abbiamo eroore si ferma
            capture_output = True,
            text = True
        )

        print(f"Creato file .tex grezzo di nome: '{file_output_tex}'")
        return True

    except FileNotFoundError:
            print(f"Comando pandoc non trovato")
            return False
    
    except subprocess.CalledProcessError as e:
        print(f"{e.stderr}")
        return False
    

# --- Agente 02: Analista e correttore LLM
def agente_analista(file_tex_grezzo, file_tex_pulito, file_json_immagini):
     """
     Usa Gemini per pulire il file .tex e identificare le immagini necessarie.
     Restituisce l'elenco delle immagini richieste o None in caso di errore
     """

     print(f"Avvio Agente 02 da file .tex grezzo '{file_tex_grezzo}'")

     try:
        # Apriamo il file .tex
        with open(file_tex_grezzo,'r', encoding='utf-8') as file:
            testo_grezzo = file.read()
        
        # Diciamo a Gemini di risponderci in JSON
        generation_config = genai.GenerationConfig(
             response_mime_type="application/json"
        )
        model = genai.GenerativeModel(
             'models/gemini-pro-latest',
             generation_config=generation_config
        )


        # Definiamo il prompt di questo agente

        prompt = f"""
        Sei un esperto di LaTeX e un analista di contenuti.
        Dato il seguente testo .tex:

        1.  Correggi la sintassi delle formule. Trasforma '$$formula$$' in \\[ formula \\] (per le formule a capo) o $formula$ (per le formule inline) in base al contesto.
        2.  Identifica UN (1) solo concetto chiave in questo breve testo che beneficerebbe di un'immagine.
        3.  Per quell'immagine, genera un segnaposto univoco (es. %%PLACEHOLDER_CONCETTO%%).
        4.  Genera una query di ricerca ottimizzata per trovare quell'immagine con licenza libera (es. "teorema di pitagora creative commons diagramma").
        5.  Genera una breve didascalia (caption) per l'immagine.

        Restituisci ESATTAMENTE un oggetto JSON con questa struttura:
        {{
          "testo_modificato": "Il tuo testo LaTeX corretto e con il segnaposto inserito...",
          "immagini_richieste": [
            {{
              "placeholder": "%%PLACEHOLDER_NOME%%",
              "query": "query di ricerca con licenza libera",
              "caption": "Didascalia per l'immagine"
            }}
          ]
        }}
        
        Ecco il testo .tex da analizzare:
        --- INIZIO TESTO ---
        {testo_grezzo}
        --- FINE TESTO ---
        """

        response = model.generate_content(prompt)
        print(f"Contatto l'API di Gemini (attendere qualche secondo)...")

        dati_risposta = json.loads(response.text)

        with open(file_tex_pulito, 'w', encoding='utf-8') as file:
            file.write(dati_risposta['testo_modificato'])
            print(f"File .tex pulito salvato con successo: '{file_tex_pulito}'")

        with open(file_json_immagini, 'w', encoding='utf-8') as file:
             json.dump(dati_risposta['immagini_richieste'], file, indent=2, ensure_ascii=False)
             print(f"Immagini salvate con successo in: '{file_json_immagini}'")

        return dati_risposta['immagini_richieste']
     
     except Exception as e:
        print(f"ERRORE Agente 2 (LLM): {e}")
        # Potrebbe essere un errore API, un errore di parsing JSON, ecc.
        return None

    

def main():
    """
        Esegue le operazioni
    """

    input_file = "documento.docx"
    output_file_grezzo = "temp_grezzo.tex"
    temp_file_grezzo_pulito = "temp_pulito.tex"
    temp_file_json = "temp_immagini.json"    

    risultato_agent_01 = agente_convertitore(input_file,output_file_grezzo)

    if risultato_agent_01:
        print(f"Operazione agente 01 eseguita con successo!")
    else:
         print(f"Operazione agente 01 fallita")

    richieste_immagini = agente_analista(
         output_file_grezzo,
         temp_file_grezzo_pulito,
         temp_file_json
    )

    if richieste_immagini is None:
        print(f"Operazione agente 02 fallita")
        return
    
    print(f"Operazione Agente 02 eseguita con successo!")


# Esegui la funzione solo se avvio lo script direttamente
if __name__ == "__main__":
     main()
