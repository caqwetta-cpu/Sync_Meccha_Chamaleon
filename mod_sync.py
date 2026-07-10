import os
import shutil
import json
import re
import urllib.request
import tkinter as tk
from tkinter import filedialog
import winreg

# --- COSTANTI GLOBALI ---
# Nome del file in cui verranno salvati i percorsi per non doverli cercare ogni volta
CONFIG_FILE = "mod_sync_settings.json"
# L'ID del gioco su Steam (usato per trovare la cartella del Workshop)
APP_ID = "4704690"
# Il nome della cartella principale del gioco
GAME_FOLDER_NAME = "MECCHA CHAMELEON"

def get_mod_name_from_steam(mod_id):
    """
    Recupera il nome della mod direttamente dalla pagina web del Workshop di Steam.
    Effettua una richiesta HTTP e usa un'espressione regolare (regex) per estrarre il titolo.
    """
    url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={mod_id}"
    try:
        # Finge di essere un browser per evitare blocchi da parte di Steam
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
        # Cerca la classe HTML che contiene il titolo della mod
        match = re.search(r'<div class="workshopItemTitle">([^<]+)</div>', html)
        if match:
            return match.group(1).strip()
    except Exception:
        # Se qualcosa va storto (es. assenza di internet), ignora l'errore
        pass
    return None

