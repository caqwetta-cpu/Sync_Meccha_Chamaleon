# 🦎 Sync Meccha Chameleon

[![Language: Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)]()

An automated Python utility to synchronize Steam Workshop mods (maps) directly into the **Meccha Chameleon** game folder, automatically configuring them to work with OnlineFix.

## 📋 Requirements

* **Python 3.x** installed on your system (if you are running the `.py` script).
* **Workshop Mods Downloaded:** Mods must already be downloaded via Steam (typical path: `...\SteamLibrary\steamapps\workshop\content\4704690`).
* **Game Installed:** The game must be located in its original Steam installation folder (typical path: `...\SteamLibrary\steamapps\common\MECCHA CHAMELEON`).
* **Configuration File:** The `OnlineFix.ini` file must be present at the following path:
  `...\MECCHA CHAMELEON\Chameleon\Binaries\Win64\OnlineFix.ini`

## ⚙️ How it works

1. **Detection:** The script automatically scans your PC's Steam libraries to locate the Workshop files and the game installation. If auto-detection fails, it will prompt you to manually select the folders.
2. **Folder Creation:** It creates a new `workshop` directory inside `...\MECCHA CHAMELEON\Chameleon\Binaries\Win64\`.
3. **Synchronization:** It copies all content (e.g., downloaded maps) from the Steam Workshop directory to the new local `workshop` folder, ensuring only missing files are copied to save time.
4. **INI Patching:** It fetches the readable mod names directly from the Steam webpage and automatically updates the `OnlineFix.ini` file (under the `[UGC]` section) so the game correctly registers and loads the custom content.

## 🚀 Usage

1. Download the script file or clone the repository.
2. Open your terminal (or Command Prompt) in the folder where the script is located.
3. Run the script by typing:
   ```bash
   python your_script_name.py
