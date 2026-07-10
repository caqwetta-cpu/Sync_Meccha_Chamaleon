import os
import shutil
import json
import re
import urllib.request
import tkinter as tk
from tkinter import filedialog
import winreg

# --- GLOBAL CONSTANTS ---
# Name of the file where paths will be saved so we don't have to search for them every time
CONFIG_FILE = "mod_sync_settings.json"
# The game's Steam ID (used to find the Workshop folder)
APP_ID = "4704690"
# The name of the main game folder
GAME_FOLDER_NAME = "MECCHA CHAMELEON"

def get_mod_name_from_steam(mod_id):
    """
    Retrieves the mod name directly from the Steam Workshop web page.
    It makes an HTTP request and uses a regular expression (regex) to extract the title.
    """
    url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={mod_id}"
    try:
        # Pretends to be a browser to prevent Steam from blocking the request
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
        # Searches for the HTML class that contains the mod's title
        match = re.search(r'<div class="workshopItemTitle">([^<]+)</div>', html)
        if match:
            return match.group(1).strip()
    except Exception:
        # If something goes wrong (e.g., no internet connection), ignore the error
        pass
    return None

def get_steam_library_paths():
    """
    Scans the Windows registry and Steam config files to find 
    all the paths where Steam games are installed.
    """
    libraries = []
    try:
        # Looks for the main Steam path in the system registry
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        steam_path = os.path.abspath(steam_path)
        libraries.append(steam_path)
        
        # Reads the libraryfolders.vdf file which contains other library drives/folders
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf_path):
            with open(vdf_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Extracts all library paths using a regex
            matches = re.findall(r'"path"\s+"([^"]+)"', content)
            for match in matches:
                clean_path = os.path.abspath(match.replace('\\\\', '\\'))
                if clean_path not in libraries:
                    libraries.append(clean_path)
    except Exception:
        pass

    # Adds default Windows paths just in case the registry check fails
    defaults = [r"C:\Program Files (x86)\Steam", r"C:\Program Files\Steam"]
    for d in defaults:
        if os.path.exists(d) and os.path.abspath(d) not in libraries:
            libraries.append(os.path.abspath(d))
            
    return libraries

def auto_detect_paths():
    """
    Attempts to automatically find the exact Workshop and game folders 
    by searching within all detected Steam libraries.
    """
    steam_libs = get_steam_library_paths()
    detected_workshop = None
    detected_game = None

    for lib in steam_libs:
        # Checks if the mod folder for this game exists in this library
        potential_workshop = os.path.join(lib, "steamapps", "workshop", "content", APP_ID)
        if os.path.exists(potential_workshop):
            detected_workshop = potential_workshop

        # Checks if the main game folder exists in this library
        potential_game = os.path.join(lib, "steamapps", "common", GAME_FOLDER_NAME)
        if os.path.exists(potential_game):
            detected_game = potential_game

    return detected_workshop, detected_game

def select_folder(title):
    """
    Opens a Windows dialog box to let the user manually select 
    a folder if auto-detection fails.
    """
    root = tk.Tk()
    root.attributes("-topmost", True) # Keeps the window on top
    root.withdraw() # Hides the empty main tkinter window
    return filedialog.askdirectory(title=title)

def get_user_paths():
    """
    Manages obtaining the necessary paths: 
    1. Reads from the config file if it exists.
    2. Attempts auto-detection.
    3. Asks the user manually as a last resort.
    """
    # 1. Checks if we have already saved the settings in the past
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            settings = json.load(file)
            if os.path.exists(settings.get("steam_workshop", "")) and os.path.exists(settings.get("game_root", "")):
                return settings

    print("Scanning your system for Steam directories...")
    
    # 2. Attempts automatic search
    auto_workshop, auto_game = auto_detect_paths()

    # 3. Manual fallback for the Workshop folder
    if not auto_workshop:
        auto_workshop = select_folder(f"Select the Steam Workshop folder ending in {APP_ID}")
        if not auto_workshop: return None

    # 3. Manual fallback for the Game folder
    if not auto_game:
        auto_game = select_folder(f"Select your main {GAME_FOLDER_NAME} game folder")
        if not auto_game: return None

    # Saves the found settings into the JSON file for future startups
    settings = {"steam_workshop": auto_workshop, "game_root": auto_game}
    with open(CONFIG_FILE, 'w') as file:
        json.dump(settings, file)
        
    print("Paths successfully established!\n")
    return settings

def sync_and_patch_mods(steam_workshop_dir, game_root_dir):
    """
    Copies the mod folders from Steam to the game folder and 
    updates the .ini file with the copied mods' data.
    """
    # Specific destination paths inside the game folder
    game_workshop_dir = os.path.join(game_root_dir, "Chameleon", "Binaries", "Win64", "workshop")
    ini_file_path = os.path.join(game_root_dir, "Chameleon", "Binaries", "Win64", "OnlineFix.ini")

    # Creates the workshop folder in the game directory if it doesn't already exist
    os.makedirs(game_workshop_dir, exist_ok=True)
    
    if not os.path.exists(steam_workshop_dir):
        print(f"Error: Steam Workshop folder does not exist at {steam_workshop_dir}")
        return

    # Gets a list of all folders (mods) inside the Steam Workshop directory
    steam_folders = [f for f in os.listdir(steam_workshop_dir) if os.path.isdir(os.path.join(steam_workshop_dir, f))]
    
    mods_processed = 0

    # Loops through each found mod
    for folder_id in steam_folders:
        source_path = os.path.join(steam_workshop_dir, folder_id)
        target_path = os.path.join(game_workshop_dir, folder_id)

        print(f"Checking mod ID: {folder_id}...")
        
        # Retrieves the readable name of the mod from the web
        mod_name = get_mod_name_from_steam(folder_id)
        if not mod_name:
            print("  -> Could not fetch name automatically from Steam.")
            mod_name = input(f"  -> Enter the Name manually for {folder_id}: ")
        else:
            print(f"  -> Name found online: {mod_name}")

        # Copies the files if the mod is not already in the game directory
        if not os.path.exists(target_path):
            print("  -> New mod. Copying files to game folder...")
            shutil.copytree(source_path, target_path)
        else:
            print("  -> Files already exist in game folder.")

        # Adds the mod to the configuration file so the game recognizes it
        update_ini_file(ini_file_path, folder_id, mod_name)
        mods_processed += 1
        print("-" * 40)
            
    if mods_processed == 0:
        print("No workshop folders found to process.")
    else:
        print("Sync and patch complete!")

def update_ini_file(ini_path, folder_id, mod_name):
    """
    Modifies the OnlineFix.ini file by adding or updating 
    the mod entry under the [UGC] section.
    """
    if not os.path.exists(ini_path):
        print(f"  -> Error: Configuration file not found at {ini_path}")
        return

    # Reads all the contents of the .ini file
    with open(ini_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Searches for the line that contains the [UGC] header
    ugc_index = -1
    for i, line in enumerate(lines):
        if line.strip() == '[UGC]':
            ugc_index = i
            break

    # The line to be inserted (e.g., "123456=Mod Name")
    new_entry = f"{folder_id}={mod_name}\n"

    # Scenario A: The [UGC] section already exists in the file
    if ugc_index != -1:
        existing_index = -1
        # Searches within the [UGC] section to see if the ID already exists
        for i in range(ugc_index + 1, len(lines)):
            if lines[i].strip().startswith('['): # If another section begins, stop searching
                break
            if lines[i].startswith(f"{folder_id}="):
                existing_index = i
                break

        # If the mod exists, update its name; otherwise, insert it as a new entry
        if existing_index != -1:
            lines[existing_index] = new_entry
            print(f"  -> Updated existing entry in OnlineFix.ini to '{folder_id}={mod_name}'")
        else:
            lines.insert(ugc_index + 1, new_entry)
            print(f"  -> Added new entry '{folder_id}={mod_name}' to OnlineFix.ini")

    # Scenario B: The [UGC] section does not exist and must be created
    else:
        print("  -> [UGC] section not found. Automatically creating section at the end of the file...")
        # Ensures there's a proper newline/spacing before appending new text
        if lines and not lines[-1].endswith('\n'):
            lines[-1] = lines[-1] + '\n'
        
        lines.append("\n[UGC]\n")
        lines.append(new_entry)
        print(f"  -> Added section and entry '{folder_id}={mod_name}' to the end of OnlineFix.ini")

    # Writes the changes back to the file
    with open(ini_path, 'w', encoding='utf-8') as file:
        file.writelines(lines)

# --- STARTING POINT OF THE PROGRAM ---
if __name__ == "__main__":
    print("=========================================")
    print("   MECCHA CHAMELEON MOD SYNC UTILITY     ")
    print("=========================================\n")
    
    # 1. Asks the user if they want to run the program
    start_choice = input("Do you want to run the program? (y/n): ").strip().lower()
    
    if start_choice in ['y', 'yes']:
        # Loads or detects paths (Workshop and Game)
        paths = get_user_paths()
        
        if paths:
            # 2. Asks for confirmation before actually starting the file copying
            sync_choice = input("Do you want to sync the workshop folders now? (y/n): ").strip().lower()
            
            if sync_choice in ['y', 'yes']:
                # Starts the main process
                sync_and_patch_mods(paths["steam_workshop"], paths["game_root"])
            else:
                print("Sync canceled by user.")
        else:
            print("Could not resolve directory paths. Configuration incomplete.")
    else:
        print("Program closed.")
    
    # Keeps the console window open until a key is pressed
    input("\nPress Enter to exit...")
