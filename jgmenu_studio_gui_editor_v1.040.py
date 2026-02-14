#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Name: Qt JGMenu GUI Editor
# Author: delliushencky/l-n0-0b
# License: GNU GPL v2
#
# This program is free software.
# You may distribute and/or modify it according to the terms of the
# GNU General Public License versions 2.
#
################################################################
import sys, os, subprocess
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit,
                             QScrollArea, QColorDialog, QFormLayout, QFontComboBox, 
                             QComboBox, QTabWidget, QSpinBox, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# Install the platform for Linux
os.environ["QT_QPA_PLATFORM"] = "xcb"
D_DIR = os.path.expanduser("~/.config/jgmenu")
D_RC = os.path.join(D_DIR, "jgmenurc")

class JGM_Styler(QWidget):
    def __init__(self):
        super().__init__()
        self.reg, self.f_reg, self.tr, self.labels = {}, {}, {}, []
        
        # Define a system language
        sys_l = os.environ.get('LANG', 'en')
        self.cur_lang = "rus" if "ru" in sys_l.lower() else "eng"
        
        if not os.path.exists(D_DIR): 
            os.makedirs(D_DIR, exist_ok=True)
        
        self.load_translation()
        self.init_ui()
        self.sync_config()

    def load_translation(self):
        """ Loading phrases from external files """
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{self.cur_lang}.ljgm")
        self.tr = {}
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                for ln in f:
                    if '=' in ln and not ln.startswith('#'):
                        k, v = map(str.strip, ln.split('=', 1))
                        self.tr[k] = v

    def _(self, k): 
        return self.tr.get(k, k)

    def init_ui(self):
        self.setWindowTitle(self._('title'))
        self.resize(850, 900)
        self.setStyleSheet("""
            QWidget { background: #2b303b; color: #f8f8f2; font-size: 13px; }
            QPushButton { background: #4f5b66; border-radius: 4px; padding: 8px; min-width: 80px; }
            QPushButton:hover { background: #65737e; }
            QLineEdit, QSpinBox, QComboBox { background: #343d46; border: 1px solid #4f5b66; padding: 3px; }
            QTabWidget::pane { border: 1px solid #4f5b66; }
            QCheckBox { spacing: 10px; }
        """)

        main_v = QVBoxLayout(self)
        
        # Top panel (Language and Initialization)
        top = QHBoxLayout()
        self.b_init = QPushButton(self._('btn_init'))
        self.b_init.clicked.connect(self.run_reset)
        
        self.lang_sel = QComboBox()
        self.lang_sel.addItems(["Русский", "English"])
        self.lang_sel.setCurrentIndex(0 if self.cur_lang == "rus" else 1)
        self.lang_sel.currentIndexChanged.connect(self.change_lang)
        
        top.addWidget(self.b_init); top.addStretch(); top.addWidget(self.lang_sel)
        main_v.addLayout(top)

        # Tabs
        self.tabs = QTabWidget()
        main_v.addWidget(self.tabs)

        self.lay_gen = self.add_sheet("tab_gen")
        self.lay_item = self.add_sheet("tab_items")
        self.lay_col = self.add_sheet("tab_colors")
        self.lay_fnt = self.add_sheet("tab_font")
        
        # CSV editor
        csv_w = QWidget(); csv_l = QVBoxLayout(csv_w)
        self.e_pre, self.e_app = QTextEdit(), QTextEdit()
        csv_l.addWidget(QLabel("Prepend.csv (Top):")); csv_l.addWidget(self.e_pre)
        csv_l.addWidget(QLabel("Append.csv (Bottom):")); csv_l.addWidget(self.e_app)
        self.tabs.addTab(csv_w, "CSV Editor")

        # Bottom buttons
        btns = QHBoxLayout()
        self.b_save = QPushButton(self._('btn_save'))
        self.b_save.setMinimumHeight(45); self.b_save.clicked.connect(self.run_save)
        
        self.b_prev = QPushButton(self._('btn_prev'))
        self.b_prev.setMinimumHeight(45); self.b_prev.setStyleSheet("background: #5e81ac;")
        self.b_prev.clicked.connect(self.run_preview)
        
        self.b_exit = QPushButton(self._('btn_exit'))
        self.b_exit.setMinimumHeight(45); self.b_exit.clicked.connect(self.close)
        
        btns.addWidget(self.b_save); btns.addWidget(self.b_prev); btns.addWidget(self.b_exit)
        main_v.addLayout(btns)

    def add_sheet(self, k):
        sc = QScrollArea(); sc.setWidgetResizable(True)
        w = QWidget(); l = QFormLayout(w); sc.setWidget(w)
        self.tabs.addTab(sc, self._(k)); return l

    def change_lang(self, idx):
        self.cur_lang = "rus" if idx == 0 else "eng"
        self.load_translation()
        self.refresh_ui_text()

    def refresh_ui_text(self):
        self.setWindowTitle(self._('title'))
        tabs_map = ["tab_gen", "tab_items", "tab_colors", "tab_font"]
        for i, k in enumerate(tabs_map): self.tabs.setTabText(i, self._(k))
        self.b_save.setText(self._('btn_save'))
        self.b_exit.setText(self._('btn_exit'))
        self.b_init.setText(self._('btn_init'))
        self.b_prev.setText(self._('btn_prev'))
        for k, lbl in self.labels: lbl.setText(self._(k))

    def pick_c(self, btn):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_c = color.name()
            btn.setText(hex_c); btn.setStyleSheet(f"background: {hex_c}")

    def add_row(self, k, v, target):
        h = QHBoxLayout()
        chk = QCheckBox(); chk.setChecked(True)
        lbl = QLabel(self._(k)); self.labels.append((k, lbl))
        
        options = {
            'menu_halign': ['left', 'right', 'center'],
            'menu_valign': ['top', 'bottom', 'center'],
            'position_mode': ['fixed', 'pointer', 'center'],
            'menu_animation_mode': ['none', 'fade', 'slideleft', 'slideright'],
            'sub_hover_action': ['0', '1'], 'tint2_look': ['0', '1'], 'sticky': ['0', '1']
        }

        if v.startswith('#'):
            p = v.split(); hex_c = p[0]; alp = p[1] if len(p)>1 else "100"
            btn = QPushButton(hex_c); btn.setStyleSheet(f"background: {hex_c}")
            sp = QSpinBox(); sp.setRange(0, 100); sp.setValue(int(alp))
            btn.clicked.connect(lambda ch, b=btn: self.pick_c(b))
            ctrl = (btn, sp); h.addWidget(btn); h.addWidget(sp)
        elif k in options:
            ctrl = QComboBox(); ctrl.addItems(options[k]); ctrl.setEditable(True); ctrl.setCurrentText(v); h.addWidget(ctrl)
            if k == 'position_mode': ctrl.currentTextChanged.connect(lambda val: self.check_conflicts('pos', val))
            if k == 'tint2_look': ctrl.currentTextChanged.connect(lambda val: self.check_conflicts('tint', val))
        elif v.replace('-','').isdigit():
            ctrl = QSpinBox(); ctrl.setRange(-1000, 2000); ctrl.setValue(int(v)); h.addWidget(ctrl)
            if k in ['item_height', 'icon_size']: ctrl.valueChanged.connect(lambda: self.validate_sizes())
        else:
            ctrl = QLineEdit(v); h.addWidget(ctrl)

        chk.toggled.connect(lambda active, c=ctrl: self._toggle_widget(c, active))
        h.insertWidget(0, chk); target.addRow(lbl, h)
        self.reg[k] = (chk, ctrl)

    def _toggle_widget(self, ctrl, active):
        if isinstance(ctrl, tuple): 
            for x in ctrl: x.setEnabled(active)
        else: ctrl.setEnabled(active)

