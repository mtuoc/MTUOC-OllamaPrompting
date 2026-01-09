# MTUOC-OllamaPrompting

## Introduction

Scripts to perform automatic queries to LLMs using Ollama. The idea is to make automatic query to LLMs easier. There are two different versions: (1) fixed prompt and (2) specific prompt from each query. All the configuration is performed via YAML files. The scripts are written in very simple Python and can be easily adapted to different situations

## Script with fixed prompt

The script with a fixed prompt is MTUOC-OllamaFP.py. Fixed prompt means that the prompt is specified in the YAML configuration file and that this prompt will be used in all the queries. The YAML configuration file has the following parameters (example1.yaml):

```
# --- FILE AND DATA SETTINGS ---

file_settings:
  input_filename: totranslate.txt
  output_filename: translated.txt
  delimiter: '\t' 
  
# --- OLLAMA API SETTINGS ---

ollama_settings:
  model: "mistral"
  url: "http://localhost:11434"
  timeout: 5 
  temperature: 0.0

# --- LLM PROMPT AND RESPONSE PARSING ---

prompt_settings:
  # The prompt template uses the list P, which will be replaced in the script by P[0], P[1]...
  prompt_template: |
    You're an experienced Russian-Catalan translator. Translate this sentence from Russian to Catalan. Provide the translation and nothing else. Don't add any note nor any explanation.
    Russian: {P[0]}
    Catalan: 
    
    

  # Regex to extract the answer or None if no regex is required
  regex_pattern: None
```

If the file to translate contains one sentence per line, as in this example:

```
В уездном городе N было так много парикмахерских заведений и бюро похоронных процессий, что казалось, жители города рождаются лишь затем, чтобы побриться, остричься, освежить голову вежеталем и сразу же умереть. 
А на самом деле в уездном городе N люди рождались, брились и умирали довольно редко. 
Жизнь города N была тишайшей. 
Весенние вечера были упоительны, грязь под луною сверкала, как антрацит, и вся молодежь города до такой степени была влюблена в секретаршу месткома коммунальников, что это мешало ей собирать членские взносы.
```

The output file translated.txt would contain:

```
В уездном городе N было так много парикмахерских заведений и бюро похоронных процессий, что казалось, жители города рождаются лишь затем, чтобы побриться, остричься, освежить голову вежеталем и сразу же умереть. 	A la ciutat de districte hi havia tant de tallers de pelatges i oficines de processons funeràries que semblava que els habitants de la ciutat només naixien per a ser pelats, tallar-se el cabell, refrescar la seva cabella amb un ventall i morir immediatament.
А на самом деле в уездном городе N люди рождались, брились и умирали довольно редко. 	En veritat, a la vila de districte N, naixien, es barbaven i morien relativament poc.
Жизнь города N была тишайшей. 	La vida de la ciutat N va ser la més tranquil·la.
Весенние вечера были упоительны, грязь под луною сверкала, как антрацит, и вся молодежь города до такой степени была влюблена в секретаршу месткома коммунальников, что это мешало ей собирать членские взносы.	Les vesprades de primavera van ser seductoris, la fang brillava sota la lluna com l'antracita, i tota la joventut de la ciutat estava tan enamorada de la secretària del local dels comunalistes que això els impedia recaptar les quotes de membres.
```

Please, note that the output file will contain the source sentences and the target sentences separated by the `delimiter`. In this case the file contains only one parameter, the source sentence.

In `file_settings` we can specify the `input_filename` (that contains the parameters of each query, one query per line) and the `output_filename` (that will contain queries parameters and the response of the query) using the `delimiter`-

In `ollama_settings`we can set the `model` (any of the modellos available in [Ollama](https://ollama.com/search), the `url`of the Ollama server (if it is running locally by default "http://localhost:11434", the `timeout` and the `temperature`.

In `prompt_settings` we can specify the `prompt_template`. You can use any number of paramenters in P and use P[0], P[1] ... in the template. The number of parameters must match with the number of parameters in the `input_file` (the fields of the file lines using the `delimiter` as separator.

We can use a `regex_pattern` to extract the required information from the response, or None to get the whole response.

We can run the script:

`python3 MTUOC-OllamaFP.py example1.yaml`
