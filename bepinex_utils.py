import os
import requests
import zipfile
import shutil
import stat
from io import BytesIO

BEPINEX_X64_URL = "https://github.com/BepInEx/BepInEx/releases/download/v5.4.22/BepInEx_x64_5.4.22.0.zip"
BEPINEX_X86_URL = "https://github.com/BepInEx/BepInEx/releases/download/v5.4.22/BepInEx_x86_5.4.22.0.zip"
BEPINEX_UNIX_URL = "https://github.com/BepInEx/BepInEx/releases/download/v5.4.22/BepInEx_unix_5.4.22.0.zip"

BEPINEX_CONFIG_CONTENT = """[Caching]

## Enable/disable assembly metadata cache
## Enabling this will speed up discovery of plugins and patchers by caching the metadata of all types BepInEx discovers.
# Setting type: Boolean
# Default value: true
EnableAssemblyCache = true

[Chainloader]

## If enabled, hides BepInEx Manager GameObject from Unity.
## This can fix loading issues in some games that attempt to prevent BepInEx from being loaded.
## Use this only if you know what this option means, as it can affect functionality of some older plugins.
## 
# Setting type: Boolean
# Default value: false
HideManagerGameObject = false

[Harmony.Logger]

## Specifies which Harmony log channels to listen to.
## NOTE: IL channel dumps the whole patch methods, use only when needed!
# Setting type: LogChannel
# Default value: Warn, Error
# Acceptable values: None, Info, IL, Warn, Error, Debug, All
# Multiple values can be set at the same time by separating them with , (e.g. Debug, Warning)
LogChannels = Warn, Error

[Logging]

## Enables showing unity log messages in the BepInEx logging system.
# Setting type: Boolean
# Default value: true
UnityLogListening = true

## If enabled, writes Standard Output messages to Unity log
## NOTE: By default, Unity does so automatically. Only use this option if no console messages are visible in Unity log
## 
# Setting type: Boolean
# Default value: false
LogConsoleToUnityLog = false

[Logging.Console]

## Enables showing a console for log output.
# Setting type: Boolean
# Default value: false
Enabled = true

## If enabled, will prevent closing the console (either by deleting the close button or in other platform-specific way).
# Setting type: Boolean
# Default value: false
PreventClose = false

## If true, console is set to the Shift-JIS encoding, otherwise UTF-8 encoding.
# Setting type: Boolean
# Default value: false
ShiftJisEncoding = false

## Hints console manager on what handle to assign as StandardOut. Possible values:
## Auto - lets BepInEx decide how to redirect console output
## ConsoleOut - prefer redirecting to console output; if possible, closes original standard output
## StandardOut - prefer redirecting to standard output; if possible, closes console out
## 
# Setting type: ConsoleOutRedirectType
# Default value: Auto
# Acceptable values: Auto, ConsoleOut, StandardOut
StandardOutType = Auto

## Which log levels to show in the console output.
# Setting type: LogLevel
# Default value: Fatal, Error, Warning, Message, Info
# Acceptable values: None, Fatal, Error, Warning, Message, Info, Debug, All
# Multiple values can be set at the same time by separating them with , (e.g. Debug, Warning)
LogLevels = Fatal, Error, Warning, Message, Info

[Logging.Disk]

## Include unity log messages in log file output.
# Setting type: Boolean
# Default value: false
WriteUnityLog = false

## Appends to the log file instead of overwriting, on game startup.
# Setting type: Boolean
# Default value: false
AppendLog = false

## Enables writing log messages to disk.
# Setting type: Boolean
# Default value: true
Enabled = true

## Which log leves are saved to the disk log output.
# Setting type: LogLevel
# Default value: Fatal, Error, Warning, Message, Info
# Acceptable values: None, Fatal, Error, Warning, Message, Info, Debug, All
# Multiple values can be set at the same time by separating them with , (e.g. Debug, Warning)
LogLevels = Fatal, Error, Warning, Message, Info

[Preloader]

## Enables or disables runtime patches.
## This should always be true, unless you cannot start the game due to a Harmony related issue (such as running .NET Standard runtime) or you know what you're doing.
# Setting type: Boolean
# Default value: true
ApplyRuntimePatches = true

## Specifies which MonoMod backend to use for Harmony patches. Auto uses the best available backend.
## This setting should only be used for development purposes (e.g. debugging in dnSpy). Other code might override this setting.
# Setting type: MonoModBackend
# Default value: auto
# Acceptable values: auto, dynamicmethod, methodbuilder, cecil
HarmonyBackend = auto

## If enabled, BepInEx will save patched assemblies into BepInEx/DumpedAssemblies.
## This can be used by developers to inspect and debug preloader patchers.
# Setting type: Boolean
# Default value: false
DumpAssemblies = false

## If enabled, BepInEx will load patched assemblies from BepInEx/DumpedAssemblies instead of memory.
## This can be used to be able to load patched assemblies into debuggers like dnSpy.
## If set to true, will override DumpAssemblies.
# Setting type: Boolean
# Default value: false
LoadDumpedAssemblies = false

## If enabled, BepInEx will call Debugger.Break() once before loading patched assemblies.
## This can be used with debuggers like dnSpy to install breakpoints into patched assemblies before they are loaded.
# Setting type: Boolean
# Default value: false
BreakBeforeLoadAssemblies = false

[Preloader.Entrypoint]

## The local filename of the assembly to target.
# Setting type: String
# Default value: UnityEngine.CoreModule.dll
Assembly = UnityEngine.CoreModule.dll

## The name of the type in the entrypoint assembly to search for the entrypoint method.
# Setting type: String
# Default value: Application
Type = Application

## The name of the method in the specified entrypoint assembly and type to hook and load Chainloader from.
# Setting type: String
# Default value: .cctor
Method = .cctor
"""

