import subprocess                   # per eseguire comandi esterni
import os                           # per operazioni sul filesystem
import json                         # lavora con i dati json ottenuti dall'LLM
import shutil                       # per copiare il file finale
import uuid                         # per generare nomi univoci

from dotenv import load_dotenv
import google.generativeai as genai

# Carico le variabili d'ambiente (le mie chiavi API)
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    # Se non trovo la chiave, stampo un errore e chiudo il programma
    print(f"Non è stata trovata la chiave API per Gemini")
    exit()

try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Configurazione chiave fallita, errore: {e}")
    exit()
          
# --- Agente 01 : Convertitore da .docx a .tex --- 
def agente_convertitore(file_input_docx):
    """
        Uso Pandoc per convertire un file .docx in .tex
        Restituisco il contenuto del file .tex come stringa
    """
    print(f"Agente 01: Avvio conversione di '{file_input_docx}' ---")

    # Verifico che l'input esista
    if not os.path.exists(file_input_docx):
        print(f"Il file '{file_input_docx}' non è stato trovato nella directory")
        return None
    
    # Creo un nome file temporaneo unico
    temp_tex = f"temp_{uuid.uuid4().hex}.tex"
    
    try:
        subprocess.run(
            ['pandoc', '-s', file_input_docx, '-o', temp_tex],
            check=True,               # Se ho errore si ferma
            capture_output=True,
            text=True
        )

        print(f"Conversione completata, leggo il contenuto...")
        # Leggo il contenuto del file
        with open(temp_tex, 'r', encoding='utf-8') as f:
            contenuto = f.read()
        
        # Elimino il file temporaneo
        os.remove(temp_tex)
        return contenuto

    except FileNotFoundError:
        print(f"Comando pandoc non trovato")
        # Pulisco in caso di errore
        if os.path.exists(temp_tex):
            os.remove(temp_tex)
        return None

    except subprocess.CalledProcessError as e:
        print(f"{e.stderr}")
        # Pulisco in caso di errore
        if os.path.exists(temp_tex):
            os.remove(temp_tex)
        return None
     

# --- Agente 02: Correttore LLM --- 
def agente_correttore(testo_grezzo):
    """
    Uso Gemini per pulire il file .tex, correggendo solo le formule.
    Restituisco il testo pulito.
    """

    print(f"Avvio Agente 02 per correggere il testo...")

    try:
        # Dico a Gemini che modello usare
        model = genai.GenerativeModel('models/gemini-2.5-pro')

        # Definisco il prompt di questo agente
        prompt = f"""
        
        Sei un esperto di LaTeX.
        Dato il seguente documento .tex completo:

        1.  Trova tutte le formule matematiche scritte come '$$formula$$'.
        2.  Correggile nella sintassi LaTeX corretta:
            - Usa \\[ formula \\] per le formule che dovrebbero stare su una riga a sé (display).
            - Usa $formula$ per le formule che dovrebbero stare dentro la frase (inline).
        3.  Assicurati che il pacchetto \\usepackage{{amsmath}} sia presente nel preambolo (PRIMA di \\begin{{document}}), se non c'è già.
        4.  Rimuovi COMPLETAMENTE il pacchetto \\usepackage{{xcolor}} e qualsiasi comando \\color{{}} dal documento.
        5.  Il testo deve essere NERO (colore predefinito) e GIUSTIFICATO (allineamento predefinito).
        6.  Mantieni tutti gli altri pacchetti necessari (hyperref, amsmath, amssymb, etc.).
        7.  Verifica che tutti gli ambienti \\begin{{}} abbiano il corrispondente \\end{{}}.
        
        IMPORTANTE:
        - Restituisci l'INTERO documento .tex, preservando tutta la struttura originale
        - Includi \\documentclass, tutti i \\usepackage necessari, \\begin{{document}}, e \\end{{document}}
        - Restituisci SOLO il codice .tex puro e completo, dall'inizio alla fine
        - NON usare blocchi di codice Markdown (come ```latex o ```)
        - NON aggiungere commenti o testo prima o dopo il codice LaTeX
        - Il testo finale deve essere in NERO

        Ecco il testo .tex da analizzare:
        --- INIZIO TESTO ---
        {testo_grezzo}
        --- FINE TESTO ---
        """

        print(f"Contatto l'API di Gemini (attendere qualche secondo)...")
        response = model.generate_content(prompt)

        testo_pulito = response.text.strip()
        
        # Rimuovo i blocchi di codice Markdown se presenti
        if testo_pulito.startswith('```'):
            prima_newline = testo_pulito.find('\n')
            if prima_newline != -1:
                testo_pulito = testo_pulito[prima_newline + 1:]
        
        if testo_pulito.endswith('```'):
            testo_pulito = testo_pulito[:-3]
        
        testo_pulito = testo_pulito.strip()

        return testo_pulito
     
    except Exception as e:
        print(f"ERRORE Agente 2 (LLM): {e}")
        return None

