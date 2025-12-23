from PySide6.QtWidgets import QApplication
from lib.GUI import MosaicGUI
from lib.Settings import Settings
import sys

global settings
settings = Settings()

def open_folder_callback(path):
    print("Selected XTF folder:", path)
    settings.directory = path
    

def apply_settings_callback(dict_settings : dict):
    print("Settings:", dict_settings)
    settings.updateSettingsFromUI(dict_settings)
    settings.writefile()
    # call your settings-saving library here

# Initiate settings

# print(settings)



app = QApplication(sys.argv)

gui = MosaicGUI(
    on_open_folder=open_folder_callback,
    on_apply_settings=apply_settings_callback
)

gui.load_settings(settings.as_dict())
gui.show()
sys.exit(app.exec())

