import os
import shutil
import json
import re
import urllib.request
import tkinter as tk
from tkinter import filedialog
import winreg

CONFIG_FILE = "mod_sync_settings.json"
APP_ID = "4704690"
GAME_FOLDER_NAME = "MECCHA CHAMELEON"

def get_mod_name_from_steam(mod_id):
    """Fetches the mod name directly from the Steam Workshop web page."""
    url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={mod_id}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
        match = re.search(r'<div class="workshopItemTitle">([^<]+)</div>', html)
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return None

def get_steam_library_paths():
    """Scans Windows registry and Steam config to find all active Steam library paths."""
    libraries = []
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        steam_path = os.path.abspath(steam_path)
        libraries.append(steam_path)
        
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf_path):
            with open(vdf_path, 'r', encoding='utf-8') as f:
                content = f.read()
            matches = re.findall(r'"path"\s+"([^"]+)"', content)
            for match in matches:
                clean_path = os.path.abspath(match.replace('\\\\', '\\'))
                if clean_path not in libraries:
                    libraries.append(clean_path)
    except Exception:
        pass

    defaults = [r"C:\Program Files (x86)\Steam", r"C:\Program Files\Steam"]
    for d in defaults:
        if os.path.exists(d) and os.path.abspath(d) not in libraries:
            libraries.append(os.path.abspath(d))
            
    return libraries

def auto_detect_paths():
    """Attempts to find the exact paths automatically across all detected Steam libraries."""
    steam_libs = get_steam_library_paths()
    detected_workshop = None
    detected_game = None

    for lib in steam_libs:
        potential_workshop = os.path.join(lib, "steamapps", "workshop", "content", APP_ID)
        if os.path.exists(potential_workshop):
            detected_workshop = potential_workshop

        potential_game = os.path.join(lib, "steamapps", "common", GAME_FOLDER_NAME)
        if os.path.exists(potential_game):
            detected_game = potential_game

    return detected_workshop, detected_game

def select_folder(title):
    """Fallback manual selection popup window."""
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    return filedialog.askdirectory(title=title)

def get_user_paths():
    """Manages loading, auto-detecting, or manually selecting paths."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            settings = json.load(file)
            if os.path.exists(settings.get("steam_workshop", "")) and os.path.exists(settings.get("game_root", "")):
                return settings

    print("Scanning your system for Steam directories...")
    auto_workshop, auto_game = auto_detect_paths()

    if not auto_workshop:
        auto_workshop = select_folder(f"Select the Steam Workshop folder ending in {APP_ID}")
        if not auto_workshop: return None

    if not auto_game:
        auto_game = select_folder(f"Select your main {GAME_FOLDER_NAME} game folder")
        if not auto_game: return None

    settings = {"steam_workshop": auto_workshop, "game_root": auto_game}
    with open(CONFIG_FILE, 'w') as file:
        json.dump(settings, file)
        
    print("Paths successfully established!\n")
    return settings

def sync_and_patch_mods(steam_workshop_dir, game_root_dir):
    game_workshop_dir = os.path.join(game_root_dir, "Chameleon", "Binaries", "Win64", "workshop")
    ini_file_path = os.path.join(game_root_dir, "Chameleon", "Binaries", "Win64", "OnlineFix.ini")

    os.makedirs(game_workshop_dir, exist_ok=True)
    
    if not os.path.exists(steam_workshop_dir):
        print(f"Error: Steam Workshop folder does not exist at {steam_workshop_dir}")
        return

    steam_folders = [f for f in os.listdir(steam_workshop_dir) if os.path.isdir(os.path.join(steam_workshop_dir, f))]
    
    mods_processed = 0

    for folder_id in steam_folders:
        source_path = os.path.join(steam_workshop_dir, folder_id)
        target_path = os.path.join(game_workshop_dir, folder_id)

        print(f"Checking mod ID: {folder_id}...")
        
        mod_name = get_mod_name_from_steam(folder_id)
        if not mod_name:
            print("  -> Could not fetch name automatically from Steam.")
            mod_name = input(f"  -> Enter the Name manually for {folder_id}: ")
        else:
            print(f"  -> Name found online: {mod_name}")

        if not os.path.exists(target_path):
            print("  -> New mod. Copying files to game folder...")
            shutil.copytree(source_path, target_path)
        else:
            print("  -> Files already exist in game folder.")

        update_ini_file(ini_file_path, folder_id, mod_name)
        mods_processed += 1
        print("-" * 40)
            
    if mods_processed == 0:
        print("No workshop folders found to process.")
    else:
        print("Sync and patch complete!")

def update_ini_file(ini_path, folder_id, mod_name):
    if not os.path.exists(ini_path):
        print(f"  -> Error: Configuration file not found at {ini_path}")
        return

    with open(ini_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Find the [UGC] section header
    ugc_index = -1
    for i, line in enumerate(lines):
        if line.strip() == '[UGC]':
            ugc_index = i
            break

    new_entry = f"{folder_id}={mod_name}\n"

    # Scenario A: [UGC] section exists
    if ugc_index != -1:
        existing_index = -1
        for i in range(ugc_index + 1, len(lines)):
            if lines[i].strip().startswith('['):
                break
            if lines[i].startswith(f"{folder_id}="):
                existing_index = i
                break

        if existing_index != -1:
            lines[existing_index] = new_entry
            print(f"  -> Updated existing entry in OnlineFix.ini to '{folder_id}={mod_name}'")
        else:
            lines.insert(ugc_index + 1, new_entry)
            print(f"  -> Added new entry '{folder_id}={mod_name}' to OnlineFix.ini")

    # Scenario B: [UGC] does not exist anywhere in the file
    else:
        print("  -> [UGC] section not found. Automatically creating section at the end of the file...")
        # Ensure there's a newline spacing at the end if needed
        if lines and not lines[-1].endswith('\n'):
            lines[-1] = lines[-1] + '\n'
        
        lines.append("\n[UGC]\n")
        lines.append(new_entry)
        print(f"  -> Added section and entry '{folder_id}={mod_name}' to the end of OnlineFix.ini")

    with open(ini_path, 'w', encoding='utf-8') as file:
        file.writelines(lines)

if __name__ == "__main__":
    print("=========================================")
    print("   MECCHA CHAMELEON MOD SYNC UTILITY     ")
    print("=========================================\n")
    
    # 1. Ask the user if they want to run the tool
    start_choice = input("Do you want to run the program? (y/n): ").strip().lower()
    
    if start_choice in ['y', 'yes']:
        # Load or detect paths
        paths = get_user_paths()
        
        if paths:
            # 2. Ask the user if they want to initiate the sync
            sync_choice = input("Do you want to sync the workshop folders now? (y/n): ").strip().lower()
            
            if sync_choice in ['y', 'yes']:
                sync_and_patch_mods(paths["steam_workshop"], paths["game_root"])
            else:
                print("Sync canceled by user.")
        else:
            print("Could not resolve directory paths. Configuration incomplete.")
    else:
        print("Program closed.")
    
    input("\nPress Enter to exit...")