# --- AGENTE 3: IL COMPILATORE (LaTeX) --- 
def agente_compilatore(testo_tex_finale, output_pdf_path):
    """
    Compilo il file .tex finale in un .pdf usando 'pdflatex'.
    Restituisco True se ha successo, False altrimenti.
    """
    print(f"Agente 3: Avvio compilazione PDF ---")

    # Controllo se pdflatex è installato prima di provare
    try:
        subprocess.run(
            ['pdflatex', '--version'],
            capture_output=True, check=True
        )
    except FileNotFoundError:
        print("ERRORE: 'pdflatex' non trovato.")
        print("Assicurati di aver installato una distribuzione LaTeX (es. MiKTeX o TeX Live).")
        return False
    
    # Creo un nome file temporaneo unico
    temp_tex = f"temp_{uuid.uuid4().hex}.tex"
    temp_pdf = temp_tex.replace('.tex', '.pdf')
    temp_log = temp_tex.replace('.tex', '.log')
    temp_aux = temp_tex.replace('.tex', '.aux')
    
    try:
        # Scrivo il file .tex temporaneo
        with open(temp_tex, 'w', encoding='utf-8') as f:
            f.write(testo_tex_finale)
        
        # Eseguo la compilazione DUE VOLTE
        for i in range(2):
            print(f"Compilazione PDF (Passaggio {i + 1}/2)...")
            processo = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', temp_tex],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if processo.returncode != 0:
                print(f"ERRORE: Compilazione LaTeX fallita (Passaggio {i + 1}).")
                if os.path.exists(temp_log):
                    with open(temp_log, 'r', encoding='utf-8') as log:
                        for linea in log:
                            if linea.startswith("!"): 
                                print(f"Dettaglio Errore: {linea.strip()}")
                                break
                # Pulisco i file temporanei
                for f in [temp_tex, temp_pdf, temp_log, temp_aux]:
                    if os.path.exists(f):
                        os.remove(f)
                return False

        # Copio il PDF alla posizione finale
        if os.path.exists(temp_pdf):
            shutil.copy2(temp_pdf, output_pdf_path)
            print(f"Successo: PDF compilato salvato come '{output_pdf_path}'")
            
            # Pulisco i file temporanei
            for f in [temp_tex, temp_pdf, temp_log, temp_aux]:
                if os.path.exists(f):
                    os.remove(f)
            return True
        else:
            print(f"ERRORE: PDF non generato")
            # Pulisco i file temporanei
            for f in [temp_tex, temp_pdf, temp_log, temp_aux]:
                if os.path.exists(f):
                    os.remove(f)
            return False
    
    except Exception as e:
        print(f"ERRORE Critico durante l'esecuzione di pdflatex: {e}")
        # Pulisco i file temporanei in caso di errore
        for f in [temp_tex, temp_pdf, temp_log, temp_aux]:
            if os.path.exists(f):
                os.remove(f)
        return False
    

def main():
    """
        Eseguo le operazioni
    """

    input_file = "documento.docx"
    output_pdf = "documento.pdf"
    
    # --- Esecuzione Agente 1 ---
    testo_grezzo = agente_convertitore(input_file)
    if not testo_grezzo:
        print(f"PIPELINE (Agente 1) FALLITA. Interruzione")
        return
    else:
        print(f"Operazione agente 1 eseguita con successo!")

    # --- Esecuzione Agente 2 ---
    testo_pulito = agente_correttore(testo_grezzo)
    if testo_pulito is None:
        print(f"PIPELINE (Agente 2) FALLITA. Interruzione.")
        return
    else:
        print(f"Operazione Agente 2 eseguita con successo!")

    # --- Esecuzione Agente 3 ---
    if not agente_compilatore(testo_pulito, output_pdf):
        print(f"PIPELINE (Agente 3) FALLITA. Interruzione.")
        return
    
    print("PIPELINE COMPLETATA CON SUCCESSO")
    print(f"File finale: {output_pdf}")

# Eseguo la funzione solo se avvio lo script direttamente
if __name__ == "__main__":
    main()
