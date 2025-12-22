from PySide6.QtWidgets import QApplication
from lib.GUI import MosaicGUI
import sys

def open_folder_callback(path):
    print("Selected XTF folder:", path)

def apply_settings_callback(settings):
    print("Settings:", settings)
    # call your settings-saving library here

app = QApplication(sys.argv)

gui = MosaicGUI(
    on_open_folder=open_folder_callback,
    on_apply_settings=apply_settings_callback
)

gui.show()
sys.exit(app.exec())