#    def check_conflicts(self, type, value):
#        if type == 'pos' and value == 'center':
#            for k in ['menu_halign', 'menu_valign', 'menu_margin_x', 'menu_margin_y']:
#                if k in self.reg: self.reg[k][0].setChecked(False)
#        if type == 'tint' and value == '1':
#            for k in self.reg:
#                if k.startswith('color_'): self.reg[k][0].setChecked(False)

    def check_conflicts(self, type, value):
        # If center is selected, turn off alignment and indentation (they do not work in this mode)
        if type == 'pos':
            is_center = (value == 'center')
            is_pointer = (value == 'pointer')
            
            targets = ['menu_halign', 'menu_valign', 'menu_margin_x', 'menu_margin_y']
            for k in targets:
                if k in self.reg:
                    # If the center - turn off everything. If pointer - leave only align
                    should_enable = not is_center
                    self.reg[k][0].setChecked(should_enable)
                    self.reg[k][1].setEnabled(should_enable)

        # If tint2 _ look is enabled, jgmenu takes colors from the tint2 panel
        if type == 'tint':
            is_tint = (value == '1')
            for k in self.reg:
                if k.startswith('color_'):
                    # Uncheck so that these colors are not written in config
                    self.reg[k][0].setChecked(not is_tint)
                    self.reg[k][1].setEnabled(not is_tint)

    def validate_sizes(self):
        try:
            h = self.reg['item_height'][1].value()
            s = self.reg['icon_size'][1].value()
            self.reg['icon_size'][1].setStyleSheet("background: #882222;" if s > h else "")
        except: pass

    def sync_config(self):
        base = {
            # --- Глобальные (General) ---
            'menu_width': '200', 'menu_height_min': '0', 'menu_height_max': '0',
            'menu_halign': 'left', 'menu_valign': 'top', 'monitor': '0',
            'menu_margin_x': '10', 'menu_margin_y': '10', 'edge_snap_x': '30',
            'position_mode': 'fixed', 'stay_alive': '1', 'z_index': '10',
            'menu_radius': '4', 'menu_border': '1', 'sticky': '0',
            
            # --- Пункты (Items) ---
            'item_height': '28', 'item_width_max': '0', 'item_padding_x': '10',
            'item_padding_y': '4', 'item_icon_spacing': '10', 'item_margin_y': '0',
            'item_radius': '2', 'item_border': '0', 'icon_size': '22',
            'sub_hover_action': '1', 'sep_height': '5',
            
            # --- Система (System) ---
            'font': 'Sans:size=10', 'terminal_exec': 'x-terminal-emulator',
            'terminal_args': '-e', 'menu_animation_mode': 'fade',
            'csv_name_format': '%n', 'case_insensitive_search': '1',
            'tint2_look': '0', 'at_pointer': '0',
            
            # --- Цвета (Colors) ---
            'color_menu_bg': '#2b303b 100', 'color_menu_border': '#4f5b66 100',
            'color_norm_bg': '#2b303b 0', 'color_norm_fg': '#f8f8f2 100',
            'color_sel_bg': '#4f5b66 100', 'color_sel_fg': '#ffffff 100',
            'color_sep_fg': '#4f5b66 40'
        }

        if os.path.exists(D_RC):
            with open(D_RC, 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        try:
                            k, v = map(str.strip, line.split('=', 1))
                            base[k] = v
                        except: pass

        for k, v in base.items():
            if k == 'font': self.ui_f(v); continue
            dest = self.lay_col if 'color_' in k else (self.lay_item if 'item_' in k else self.lay_gen)
            self.add_row(k, v, dest)

    def ui_f(self, v):
        self.f_reg = {'f': QFontComboBox(), 's': QSpinBox()}
        self.f_reg['s'].setRange(6, 72); 
        self.lay_fnt.addRow(self._('font_family'), self.f_reg['f'])
        self.lay_fnt.addRow(self._('font_size'), self.f_reg['s'])

#    def run_save(self):
#        try:
#            with open(D_RC, 'w', encoding='utf-8') as f:
#                f.write(self.get_cfg_text())
#           ##QMessageBox.information(self, "OK", self._('msg_saved'))##
#        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def run_save(self):
        try:
            # Save the file
            with open(D_RC, 'w', encoding='utf-8') as f:
                f.write(self.get_cfg_text())
            
            # Save the CSV
            for n, box in [("prepend.csv", self.e_pre), ("append.csv", self.e_app)]:
                with open(os.path.join(D_DIR, n), 'w', encoding='utf-8') as f:
                    f.write(box.toPlainText())

            # Change the text on the button
            original_text = self.b_save.text()
            self.b_save.setText("OK")
            self.b_save.setStyleSheet("background: #a3be8c; color: #2b303b; font-weight: bold;") # Making it green for clarity
            self.b_save.setEnabled(False) # Turn off for the duration of the animation

            # We return everything back in 2000 ms (2 seconds)
            QTimer.singleShot(1000, lambda: self.reset_save_btn(original_text))

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def reset_save_btn(self, text):
        self.b_save.setText(text)
        self.b_save.setStyleSheet("background: #4f5b66; border-radius: 4px;")
        self.b_save.setEnabled(True) # end

    def get_cfg_text(self):
        # 1. font settings
        lines = [f"font = {self.f_reg['f'].currentFont().family()}:size={self.f_reg['s'].value()}"]
        
        # 2. all the parameters from the tabs
        for k, (chk, ctrl) in self.reg.items():
            if chk.isChecked():
                if isinstance(ctrl, tuple): 
                    # For colors: ctrl [0] is a button (HEX), ctrl [1] is a SpinBox (transparency)
                    val = f"{ctrl[0].text()} {ctrl[1].value()}"
                elif isinstance(ctrl, QComboBox): 
                    val = ctrl.currentText()
                elif isinstance(ctrl, QSpinBox): 
                    val = str(ctrl.value())
                else: 
                    val = ctrl.text()
                
                lines.append(f"{k} = {val}")
        
        return "\n".join(lines)

    def run_preview(self):
        """ Starts the jgmenu with a temporary config, having previously closed the old one """
        try:
            # First, force the running jgmenu to close
            subprocess.run(['pkill', 'jgmenu'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Deleting the lock file
            lock_path = os.path.expanduser("~/.jgmenu-lockfile")
            if os.path.exists(lock_path):
                try: os.remove(lock_path)
                except: pass

            temp_rc = "/tmp/jgmenurc_test" # creating a temporary configuration file
            with open(temp_rc, 'w', encoding='utf-8') as f: 
                f.write(self.get_cfg_text())
            
            subprocess.Popen(['jgmenu', '--config-file=' + temp_rc])
        except Exception as e:
            QMessageBox.warning(self, "Preview Error", f"Could not launch: {str(e)}")


    def run_reset(self):#exit program
        subprocess.run(['jgmenu', 'init'])
        QMessageBox.information(self, "Init", "jgmenu init executed")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, self._('exit_title'), self._('exit_confirm'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes: event.accept()
        else: event.ignore()

if __name__ == "__main__": 
    app = QApplication(sys.argv)
    ex = JGM_Styler(); ex.show()
    sys.exit(app.exec())
