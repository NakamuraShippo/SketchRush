import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QLabel, QVBoxLayout, QWidget,
                            QAction, QMenu, QInputDialog, QColorDialog, QDialog, QGridLayout, QPushButton, QLineEdit)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QCursor, QImage, QKeySequence
from PyQt5.QtCore import Qt, QPoint, QSize, QRect
from PIL import Image
from PyQt5.QtCore import QTimer

class KeyConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Key Configuration")
        layout = QGridLayout()
        self.key_inputs = {}
        
        for i, (action, key) in enumerate(parent.key_config.items()):
            layout.addWidget(QLabel(action), i, 0)
            key_input = QLineEdit(QKeySequence(key).toString())
            layout.addWidget(key_input, i, 1)
            self.key_inputs[action] = key_input
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        layout.addWidget(save_button, len(parent.key_config), 0, 1, 2)
        
        self.setLayout(layout)

class PaintApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Black Line Paint App")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.image_label = QLabel(self.central_widget)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMouseTracking(True)

        layout = QVBoxLayout(self.central_widget)
        layout.addWidget(self.image_label)

        self.folder_path = ""
        self.image_files = []
        self.current_image_index = 0
        self.drawing = False
        self.last_point = QPoint()
        self.pen_size = 5
        self.eraser_mode = False

        self.original_pixmap = None
        self.paint_layer = None

        self.undo_stack = []
        self.redo_stack = []

        self.colors = [Qt.black, Qt.white, Qt.blue, Qt.red, Qt.yellow, Qt.green, Qt.magenta]
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
            "Next Image": Qt.Key_Right
        }

        self.create_menu()
        self.select_folder()

    def create_menu(self):
        menubar = self.menuBar()
        settings_menu = menubar.addMenu('Settings')

        change_save_folder = QAction('Change Save Folder', self)
        change_save_folder.triggered.connect(self.change_save_folder)
        settings_menu.addAction(change_save_folder)

        change_save_name = QAction('Change Save Name Template', self)
        change_save_name.triggered.connect(self.change_save_name)
        settings_menu.addAction(change_save_name)

        key_config = QAction('Key Configuration', self)
        key_config.triggered.connect(self.open_key_config)
        settings_menu.addAction(key_config)

    def change_save_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Folder")
        if folder:
            self.save_folder = folder

    def change_save_name(self):
        name, ok = QInputDialog.getText(self, 'Change Save Name Template', 
                                        'Enter new name template (use {:03d} for number):',
                                        text=self.save_name_template)
        if ok:
            self.save_name_template = name

    def open_key_config(self):
        dialog = KeyConfigDialog(self)
        if dialog.exec_():
            for action, input_field in dialog.key_inputs.items():
                self.key_config[action] = QKeySequence(input_field.text())[0]

    def select_folder(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if self.folder_path:
            self.image_files = [f for f in os.listdir(self.folder_path) if f.lower().endswith(('.png', '.jpg', '.webp', '.gif', '.bmp', '.jpeg'))]
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
            self.update_display()
            self.current_image_index = index
            self.update_cursor()
            self.undo_stack.clear()
            self.redo_stack.clear()

    def update_display(self):
        if self.original_pixmap and self.paint_layer:
            display_pixmap = QPixmap(self.original_pixmap)
            painter = QPainter(display_pixmap)
            painter.drawImage(0, 0, self.paint_layer)
            painter.end()
            self.image_label.setPixmap(display_pixmap)

    def get_image_coordinates(self, pos):
        return self.image_label.mapFrom(self, pos)

    def mousePressEvent(self, event):
        pos = self.get_image_coordinates(event.pos())
        if self.image_label.rect().contains(pos):
            if event.button() == Qt.LeftButton:
                self.drawing = True
                self.last_point = pos
                self.undo_stack.append(self.paint_layer.copy())
                self.redo_stack.clear()
                if len(self.undo_stack) > 10:
                    self.undo_stack.pop(0)
                self.draw_point(pos)
            elif event.button() == Qt.RightButton:
                self.eraser_mode = True
                self.update_cursor()

    def mouseMoveEvent(self, event):
        pos = self.get_image_coordinates(event.pos())
        if self.drawing and self.image_label.rect().contains(pos):
            self.draw_line(self.last_point, pos)
            self.last_point = pos

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
        elif event.button() == Qt.RightButton:
            self.eraser_mode = False
            self.update_cursor()

    def draw_point(self, point):
        if not self.paint_layer:
            return
        
        painter = QPainter(self.paint_layer)
        painter.setPen(QPen(self.colors[self.current_color_index], self.pen_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        if self.eraser_mode:
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.drawPoint(point)
        painter.end()
        self.update_display()

    def draw_line(self, start, end):
        if not self.paint_layer:
            return
        
        painter = QPainter(self.paint_layer)
        painter.setPen(QPen(self.colors[self.current_color_index], self.pen_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        if self.eraser_mode:
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.drawLine(start, end)
        painter.end()
        self.update_display()

    def wheelEvent(self, event):
        self.pen_size = max(1, min(50, self.pen_size + event.angleDelta().y() // 120))
        self.update_cursor()

    def keyPressEvent(self, event):
        if event.key() == self.key_config["Undo"]:
            self.undo()
        elif event.key() == self.key_config["Redo"]:
            self.redo()
        elif event.key() == self.key_config["Clear"]:
            self.clear_paint_layer()
        elif event.key() == self.key_config["Next Color"]:
            self.change_color(1)
        elif event.key() == self.key_config["Previous Color"]:
            self.change_color(-1)
        elif event.key() == self.key_config["Save"]:
            self.save_image()
        elif event.key() == self.key_config["Previous Image"]:
            self.change_image(-1)
        elif event.key() == self.key_config["Next Image"]:
            self.change_image(1)

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
        painter.drawEllipse(0, 0, cursor_size-1, cursor_size-1)
        painter.end()
        
        return QCursor(cursor_pixmap)

    def update_cursor(self):
        cursor = self.create_cursor()
        self.setCursor(cursor)

    def save_image(self):
        if self.paint_layer:
            save_folder = self.save_folder if self.save_folder else self.folder_path
            base_filename = self.save_name_template.format(self.current_image_index)
            save_path = self.get_unique_filename(save_folder, base_filename)
            
            self.paint_layer.save(save_path, "PNG")
            print(f"Image saved as {save_path}")
            
            # Load the next image
            self.change_image(1)
            
            # Clear the painted content
            self.paint_layer.fill(Qt.transparent)
            self.update_display()
            
            # Reset undo/redo stacks
            self.undo_stack.clear()
            self.redo_stack.clear()
            
            # Load the next image after a short delay
            QTimer.singleShot(100, self.load_next_image)

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
        next_index = (self.current_image_index + 1) % len(self.image_files)
        self.load_image(next_index)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.original_pixmap:
            self.update_display()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    paint_app = PaintApp()
    paint_app.show()
    sys.exit(app.exec_())