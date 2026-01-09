import ollama
import csv
import subprocess
import time
import requests
import yaml
import re
import codecs
import sys

# Variable de configuració global
CONFIG = {}

def load_config(config_path):
    global CONFIG
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            CONFIG = yaml.safe_load(f)
        return True
    except FileNotFoundError:
        print(f"ERROR: Configuration file '{config_path}' not found.")
        return False
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse YAML file: {e}")
        return False

def is_ollama_running(url, timeout):
    """Comprova si el servei Ollama està accessible."""
    try:
        requests.get(url, timeout=timeout)
        return True
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False

def start_ollama_server(url, timeout):
    """Intenta iniciar el servidor Ollama i verifica que estigui actiu."""
    print("Trying to start the Ollama server...")
    try:
        subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        for i in range(5):
            time.sleep(2)
            if is_ollama_running(url, timeout):
                print("Ollama server started.")
                return True
            print(f"   ...waiting the ollama server ({i+1}/5)")
        
        print("We couldn't check whether Ollama server is running.")
        return False
            
    except FileNotFoundError:
        print("Ollama command not found in PATH.")
        return False

def pull_ollama_model(model: str):
    try:
        print(f"Checking model's availability: '{model}'...")
        for chunk in ollama.pull(model=model, stream=True):
            status = chunk.get("status", "")
            total = chunk.get("total", 0)
            completed = chunk.get("completed", 0)
            
            if total > 0:
                progress = int((completed / total) * 100)
                print(f"   Status: {status} | Progress: {progress}%", end='\r')
            elif status:
                print(f"   Status: {status}", end='\r')
                
        print("\nModel loaded and ready.")
        return True
    except Exception as e:
        print(f"\nERROR loading model '{model}': {e}")
        return False

def obtenir_resposta_ollama(prompt: str, model: str, options: dict):
    """
    Envia el prompt a Ollama passant el diccionari d'opcions complet.
    """
    try:
        response = ollama.generate(
            model=model,
            prompt=prompt,
            stream=False,
            options=options  # Aquí passem tots els paràmetres (temp, num_ctx, etc.)
        )
        return response['response'].strip()
    except Exception as e:
        return f"ERROR: {e}"

def process_file(file_cfg, ollama_cfg, prompt_cfg):
    """
    Processa el fitxer utilitzant la configuració per blocs.
    """
    nom_fitxer = file_cfg["input_filename"]
    nom_fitxer_sortida = file_cfg["output_filename"]
    separador = file_cfg["delimiter"]
    
    model = ollama_cfg["model"]
    url_ollama = ollama_cfg["url"]
    timeout_ollama = ollama_cfg["timeout"]
    
    # Extraiem els paràmetres de generació (tots menys model, url i timeout)
    # per passar-los com a 'options'
    generation_options = {k: v for k, v in ollama_cfg.items() if k not in ['model', 'url', 'timeout']}
    
    prompt_template = prompt_cfg["prompt_template"]
    regex_pattern = prompt_cfg["regex_pattern"]
    if regex_pattern == "None": regex_pattern = None

    print(f"\nStart processing '{nom_fitxer}'...")

    # 1. Gestió del Servei
    if not is_ollama_running(url_ollama, timeout_ollama):
        if not start_ollama_server(url_ollama, timeout_ollama):
            print("Not able to connect with Ollama.")
            return

    # 2. Verificació del Model
    if not pull_ollama_model(model):
        return

    # 3. Processament de l'Arxiu
    try:
        separator = '\t' if separador == '\\t' else separador
        
        with open(nom_fitxer, 'r', encoding='utf-8') as input_file, \
            codecs.open(nom_fitxer_sortida, "w", encoding="utf-8") as output_file:
            
            lector = csv.reader(input_file, delimiter=separator)

            for i, fila in enumerate(lector):
                # Permet el format P[0], P[1]... en el template
                prompt = prompt_template.format(P=fila)
                
                # Cridem a Ollama amb les opcions dinàmiques
                response = obtenir_resposta_ollama(prompt, model, generation_options)
                
                if regex_pattern:
                    match = re.search(regex_pattern, response)
                    respostafinal = match.group(1).strip() if match else response
                else:
                    respostafinal = response
                
                # Neteja de salts de línia en la resposta per mantenir format CSV/TSV
                respostafinal = respostafinal.replace("\n", " ")
                
                print(f"{separator.join(fila)}{separator}{respostafinal}")
                output_file.write(f"{separator.join(fila)}{separator}{respostafinal}\n")
                
        print(f"\nProcess ended. Results saved at: {nom_fitxer_sortida}")

    except Exception as e:
        print(f"\nUnexpected ERROR: {e}")

if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    
    if load_config(config_file):
        process_file(
            CONFIG["file_settings"],
            CONFIG["ollama_settings"],
            CONFIG["prompt_settings"]
        )
