import customtkinter as ctk
import steam_utils
import bepinex_utils
import threading
import tkinter
from tkinter import messagebox

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("BepInEx Auto-Installer")
        self.geometry("700x500")
        
        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="BepInEx\nInstaller", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.scan_button = ctk.CTkButton(self.sidebar_frame, text="Rescan Games", command=self.scan_games)
        self.scan_button.grid(row=1, column=0, padx=20, pady=10)

        # Settings Section
        self.settings_label = ctk.CTkLabel(self.sidebar_frame, text="Settings:", anchor="w", font=ctk.CTkFont(size=14, weight="bold"))
        self.settings_label.grid(row=2, column=0, padx=20, pady=(20, 0), sticky="w")
        
        self.logging_console_switch = ctk.CTkSwitch(self.sidebar_frame, text="Logging Console")
        self.logging_console_switch.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 20))
        
        # Main Content
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.game_list_label = ctk.CTkLabel(self.main_frame, text="Detected Unity Games:", font=ctk.CTkFont(size=16, weight="bold"))
        self.game_list_label.grid(row=0, column=0, pady=10, padx=10, sticky="w")
        
        self.game_list_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.game_list_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        # Details Area
        self.details_frame = ctk.CTkFrame(self.main_frame)
        self.details_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        self.selected_game_label = ctk.CTkLabel(self.details_frame, text="Select a game from the list above", font=ctk.CTkFont(size=14))
        self.selected_game_label.pack(pady=10)
        
        self.status_label = ctk.CTkLabel(self.details_frame, text="")
        self.status_label.pack(pady=5)
        
        self.action_buttons_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        self.action_buttons_frame.pack(pady=10)

        self.action_button = ctk.CTkButton(self.action_buttons_frame, text="Install BepInEx", state="disabled", command=self.install_bepinex)
        self.action_button.pack(side="left", padx=5)
        
        self.uninstall_button = ctk.CTkButton(self.action_buttons_frame, text="Uninstall", state="disabled", fg_color="red", hover_color="darkred", command=self.uninstall_bepinex)
        self.uninstall_button.pack(side="left", padx=5)
        
        # Initialize
        self.games = []
        self.selected_game = None
        
        # Auto-scan on startup
        self.scan_games()

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def scan_games(self):
        self.status_label.configure(text="Scanning for Unity games...")
        self.update()
        threading.Thread(target=self._scan_games_thread).start()

    def _scan_games_thread(self):
        try:
            self.games = steam_utils.get_installed_games()
            self.after(0, self.update_game_list)
        except Exception as e:
            print(f"Error scanning games: {e}")
            self.after(0, lambda: self.status_label.configure(text="Error scanning games."))

    def update_game_list(self):
        # Clear existing buttons
        for widget in self.game_list_frame.winfo_children():
            widget.destroy()
            
        if not self.games:
            self.status_label.configure(text="No Unity games found.")
            return

        for game in self.games:
            # Create a frame for each game item to hold name and status
            # Or just a button
            btn_text = game["name"]
            if game.get("is_gorilla_tag", False):
                btn_text += " (Gorilla Tag)"
                
            btn = ctk.CTkButton(self.game_list_frame, text=btn_text, 
                                command=lambda g=game: self.select_game(g),
                                fg_color="transparent", border_width=1, text_color=("gray10", "#DCE4EE"))
            btn.pack(pady=2, padx=5, fill="x")
            
        self.status_label.configure(text=f"Found {len(self.games)} Unity games.")

    def select_game(self, game):
        self.selected_game = game
        name = game["name"]
        path = game["path"]
        is_installed = bepinex_utils.check_bepinex_installed(path)
        
        status_text = "BepInEx INSTALLED" if is_installed else "BepInEx NOT installed"
        self.selected_game_label.configure(text=f"{name}\n{path}\n\n{status_text}")
        
        if game.get("is_gorilla_tag", False):
            self.action_button.configure(state="normal", text="Read Warning", command=self.show_gorilla_tag_warning, fg_color="orange", hover_color="darkorange")
            self.uninstall_button.configure(state="disabled") 
        else:
            self.action_button.configure(fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#36719F", "#144870"]) # Reset color
            if is_installed:
                self.action_button.configure(state="disabled", text="Installed")
                self.uninstall_button.configure(state="normal")
            else:
                self.action_button.configure(state="normal", text="Install BepInEx", command=self.install_bepinex)
                self.uninstall_button.configure(state="disabled")

    def show_gorilla_tag_warning(self):
        messagebox.showinfo("Gorilla Tag Detected", 
                                    "For Gorilla Tag, it is highly recommended to use 'Monkey Mod Manager'.\n\n"
                                    "It handles dependencies and specific mods better than a manual BepInEx install.")

    def install_bepinex(self):
        if not self.selected_game:
            return
            
        path = self.selected_game["path"]
        platform = self.selected_game.get("platform", "Windows")
        self.status_label.configure(text="Downloading and Installing BepInEx...")
        self.action_button.configure(state="disabled")
        
        enable_console = self.logging_console_switch.get() == 1

        def run_install():
            success, msg = bepinex_utils.install_bepinex(path, enable_console=enable_console, platform=platform)
            self.after(0, lambda: self.finish_install(success, msg))
            
        threading.Thread(target=run_install).start()

    def finish_install(self, success, msg):
        if success:
            self.status_label.configure(text="Installation Successful!")
            messagebox.showinfo("Success", "BepInEx installed successfully!")
        else:
            self.status_label.configure(text="Installation Failed!")
            messagebox.showerror("Error", f"Failed to install: {msg}")
            
        # Refresh selection
        if self.selected_game:
            self.select_game(self.selected_game)

    def uninstall_bepinex(self):
        if not self.selected_game:
            return
            
        path = self.selected_game["path"]
        if messagebox.askyesno("Uninstall", "Are you sure you want to remove BepInEx?"):
             success, msg = bepinex_utils.uninstall_bepinex(path)
             if success:
                 self.status_label.configure(text="Uninstalled successfully.")
                 messagebox.showinfo("Success", "BepInEx uninstalled.")
             else:
                 self.status_label.configure(text="Uninstall failed.")
                 messagebox.showerror("Error", f"Failed to uninstall: {msg}")
             
             if self.selected_game:
                 self.select_game(self.selected_game)

if __name__ == "__main__":
    app = App()
    app.mainloop()
