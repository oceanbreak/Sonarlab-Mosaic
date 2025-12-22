from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit,
    QFileDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QApplication, QFrame
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
import numpy as np


class MosaicGUI(QWidget):
    """
    GUI module for sidescan sonar mosaic preview & settings.
    """

    def __init__(self, on_open_folder=None, on_apply_settings=None):
        super().__init__()

        self.on_open_folder = on_open_folder
        self.on_apply_settings = on_apply_settings

        self.setWindowTitle("Sidescan Mosaic Builder")
        self.setMinimumSize(820, 500)

        self._build_ui()
        self._apply_style()

    # ---------------- UI ---------------- #

    def _build_ui(self):
        main_layout = QHBoxLayout(self)

        # === LEFT SIDE ===
        left_layout = QVBoxLayout()

        self.open_btn = QPushButton("Open XTF Folder")
        self.open_btn.clicked.connect(self._open_folder)

        self.preview_label = QLabel("Mosaic Preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(420, 300)
        self.preview_label.setStyleSheet("border: 1px solid #444;")

        # ---- STATUS AREA ----
        self.status_frame = QFrame()
        self.status_frame.setFixedHeight(50)
        self.status_frame.setFrameShape(QFrame.StyledPanel)

        status_layout = QVBoxLayout(self.status_frame)
        status_layout.setContentsMargins(6, 4, 6, 4)

        self.status_text = QLabel("Ready")
        self.status_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        status_layout.addWidget(self.status_text)

        left_layout.addWidget(self.open_btn)
        left_layout.addWidget(self.preview_label)
        left_layout.addWidget(self.status_frame)
        left_layout.addStretch()

        # === RIGHT SIDE (SETTINGS) ===
        right_layout = QVBoxLayout()

        settings_title = QLabel("Settings")
        settings_title.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.settings_form = QFormLayout()
        self.settings_form.setLabelAlignment(Qt.AlignLeft)

        # ---- SCALE SETTING ----
        scale_label = QLabel("Scale:")
        scale_label.setToolTip(
            "Scaling factor for the output mosaic.\n"
            "Example: 1.0 = original resolution"
        )

        self.scale_edit = QLineEdit("1.0")

        self.settings_form.addRow(scale_label, self.scale_edit)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._apply_settings)

        right_layout.addWidget(settings_title)
        right_layout.addLayout(self.settings_form)
        right_layout.addStretch()
        right_layout.addWidget(self.apply_btn)

        # === ASSEMBLE ===
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

    # ---------------- ACTIONS ---------------- #

    def _open_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select folder with XTF files"
        )
        if folder:
            self.set_status(f"Selected folder: {folder}")
            if self.on_open_folder:
                self.on_open_folder(folder)

    def _apply_settings(self):
        try:
            settings = {
                "scale": float(self.scale_edit.text())
            }
        except ValueError:
            self.set_status("Invalid scale value", error=True)
            return

        self.set_status("Settings applied")
        if self.on_apply_settings:
            self.on_apply_settings(settings)

    # ---------------- PUBLIC API ---------------- #

    def set_preview_image(self, image):
        """
        Set preview image.

        Parameters
        ----------
        image : np.ndarray or QImage
        """
        if isinstance(image, np.ndarray):
            image = self._numpy_to_qimage(image)

        pixmap = QPixmap.fromImage(image)
        pixmap = pixmap.scaled(
            self.preview_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.preview_label.setPixmap(pixmap)

    def set_status(self, text, error=False):
        """
        Update status text.

        Parameters
        ----------
        text : str
        error : bool
            If True, status text is shown as error
        """
        self.status_text.setText(text)
        if error:
            self.status_text.setStyleSheet("color: #ff6666;")
        else:
            self.status_text.setStyleSheet("color: #aaaaaa;")

    # ---------------- UTILS ---------------- #

    def _numpy_to_qimage(self, img):
        if img.ndim == 2:
            h, w = img.shape
            return QImage(img.data, w, h, w, QImage.Format_Grayscale8)

        elif img.ndim == 3:
            h, w, c = img.shape
            return QImage(img.data, w, h, w * c, QImage.Format_RGB888)

        raise ValueError("Unsupported image format")

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #dddddd;
                font-family: Segoe UI;
                font-size: 12px;
            }

            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #444;
                padding: 6px;
                border-radius: 4px;
            }

            QPushButton:hover {
                background-color: #3a3a3a;
            }

            QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #444;
                padding: 4px;
                border-radius: 3px;
            }

            QFrame {
                background-color: #252525;
                border: 1px solid #444;
            }

            QLabel {
                color: #cccccc;
            }

            QToolTip {
                background-color: #2b2b2b;
                color: #dddddd;
                border: 1px solid #555;
                padding: 4px;
            }
        """)
