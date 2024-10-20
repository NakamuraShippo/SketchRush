from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSizePolicy, QAction, QFileDialog, QMessageBox
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtCore import QSize, Qt
from drawing_area import DrawingArea
from settings_manager import SettingsManager
from settings_dialog import SettingsDialog
from path_tool_settings_window import PathToolSettingsWindow
import os
import yaml


class PaintApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SketchRush")
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.translations = {}
        self.folder_path = ""
        self.image_files = []
        self.current_image_index = 0

        self.pen_size = 5
        self.current_color_index = 0
        self.save_folder = ""
        self.save_name_template = "blackline{:03d}.png"
        self.save_counter = 0
        self.save_mode = 1  # デフォルトは 1: ペンツールのみセーブ
        self.default_canvas_size = QSize(512, 512)
        self.use_tablet = True
        self.language_code = 'EN'
        self.auto_advance = True
        self.colors = [QColor(Qt.black), QColor(Qt.white), QColor(Qt.blue), QColor(Qt.red), QColor(Qt.yellow),
                       QColor(Qt.green), QColor(Qt.magenta)]
        self.background_color = QColor(Qt.white)

        self.path_tool_settings_window = None

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
            "Merged Save": Qt.Key_S,
            "Toggle Tool": Qt.Key_Tab,
            "Toggle Fill": Qt.Key_F,
            "Add Control Point Modifier": Qt.ControlModifier,
            "Delete Control Point Modifier": Qt.AltModifier,
            "Toggle Path Mode": Qt.Key_Q  # <-- 追加
        }

        self.mouse_config = {
            "Pen Tool": Qt.LeftButton,
            "Eraser Tool": Qt.RightButton,
            "Increase Pen Size": "Wheel Up",
            "Decrease Pen Size": "Wheel Down"
        }

        self.key_name_to_code = {}
        self.code_to_key_name = {}
        self.create_key_mappings()

        # パスツールのデフォルト設定を DrawingArea の初期化前に設定
        self.default_simplify_tolerance = 1
        self.default_smooth_strength = 1
        self.path_hit_threshold = 2.0

        # 手ブレ補正の度合いを初期化
        self.stabilization_degree = 0

        # Deleteモードのデフォルト設定
        self.delete_mode = 'Delete Current Tool'  # または 'Delete All'

        # DrawingArea の初期化
        self.drawing_area = DrawingArea(self)
        self.drawing_area.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout = QVBoxLayout(self.central_widget)
        layout.addWidget(self.drawing_area)

        self.settings_manager = SettingsManager(self)
        self.load_language()

        self.create_menu()
        self.resize(self.default_canvas_size)
        self.create_default_image()
        self.update_cursor()

        # 設定の読み込み
        self.settings_manager.load_settings()

        # 手ブレ補正の度合いを適用
        self.drawing_area.set_stabilization_degree(self.stabilization_degree)

    def update_background_color(self):
        if not self.drawing_area.original_pixmap:
            self.drawing_area.background_color = self.background_color
            self.drawing_area.update()

    def create_key_mappings(self):
        key_names = [
            "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
            "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
            "U", "V", "W", "X", "Y", "Z",
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10",
            "F11", "F12",
            "Enter", "Space", "Up", "Down", "Left", "Right",
            "Delete", "Ctrl", "Shift", "Alt", "Esc", "Plus", "Minus", "Tab",
            "Meta", "No Modifier"
        ]
        for name in key_names:
            code = getattr(Qt, f'Key_{name}', None)
            if code is None:
                special_keys = {
                    "Enter": Qt.Key_Return,
                    "Space": Qt.Key_Space,
                    "Ctrl": Qt.Key_Control,
                    "Shift": Qt.Key_Shift,
                    "Alt": Qt.Key_Alt,
                    "Esc": Qt.Key_Escape,
                    "Plus": Qt.Key_Plus,
                    "Minus": Qt.Key_Minus,
                    "Tab": Qt.Key_Tab
                }
                code = special_keys.get(name)
            if code:
                self.key_name_to_code[name] = code
                self.code_to_key_name[code] = name

        # 修飾キーの追加
        modifier_names = ["Ctrl", "Alt", "Shift", "Meta", "No Modifier"]
        modifier_codes = [Qt.ControlModifier, Qt.AltModifier, Qt.ShiftModifier, Qt.MetaModifier, Qt.NoModifier]

        for name, code in zip(modifier_names, modifier_codes):
            self.key_name_to_code[name] = code
            self.code_to_key_name[code] = name

    def load_language(self):
        language_folder = os.path.join(os.getcwd(), 'language')
        if not os.path.exists(language_folder):
            os.makedirs(language_folder)
        language_file = os.path.join(language_folder, f'language_{self.language_code}.yaml')
        try:
            with open(language_file, 'r', encoding='utf-8') as f:
                self.translations = yaml.safe_load(f)
        except Exception as e:
            print(f"Could not load language file: {e}")
            self.translations = {}
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
            'Delete Selected Color': 'Delete Selected Color',
            'Select Background Color': 'Select Background Color',
            'Select Pen Color': 'Select Pen Color',
            'Shortcut Keys': 'Shortcut Keys',
            'Undo': 'Undo',
            'Redo': 'Redo',
            'Clear': 'Clear',
            'Next Color': 'Next Color',
            'Previous Color': 'Previous Color',
            'Next Image': 'Next Image',
            'Previous Image': 'Previous Image',
            'Eraser Tool': 'Eraser Tool',
            'Increase Pen Size': 'Increase Pen Size',
            'Decrease Pen Size': 'Decrease Pen Size',
            'Merged Save': 'Merged Save',
            'Toggle Tool': 'Toggle Tool',
            'Mouse Settings': 'Mouse Settings',
            'Pen Tool': 'Pen Tool',
            'Pen Colors': 'Pen Colors',
            'File': 'File',
            'Load Folder': 'Load Folder',
            'Change Save Folder': 'Change Save Folder',
            'Auto-advance Image on Save': 'Auto-advance Image on Save',
            'Warning': 'Warning',
            'No color selected to delete.': 'No color selected to delete.',
            'Select Save Folder': 'Select Save Folder',
            'Stabilization Degree': 'Stabilization Degree',
            'Default Simplification Tolerance': 'Default Simplification Tolerance',
            'Default Smoothing Strength': 'Default Smoothing Strength',
            'Path Hit Detection Threshold': 'Path Hit Detection Threshold',
            'Path Tool Settings': 'Path Tool Settings',  # 多言語対応のラベル
            'Modifier Keys': 'Modifier Keys',
            'Add Control Point Modifier': 'Add Control Point Modifier',
            'Delete Control Point Modifier': 'Delete Control Point Modifier',
            'Toggle Fill': 'Toggle Fill',
            'No Modifier': 'No Modifier',
            'Ctrl': 'Ctrl',
            'Alt': 'Alt',
            'Shift': 'Shift',
            'Meta': 'Meta',
            'Pen Tool Only': 'Pen Tool Only',
            'Path Tool Only': 'Path Tool Only',
            'Pen and Path Tools Combined': 'Pen and Path Tools Combined',
            'Save Mode': 'Save Mode',
            'Delete Mode': 'Delete Mode',
            'Delete Current Tool': 'Delete Current Tool',
            'Delete All': 'Delete All',
        }
        for key, value in default_translations.items():
            if key not in self.translations:
                self.translations[key] = value

    def update_gui_texts(self):
        self.file_menu.setTitle(self.translations['File'])
        self.load_folder_action.setText(self.translations['Load Folder'])
        self.change_save_folder_action.setText(self.translations['Change Save Folder'])
        self.settings_action.setText(self.translations['Settings'])

    def create_menu(self):
        menubar = self.menuBar()
        self.file_menu = menubar.addMenu(self.translations['File'])

        self.load_folder_action = QAction(self.translations['Load Folder'], self)
        self.load_folder_action.triggered.connect(self.select_folder)
        self.file_menu.addAction(self.load_folder_action)

        self.change_save_folder_action = QAction(self.translations['Change Save Folder'], self)
        self.change_save_folder_action.triggered.connect(self.change_save_folder)
        self.file_menu.addAction(self.change_save_folder_action)

        self.settings_action = QAction(self.translations['Settings'], self)
        self.settings_action.triggered.connect(self.open_settings)
        menubar.addAction(self.settings_action)

    def open_settings(self):
        dialog = SettingsDialog(self, self.key_name_to_code, self.code_to_key_name)
        if dialog.exec_():
            self.update_cursor()
            self.update_gui_texts()
            self.settings_manager.save_settings()
            self.drawing_area.undo_stack.clear()
            self.drawing_area.redo_stack.clear()

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
            self.drawing_area.set_image(QPixmap(image_path))
            self.current_image_index = index
            self.drawing_area.undo_stack.clear()
            self.drawing_area.redo_stack.clear()

    def create_default_image(self):
        self.drawing_area.create_default_image(self.default_canvas_size)

    def update_cursor(self):
        self.drawing_area.update_cursor()

    def change_save_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.translations['Select Save Folder'])
        if folder:
            self.save_folder = folder
            self.settings_manager.save_settings()

    def get_unique_filename(self, folder, base_filename):
        name, ext = os.path.splitext(base_filename)
        counter = 0
        while True:
            filename = f"{name}_{counter}{ext}" if counter > 0 else f"{name}{ext}"
            full_path = os.path.join(folder, filename)
            if not os.path.exists(full_path):
                return full_path
            counter += 1

    def save_image(self):
        save_folder = self.save_folder if self.save_folder else self.folder_path
        if not save_folder:
            save_folder = QFileDialog.getExistingDirectory(self, self.translations["Select Save Folder"])
            if not save_folder:
                return
            self.save_folder = save_folder

        base_filename = self.save_name_template.format(self.save_counter)
        # ファイル拡張子を決定
        if self.save_mode == 2:
            ext = ".svg"
        else:
            ext = ".png"
        save_path = self.get_unique_filename(save_folder, base_filename + ext)

        if self.save_mode == 1:
            # ペンツールのみセーブ（ラスターレイヤー）
            if not self.drawing_area.raster_layer.isNull():
                self.drawing_area.raster_layer.save(save_path, "PNG")
                print(f"Pen tool layer saved as {save_path}")
            else:
                print("No raster layer to save.")

        elif self.save_mode == 2:
            # パスツールのみセーブ（SVG形式）
            if self.drawing_area.spline_manager.paths:
                self.save_paths_as_svg(save_path)
                print(f"Path tool layer saved as {save_path}")
            else:
                print("No paths to save.")
        elif self.save_mode == 3:
            # ペンツールとパスツールのレイヤーを結合して保存
            if not self.drawing_area.raster_layer.isNull():
                merged_image = QPixmap(self.drawing_area.raster_layer.size())
                merged_image.fill(Qt.transparent)
                painter = QPainter(merged_image)
                if self.drawing_area.original_pixmap:
                    painter.drawPixmap(0, 0, self.drawing_area.original_pixmap)
                else:
                    painter.fillRect(merged_image.rect(), self.background_color)
                painter.drawPixmap(0, 0, self.drawing_area.raster_layer)
                painter.drawPixmap(0, 0, self.drawing_area.vector_layer)
                painter.end()
                merged_image.save(save_path, "PNG")
                print(f"Merged image saved as {save_path}")
            else:
                print("No raster layer to save.")
        else:
            print("Invalid save mode.")

        self.save_counter += 1
        self.settings_manager.save_settings()

    def save_paths_as_svg(self, save_path):
        from xml.etree.ElementTree import Element, SubElement, ElementTree
        svg = Element('svg', xmlns="http://www.w3.org/2000/svg")
        width = str(self.drawing_area.vector_layer.width())
        height = str(self.drawing_area.vector_layer.height())
        svg.set('width', width)
        svg.set('height', height)
        svg.set('viewBox', f"0 0 {width} {height}")

        for path in self.drawing_area.spline_manager.paths:
            path_element = SubElement(svg, 'path')
            d = path.path_to_svg_d()
            path_element.set('d', d)
            path_element.set('fill', 'none' if not path.fill_enabled else path.fill_color.name())
            path_element.set('stroke', path.pen_color.name())
            path_element.set('stroke-width', str(path.pen_width))

        tree = ElementTree(svg)
        tree.write(save_path)

    def save_merged_image(self):
        if not self.drawing_area.raster_layer.isNull():
            save_folder = self.save_folder if self.save_folder else self.folder_path
            if not save_folder:
                save_folder = QFileDialog.getExistingDirectory(self, self.translations["Select Save Folder"])
                if not save_folder:
                    return
                self.save_folder = save_folder

            base_filename = self.save_name_template.format(self.save_counter)
            save_path = self.get_unique_filename(save_folder, base_filename)

            # ラスターレイヤーとベクターレイヤーを統合して保存
            merged_image = QPixmap(self.drawing_area.raster_layer.size())
            merged_image.fill(Qt.transparent)
            painter = QPainter(merged_image)
            if self.drawing_area.original_pixmap:
                painter.drawPixmap(0, 0, self.drawing_area.original_pixmap)
            else:
                painter.fillRect(merged_image.rect(), self.background_color)
            painter.drawPixmap(0, 0, self.drawing_area.raster_layer)
            # ベクターレイヤーを描画
            painter.drawPixmap(0, 0, self.drawing_area.vector_layer)
            painter.end()

            merged_image.save(save_path, "PNG")
            print(f"Merged image saved as {save_path}")

            self.save_counter += 1
            self.settings_manager.save_settings()
        else:
            print("No raster layer to save.")

    def load_next_image(self):
        if self.image_files:
            next_index = (self.current_image_index + 1) % len(self.image_files)
            self.load_image(next_index)

    def undo(self):
        self.drawing_area.undo()

    def redo(self):
        self.drawing_area.redo()

    def keyPressEvent(self, event):
        key = event.key()
        toggle_tool_key = self.key_config.get("Toggle Tool", Qt.Key_Tab)
        if key == toggle_tool_key:
            # モード切替
            if self.drawing_area.mode == 'draw':
                self.drawing_area.mode = 'spline'
                self.drawing_area.current_layer = self.drawing_area.vector_layer
                print("Mode switched to spline")
            else:
                self.drawing_area.mode = 'draw'
                self.drawing_area.current_layer = self.drawing_area.raster_layer
                print("Mode switched to draw")
            return

        if key == self.key_config.get("Save"):
            # Save キーで save_image を呼び出す
            self.save_image()
            return
        elif key == self.key_config.get("Merged Save"):
            # Merged Save キーで save_image を呼び出す（save_mode を一時的に 3 に設定）
            original_save_mode = self.save_mode
            self.save_mode = 3  # ペンとパスの結合保存
            self.save_image()
            self.save_mode = original_save_mode  # 元に戻す
            return

        if key == self.key_config.get("Undo"):
            self.undo()
            return
        elif key == self.key_config.get("Redo"):
            self.redo()
            return
        elif key == self.key_config.get("Next Color"):
            self.drawing_area.change_color(1)
            return
        elif key == self.key_config.get("Previous Color"):
            self.drawing_area.change_color(-1)
            return
        elif key == self.key_config.get("Save"):
            self.save_image()
            return
        elif key == self.key_config.get("Previous Image"):
            self.change_image(-1)
            return
        elif key == self.key_config.get("Next Image"):
            self.change_image(1)
            return
        elif key == self.key_config.get("Merged Save"):
            self.save_merged_image()
            return
        elif key == self.key_config.get("Increase Pen Size"):
            self.drawing_area.change_pen_size(1)
            return
        elif key == self.key_config.get("Decrease Pen Size"):
            self.drawing_area.change_pen_size(-1)
            return
        elif key == self.key_config.get("Toggle Tool"):
            # 既に上で処理済み
            return
        elif key == self.key_config.get("Delete"):
            self.handle_delete_key()
            return

        #Clearキーの挙動
        if key == self.key_config.get("Clear"):
            if self.delete_mode == 'Delete All':
                self.drawing_area.clear_all_layers()
            else:  # 'Delete Current Tool'
                if self.drawing_area.mode == 'draw':
                    self.drawing_area.clear_paint_layer()
                elif self.drawing_area.mode == 'spline':
                    self.drawing_area.clear_vector_layer()
            return

        # 消しゴムモードの切替
        if key == self.key_config.get("Eraser Tool"):
            self.drawing_area.eraser_key_pressed = True
            self.drawing_area.update_cursor()
            return

        # その他のキーイベント処理
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        key = event.key()
        if key == self.key_config.get("Eraser Tool"):
            self.drawing_area.eraser_key_pressed = False
            self.drawing_area.update_cursor()
        super().keyReleaseEvent(event)

    def handle_delete_key(self):
        if self.delete_mode == 'Delete All':
            self.drawing_area.clear_all_layers()
        else:  # 'Delete Current Tool'
            if self.drawing_area.mode == 'draw':
                self.drawing_area.clear_paint_layer()
            elif self.drawing_area.mode == 'spline':
                self.drawing_area.clear_vector_layer()
        self.drawing_area.update()

    def change_image(self, direction):
        if self.image_files:
            new_index = (self.current_image_index + direction) % len(self.image_files)
            self.load_image(new_index)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            action = "Increase Pen Size"
        else:
            action = "Decrease Pen Size"
        config_action = self.mouse_config.get(action, "No Action")
        if config_action == "Wheel Up" and delta > 0:
            self.drawing_area.change_pen_size(1)
        elif config_action == "Wheel Down" and delta < 0:
            self.drawing_area.change_pen_size(-1)

    def name_to_mouse_button(self, name):
        return {
            "Left Button": Qt.LeftButton,
            "Middle Button": Qt.MiddleButton,
            "Right Button": Qt.RightButton,
            "No Button": Qt.NoButton
        }.get(name, Qt.NoButton)

    def mouse_button_to_name(self, button):
        return {
            Qt.LeftButton: "Left Button",
            Qt.MiddleButton: "Middle Button",
            Qt.RightButton: "Right Button",
            Qt.NoButton: "No Button"
        }.get(button, "No Button")

    def resize_canvas(self, new_size):
        self.default_canvas_size = new_size
        self.drawing_area.create_default_image(new_size)
        self.drawing_area.setFixedSize(new_size)
        self.resize(self.sizeHint())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.drawing_area.update()

    def showEvent(self, event):
        super().showEvent(event)
        self.drawing_area.update()

    def handle_delete_mode_change(self, mode):
        self.delete_mode = mode
        self.settings_manager.settings['delete_mode'] = mode
        self.settings_manager.save_settings()
