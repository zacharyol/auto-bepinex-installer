# BepInEx Auto-Installer

This is a desktop application that automatically detects Unity games installed via Steam and allows you to install BepInEx (mod loader) with a single click.

## Features
- Auto-detects Steam Unity games.
- Installs the latest stable BepInEx (x64) automatically.
- Detects **Gorilla Tag** and advises using **Monkey Mod Manager** instead.
- Modern GUI using CustomTkinter.

## Requirements
- Python 3.8+
- Steam installed

## Installation
1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the application:
```bash
python main.py
```

1. The app will scan your Steam libraries for Unity games.
2. Select a game from the list.
3. Click **Install BepInEx**.
   - If **Gorilla Tag** is selected, you will see a warning to use Monkey Mod Manager.
4. To uninstall, select the game and click **Uninstall**.

## Files
- `main.py`: The main GUI application.
- `steam_utils.py`: Logic for detecting Steam games.
- `bepinex_utils.py`: Logic for downloading and installing BepInEx.
- `requirements.txt`: List of dependencies.
