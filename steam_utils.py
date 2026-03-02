import os
import vdf
import platform
import sys

def get_steam_path_windows():
    try:
        import winreg
        # Try to find Steam path in HKEY_CURRENT_USER
        hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Valve\\Steam")
        steam_path, _ = winreg.QueryValueEx(hkey, "SteamPath")
        winreg.CloseKey(hkey)
        return steam_path
    except (OSError, ImportError):
        pass

    try:
        import winreg
        # Try to find Steam path in HKEY_LOCAL_MACHINE (32-bit)
        hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Valve\\Steam")
        steam_path, _ = winreg.QueryValueEx(hkey, "InstallPath")
        winreg.CloseKey(hkey)
        return steam_path
    except (OSError, ImportError):
        pass

    # Fallback to default location
    default_path = r"C:\Program Files (x86)\Steam"
    if os.path.exists(default_path):
        return default_path
    
    return None

def get_steam_path_linux():
    # Common locations for Steam on Linux
    home = os.path.expanduser("~")
    paths = [
        os.path.join(home, ".steam", "steam"),
        os.path.join(home, ".local", "share", "Steam"),
    ]
    
    for path in paths:
        if os.path.isdir(path):
            return path
    return None

def get_steam_path_macos():
    # Common location for Steam on macOS
    home = os.path.expanduser("~")
    path = os.path.join(home, "Library", "Application Support", "Steam")
    if os.path.isdir(path):
        return path
    return None

def get_steam_path():
    """
    Retrieves the Steam installation path based on the OS.
    """
    system = platform.system()
    if system == "Windows":
        return get_steam_path_windows()
    elif system == "Linux":
        return get_steam_path_linux()
    elif system == "Darwin": # macOS
        return get_steam_path_macos()
    else:
        return None

def get_library_folders(steam_path):
    """
    Parses libraryfolders.vdf to find all Steam library folders.
    """
    library_folders = []
    
    # On Linux/Mac, the casing might differ, but usually it's lowercase 'steamapps'
    # Windows is case-insensitive.
    vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    
    # Check for capitalization variations if on Linux
    if not os.path.exists(vdf_path) and platform.system() != "Windows":
         # Sometimes it's SteamApps on older installs? Unlikely for libraryfolders.vdf
         pass
         
    if not os.path.exists(vdf_path):
        # Fallback: assume the steam path itself is a library
        return [steam_path]

    try:
        with open(vdf_path, 'r', encoding='utf-8') as f:
            data = vdf.load(f)
        
        if "libraryfolders" in data:
            for key in data["libraryfolders"]:
                entry = data["libraryfolders"][key]
                if isinstance(entry, dict) and "path" in entry:
                    library_folders.append(entry["path"])
                elif isinstance(entry, str): 
                     # Should not happen in new format but just in case
                     pass
    except Exception as e:
        print(f"Error parsing libraryfolders.vdf: {e}")
        # Return at least the main steam path if parsing fails
        return [steam_path]
        
    return library_folders

def is_unity_game(game_path):
    """
    Checks if the game at the given path is a Unity game.
    Look for UnityPlayer.dll (Windows), UnityPlayer.so (Linux), or *_Data folder.
    """
    if not os.path.isdir(game_path):
        return False
        
    # Check for UnityPlayer.dll (Windows)
    if os.path.exists(os.path.join(game_path, "UnityPlayer.dll")):
        return True
        
    # Check for UnityPlayer.so (Linux)
    if os.path.exists(os.path.join(game_path, "UnityPlayer.so")):
        return True
    
    # Check for *_Data folder
    # Most Unity games have a folder named <GameName>_Data
    for item in os.listdir(game_path):
        if item.endswith("_Data") and os.path.isdir(os.path.join(game_path, item)):
            return True
            
    # Check for macOS .app bundle
    if platform.system() == "Darwin":
        for item in os.listdir(game_path):
             if item.endswith(".app") and os.path.isdir(os.path.join(game_path, item)):
                 # Check inside the app bundle
                 contents_path = os.path.join(game_path, item, "Contents")
                 frameworks_path = os.path.join(contents_path, "Frameworks", "UnityPlayer.dylib")
                 if os.path.exists(frameworks_path):
                     return True
                     
    return False

def determine_game_platform(game_path):
    """
    Determines if the installed game is Windows, Linux, or macOS build.
    This is important for installing the correct BepInEx version (e.g. Proton usage).
    """
    # Check for Windows executable/dll
    if os.path.exists(os.path.join(game_path, "UnityPlayer.dll")) or any(f.endswith(".exe") for f in os.listdir(game_path)):
        return "Windows"
    
    # Check for Linux
    if os.path.exists(os.path.join(game_path, "UnityPlayer.so")) or any(f.endswith(".x86_64") for f in os.listdir(game_path)):
        return "Linux"
        
    # Check for macOS
    if any(f.endswith(".app") for f in os.listdir(game_path)):
        return "MacOS"
        
    # Fallback to host OS
    system = platform.system()
    if system == "Darwin": return "MacOS"
    if system == "Linux": return "Linux"
    return "Windows"

def get_installed_games():
    """
    Scans all Steam libraries for installed games.
    Returns a list of dictionaries:
    {
        "name": "Game Name",
        "path": "Full Path",
        "appid": "AppID",
        "is_unity": True/False,
        "is_gorilla_tag": True/False,
        "platform": "Windows" | "Linux" | "MacOS"
    }
    """
    steam_path = get_steam_path()
    if not steam_path:
        print("Steam not found.")
        return []

    libraries = get_library_folders(steam_path)
    games = []

    for lib in libraries:
        steamapps_path = os.path.join(lib, "steamapps")
        common_path = os.path.join(steamapps_path, "common")
        
        if not os.path.exists(steamapps_path):
            continue

        # Iterate over appmanifest files to get installed games
        for filename in os.listdir(steamapps_path):
            if filename.startswith("appmanifest_") and filename.endswith(".acf"):
                try:
                    with open(os.path.join(steamapps_path, filename), 'r', encoding='utf-8') as f:
                        manifest = vdf.load(f)
                    
                    if "AppState" in manifest:
                        app_state = manifest["AppState"]
                        name = app_state.get("name", "Unknown Game")
                        install_dir = app_state.get("installdir", "")
                        appid = app_state.get("appid", "")
                        
                        full_path = os.path.join(common_path, install_dir)
                        
                        if os.path.exists(full_path):
                            is_unity = is_unity_game(full_path)
                            is_gorilla_tag = (str(appid) == "1533390") or ("Gorilla Tag" in name)
                            
                            if is_unity:
                                game_platform = determine_game_platform(full_path)
                                games.append({
                                    "name": name,
                                    "path": full_path,
                                    "appid": appid,
                                    "is_unity": is_unity,
                                    "is_gorilla_tag": is_gorilla_tag,
                                    "platform": game_platform
                                })
                except Exception as e:
                    print(f"Error reading manifest {filename}: {e}")
                    continue
                    
    return games
