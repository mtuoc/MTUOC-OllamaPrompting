import ollama
import csv
import subprocess
import time
import requests
import yaml # Used for reading the config.yaml file
import re
import codecs
import sys

# Global configuration variable
CONFIG = {}



def load_config(config_path):
    global CONFIG
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            CONFIG = yaml.safe_load(f)
        print("✅ Configuration loaded successfully.")
        return True
    except FileNotFoundError:
        print(f"❌ ERROR: Configuration file '{config_path}' not found.")
        return False
    except yaml.YAMLError as e:
        print(f"❌ ERROR: Failed to parse YAML file: {e}")
        return False

def is_ollama_running(url, timeout):
    """Comprova si el servei Ollama està accessible a l'URL per defecte."""
    try:
        # Intentem connectar-nos al punt final d'informació (per exemple)
        requests.get(url, timeout=timeout)
        return True
    except requests.exceptions.ConnectionError:
        return False

def start_ollama_server():
    """Intenta iniciar el servidor Ollama utilitzant el subprocess."""
    print("▶️ Intentant iniciar el servei Ollama amb 'ollama serve'...")
    try:
        # Utilitzem Popen per executar 'ollama serve' en segon pla (sense bloquejar)
        subprocess.Popen(['ollama', 'serve'])
        
        # Esperem un moment perquè el servidor s'iniciï
        time.sleep(3)
        
        if is_ollama_running():
            print("✅ Servei Ollama iniciat amb èxit.")
            return True
        else:
            print("❌ No s'ha pogut iniciar el servei Ollama. Assegura't que l'executable 'ollama' estigui al PATH.")
            return False
            
    except FileNotFoundError:
        print("❌ ERROR: El comando 'ollama' no es troba. Assegura't que Ollama està instal·lat correctament i al PATH.")
        return False


def pull_ollama_model(model: str):
    """Descarrega el model si no el té. La funció ollama.generate/chat ho fa automàticament."""
    try:
        print(f"▶️ Verificant la disponibilitat del model '{model}'...")
        # L'API de Python d'Ollama executa automàticament el 'pull' si el model no existeix 
        # quan es crida a generate, chat, o pull. Fem una crida explícita a pull per assegurar-nos.
        
        # ollama.pull (o la crida a una funció que utilitzi el model) fa el pull/download
        # si el model no està ja al sistema.
        
        # Cridem a ollama.pull amb 'stream=True' per veure el procés de descàrrega
        for chunk in ollama.pull(model=model, stream=True):
             # Només imprimim l'últim estat de la descàrrega
             status = chunk.get("status", "")
             total = chunk.get("total", 0)
             completed = chunk.get("completed", 0)
             
             if total > 0:
                 progress = int((completed / total) * 100)
                 print(f"   Estat: {status} | Progrés: {progress}% ({completed}/{total})", end='\r')
             elif status:
                 print(f"   Estat: {status}", end='\r')
                 
        print("\n✅ Model carregat i preparat.")
        return True
    except Exception as e:
        print(f"\n❌ ERROR carregant/descarregant el model '{model}': {e}")
        return False

# --- FUNCIONS DE PROCESSAMENT (SIMILARS A L'ANTERIOR) ---

def obtenir_resposta_ollama(prompt: str, model: str, temperature: float):
    """Envia un prompt al model d'Ollama i retorna la resposta."""
    try:
        response = ollama.generate(
            model=model,
            prompt=prompt,
            stream=False, # Esperem la resposta completa
            options={
                'temperature': temperature # Apliquem el paràmetre de temperatura per a consistència.
            }
        )
        return response['response'].strip()
    except ollama.ResponseError as e:
        return f"ERROR amb Ollama: {e}"
    except Exception as e:
        return f"ERROR general: {e}"