def get_steam_library_paths():
    """
    Scansiona il registro di Windows e i file di configurazione di Steam per trovare 
    tutti i percorsi in cui sono installati i giochi.
    """
    libraries = []
    try:
        # Cerca il percorso principale di Steam nel registro di sistema
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        steam_path = os.path.abspath(steam_path)
        libraries.append(steam_path)
        
        # Legge il file libraryfolders.vdf che contiene gli altri dischi/cartelle di libreria
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf_path):
            with open(vdf_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Estrae tutti i percorsi delle librerie usando una regex
            matches = re.findall(r'"path"\s+"([^"]+)"', content)
            for match in matches:
                clean_path = os.path.abspath(match.replace('\\\\', '\\'))
                if clean_path not in libraries:
                    libraries.append(clean_path)
    except Exception:
        pass

    # Aggiunge i percorsi di default di Windows nel caso in cui il registro fallisca
    defaults = [r"C:\Program Files (x86)\Steam", r"C:\Program Files\Steam"]
    for d in defaults:
        if os.path.exists(d) and os.path.abspath(d) not in libraries:
            libraries.append(os.path.abspath(d))
            
    return libraries

def auto_detect_paths():
    """
    Tenta di trovare automaticamente le cartelle esatte del Workshop e del gioco 
    cercando all'interno di tutte le librerie di Steam rilevate.
    """
    steam_libs = get_steam_library_paths()
    detected_workshop = None
    detected_game = None

    for lib in steam_libs:
        # Controlla se la cartella delle mod per questo gioco esiste in questa libreria
        potential_workshop = os.path.join(lib, "steamapps", "workshop", "content", APP_ID)
        if os.path.exists(potential_workshop):
            detected_workshop = potential_workshop

        # Controlla se la cartella principale del gioco esiste in questa libreria
        potential_game = os.path.join(lib, "steamapps", "common", GAME_FOLDER_NAME)
        if os.path.exists(potential_game):
            detected_game = potential_game

    return detected_workshop, detected_game

def select_folder(title):
    """
    Apre una finestra di dialogo di Windows per far selezionare manualmente 
    una cartella all'utente se la rilevazione automatica fallisce.
    """
    root = tk.Tk()
    root.attributes("-topmost", True) # Mantiene la finestra in primo piano
    root.withdraw() # Nasconde la finestra principale vuota di tkinter
    return filedialog.askdirectory(title=title)

def get_user_paths():
    """
    Gestisce l'ottenimento dei percorsi necessari: 
    1. Legge dal file di configurazione se esiste.
    2. Prova l'autorilevamento.
    3. Chiede manualmente all'utente come ultima risorsa.
    """
    # 1. Controlla se abbiamo già salvato le impostazioni in passato
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            settings = json.load(file)
            if os.path.exists(settings.get("steam_workshop", "")) and os.path.exists(settings.get("game_root", "")):
                return settings

    print("Scansione del sistema per trovare le cartelle di Steam...")
    
    # 2. Tenta la ricerca automatica
    auto_workshop, auto_game = auto_detect_paths()

    # 3. Fallback manuale per la cartella del Workshop
    if not auto_workshop:
        auto_workshop = select_folder(f"Seleziona la cartella del Workshop di Steam che finisce per {APP_ID}")
        if not auto_workshop: return None

    # 3. Fallback manuale per la cartella del Gioco
    if not auto_game:
        auto_game = select_folder(f"Seleziona la tua cartella principale del gioco {GAME_FOLDER_NAME}")
        if not auto_game: return None

    # Salva le impostazioni trovate nel file JSON per i futuri avvii
    settings = {"steam_workshop": auto_workshop, "game_root": auto_game}
    with open(CONFIG_FILE, 'w') as file:
        json.dump(settings, file)
        
    print("Percorsi stabiliti con successo!\n")
    return settings

def sync_and_patch_mods(steam_workshop_dir, game_root_dir):
    """
    Copia le cartelle delle mod da Steam alla cartella del gioco e 
    aggiorna il file .ini con i dati delle mod copiate.
    """
    # Percorsi di destinazione specifici all'interno della cartella del gioco
    game_workshop_dir = os.path.join(game_root_dir, "Chameleon", "Binaries", "Win64", "workshop")
    ini_file_path = os.path.join(game_root_dir, "Chameleon", "Binaries", "Win64", "OnlineFix.ini")

    # Crea la cartella del workshop nel gioco se non esiste già
    os.makedirs(game_workshop_dir, exist_ok=True)
    
    if not os.path.exists(steam_workshop_dir):
        print(f"Errore: La cartella del Workshop di Steam non esiste in {steam_workshop_dir}")
        return

    # Ottiene la lista di tutte le cartelle (mod) all'interno del Workshop di Steam
    steam_folders = [f for f in os.listdir(steam_workshop_dir) if os.path.isdir(os.path.join(steam_workshop_dir, f))]
    
    mods_processed = 0

    # Cicla attraverso ogni mod trovata
    for folder_id in steam_folders:
        source_path = os.path.join(steam_workshop_dir, folder_id)
        target_path = os.path.join(game_workshop_dir, folder_id)

        print(f"Controllo della mod ID: {folder_id}...")
        
        # Recupera il nome leggibile della mod dal web
        mod_name = get_mod_name_from_steam(folder_id)
        if not mod_name:
            print("  -> Impossibile recuperare il nome automaticamente da Steam.")
            mod_name = input(f"  -> Inserisci il nome manualmente per {folder_id}: ")
        else:
            print(f"  -> Nome trovato online: {mod_name}")

        # Copia i file se la mod non è già presente nel gioco
        if not os.path.exists(target_path):
            print("  -> Nuova mod. Copia dei file nella cartella del gioco...")
            shutil.copytree(source_path, target_path)
        else:
            print("  -> I file esistono già nella cartella del gioco.")

        # Aggiunge la mod al file di configurazione per farla riconoscere al gioco
        update_ini_file(ini_file_path, folder_id, mod_name)
        mods_processed += 1
        print("-" * 40)
            
    if mods_processed == 0:
        print("Nessuna cartella workshop trovata da processare.")
    else:
        print("Sincronizzazione e patching completati!")

def update_ini_file(ini_path, folder_id, mod_name):
    """
    Modifica il file OnlineFix.ini aggiungendo o aggiornando 
    la voce relativa alla mod sotto la sezione [UGC].
    """
    if not os.path.exists(ini_path):
        print(f"  -> Errore: File di configurazione non trovato in {ini_path}")
        return

    # Legge tutto il contenuto del file .ini
    with open(ini_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Cerca la riga in cui è presente l'intestazione [UGC]
    ugc_index = -1
    for i, line in enumerate(lines):
        if line.strip() == '[UGC]':
            ugc_index = i
            break

    # La riga da inserire (es: "123456=Nome Mod")
    new_entry = f"{folder_id}={mod_name}\n"

    # Scenario A: La sezione [UGC] esiste già nel file
    if ugc_index != -1:
        existing_index = -1
        # Cerca all'interno della sezione [UGC] per vedere se l'ID esiste già
        for i in range(ugc_index + 1, len(lines)):
            if lines[i].strip().startswith('['): # Se inizia un'altra sezione, fermati
                break
            if lines[i].startswith(f"{folder_id}="):
                existing_index = i
                break

        # Se la mod esiste, aggiorna il suo nome, altrimenti inseriscila come nuova voce
        if existing_index != -1:
            lines[existing_index] = new_entry
            print(f"  -> Aggiornata voce esistente in OnlineFix.ini in '{folder_id}={mod_name}'")
        else:
            lines.insert(ugc_index + 1, new_entry)
            print(f"  -> Aggiunta nuova voce '{folder_id}={mod_name}' in OnlineFix.ini")

    # Scenario B: La sezione [UGC] non esiste, deve essere creata
    else:
        print("  -> Sezione [UGC] non trovata. Creazione automatica della sezione alla fine del file...")
        # Assicura che ci sia uno spazio/a capo corretto prima di aggiungere nuovo testo
        if lines and not lines[-1].endswith('\n'):
            lines[-1] = lines[-1] + '\n'
        
        lines.append("\n[UGC]\n")
        lines.append(new_entry)
        print(f"  -> Sezione e voce '{folder_id}={mod_name}' aggiunte alla fine di OnlineFix.ini")

    # Scrive le modifiche nel file
    with open(ini_path, 'w', encoding='utf-8') as file:
        file.writelines(lines)

# --- PUNTO DI INIZIO DEL PROGRAMMA ---
if __name__ == "__main__":
    print("=========================================")
    print("   MECCHA CHAMELEON MOD SYNC UTILITY     ")
    print("=========================================\n")
    
    # 1. Chiede all'utente se vuole eseguire il programma
    start_choice = input("Vuoi avviare il programma? (y/n): ").strip().lower()
    
    if start_choice in ['y', 'yes']:
        # Carica o rileva i percorsi (Workshop e Gioco)
        paths = get_user_paths()
        
        if paths:
            # 2. Chiede conferma prima di avviare effettivamente la copia dei file
            sync_choice = input("Vuoi sincronizzare le cartelle del workshop ora? (y/n): ").strip().lower()
            
            if sync_choice in ['y', 'yes']:
                # Avvia il processo principale
                sync_and_patch_mods(paths["steam_workshop"], paths["game_root"])
            else:
                print("Sincronizzazione annullata dall'utente.")
        else:
            print("Impossibile risolvere i percorsi delle cartelle. Configurazione incompleta.")
    else:
        print("Programma chiuso.")
    
    # Mantiene la finestra della console aperta fino alla pressione di un tasto
    input("\nPremi Invio per uscire...")
