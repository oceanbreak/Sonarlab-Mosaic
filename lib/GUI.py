import numpy as np
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QFormLayout, QFrame, QCheckBox
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt


class MosaicGUI(QWidget):
    """
    GUI module for sidescan sonar mosaic builder.
    """

    def __init__(self, on_open_folder=None, on_apply_settings=None, on_convert_rastr=None):
        super().__init__()

        self.on_open_folder = on_open_folder
        self.on_apply_settings = on_apply_settings
        self.on_convert_rastr = on_convert_rastr

        self.setWindowTitle("Sidescan Mosaic Builder")
        self.setMinimumSize(900, 550)

        self._build_ui()
        self._apply_style()

    # ==========================================================
    # UI BUILD
    # ==========================================================

    def _build_ui(self):
        main_layout = QHBoxLayout(self)

        # ================= LEFT PANEL =================
        left_layout = QVBoxLayout()

        self.open_btn = QPushButton("Open Folder")
        self.convert_btn = QPushButton("Convert RASTR to XTF")
        self.open_btn.clicked.connect(self._open_folder)
        self.convert_btn.clicked.connect(self._convert_rastr)

        self.preview_label = QLabel("Mosaic Preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(450, 300)
        self.preview_label.setStyleSheet("border: 1px solid #444;")

        # ---- STATUS BAR ----
        self.status_frame = QFrame()
        self.status_frame.setFixedHeight(50)
        self.status_frame.setFrameShape(QFrame.StyledPanel)

        status_layout = QVBoxLayout(self.status_frame)
        status_layout.setContentsMargins(6, 4, 6, 4)

        self.status_text = QLabel("Ready")
        self.status_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        status_layout.addWidget(self.status_text)

        top_btn_layout = QHBoxLayout()
        top_btn_layout.addWidget(self.open_btn)
        top_btn_layout.addWidget(self.convert_btn)

        # left_layout
        # left_layout.addWidget(self.convert_btn)

        left_layout.addLayout(top_btn_layout)
        
        left_layout.addWidget(self.preview_label)
        left_layout.addWidget(self.status_frame)
        left_layout.addStretch()

        # ---- START / CANCEL BUTTONS ----
        self.start_btn = QPushButton("Start")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.cancel_btn)

        left_layout.addLayout(btn_layout)

        # ================= RIGHT PANEL (SETTINGS) =================
        right_layout = QVBoxLayout()

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.settings_form = QFormLayout()
        self.settings_form.setLabelAlignment(Qt.AlignLeft)

        # ---- SETTINGS FIELDS ----
        self.directory_edit = QLineEdit()
        self.mapscale_edit = QLineEdit()
        self.cableout_edit = QLineEdit()
        self.margins_edit = QLineEdit()
        self.gamma_edit = QLineEdit()
        self.corwindow_edit = QLineEdit()
        self.slantthreshold_edit = QLineEdit()
        self.startsearchbottom_edit = QLineEdit()
        self.stripescale_edit = QLineEdit()
        self.corsltrg_searchwindow_edit = QLineEdit()
        self.corcltrg_frst_refl_bias_edit = QLineEdit()

        self.debug_check = QCheckBox()
        self.correct_slantrange_check = QCheckBox()

        self._add_setting("Directory:", self.directory_edit, "Path to data directory")
        self._add_setting("Map Scale (px/m):", self.mapscale_edit, "Resulting scale in Pixels per meter")
        self._add_setting("Cable out (m):", self.cableout_edit, "Cable out correction value")
        self._add_setting("Image Margins (px):", self.margins_edit, "Image margin size in pixels")
        self._add_setting("Gamma:", self.gamma_edit, "Gamma correction value")
        self._add_setting("Filter Window Size:", self.corwindow_edit, "Window of filtering rotations of stripes")
        self._add_setting("Stripe Thickness:", self.stripescale_edit, "Scale of one individual sonar stripe in pixels (1 minimum)")
        self._add_setting("Slant Range Correction:", self.correct_slantrange_check, "Enable slant range correction")
        # self._add_setting("Threshold:", self.slantthreshold_edit, "Slant range threshold, not used")
        self._add_setting("Start Bottom Search (m):", self.startsearchbottom_edit, "Start searching bottom from this value")
        self._add_setting("Convolution Window (px):", self.corsltrg_searchwindow_edit, "Window used to detect first reflection")
        self._add_setting("First Reflection Shift (px):", self.corcltrg_frst_refl_bias_edit, "Shift first reflection to avoid black stripe in the middle, pixels")
        # self._add_setting("Debug:", self.debug_check, "Enable debug output")

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._apply_settings)

        right_layout.addWidget(title)
        right_layout.addLayout(self.settings_form)
        right_layout.addStretch()
        right_layout.addWidget(self.apply_btn)

        # ================= ASSEMBLE =================
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

    def _add_setting(self, name, widget, tooltip):
        label = QLabel(name)
        label.setToolTip(tooltip)
        self.settings_form.addRow(label, widget)

    # ==========================================================
    # ACTIONS
    # ==========================================================

    def _open_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select folder with XTF files", self.directory_edit.text()
        )
        if folder:
            self.set_status(f"Selected folder: {folder}")
            if self.on_open_folder:
                self.on_open_folder(folder)
                # Update directory setting
                self.directory_edit.setText(folder)
        if self.on_apply_settings:
            settings_dict = self.get_settings()
            self.on_apply_settings(settings_dict)

    def _convert_rastr(self):
        if self.on_convert_rastr:
            self.on_convert_rastr()

    def _apply_settings(self):
        settings_dict = self.get_settings()
        self.set_status("Settings applied")
        if self.on_apply_settings:
            self.on_apply_settings(settings_dict)

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def set_running(self, running: bool):
        self.start_btn.setEnabled(not running)
        self.cancel_btn.setEnabled(running)


    def load_settings(self, settings: dict):
        self.directory_edit.setText(str(settings.get("directory", "")))
        self.mapscale_edit.setText(str(settings.get("mapscale", "")))
        self.cableout_edit.setText(str(settings.get("cableout", "")))
        self.margins_edit.setText(str(settings.get("margins", "")))
        self.gamma_edit.setText(str(settings.get("gamma", "")))
        self.corwindow_edit.setText(str(settings.get("corwindow", "")))
        # self.slantthreshold_edit.setText(str(settings.get("slantthreshold", "")))
        self.startsearchbottom_edit.setText(str(settings.get("startsearchbottom", "")))
        self.stripescale_edit.setText(str(settings.get("stripescale", "")))
        self.corsltrg_searchwindow_edit.setText(str(settings.get("corsltrg_searchwindow", "")))
        self.corcltrg_frst_refl_bias_edit.setText(str(settings.get("corcltrg_frst_refl_bias", "")))

        # self.debug_check.setChecked(bool(int(settings.get("debug", 0))))
        self.correct_slantrange_check.setChecked(bool(int(settings.get("correct_slantrange", 0))))

    def get_settings(self) -> dict:
        return {
            "directory": self.directory_edit.text(),
            "mapscale": float(self.mapscale_edit.text()),
            "cableout": int(self.cableout_edit.text()),
            "margins": int(self.margins_edit.text()),
            "gamma": float(self.gamma_edit.text()),
            "corwindow": int(self.corwindow_edit.text()),
            # "slantthreshold": int(self.slantthreshold_edit.text()),
            "slantthreshold" : 0,
            "startsearchbottom": int(self.startsearchbottom_edit.text()),
            "stripescale": int(self.stripescale_edit.text()),
            # "debug": int(self.debug_check.isChecked()),
            "debug" : 0,
            "correct_slantrange": int(self.correct_slantrange_check.isChecked()),
            "corsltrg_searchwindow": int(self.corsltrg_searchwindow_edit.text()),
            "corcltrg_frst_refl_bias": int(self.corcltrg_frst_refl_bias_edit.text())
        }

    def set_preview_image(self, image):
        if image is None:
            self.preview_label.clear()
            return
        if isinstance(image, np.ndarray):
            image = self._numpy_to_qimage(image)

        pixmap = QPixmap.fromImage(image).scaled(
            self.preview_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.preview_label.setPixmap(pixmap)

    def set_status(self, text, error=False):
        self.status_text.setText(text)
        color = "#EC0909" if error else "#aaaaaa"
        self.status_text.setStyleSheet(f"color: {color};")

    # ==========================================================
    # UTILS
    # ==========================================================

    def _numpy_to_qimage(self, img):
        if img.ndim == 2:
            h, w = img.shape
            return QImage(img.data, w, h, w, QImage.Format_Grayscale8)
        elif img.ndim == 3:
            h, w, c = img.shape
            return QImage(img.data, w, h, w * c, QImage.Format_RGB888)
        else:
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
            QToolTip {
                background-color: #2b2b2b;
                color: #dddddd;
                border: 1px solid #555;
                padding: 4px;
            }
        """)
