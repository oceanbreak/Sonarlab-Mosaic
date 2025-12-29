import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread

from lib.GUI import MosaicGUI
from lib.RastrWorker import RastrWorker
from lib.MosaicWorker import MosaicWorker
from lib.Settings import Settings

import os

if 'PROJ_LIB' in os.environ:
    del os.environ['PROJ_LIB']

# !!!!!!!! UNCOMMENT the following  line for pyinstaller make
# os.environ["PROJ_LIB"] = '_internal\pyproj\proj_dir\share\proj'


class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)

        self.gui = MosaicGUI(
            on_open_folder=self.on_open_folder,
            on_apply_settings=self.on_apply_settings
        )

        self.thread = None
        self.worker = None
        self.rastr_worker = None
        self.current_folder = None

        self._cur_worker = 0 # 1 for  main, 2 for rastr

        self.settings = Settings()

        # ---- BUTTON CONNECTIONS ----
        self.gui.start_btn.clicked.connect(self.start_processing)
        self.gui.cancel_btn.clicked.connect(self.cancel_processing)
        self.gui.convert_btn.clicked.connect(self.start_rastr2xtf)

        self.gui.load_settings(self.settings.as_dict())
        self.gui.show()
        sys.exit(self.app.exec())

    # ================= USER ACTIONS =================

    def on_open_folder(self, folder):
        self.current_folder = folder
        self.gui.set_status(f"Folder selected: {folder}")

    def on_apply_settings(self, dict_settings):
        self.gui.set_status("Settings saved")
        self.settings.updateSettingsFromUI(dict_settings)
        self.settings.writefile()

    # ================= THREAD CONTROL =================

    def start_rastr2xtf(self):
        self._cur_worker = 2
        self.gui.set_running(True)
        self.gui.set_status("Starting converting to XTF...")

        self.thread = QThread()
        self.rastr_worker = RastrWorker(self.settings)
        self.rastr_worker.moveToThread(self.thread)

        # ---- CONNECT SIGNALS ----
        self.thread.started.connect(self.rastr_worker.process)

        self.rastr_worker.status.connect(self.gui.set_status)
        # self.rastr_worker.image.connect(self.gui.set_preview_image)

        self.rastr_worker.finished.connect(self.cleanup_thread)
        self.rastr_worker.cancelled.connect(self.cleanup_thread)

        self.thread.start()


    def start_processing(self):
        # if not self.current_folder:
        #     self.gui.set_status("No folder selected", error=True)
        #     return
        self._cur_worker = 1
        self.gui.set_running(True)
        self.gui.set_status("Starting processing...")

        self.thread = QThread()
        self.worker = MosaicWorker(self.settings)
        self.worker.moveToThread(self.thread)

        # ---- CONNECT SIGNALS ----
        self.thread.started.connect(self.worker.process)

        self.worker.status.connect(self.gui.set_status)
        self.worker.image.connect(self.gui.set_preview_image)

        self.worker.finished.connect(self.cleanup_thread)
        self.worker.cancelled.connect(self.cleanup_thread)

        self.thread.start()

    def cancel_processing(self):
        if self.worker:
            self.gui.set_status("Cancelling...")
            self.worker.abort()
            # self.cleanup_thread()

    # ================= CLEANUP =================

    def cleanup_thread(self):
        self.gui.set_running(False)

        self.thread.quit()
        # self.thread.wait()
        if self._cur_worker == 1:
            self.worker.deleteLater()
        elif self._cur_worker == 2:
            self.rastr_worker.deleteLater()
        self.thread.deleteLater()
        self._cur_worker = 0




if __name__ == "__main__":
    AppController()
