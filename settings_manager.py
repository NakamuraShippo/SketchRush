import os
import yaml
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QSize


class SettingsManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.settings = {}
        self.config_file = "config.yaml"
        self.load_settings()

    def load_settings(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.settings = yaml.safe_load(f) or {}
            self.main_window.key_config.update(
                {k: self.main_window.key_name_to_code.get(v, v) for k, v in self.settings.get('key_config', {}).items()})
            self.main_window.mouse_config = self.deserialize_mouse_config(
                self.settings.get('mouse_config', {}))
            self.main_window.save_name_template = self.settings.get('save_name_template', "blackline{:03d}.png")
            self.main_window.save_folder = self.settings.get('save_folder', "")
            bg_color = QColor(self.settings.get('background_color', '#ffffff'))
            if bg_color.isValid():
                self.main_window.background_color = bg_color
            self.main_window.default_canvas_size = QSize(*self.settings.get('canvas_size', [512, 512]))
            self.main_window.save_counter = self.settings.get('save_counter', 0)
            self.main_window.save_mode = self.settings.get('save_mode', 1)
            self.main_window.use_tablet = self.settings.get('use_tablet', True)
            self.main_window.language_code = self.settings.get('language_code', 'EN')
            self.main_window.colors = [QColor(name) for name in self.settings.get('colors', [])] or self.main_window.colors
            self.main_window.auto_advance = self.settings.get('auto_advance', True)
            self.main_window.default_simplify_tolerance = self.settings.get('default_simplify_tolerance', 1)
            self.main_window.default_smooth_strength = self.settings.get('default_smooth_strength', 1)
            self.main_window.path_hit_threshold = self.settings.get('path_hit_threshold', 2.0)
            self.main_window.delete_mode = self.settings.get('delete_mode', 'Delete Current Tool')
            self.main_window.stabilization_degree = self.settings.get('stabilization_degree', 0)
            # 修飾キーの読み込み
            self.main_window.key_config.update(
                {k: self.main_window.key_name_to_code.get(v, v) for k, v in self.settings.get('key_config', {}).items()})
        except Exception as e:
            print(f"Could not load settings: {e}")

    def save_settings(self):
        key_config_serialized = {k: self.main_window.code_to_key_name.get(v, str(v)) for k, v in self.main_window.key_config.items()}
        mouse_config_serialized = self.serialize_mouse_config(self.main_window.mouse_config)
        self.settings.update({
            'key_config': key_config_serialized,
            'mouse_config': mouse_config_serialized,
            'save_name_template': self.main_window.save_name_template,
            'save_folder': self.main_window.save_folder,
            'background_color': self.main_window.background_color.name(),
            'canvas_size': [self.main_window.default_canvas_size.width(), self.main_window.default_canvas_size.height()],
            'save_counter': self.main_window.save_counter,
            'save_mode': self.main_window.save_mode,
            'use_tablet': self.main_window.use_tablet,
            'language_code': self.main_window.language_code,
            'colors': [color.name() for color in self.main_window.colors],
            'auto_advance': self.main_window.auto_advance,
            'stabilization_degree': self.main_window.stabilization_degree,
            'default_simplify_tolerance': self.main_window.default_simplify_tolerance,
            'default_smooth_strength': self.main_window.default_smooth_strength,
            'path_hit_threshold': self.main_window.path_hit_threshold,
            'delete_mode': self.main_window.delete_mode,
        })
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self.settings, f)

    def serialize_mouse_config(self, mouse_config):
        serialized = {}
        for k, v in mouse_config.items():
            if isinstance(v, int):
                serialized[k] = self.main_window.mouse_button_to_name(v)
            elif isinstance(v, str):
                serialized[k] = v
            else:
                serialized[k] = self.main_window.code_to_key_name.get(v, str(v))
        return serialized

    def deserialize_mouse_config(self, mouse_config_serialized):
        deserialized = {}
        for k, v in mouse_config_serialized.items():
            if k in ["Pen Tool", "Eraser Tool"]:
                deserialized[k] = self.main_window.name_to_mouse_button(v)
            elif k in ["Increase Pen Size", "Decrease Pen Size"]:
                if v in ["Wheel Up", "Wheel Down", "No Action"]:
                    deserialized[k] = v
                else:
                    deserialized[k] = self.main_window.key_name_to_code.get(v, v)
            else:
                deserialized[k] = v
        return deserialized