def download_bepinex(url):
    """
    Downloads BepInEx zip from the given URL.
    Returns the zip file content as BytesIO object.
    """
    print(f"Downloading BepInEx from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    return BytesIO(response.content)

def install_bepinex(game_path, is_x64=True, enable_console=False, platform="Windows"):
    """
    Installs BepInEx to the specified game directory.
    If enable_console is True, installs the custom config file.
    platform: "Windows", "Linux", or "MacOS"
    """
    if platform == "Windows":
        url = BEPINEX_X64_URL if is_x64 else BEPINEX_X86_URL
    else:
        # Unix version (Linux/MacOS)
        url = BEPINEX_UNIX_URL
    
    try:
        zip_data = download_bepinex(url)
        
        with zipfile.ZipFile(zip_data, 'r') as zip_ref:
            print(f"Extracting BepInEx to {game_path}...")
            zip_ref.extractall(game_path)
            
        # Set execute permissions for run_bepinex.sh on Unix
        if platform in ["Linux", "MacOS"]:
            run_script = os.path.join(game_path, "run_bepinex.sh")
            if os.path.exists(run_script):
                st = os.stat(run_script)
                os.chmod(run_script, st.st_mode | stat.S_IEXEC)
                print(f"Made {run_script} executable.")

        if enable_console:
            print("Configuring BepInEx for console logging...")
            config_dir = os.path.join(game_path, "BepInEx", "config")
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, "BepInEx.cfg")
            
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(BEPINEX_CONFIG_CONTENT)
            print("Custom config installed.")
            
        print("BepInEx installation complete.")
        return True, "Installation successful."
    except Exception as e:
        print(f"Error installing BepInEx: {e}")
        return False, str(e)

def check_bepinex_installed(game_path):
    """
    Checks if BepInEx is already installed in the game directory.
    Checks for winhttp.dll (Windows) or run_bepinex.sh (Unix).
    """
    bepinex_folder = os.path.join(game_path, "BepInEx")
    
    winhttp_dll = os.path.join(game_path, "winhttp.dll")
    run_script = os.path.join(game_path, "run_bepinex.sh")
    
    has_files = os.path.isfile(winhttp_dll) or os.path.isfile(run_script)
    
    return os.path.isdir(bepinex_folder) and has_files

def uninstall_bepinex(game_path):
    """
    Removes BepInEx from the game directory.
    """
    bepinex_folder = os.path.join(game_path, "BepInEx")
    
    # Windows files
    winhttp_dll = os.path.join(game_path, "winhttp.dll")
    doorstop_ini = os.path.join(game_path, "doorstop_config.ini")
    
    # Unix files
    run_script = os.path.join(game_path, "run_bepinex.sh")
    doorstop_libs = os.path.join(game_path, "doorstop_libs")
    
    try:
        if os.path.exists(bepinex_folder):
            shutil.rmtree(bepinex_folder)
        if os.path.exists(winhttp_dll):
            os.remove(winhttp_dll)
        if os.path.exists(doorstop_ini):
            os.remove(doorstop_ini)
        if os.path.exists(run_script):
            os.remove(run_script)
        if os.path.exists(doorstop_libs):
             shutil.rmtree(doorstop_libs)
             
        return True, "Uninstallation successful."
    except Exception as e:
        return False, str(e)