def process_file(nom_fitxer: str, nom_fitxer_sortida: str, separador: str, model: str, url_ollama: str, timeout_ollama: int, temperature_ollama: float, sl_lang: str, tl_lang: str, prompt_template: str, regex_pattern: str):
    """
    Obre el fitxer, processa cada línia i consulta Ollama.
    """
    print(f"\n✨ Iniciant el processament del fitxer '{nom_fitxer}'...")

    # Pas 1: Gestió del Servei i Model
    if not is_ollama_running(url_ollama, timeout_ollama):
        # We pass the URL here since start_ollama_server needs it
        if not start_ollama_server(url_ollama): 
            print("🛑 No s'ha pogut connectar o iniciar Ollama. El programa finalitza.")
            return

    if not pull_ollama_model(model):
        print("🛑 Error al carregar el model d'Ollama. El programa finalitza.")
        return

    # Pas 2: Processament de l'Arxiu
    try:
        output_file=codecs.open(nom_fitxer_sortida,"w",encoding="utf-8")
        with open(nom_fitxer, 'r', encoding='utf-8') as input_file:
            # FIX: Convertir '\\t' (de YAML) a '\t' (per a CSV)
            if separador == '\\t':
                separator = '\t'
            else:
                 separator = separador # Use original if not '\t'

            lector = csv.reader(input_file, delimiter=separator)

            for i, fila in enumerate(lector):
                line_number = i + 1

                if len(fila) < 2:
                    print(f"⚠️ Línia {line_number} omesa: No té prou columnes.")
                    continue

                sl_term = fila[0].strip() # Source Language term (Spanish)
                tl_term = fila[1].strip() # Target Language term (Catalan)
                
                # --- PROCESS SOURCE LANGUAGE (SL) ---
                
                # CORRECCIÓ CLAU: Usem .format() a la plantilla per substituir {lang} i {term}
                sl_prompt = prompt_template.format(lang=sl_lang, term=sl_term)
                
                # Crida a Ollama
                sl_response = obtenir_resposta_ollama(sl_prompt, model, temperature_ollama)
                # Extreure el plural
                match = re.search(regex_pattern, sl_response)
                sl_plural = match.group(1).strip() if match else None

                
                # --- PROCESS TARGET LANGUAGE (TL) ---
                
                # CORRECCIÓ CLAU: Usem .format() a la plantilla per substituir {lang} i {term}
                tl_prompt = prompt_template.format(lang=tl_lang, term=tl_term)
                
                # Crida a Ollama
                tl_response = obtenir_resposta_ollama(tl_prompt, model, temperature_ollama)
                # Extreure el plural
                match = re.search(regex_pattern, tl_response)
                tl_plural = match.group(1).strip() if match else None
                
                # --- WRITE RESULTS (FALLBACK LOGIC) ---
                
                # 1. Sempre escriure la parella singular (original)
                singular_pair = f"{sl_term}{separator}{tl_term}"
                print(singular_pair)
                output_file.write(singular_pair + "\n")
                # 2. Determinar el contingut per a la línia "plural"
                if sl_plural and tl_plural:
                    # Èxit: Utilitzar les formes plurals extretes
                    
                    plural_pair = f"{sl_plural}{separator}{tl_plural}"
                    print(plural_pair)
                    output_file.write(plural_pair + "\n")
                

        output_file.close()
        

    except FileNotFoundError:
        print(f"\n❌ ERROR: El fitxer '{nom_fitxer}' no s'ha trobat.")
        print("Assegura't que el fitxer es troba a la mateixa carpeta que l'script.")
    except Exception as e:
        print(f"\n❌ ERROR inesperat durant la lectura o processament: {e}")
        # Ensure file is closed even on error
        if 'output_file' in locals() and not output_file.closed:
            output_file.close()

# Main execution block
if __name__ == "__main__":
    try:
        config_file=sys.argv[1]
    except:
        config_file="config.yaml"
    if load_config(config_file):
        NOM_FITXER=CONFIG["file_settings"]["input_filename"]
        NOM_FITXER_SORTIDA=CONFIG["file_settings"]["output_filename"]
        SEPARADOR=CONFIG["file_settings"]["delimiter"]
        MODEL_OLLAMA=CONFIG["ollama_settings"]["model"]
        URL_OLLAMA=CONFIG["ollama_settings"]["url"]
        TIMEOUT_OLLAMA=CONFIG["ollama_settings"]["timeout"]
        TEMPERATURE_OLLAMA=CONFIG["ollama_settings"]["temperature"]
        SL_LANG=CONFIG["language_settings"]["source_lang_name"]
        TL_LANG=CONFIG["language_settings"]["target_lang_name"]
        PROMPT=CONFIG["prompt_settings"]["prompt_template"]
        REGEX=CONFIG["prompt_settings"]["regex_pattern"]
        process_file(NOM_FITXER, NOM_FITXER_SORTIDA, SEPARADOR, MODEL_OLLAMA, URL_OLLAMA, TIMEOUT_OLLAMA, TEMPERATURE_OLLAMA, SL_LANG, TL_LANG, PROMPT, REGEX)


