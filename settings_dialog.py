from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QSlider, QHBoxLayout, QPushButton, QComboBox,
    QListWidget, QListWidgetItem, QAbstractItemView, QMessageBox, QLineEdit, QGridLayout, QWidget, QTabWidget, QColorDialog
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QSize
import os
import yaml

class SettingsDialog(QDialog):
    def __init__(self, parent=None, key_name_to_code=None, code_to_key_name=None):
        super().__init__(parent)
        self.setWindowTitle(parent.translations['Settings'])
        self.main_window = parent

        self.key_name_to_code = key_name_to_code
        self.code_to_key_name = code_to_key_name

        self.wheel_actions = ["Wheel Up", "Wheel Down", "No Action"]
        self.mouse_buttons = ["Left Button", "Middle Button", "Right Button", "No Button"]

        self.colors = self.main_window.colors.copy()

        self.tab_widget = QTabWidget()
        self.basic_settings_tab = QWidget()
        self.key_config_tab = QWidget()

        self.create_basic_settings_tab()
        self.create_key_config_tab()

        self.tab_widget.addTab(self.basic_settings_tab, self.main_window.translations['Basic Settings'])
        self.tab_widget.addTab(self.key_config_tab, self.main_window.translations['Key Config'])

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)

        save_button = QPushButton(self.main_window.translations['Save'])
        save_button.clicked.connect(self.accept)
        main_layout.addWidget(save_button)

        self.setLayout(main_layout)

    def create_basic_settings_tab(self):
        layout = QGridLayout()
        row = 0

        layout.addWidget(QLabel(self.main_window.translations['Save Name Template']), row, 0)
        self.save_name_input = QLineEdit(self.main_window.save_name_template)
        layout.addWidget(self.save_name_input, row, 1)
        row += 1

        layout.addWidget(QLabel(self.main_window.translations['Background Color']), row, 0)
        self.bg_color_button = QPushButton(self.main_window.background_color.name())
        self.bg_color_button.clicked.connect(self.change_background_color)
        layout.addWidget(self.bg_color_button, row, 1)
        row += 1

        layout.addWidget(QLabel(self.main_window.translations['Canvas Size']), row, 0)
        self.canvas_width_input = QLineEdit(str(self.main_window.default_canvas_size.width()))
        self.canvas_height_input = QLineEdit(str(self.main_window.default_canvas_size.height()))
        canvas_size_layout = QHBoxLayout()
        canvas_size_layout.addWidget(QLabel(self.main_window.translations['Width']))
        canvas_size_layout.addWidget(self.canvas_width_input)
        canvas_size_layout.addWidget(QLabel(self.main_window.translations['Height']))
        canvas_size_layout.addWidget(self.canvas_height_input)
        layout.addLayout(canvas_size_layout, row, 1)
        row += 1

        layout.addWidget(QLabel(self.main_window.translations['Pen Tablet Support']), row, 0)
        self.pen_tablet_checkbox = QComboBox()
        self.pen_tablet_checkbox.addItems([self.main_window.translations['Enabled'], self.main_window.translations['Disabled']])
        self.pen_tablet_checkbox.setCurrentIndex(0 if self.main_window.use_tablet else 1)
        layout.addWidget(self.pen_tablet_checkbox, row, 1)
        row += 1

        layout.addWidget(QLabel(self.main_window.translations['Auto-advance Image on Save']), row, 0)
        self.auto_advance_checkbox = QComboBox()
        self.auto_advance_checkbox.addItems([self.main_window.translations['Enabled'], self.main_window.translations['Disabled']])
        self.auto_advance_checkbox.setCurrentIndex(0 if self.main_window.auto_advance else 1)
        layout.addWidget(self.auto_advance_checkbox, row, 1)
        row += 1

        layout.addWidget(QLabel(self.main_window.translations['Language']), row, 0)
        self.language_combo = QComboBox()
        self.load_languages()
        layout.addWidget(self.language_combo, row, 1)
        row += 1

        layout.addWidget(QLabel(self.main_window.translations['Pen Colors']), row, 0)
        self.colors_list_widget = QListWidget()
        self.colors_list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.update_color_buttons()
        layout.addWidget(self.colors_list_widget, row, 1)
        color_buttons_layout = QHBoxLayout()
        self.add_color_button = QPushButton(self.main_window.translations['Add Color'])
        self.add_color_button.clicked.connect(self.add_pen_color)
        color_buttons_layout.addWidget(self.add_color_button)
        self.delete_color_button = QPushButton(self.main_window.translations['Delete Selected Color'])
        self.delete_color_button.clicked.connect(self.delete_selected_color)
        color_buttons_layout.addWidget(self.delete_color_button)
        layout.addLayout(color_buttons_layout, row + 1, 1)
        row += 2

        # 手ブレ補正のスライダーを追加
        layout.addWidget(QLabel(self.main_window.translations['Stabilization Degree']), row, 0)
        self.stabilization_slider = QSlider(Qt.Horizontal)
        self.stabilization_slider.setMinimum(0)
        self.stabilization_slider.setMaximum(25)  # 補正度合いの上限を設定
        self.stabilization_slider.setValue(self.main_window.stabilization_degree)
        self.stabilization_slider.setTickPosition(QSlider.TicksBelow)
        self.stabilization_slider.setTickInterval(1)
        stabilization_label = QLabel(str(self.main_window.stabilization_degree))
        self.stabilization_slider.valueChanged.connect(lambda value: stabilization_label.setText(str(value)))
        stabilization_layout = QHBoxLayout()
        stabilization_layout.addWidget(self.stabilization_slider)
        stabilization_layout.addWidget(stabilization_label)
        layout.addLayout(stabilization_layout, row, 1)
        row += 1

        # Delete Mode 設定を追加
        layout.addWidget(QLabel(self.main_window.translations['Delete Mode']), row, 0)
        self.delete_mode_combo = QComboBox()
        delete_mode_options = [
            self.main_window.translations['Delete Current Tool'],
            self.main_window.translations['Delete All'],
        ]
        self.delete_mode_combo.addItems(delete_mode_options)
        current_mode = self.main_window.delete_mode
        index = self.delete_mode_combo.findText(current_mode)
        if index != -1:
            self.delete_mode_combo.setCurrentIndex(index)
        layout.addWidget(self.delete_mode_combo, row, 1)
        row += 1

        # Save Mode 設定を追加
        layout.addWidget(QLabel(self.main_window.translations.get('Save Mode', 'Save Mode')), row, 0)
        self.save_mode_combo = QComboBox()
        save_mode_options = [
            self.main_window.translations.get('Pen Tool Only', 'Pen Tool Only'),
            self.main_window.translations.get('Path Tool Only', 'Path Tool Only'),
            self.main_window.translations.get('Pen and Path Tools Combined', 'Pen and Path Tools Combined')
        ]
        self.save_mode_combo.addItems(save_mode_options)
        current_mode_index = self.main_window.save_mode - 1  # save_mode は 1, 2, 3
        self.save_mode_combo.setCurrentIndex(current_mode_index)
        layout.addWidget(self.save_mode_combo, row, 1)
        row += 1

        # パスツール設定セクションのタイトルを追加
        path_tool_label = QLabel(self.main_window.translations['Path Tool Settings'])
        path_tool_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(path_tool_label, row, 0, 1, 2)
        row += 1

        # 単純化の度合い設定
        layout.addWidget(QLabel(self.main_window.translations['Default Simplification Tolerance']), row, 0)
        self.simplify_slider = QSlider(Qt.Horizontal)
        self.simplify_slider.setMinimum(0)
        self.simplify_slider.setMaximum(10)
        self.simplify_slider.setValue(self.main_window.default_simplify_tolerance)
        self.simplify_slider.setTickPosition(QSlider.TicksBelow)
        self.simplify_slider.setTickInterval(1)
        simplify_value_label = QLabel(str(self.main_window.default_simplify_tolerance))
        self.simplify_slider.valueChanged.connect(lambda value: simplify_value_label.setText(str(value)))
        simplify_layout = QHBoxLayout()
        simplify_layout.addWidget(self.simplify_slider)
        simplify_layout.addWidget(simplify_value_label)
        layout.addLayout(simplify_layout, row, 1)
        row += 1

        # 滑らかさの度合い設定
        layout.addWidget(QLabel(self.main_window.translations['Default Smoothing Strength']), row, 0)
        self.smooth_slider = QSlider(Qt.Horizontal)
        self.smooth_slider.setMinimum(0)
        self.smooth_slider.setMaximum(5)
        self.smooth_slider.setValue(self.main_window.default_smooth_strength)
        self.smooth_slider.setTickPosition(QSlider.TicksBelow)
        self.smooth_slider.setTickInterval(1)
        smooth_value_label = QLabel(str(self.main_window.default_smooth_strength))
        self.smooth_slider.valueChanged.connect(lambda value: smooth_value_label.setText(str(value)))
        smooth_layout = QHBoxLayout()
        smooth_layout.addWidget(self.smooth_slider)
        smooth_layout.addWidget(smooth_value_label)
        layout.addLayout(smooth_layout, row, 1)
        row += 1

        # パスの当たり判定の設定
        layout.addWidget(QLabel(self.main_window.translations['Path Hit Detection Threshold']), row, 0)
        self.hit_threshold_slider = QSlider(Qt.Horizontal)
        self.hit_threshold_slider.setMinimum(1)  # スライダーは整数値なので10倍して扱う
        self.hit_threshold_slider.setMaximum(200)
        self.hit_threshold_slider.setValue(int(self.main_window.path_hit_threshold * 10))
        self.hit_threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.hit_threshold_slider.setTickInterval(10)
        hit_threshold_value_label = QLabel(f"{self.main_window.path_hit_threshold:.1f}")
        self.hit_threshold_slider.valueChanged.connect(lambda value: hit_threshold_value_label.setText(f"{value / 10:.1f}"))
        hit_threshold_layout = QHBoxLayout()
        hit_threshold_layout.addWidget(self.hit_threshold_slider)
        hit_threshold_layout.addWidget(hit_threshold_value_label)
        layout.addLayout(hit_threshold_layout, row, 1)
        row += 1

        self.basic_settings_tab.setLayout(layout)

    def change_background_color(self):
        color = QColorDialog.getColor(initial=self.main_window.background_color,
                                      title=self.main_window.translations['Select Background Color'])
        if color.isValid():
            self.main_window.background_color = color
            self.bg_color_button.setText(color.name())
            self.bg_color_button.setStyleSheet(f"background-color: {color.name()}")

    def change_pen_color(self, color):
        new_color = QColorDialog.getColor(initial=color, title=self.main_window.translations['Select Pen Color'])
        if new_color.isValid():
            index = self.colors.index(color)
            self.colors[index] = new_color
            self.update_color_buttons()

    def add_pen_color(self):
        new_color = QColorDialog.getColor(title=self.main_window.translations['Select Pen Color'])
        if new_color.isValid():
            self.colors.append(new_color)
            self.update_color_buttons()

    def delete_selected_color(self):
        selected_items = self.colors_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.main_window.translations['Warning'],
                                self.main_window.translations['No color selected to delete.'])
            return
        for item in selected_items:
            row = self.colors_list_widget.row(item)
            self.colors.pop(row)
            self.colors_list_widget.takeItem(row)

    def update_color_buttons(self):
        self.colors_list_widget.clear()
        for color in self.colors:
            item = QListWidgetItem()
            item_widget = QPushButton()
            item_widget.setStyleSheet(f"background-color: {color.name()}")
            item_widget.clicked.connect(lambda checked, c=color: self.change_pen_color(c))
            item.setSizeHint(item_widget.sizeHint())
            self.colors_list_widget.addItem(item)
            self.colors_list_widget.setItemWidget(item, item_widget)

    def load_languages(self):
        language_folder = os.path.join(os.getcwd(), 'language')
        if not os.path.exists(language_folder):
            os.makedirs(language_folder)
        language_files = [f for f in os.listdir(language_folder) if f.startswith('language_') and f.endswith('.yaml')]
        self.languages = {}
        for file in language_files:
            lang_code = file[len('language_'):-len('.yaml')]
            self.languages[lang_code] = os.path.join(language_folder, file)
            self.language_combo.addItem(lang_code)
        current_language = self.main_window.language_code
        index = self.language_combo.findText(current_language)
        if index != -1:
            self.language_combo.setCurrentIndex(index)

    def create_key_config_tab(self):
        layout = QGridLayout()
        self.inputs = {}
        row = 0

        layout.addWidget(QLabel(f"<b>{self.main_window.translations['Shortcut Keys']}</b>"), row, 0, 1, 2)
        row += 1

        key_actions = [
            "Undo", "Redo", "Clear", "Next Color", "Previous Color", "Save", "Next Image",
            "Previous Image", "Eraser Tool", "Increase Pen Size", "Decrease Pen Size",
            "Merged Save", "Toggle Tool", "Toggle Fill", "Toggle Path Mode"  # <-- 追加
        ]
        for action in key_actions:
            layout.addWidget(QLabel(self.main_window.translations.get(action, action)), row, 0)
            combo = QComboBox()
            combo.addItems(self.key_name_to_code.keys())
            key = self.main_window.key_config.get(action, Qt.Key_No)
            key_name = self.code_to_key_name.get(key, "")
            index = combo.findText(key_name)
            if index != -1:
                combo.setCurrentIndex(index)
            layout.addWidget(combo, row, 1)
            self.inputs[action] = ('key', combo)
            row += 1

        layout.addWidget(QLabel(f"<b>{self.main_window.translations['Mouse Settings']}</b>"), row, 0, 1, 2)
        row += 1

        for action in ["Pen Tool", "Eraser Tool", "Increase Pen Size", "Decrease Pen Size"]:
            layout.addWidget(QLabel(self.main_window.translations.get(action, action)), row, 0)
            if action in ["Increase Pen Size", "Decrease Pen Size"]:
                combo = QComboBox()
                combo.addItems(self.wheel_actions + list(self.key_name_to_code.keys()))
                button = self.main_window.mouse_config.get(action, "No Action")
                if isinstance(button, int):
                    button_name = self.main_window.mouse_button_to_name(button)
                else:
                    button_name = button
                index = combo.findText(button_name)
                if index != -1:
                    combo.setCurrentIndex(index)
                layout.addWidget(combo, row, 1)
                self.inputs[action] = ('input', combo)
            else:
                combo = QComboBox()
                combo.addItems(self.mouse_buttons)
                button = self.main_window.mouse_config.get(action, Qt.LeftButton if action == "Pen Tool" else Qt.RightButton)
                button_name = self.main_window.mouse_button_to_name(button)
                index = combo.findText(button_name)
                if index != -1:
                    combo.setCurrentIndex(index)
                layout.addWidget(combo, row, 1)
                self.inputs[action] = ('mouse', combo)
            row += 1

        # 修飾キー設定のセクションを追加
        layout.addWidget(QLabel(f"<b>{self.main_window.translations['Modifier Keys']}</b>"), row, 0, 1, 2)
        row += 1

        modifier_actions = ["Add Control Point Modifier", "Delete Control Point Modifier"]
        modifier_names = ["Ctrl", "Alt", "Shift", "Meta", "No Modifier"]
        for action in modifier_actions:
            layout.addWidget(QLabel(self.main_window.translations.get(action, action)), row, 0)
            combo = QComboBox()
            combo.addItems(modifier_names)
            modifier = self.main_window.key_config.get(action, Qt.NoModifier)
            modifier_name = self.main_window.code_to_key_name.get(modifier, "No Modifier")
            index = combo.findText(modifier_name)
            if index != -1:
                combo.setCurrentIndex(index)
            layout.addWidget(combo, row, 1)
            self.inputs[action] = ('modifier', combo)
            row += 1

        self.key_config_tab.setLayout(layout)

    def accept(self):
        # 基本設定の保存
        self.main_window.save_name_template = self.save_name_input.text()

        try:
            width = int(self.canvas_width_input.text())
            height = int(self.canvas_height_input.text())
            new_size = QSize(width, height)
            if new_size != self.main_window.default_canvas_size:
                self.main_window.resize_canvas(new_size)
        except ValueError:
            QMessageBox.warning(self, self.main_window.translations['Warning'],
                                "Invalid canvas size. Please enter integer values.")
            return

        # ペンタブレットサポートの設定を更新
        self.main_window.use_tablet = (self.pen_tablet_checkbox.currentIndex() == 0)
        self.main_window.drawing_area.use_tablet = self.main_window.use_tablet
        self.main_window.drawing_area.setTabletTracking(self.main_window.use_tablet)

        # Auto-advanceの設定を更新
        self.main_window.auto_advance = (self.auto_advance_checkbox.currentIndex() == 0)

        # 言語の設定を更新
        selected_language = self.language_combo.currentText()
        if selected_language != self.main_window.language_code:
            self.main_window.language_code = selected_language
            self.main_window.load_language()
            self.main_window.update_gui_texts()

        # 背景色の変更を即時反映
        self.main_window.background_color = QColor(self.bg_color_button.text())
        self.main_window.update_background_color()

        # ペンの色を更新
        self.main_window.colors = self.colors
        self.main_window.drawing_area.colors = self.colors

        # 現在の色のインデックスが範囲内か確認
        if self.main_window.current_color_index >= len(self.colors):
            self.main_window.current_color_index = 0
        self.main_window.drawing_area.current_color_index = self.main_window.current_color_index

        # カーソルを更新
        self.main_window.drawing_area.update_cursor()

        # 手ブレ補正の度合いを取得
        self.main_window.stabilization_degree = self.stabilization_slider.value()
        self.main_window.drawing_area.set_stabilization_degree(self.main_window.stabilization_degree)

        # パスツール設定の保存
        self.main_window.default_simplify_tolerance = self.simplify_slider.value()
        self.main_window.default_smooth_strength = self.smooth_slider.value()
        self.main_window.path_hit_threshold = self.hit_threshold_slider.value() / 10

        # スプラインマネージャーに適用
        self.main_window.drawing_area.spline_manager.hit_threshold = self.main_window.path_hit_threshold

        # Deleteモードの保存
        self.main_window.handle_delete_mode_change(self.delete_mode_combo.currentText())

        # Undo/Redoスタックのリセット
        self.main_window.drawing_area.undo_stack.clear()
        self.main_window.drawing_area.redo_stack.clear()

        # パスツールの色と太さを更新
        if self.main_window.drawing_area.mode == 'spline':
            for vp in self.main_window.drawing_area.spline_manager.selected_paths:
                vp.pen_color = self.main_window.colors[self.main_window.current_color_index]
                vp.pen_width = self.main_window.pen_size
                vp.generate_path_from_bspline()

        self.main_window.drawing_area.update()

        # キー設定の保存
        for action, (input_type, input_widget) in self.inputs.items():
            if input_type == 'key':
                selected_key_name = input_widget.currentText()
                self.main_window.key_config[action] = self.key_name_to_code.get(selected_key_name, selected_key_name)
            elif input_type == 'mouse':
                selected = input_widget.currentText()
                self.main_window.mouse_config[action] = self.main_window.name_to_mouse_button(selected)
            elif input_type == 'input':
                selected = input_widget.currentText()
                if selected in self.wheel_actions:
                    self.main_window.mouse_config[action] = selected
                elif selected in self.key_name_to_code:
                    self.main_window.mouse_config[action] = self.key_name_to_code[selected]
                else:
                    self.main_window.mouse_config[action] = "No Action"
            elif input_type == 'modifier':
                selected_modifier_name = input_widget.currentText()
                self.main_window.key_config[action] = self.key_name_to_code.get(selected_modifier_name, Qt.NoModifier)

        # Save Mode の設定を保存
        self.main_window.save_mode = self.save_mode_combo.currentIndex() + 1  # インデックスは0から始まるので+1

        # 設定を保存
        self.main_window.settings_manager.save_settings()
        super().accept()
