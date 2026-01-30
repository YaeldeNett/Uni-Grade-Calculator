import os
import sys
import shutil
import winshell
from win32com.client import Dispatch

def create_shortcut(target, path, description=""):
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = os.path.dirname(target)
    shortcut.Description = description
    shortcut.IconLocation = target
    shortcut.save()

def install():
    # Identify source directory (where this installer is running from)
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    source_folder = os.path.join(base_dir, "GradeCalculator_Files")
    
    # Destination: %LOCALAPPDATA%\Programs\GradeCalculator
    local_app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
    dest_folder = os.path.join(local_app_data, "Programs", "GradeCalculator")
    
    print(f"Installing to {dest_folder}...")
    
    # Remove existing installation if present
    if os.path.exists(dest_folder):
        try:
            shutil.rmtree(dest_folder)
        except Exception as e:
            print(f"Error removing old version: {e}")
            return
            
    # Copy files
    try:
        shutil.copytree(source_folder, dest_folder)
    except Exception as e:
        print(f"Error copying files: {e}")
        return
        
    exe_path = os.path.join(dest_folder, "GradeCalculator_Fast.exe")
    
    # Create Shortcuts
    desktop = winshell.desktop()
    start_menu = winshell.programs()
    
    print("Creating shortcuts...")
    create_shortcut(exe_path, os.path.join(desktop, "Grade Calculator.lnk"), "Uni Grade Calculator")
    create_shortcut(exe_path, os.path.join(start_menu, "Grade Calculator.lnk"), "Uni Grade Calculator")
    
    print("Installation Complete!")
    input("Press Enter to exit...")

if __name__ == "__main__":
    install()
