import sys
import os
import yaml
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QLabel, QVBoxLayout, QWidget,
                            QAction, QMenu, QInputDialog, QColorDialog, QDialog, QGridLayout, QPushButton, QLineEdit, QSizePolicy, QComboBox, QMessageBox, QTabWidget, QListWidget, QListWidgetItem, QHBoxLayout, QAbstractItemView)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QCursor, QImage, QKeySequence, QTabletEvent
from PyQt5.QtCore import Qt, QPoint, QSize, QRect, QEvent
from PIL import Image
from PyQt5.QtCore import QTimer

class SettingsDialog(QDialog):
    def __init__(self, parent=None, key_name_to_code=None, code_to_key_name=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.parent = parent
        self.key_name_to_code = key_name_to_code
        self.code_to_key_name = code_to_key_name

        # Define wheel_actions and mouse_buttons as instance variables
        self.wheel_actions = ["Wheel Up", "Wheel Down", "No Action"]
        self.mouse_buttons = ["Left Button", "Middle Button", "Right Button", "No Button"]

        self.colors = self.parent.colors.copy()  # Local copy of colors

        self.tab_widget = QTabWidget()
        self.basic_settings_tab = QWidget()
        self.key_config_tab = QWidget()

        self.create_basic_settings_tab()
        self.create_key_config_tab()

        self.tab_widget.addTab(self.basic_settings_tab, self.parent.translations['Basic Settings'])
        self.tab_widget.addTab(self.key_config_tab, self.parent.translations['Key Config'])

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)

        save_button = QPushButton(self.parent.translations['Save'])
        save_button.clicked.connect(self.accept)
        main_layout.addWidget(save_button)

        self.setLayout(main_layout)

    def create_basic_settings_tab(self):
        layout = QGridLayout()
        row = 0

        # Save Name Template
        layout.addWidget(QLabel(self.parent.translations['Save Name Template']), row, 0)
        self.save_name_input = QLineEdit(self.parent.save_name_template)
        layout.addWidget(self.save_name_input, row, 1)
        row += 1

        # Background Color
        layout.addWidget(QLabel(self.parent.translations['Background Color']), row, 0)
        self.bg_color_button = QPushButton(self.parent.background_color.name())
        self.bg_color_button.clicked.connect(self.change_background_color)
        layout.addWidget(self.bg_color_button, row, 1)
        row += 1

        # Canvas Size
        layout.addWidget(QLabel(self.parent.translations['Canvas Size']), row, 0)
        self.canvas_width_input = QLineEdit(str(self.parent.default_canvas_size.width()))
        self.canvas_height_input = QLineEdit(str(self.parent.default_canvas_size.height()))
        canvas_size_layout = QHBoxLayout()
        canvas_size_layout.addWidget(QLabel(self.parent.translations['Width']))
        canvas_size_layout.addWidget(self.canvas_width_input)
        canvas_size_layout.addWidget(QLabel(self.parent.translations['Height']))
        canvas_size_layout.addWidget(self.canvas_height_input)
        layout.addLayout(canvas_size_layout, row, 1)
        row += 1

        # Pen Tablet Support
        layout.addWidget(QLabel(self.parent.translations['Pen Tablet Support']), row, 0)
        self.pen_tablet_checkbox = QComboBox()
        self.pen_tablet_checkbox.addItems([self.parent.translations['Enabled'], self.parent.translations['Disabled']])
        self.pen_tablet_checkbox.setCurrentIndex(0 if self.parent.use_tablet else 1)
        layout.addWidget(self.pen_tablet_checkbox, row, 1)
        row += 1

        # Auto-advance Image on Save
        layout.addWidget(QLabel(self.parent.translations['Auto-advance Image on Save']), row, 0)
        self.auto_advance_checkbox = QComboBox()
        self.auto_advance_checkbox.addItems([self.parent.translations['Enabled'], self.parent.translations['Disabled']])
        self.auto_advance_checkbox.setCurrentIndex(0 if self.parent.auto_advance else 1)
        layout.addWidget(self.auto_advance_checkbox, row, 1)
        row += 1

        # Language Selection
        layout.addWidget(QLabel(self.parent.translations['Language']), row, 0)
        self.language_combo = QComboBox()
        self.load_languages()
        layout.addWidget(self.language_combo, row, 1)
        row += 1

        # Color Settings
        layout.addWidget(QLabel(self.parent.translations['Pen Colors']), row, 0)
        self.colors_list_widget = QListWidget()
        self.colors_list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.update_color_buttons()
        layout.addWidget(self.colors_list_widget, row, 1)
        color_buttons_layout = QHBoxLayout()
        self.add_color_button = QPushButton(self.parent.translations['Add Color'])
        self.add_color_button.clicked.connect(self.add_pen_color)
        color_buttons_layout.addWidget(self.add_color_button)
        self.delete_color_button = QPushButton(self.parent.translations['Delete Selected Color'])
        self.delete_color_button.clicked.connect(self.delete_selected_color)
        color_buttons_layout.addWidget(self.delete_color_button)
        layout.addLayout(color_buttons_layout, row + 1, 1)
        row += 2

        self.basic_settings_tab.setLayout(layout)

    def change_background_color(self):
        color = QColorDialog.getColor(initial=self.parent.background_color, title=self.parent.translations['Select Background Color'])
        if color.isValid():
            self.parent.background_color = color
            self.bg_color_button.setText(color.name())
            self.bg_color_button.setStyleSheet(f"background-color: {color.name()}")

    def change_pen_color(self, color):
        new_color = QColorDialog.getColor(initial=color, title=self.parent.translations['Select Pen Color'])
        if new_color.isValid():
            index = self.colors.index(color)
            self.colors[index] = new_color
            self.update_color_buttons()

    def add_pen_color(self):
        new_color = QColorDialog.getColor(title=self.parent.translations['Select Pen Color'])
        if new_color.isValid():
            self.colors.append(new_color)
            self.update_color_buttons()

    def delete_selected_color(self):
        selected_items = self.colors_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.parent.translations['Warning'], self.parent.translations['No color selected to delete.'])
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
        language_files = [f for f in os.listdir(language_folder) if f.startswith('language_') and f.endswith('.yaml')]
        self.languages = {}
        for file in language_files:
            lang_code = file[len('language_'):-len('.yaml')]
            self.languages[lang_code] = os.path.join(language_folder, file)
            self.language_combo.addItem(lang_code)
        current_language = self.parent.language_code
        index = self.language_combo.findText(current_language)
        if index != -1:
            self.language_combo.setCurrentIndex(index)

    def create_key_config_tab(self):
        layout = QGridLayout()
        self.inputs = {}
        row = 0

        # Shortcut Keys Heading
        layout.addWidget(QLabel(f"<b>{self.parent.translations['Shortcut Keys']}</b>"), row, 0, 1, 2)
        row += 1

        # Key configurations
        key_actions = ["Undo", "Redo", "Clear", "Next Color", "Previous Color", "Save", "Next Image", "Previous Image", "Eraser Tool", "Increase Pen Size", "Decrease Pen Size", "Merged Save"]
        for action in key_actions:
            layout.addWidget(QLabel(self.parent.translations.get(action, action)), row, 0)
            combo = QComboBox()
            combo.addItems(self.key_name_to_code.keys())
            key = self.parent.key_config.get(action, Qt.Key_No)
            key_name = self.code_to_key_name.get(key, "")
            index = combo.findText(key_name)
            if index != -1:
                combo.setCurrentIndex(index)
            layout.addWidget(combo, row, 1)
            self.inputs[action] = ('key', combo)
            row += 1

        # Mouse Settings Heading
        layout.addWidget(QLabel(f"<b>{self.parent.translations['Mouse Settings']}</b>"), row, 0, 1, 2)
        row += 1

        for action in ["Pen Tool", "Eraser Tool", "Increase Pen Size", "Decrease Pen Size"]:
            layout.addWidget(QLabel(self.parent.translations.get(action, action)), row, 0)
            if action in ["Increase Pen Size", "Decrease Pen Size"]:
                combo = QComboBox()
                combo.addItems(self.wheel_actions + list(self.key_name_to_code.keys()))
                button = self.parent.mouse_config.get(action, "No Action")
                if isinstance(button, int):
                    button_name = self.code_to_key_name.get(button, "No Action")
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
                button = self.parent.mouse_config.get(action, Qt.NoButton)
                button_name = self.parent.mouse_button_to_name(button)
                index = combo.findText(button_name)
                if index != -1:
                    combo.setCurrentIndex(index)
                layout.addWidget(combo, row, 1)
                self.inputs[action] = ('mouse', combo)
            row += 1

        self.key_config_tab.setLayout(layout)

    def accept(self):
        # Save Basic Settings
        self.parent.save_name_template = self.save_name_input.text()

        width = int(self.canvas_width_input.text())
        height = int(self.canvas_height_input.text())
        new_size = QSize(width, height)
        if new_size != self.parent.default_canvas_size:
            self.parent.resize_canvas(new_size)

        self.parent.use_tablet = (self.pen_tablet_checkbox.currentIndex() == 0)

        self.parent.auto_advance = (self.auto_advance_checkbox.currentIndex() == 0)

        # Update language
        selected_language = self.language_combo.currentText()
        if selected_language != self.parent.language_code:
            self.parent.language_code = selected_language
            self.parent.load_language()
            self.parent.update_gui_texts()

        # Save colors
        self.parent.colors = self.colors
        self.parent.update_cursor()

        # 背景色を変更した後に画面を更新
        self.parent.update_display()

        # Save Key Configurations
        for action, (input_type, input_widget) in self.inputs.items():
            if input_type == 'key':
                selected_key_name = input_widget.currentText()
                self.parent.key_config[action] = self.key_name_to_code[selected_key_name]
            elif input_type == 'mouse':
                selected = input_widget.currentText()
                self.parent.mouse_config[action] = self.parent.name_to_mouse_button(selected)
            elif input_type == 'input':
                selected = input_widget.currentText()
                if selected in self.wheel_actions:
                    self.parent.mouse_config[action] = selected
                elif selected in self.key_name_to_code:
                    self.parent.mouse_config[action] = self.key_name_to_code[selected]
                else:
                    self.parent.mouse_config[action] = "No Action"

        self.parent.save_settings()
        super().accept()

class PaintApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SketchRush")

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.image_label = QLabel(self.central_widget)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMouseTracking(True)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self.central_widget)
        layout.addWidget(self.image_label)

        self.folder_path = ""
        self.image_files = []
        self.current_image_index = 0
        self.drawing = False
        self.last_point = QPoint()
        self.pen_size = 5
        self.eraser_mode = False
        self.eraser_key_pressed = False  # Initialize the eraser key state

        self.background_color = QColor(Qt.white)
        self.original_pixmap = None
        self.paint_layer = QPixmap()
        self.auto_advance = True  # Auto-advance after saving

        self.undo_stack = []
        self.redo_stack = []

        self.colors = [QColor(Qt.black), QColor(Qt.white), QColor(Qt.blue), QColor(Qt.red), QColor(Qt.yellow), QColor(Qt.green), QColor(Qt.magenta)]
        self.current_color_index = 0

        self.save_folder = ""
        self.save_name_template = "blackline{:03d}.png"

        self.key_config = {
            "Undo": Qt.Key_Z,
            "Redo": Qt.Key_X,
            "Clear": Qt.Key_Delete,
            "Next Color": Qt.Key_C,
            "Previous Color": Qt.Key_V,
            "Save": Qt.Key_Return,
            "Previous Image": Qt.Key_Left,
            "Next Image": Qt.Key_Right,
            "Eraser Tool": Qt.Key_E,
            "Increase Pen Size": Qt.Key_Plus,
            "Decrease Pen Size": Qt.Key_Minus,
            "Merged Save": Qt.Key_S
        }

        self.mouse_config = {
            "Pen Tool": Qt.LeftButton,
            "Eraser Tool": Qt.RightButton,
            "Increase Pen Size": "Wheel Up",
            "Decrease Pen Size": "Wheel Down"
        }

        self.save_counter = 0
        self.default_canvas_size = QSize(512, 512)
        self.use_tablet = True  # Default to using tablet support
        self.language_code = 'EN'  # Default language code

        # Create mappings between key names and key codes
        self.key_name_to_code = {}
        self.code_to_key_name = {}
        key_names = [
            "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
            "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
            "U", "V", "W", "X", "Y", "Z",
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10",
            "F11", "F12",
            "Enter", "Space", "Up", "Down", "Left", "Right",
            "Delete", "Ctrl", "Shift", "Alt", "Esc", "Plus", "Minus"
        ]
        for name in key_names:
            code = getattr(Qt, f'Key_{name}') if hasattr(Qt, f'Key_{name}') else None
            if code is None:
                # Handle special cases
                if name == "Enter":
                    code = Qt.Key_Return
                elif name == "Space":
                    code = Qt.Key_Space
                elif name == "Ctrl":
                    code = Qt.Key_Control
                elif name == "Shift":
                    code = Qt.Key_Shift
                elif name == "Alt":
                    code = Qt.Key_Alt
                elif name == "Esc":
                    code = Qt.Key_Escape
                elif name == "Plus":
                    code = Qt.Key_Plus
                elif name == "Minus":
                    code = Qt.Key_Minus
                else:
                    continue
            self.key_name_to_code[name] = code
            self.code_to_key_name[code] = name

        self.translations = {}
        self.load_settings()
        self.load_language()
        self.create_menu()
        self.resize(self.default_canvas_size)
        self.create_default_image()
        self.update_cursor()

    def load_language(self):
        language_folder = os.path.join(os.getcwd(), 'language')
        language_file = os.path.join(language_folder, f'language_{self.language_code}.yaml')
        try:
            with open(language_file, 'r', encoding='utf-8') as f:
                self.translations = yaml.safe_load(f)
        except Exception as e:
            print(f"Could not load language file: {e}")
            self.translations = {}
        # Set default translations if missing
        default_translations = {
            'Settings': 'Settings',
            'Basic Settings': 'Basic Settings',
            'Key Config': 'Key Config',
            'Save': 'Save',
            'Save Name Template': 'Save Name Template',
            'Background Color': 'Background Color',
            'Canvas Size': 'Canvas Size',
            'Width': 'Width',
            'Height': 'Height',
            'Pen Tablet Support': 'Pen Tablet Support',
            'Enabled': 'Enabled',
            'Disabled': 'Disabled',
            'Language': 'Language',
            'Add Color': 'Add Color',
            'Delete Selected Color': 'Delete Selected Color',  # Added
            'Select Background Color': 'Select Background Color',
            'Select Pen Color': 'Select Pen Color',
            'Shortcut Keys': 'Shortcut Keys',
            'Undo': 'Undo',
            'Redo': 'Redo',
            'Clear': 'Clear',
            'Next Color': 'Next Color',
            'Previous Color': 'Previous Color',
            'Save': 'Save',
            'Next Image': 'Next Image',
            'Previous Image': 'Previous Image',
            'Eraser Tool': 'Eraser Tool',
            'Increase Pen Size': 'Increase Pen Size',
            'Decrease Pen Size': 'Decrease Pen Size',
            'Merged Save': 'Merged Save',  # Added
            'Mouse Settings': 'Mouse Settings',
            'Pen Tool': 'Pen Tool',
            'Pen Colors': 'Pen Colors',
            'File': 'File',
            'Load Folder': 'Load Folder',
            'Change Save Folder': 'Change Save Folder',
            'Auto-advance Image on Save': 'Auto-advance Image on Save',  # Added
            'Warning': 'Warning',  # Added
            'No color selected to delete.': 'No color selected to delete.',  # Added
            'Select Save Folder': 'Select Save Folder',  # Added
            # Add any other missing translations here
        }
        for key, value in default_translations.items():
            if key not in self.translations:
                self.translations[key] = value

    def update_gui_texts(self):
        # Update menu texts
        self.file_menu.setTitle(self.translations['File'])
        self.load_folder_action.setText(self.translations['Load Folder'])
        self.change_save_folder_action.setText(self.translations['Change Save Folder'])
        self.settings_menu.setTitle(self.translations['Settings'])
        self.settings_action.setText(self.translations['Settings'])

    def mouse_button_to_name(self, button):
        if button == Qt.LeftButton:
            return "Left Button"
        elif button == Qt.MiddleButton:
            return "Middle Button"
        elif button == Qt.RightButton:
            return "Right Button"
        else:
            return "No Button"

    def create_menu(self):
        menubar = self.menuBar()
        self.file_menu = menubar.addMenu(self.translations['File'])

        self.load_folder_action = QAction(self.translations['Load Folder'], self)
        self.load_folder_action.triggered.connect(self.select_folder)
        self.file_menu.addAction(self.load_folder_action)

        self.change_save_folder_action = QAction(self.translations['Change Save Folder'], self)
        self.change_save_folder_action.triggered.connect(self.change_save_folder)
        self.file_menu.addAction(self.change_save_folder_action)

        self.settings_menu = menubar.addMenu(self.translations['Settings'])

        self.settings_action = QAction(self.translations['Settings'], self)
        self.settings_action.triggered.connect(self.open_settings)
        self.settings_menu.addAction(self.settings_action)

    def open_settings(self):
        dialog = SettingsDialog(self, self.key_name_to_code, self.code_to_key_name)
        if dialog.exec_():
            self.update_cursor()
            self.update_gui_texts()
            self.save_settings()

    def resize_canvas(self, new_size):
        self.default_canvas_size = new_size
        if self.original_pixmap:
            self.original_pixmap = self.original_pixmap.scaled(new_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        else:
            self.create_default_image()
        new_paint_layer = QPixmap(new_size)
        new_paint_layer.fill(Qt.transparent)
        painter = QPainter(new_paint_layer)
        # self.paint_layer が QPixmap であることを確認
        if isinstance(self.paint_layer, QImage):
            self.paint_layer = QPixmap.fromImage(self.paint_layer)
        painter.drawPixmap(0, 0, self.paint_layer)
        painter.end()
        self.paint_layer = new_paint_layer
        self.update_display()
        self.resize(new_size)

    def toggle_tablet_support(self, state):
        self.use_tablet = state
        if self.use_tablet:
            print("Pen Tablet Support Enabled")
        else:
            print("Pen Tablet Support Disabled")

    def change_canvas_size(self):
        width, ok1 = QInputDialog.getInt(self, "Canvas Width", "Enter canvas width:", value=self.default_canvas_size.width(), min=1)
        if ok1:
            height, ok2 = QInputDialog.getInt(self, "Canvas Height", "Enter canvas height:", value=self.default_canvas_size.height(), min=1)
            if ok2:
                self.default_canvas_size = QSize(width, height)
                self.create_default_image()
                self.resize(self.default_canvas_size)
                self.save_settings()

    def change_background_color(self):
        color = QColorDialog.getColor(initial=self.background_color, title="Select Background Color")
        if color.isValid():
            self.background_color = color
            if not self.original_pixmap:
                self.create_default_image()
            else:
                self.original_pixmap.fill(self.background_color)
                self.update_display()
            self.save_settings()

    def name_to_mouse_button(self, name):
        if name == "Left Button":
            return Qt.LeftButton
        elif name == "Middle Button":
            return Qt.MiddleButton
        elif name == "Right Button":
            return Qt.RightButton
        else:
            return Qt.NoButton

    # Update the open_key_config method
    def open_key_config(self):
        dialog = KeyConfigDialog(self, self.key_name_to_code, self.code_to_key_name)
        if dialog.exec_():
            for action, (input_type, input_widget) in dialog.inputs.items():
                if input_type == 'key':
                    selected_key_name = input_widget.currentText()
                    self.key_config[action] = self.key_name_to_code[selected_key_name]
                elif input_type == 'mouse':
                    selected = input_widget.currentText()
                    self.mouse_config[action] = self.name_to_mouse_button(selected)
                elif input_type == 'wheel':
                    selected = input_widget.currentText()
                    self.mouse_config[action] = selected
            self.save_settings()

    def change_save_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.translations['Change Save Folder'])
        if folder:
            self.save_folder = folder
            self.save_settings()

    def change_save_name(self):
        name, ok = QInputDialog.getText(self, 'Change Save Name Template',
                                        'Enter new name template (use {:03d} for number):',
                                        text=self.save_name_template)
        if ok:
            self.save_name_template = name
            self.save_settings()

    def select_folder(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if self.folder_path:
            self.image_files = [f for f in os.listdir(self.folder_path) if f.lower().endswith(
                ('.png', '.jpg', '.webp', '.gif', '.bmp', '.jpeg'))]
            if self.image_files:
                self.load_image(0)
            else:
                print("No compatible images found in the selected folder.")

    def load_image(self, index):
        if 0 <= index < len(self.image_files):
            image_path = os.path.join(self.folder_path, self.image_files[index])
            self.original_pixmap = QPixmap(image_path)
            self.paint_layer = QImage(self.original_pixmap.size(), QImage.Format_ARGB32_Premultiplied)
            self.paint_layer.fill(Qt.transparent)
            self.current_image_index = index
            self.update_cursor()
            self.undo_stack.clear()
            self.redo_stack.clear()
            QTimer.singleShot(0, self.update_display)

    def update_display(self):
        if self.original_pixmap:
            display_pixmap = QPixmap(self.original_pixmap)
        else:
            display_pixmap = QPixmap(self.default_canvas_size)
            display_pixmap.fill(self.background_color)
        painter = QPainter(display_pixmap)
        # self.paint_layer が QPixmap であることを確認
        if isinstance(self.paint_layer, QImage):
            self.paint_layer = QPixmap.fromImage(self.paint_layer)
        painter.drawPixmap(0, 0, self.paint_layer)
        painter.end()
        self.image_label.setPixmap(display_pixmap)

    def create_default_image(self):
        self.original_pixmap = None
        self.paint_layer = QPixmap(self.default_canvas_size)
        self.paint_layer.fill(Qt.transparent)
        self.update_display()

    def get_image_coordinates(self, global_pos):
        local_pos = self.image_label.mapFromGlobal(global_pos)
        pixmap = self.original_pixmap if self.original_pixmap else QPixmap(self.default_canvas_size)
        if (pixmap.width() / pixmap.height()) > (self.image_label.width() / self.image_label.height()):
            # 画像がラベルより横長の場合
            scaled_width = self.image_label.width()
            scaled_height = pixmap.height() * scaled_width / pixmap.width()
            offset = (self.image_label.height() - scaled_height) / 2
            x = local_pos.x() * pixmap.width() / self.image_label.width()
            y = (local_pos.y() - offset) * pixmap.height() / scaled_height
        else:
            # 画像がラベルより縦長の場合
            scaled_height = self.image_label.height()
            scaled_width = pixmap.width() * scaled_height / pixmap.height()
            offset = (self.image_label.width() - scaled_width) / 2
            x = (local_pos.x() - offset) * pixmap.width() / scaled_width
            y = local_pos.y() * pixmap.height() / self.image_label.height()
        return QPoint(int(x), int(y))

    # def get_image_coordinates(self, pos):
    #     # Map from the main window coordinates to image_label coordinates
    #     label_pos = self.image_label.mapFromGlobal(pos)

    #     pixmap = self.image_label.pixmap()
    #     if not pixmap:
    #         return QPoint(-1, -1)

    #     # Get the size of the displayed pixmap
    #     pixmap_size = pixmap.size()

    #     # Get the size of the image_label
    #     label_size = self.image_label.size()

    #     # Calculate the scale factor and offsets
    #     if (self.original_pixmap.width() / self.original_pixmap.height()) > (
    #             label_size.width() / label_size.height()):
    #         # Image is wider than the label
    #         scale = label_size.width() / self.original_pixmap.width()
    #         scaled_height = self.original_pixmap.height() * scale
    #         offset_x = 0
    #         offset_y = (label_size.height() - scaled_height) / 2
    #     else:
    #         # Image is taller than the label
    #         scale = label_size.height() / self.original_pixmap.height()
    #         scaled_width = self.original_pixmap.width() * scale
    #         offset_x = (label_size.width() - scaled_width) / 2
    #         offset_y = 0

    #     # Adjust label_pos to remove the offset
    #     x = label_pos.x() - offset_x
    #     y = label_pos.y() - offset_y

    #     if x < 0 or y < 0 or x > pixmap_size.width() or y > pixmap_size.height():
    #         return QPoint(-1, -1)

    #     # Map the x, y to image coordinates
    #     image_x = x / scale
    #     image_y = y / scale

    #     return QPoint(int(image_x), int(image_y))

    def mousePressEvent(self, event):
        if self.use_tablet:
            event.ignore()
            return
        pos = self.get_image_coordinates(event.globalPos())
        if pos.x() >= 0 and pos.y() >= 0:
            button = event.button()
            if button == self.mouse_config.get("Pen Tool", Qt.LeftButton):
                self.drawing = True
                self.last_point = pos
                self.undo_stack.append(self.paint_layer.copy())
                self.redo_stack.clear()
                if len(self.undo_stack) > 10:
                    self.undo_stack.pop(0)
                self.draw_point(pos)
            elif button == self.mouse_config.get("Eraser Tool", Qt.RightButton):
                self.eraser_mode = True
                self.update_cursor()

    def mouseMoveEvent(self, event):
        if self.use_tablet:
            event.ignore()
            return
        pos = self.get_image_coordinates(event.globalPos())
        if self.drawing and pos.x() >= 0 and pos.y() >= 0:
            self.draw_line(self.last_point, pos)
            self.last_point = pos

    def mouseReleaseEvent(self, event):
        if self.use_tablet:
            event.ignore()
            return
        button = event.button()
        if button == self.mouse_config.get("Pen Tool", Qt.LeftButton):
            self.drawing = False
        elif button == self.mouse_config.get("Eraser Tool", Qt.RightButton):
            self.eraser_mode = False
            self.update_cursor()

    # Modify tabletEvent to handle eraser key
    def tabletEvent(self, event):
        if not self.use_tablet:
            event.ignore()
            return
        pos = event.pos()
        img_pos = self.get_image_coordinates(self.mapToGlobal(pos))
        pressure = event.pressure()
        pressure_pen_size = max(1, self.pen_size * pressure)
        if event.pointerType() == QTabletEvent.Eraser or self.eraser_key_pressed:
            self.eraser_mode = True
        else:
            self.eraser_mode = False

        if event.type() == QEvent.TabletPress:
            self.drawing = True
            self.last_point = img_pos
            self.undo_stack.append(self.paint_layer.copy())
            self.redo_stack.clear()
            if len(self.undo_stack) > 10:
                self.undo_stack.pop(0)
            self.draw_point(img_pos, pressure_pen_size)
            event.accept()
        elif event.type() == QEvent.TabletMove and self.drawing:
            self.draw_line(self.last_point, img_pos, pressure_pen_size)
            self.last_point = img_pos
            event.accept()
        elif event.type() == QEvent.TabletRelease:
            self.drawing = False
            event.accept()
        else:
            event.ignore()

    def draw_point(self, point, pen_size=None):
        if not self.paint_layer:
            return
        if pen_size is None:
            pen_size = self.pen_size
        painter = QPainter(self.paint_layer)
        painter.setPen(QPen(self.colors[self.current_color_index], pen_size, Qt.SolidLine, Qt.RoundCap,
                            Qt.RoundJoin))
        if self.eraser_mode:
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.drawPoint(point)
        painter.end()
        self.update_display()

    def draw_line(self, start, end, pen_size=None):
        if not self.paint_layer:
            return
        if pen_size is None:
            pen_size = self.pen_size
        painter = QPainter(self.paint_layer)
        painter.setPen(QPen(self.colors[self.current_color_index], pen_size, Qt.SolidLine, Qt.RoundCap,
                            Qt.RoundJoin))
        if self.eraser_mode:
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.drawLine(start, end)
        painter.end()
        self.update_display()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            direction = "Wheel Up"
            action = "Pen Size Increase"
        else:
            direction = "Wheel Down"
            action = "Pen Size Decrease"
        if self.mouse_config.get(action) == direction:
            if delta > 0:
                self.pen_size = max(1, min(50, self.pen_size + 1))
            else:
                self.pen_size = max(1, min(50, self.pen_size - 1))
            self.update_cursor()

    def keyPressEvent(self, event):
        key = event.key()
        if key == self.key_config["Undo"]:
            self.undo()
        elif key == self.key_config["Redo"]:
            self.redo()
        elif key == self.key_config["Clear"]:
            self.clear_paint_layer()
        elif key == self.key_config["Next Color"]:
            self.change_color(1)
        elif key == self.key_config["Previous Color"]:
            self.change_color(-1)
        elif key == self.key_config["Save"]:
            self.save_image()
        elif key == self.key_config["Previous Image"]:
            self.change_image(-1)
        elif key == self.key_config["Next Image"]:
            self.change_image(1)
        elif key == self.key_config.get("Merged Save"):
            self.save_merged_image()
        elif key == self.mouse_config.get("Eraser Tool"):
            self.eraser_key_pressed = True
            self.update_cursor()
        elif key == self.key_config.get("Increase Pen Size"):
            self.change_pen_size(1)
        elif key == self.key_config.get("Decrease Pen Size"):
            self.change_pen_size(-1)

    def keyReleaseEvent(self, event):
        key = event.key()
        if key == self.mouse_config.get("Eraser Tool"):
            self.eraser_key_pressed = False
            self.update_cursor()

    def change_image(self, direction):
        if self.image_files:
            new_index = (self.current_image_index + direction) % len(self.image_files)
            self.load_image(new_index)

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.paint_layer.copy())
            self.paint_layer = self.undo_stack.pop()
            self.update_display()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.paint_layer.copy())
            self.paint_layer = self.redo_stack.pop()
            self.update_display()

    def clear_paint_layer(self):
        self.undo_stack.append(self.paint_layer.copy())
        self.paint_layer.fill(Qt.transparent)
        self.update_display()

    def change_color(self, direction):
        self.current_color_index = (self.current_color_index + direction) % len(self.colors)
        self.update_cursor()

    def create_cursor(self):
        if self.pen_size < 10:
            return QCursor(Qt.CrossCursor)

        cursor_size = self.pen_size
        cursor_pixmap = QPixmap(QSize(cursor_size, cursor_size))
        cursor_pixmap.fill(Qt.transparent)

        painter = QPainter(cursor_pixmap)
        painter.setPen(QPen(self.colors[self.current_color_index], 1, Qt.SolidLine))
        painter.drawEllipse(0, 0, cursor_size - 1, cursor_size - 1)
        painter.end()

        return QCursor(cursor_pixmap)

    def update_cursor(self):
        cursor = self.create_cursor()
        self.setCursor(cursor)

    def save_image(self):
        if self.paint_layer:
            save_folder = self.save_folder if self.save_folder else self.folder_path
            if not save_folder:
                save_folder = QFileDialog.getExistingDirectory(self, self.translations["Select Save Folder"])
                if not save_folder:
                    return  # User canceled
                self.save_folder = save_folder

            base_filename = self.save_name_template.format(self.save_counter)
            save_path = self.get_unique_filename(save_folder, base_filename)
            self.paint_layer.save(save_path, "PNG")
            print(f"Image saved as {save_path}")

            self.save_counter += 1  # Increment save counter
            self.save_settings()

            # Clear the painted content only if auto_advance is OFF
            if not self.auto_advance:
                self.paint_layer.fill(Qt.transparent)
                self.update_display()
                # Reset undo/redo stacks
                self.undo_stack.clear()
                self.redo_stack.clear()

            if self.auto_advance and self.image_files:
                # Load the next image after a short delay
                QTimer.singleShot(100, self.load_next_image)
        else:
            print("No paint layer to save.")

    def save_merged_image(self):
        if self.paint_layer:
            save_folder = self.save_folder if self.save_folder else self.folder_path
            if not save_folder:
                save_folder = QFileDialog.getExistingDirectory(self, self.translations["Select Save Folder"])
                if not save_folder:
                    return  # ユーザーがキャンセル
                self.save_folder = save_folder

            base_filename = self.save_name_template.format(self.save_counter)
            save_path = self.get_unique_filename(save_folder, base_filename)

            # レイヤーをマージ
            merged_image = QPixmap(self.paint_layer.size())
            painter = QPainter(merged_image)
            if self.original_pixmap:
                # original_pixmap が QPixmap であることを確認
                if isinstance(self.original_pixmap, QImage):
                    self.original_pixmap = QPixmap.fromImage(self.original_pixmap)
                painter.drawPixmap(0, 0, self.original_pixmap)
            else:
                painter.fillRect(merged_image.rect(), self.background_color)

            # self.paint_layer が QPixmap であることを確認
            if isinstance(self.paint_layer, QImage):
                self.paint_layer = QPixmap.fromImage(self.paint_layer)
            painter.drawPixmap(0, 0, self.paint_layer)

            painter.end()

            merged_image.save(save_path, "PNG")
            print(f"Merged image saved as {save_path}")

            self.save_counter += 1  # 保存カウンタをインクリメント
            self.save_settings()
        else:
            print("No paint layer to save.")

    def get_unique_filename(self, folder, base_filename):
        name, ext = os.path.splitext(base_filename)
        counter = 0
        while True:
            if counter == 0:
                filename = f"{name}{ext}"
            else:
                filename = f"{name}_{counter}{ext}"

            full_path = os.path.join(folder, filename)
            if not os.path.exists(full_path):
                return full_path
            counter += 1

    def load_next_image(self):
        if self.image_files:
            next_index = (self.current_image_index + 1) % len(self.image_files)
            self.load_image(next_index)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.original_pixmap:
            self.update_display()
        else:
            self.create_default_image()

    def showEvent(self, event):
        super().showEvent(event)
        if self.original_pixmap:
            self.update_display()
        else:
            self.create_default_image()

    def load_settings(self):
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            if not config:
                config = {}
            if 'key_config' in config:
                self.key_config.update({k: self.key_name_to_code.get(v, v) for k, v in config['key_config'].items()})
            if 'mouse_config' in config:
                for k, v in config['mouse_config'].items():
                    if k in ["Pen Tool", "Eraser Tool"]:
                        self.mouse_config[k] = self.name_to_mouse_button(v)
                    elif k in ["Increase Pen Size", "Decrease Pen Size"]:
                        if v in ["Wheel Up", "Wheel Down", "No Action"]:
                            self.mouse_config[k] = v
                        else:
                            self.mouse_config[k] = self.key_name_to_code.get(v, v)
                    else:
                        self.mouse_config[k] = v
            if 'save_name_template' in config:
                self.save_name_template = config['save_name_template']
            if 'save_folder' in config:
                self.save_folder = config['save_folder']
            if 'background_color' in config:
                color = QColor(config['background_color'])
                if color.isValid():
                    self.background_color = color
            if 'canvas_size' in config:
                self.default_canvas_size = QSize(*config['canvas_size'])
            else:
                self.default_canvas_size = QSize(512, 512)
            if 'save_counter' in config:
                self.save_counter = config['save_counter']
            else:
                self.save_counter = 0
            if 'use_tablet' in config:
                self.use_tablet = config['use_tablet']
            else:
                self.use_tablet = True  # Default value
            if 'language_code' in config:
                self.language_code = config['language_code']
            else:
                self.language_code = 'EN'
            if 'colors' in config:
                self.colors = [QColor(name) for name in config['colors']]
            if 'auto_advance' in config:
                self.auto_advance = config['auto_advance']
            else:
                self.auto_advance = True
        except Exception as e:
            print(f"Could not load settings: {e}")
            self.default_canvas_size = QSize(512, 512)
            self.save_counter = 0
            self.use_tablet = True
            self.language_code = 'EN'
            self.auto_advance = True

    def save_settings(self):
        key_config_serialized = {k: self.code_to_key_name.get(v, v) for k, v in self.key_config.items()}
        mouse_config_serialized = {}
        for k, v in self.mouse_config.items():
            if isinstance(v, int):  # Mouse button
                mouse_config_serialized[k] = self.mouse_button_to_name(v)
            else:  # Wheel action or key
                if isinstance(v, str):
                    mouse_config_serialized[k] = v
                else:
                    mouse_config_serialized[k] = self.code_to_key_name.get(v, "No Action")
        config = {
            'key_config': key_config_serialized,
            'mouse_config': mouse_config_serialized,
            'save_name_template': self.save_name_template,
            'save_folder': self.save_folder,
            'background_color': self.background_color.name(),
            'canvas_size': (self.default_canvas_size.width(), self.default_canvas_size.height()),
            'save_counter': self.save_counter,
            'use_tablet': self.use_tablet,
            'language_code': self.language_code,
            'colors': [color.name() for color in self.colors],
            'auto_advance': self.auto_advance
        }
        with open('config.yaml', 'w') as f:
            yaml.safe_dump(config, f)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    paint_app = PaintApp()
    paint_app.show()
    sys.exit(app.exec_())
