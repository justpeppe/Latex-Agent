import subprocess                   #per eseguire comandi esterni
import os                           #per operazioni sul filesystem

# Primo agente
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

    except FileNotFoundError:
            print(f"Comando pandoc non trovato")
            return False
    
    except subprocess.CalledProcessError as e:
        print(f"{e.stderr}")
        return False
    

def main():
    """
        Esegue le operazioni
    """

    input_file = "documento.docx"
    output_file_grezzo = "temp_grezzo.tex"     

    risultato_agent_01 = agente_convertitore(input_file,output_file_grezzo)

    if risultato_agent_01:
        print(f"Operazione agente 01 eseguita con successo!")
    else:
         print(f"Operazione agente 01 fallita")


# Esegui la funzione solo se avvio lo script direttamente
if __name__ == "__main__":
     main()
