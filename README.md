# 🦎 Sync Meccha Chameleon

[![Language: Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)]()

*Read this in other languages: [Italiano](#it-versione-italiana) | [English](#en-english-version)*

---

## IT Versione Italiana

Uno strumento automatizzato in Python per sincronizzare le mod (mappe) del Workshop di Steam direttamente nella cartella di gioco di **Meccha Chameleon**, configurandole automaticamente per funzionare con OnlineFix.

### 📋 Requisiti

* **Python 3.x** installato sul sistema (se esegui lo script `.py`).
* **Mod scaricate dal Workshop:** Le mod devono essere già state scaricate tramite Steam (percorso tipico: `...\SteamLibrary\steamapps\workshop\content\4704690`).
* **Gioco installato:** Il gioco deve trovarsi nella sua cartella di installazione Steam originale (percorso tipico: `...\SteamLibrary\steamapps\common\MECCHA CHAMELEON`).
* **File di configurazione:** Il file `OnlineFix.ini` deve essere presente nel seguente percorso:
  `...\MECCHA CHAMELEON\Chameleon\Binaries\Win64\OnlineFix.ini`

### ⚙️ Come funziona

1. **Rilevamento:** Il programma cerca automaticamente le librerie di Steam sul tuo PC per trovare i file del Workshop e l'installazione del gioco. Se il rilevamento automatico fallisce, aprirà una finestra per farti selezionare le cartelle manualmente.
2. **Creazione cartella:** Genera una nuova directory chiamata `workshop` all'interno di `...\MECCHA CHAMELEON\Chameleon\Binaries\Win64\`.
3. **Sincronizzazione:** Copia tutti i contenuti (come le mappe scaricate) dalla directory del Workshop di Steam alla nuova cartella `workshop` del gioco, copiando solo i file non ancora presenti.
4. **Patching del file .ini:** Recupera i nomi delle mod leggendoli direttamente dalla pagina web di Steam e aggiorna automaticamente il file `OnlineFix.ini` (aggiungendole alla sezione `[UGC]`) affinché il gioco riconosca correttamente i contenuti aggiuntivi.

### 🚀 Utilizzo

1. Scarica il file del programma o clona la repository.
2. Apri il terminale (o Prompt dei Comandi) nella cartella in cui si trova il file.
3. Esegui lo script:
   ```bash
   python nome_del_file.py
