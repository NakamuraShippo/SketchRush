# drawing_area.py

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QCursor, QPainterPath, QImage, QTabletEvent
from PyQt5.QtCore import Qt, QPoint, QPointF, QSize, QEvent
from spline_manager import SplineManager


class DrawingArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAttribute(Qt.WA_StaticContents)
        self.setTabletTracking(True)

        initial_size = self.main_window.default_canvas_size
        self.raster_layer = QPixmap(initial_size)
        self.raster_layer.fill(Qt.transparent)

        self.vector_layer = QPixmap(initial_size)
        self.vector_layer.fill(Qt.transparent)

        self.current_layer = self.raster_layer

        self.drawing = False
        self.last_point = QPoint()
        self.pen_size = self.main_window.pen_size
        self.eraser_key_pressed = False
        self.right_button_pressed = False
        self.undo_stack = []
        self.redo_stack = []
        self.colors = self.main_window.colors
        self.current_color_index = self.main_window.current_color_index
        self.background_color = self.main_window.background_color
        self.use_tablet = self.main_window.use_tablet
        self.original_pixmap = None
        self.current_tablet_device = None
        self.update_cursor()

        self.stabilization_degree = self.main_window.stabilization_degree
        self.point_buffer = []

        self.setFixedSize(initial_size)

        self.spline_manager = SplineManager(self)
        self.mode = 'draw'
        self.setup_spline_manager_callbacks()

    def set_stabilization_degree(self, degree):
        self.stabilization_degree = degree
        self.point_buffer = []

    def set_image(self, pixmap):
        self.original_pixmap = pixmap
        new_size = self.original_pixmap.size()
        self.raster_layer = QPixmap(new_size)
        self.raster_layer.fill(Qt.transparent)
        self.vector_layer = QPixmap(new_size)
        self.vector_layer.fill(Qt.transparent)
        self.setFixedSize(new_size)
        self.update()
        self.main_window.resize(self.main_window.sizeHint())

    def create_default_image(self, size):
        self.raster_layer = QPixmap(size)
        self.raster_layer.fill(Qt.transparent)
        self.vector_layer = QPixmap(size)
        self.vector_layer.fill(Qt.transparent)
        self.setFixedSize(size)
        self.update()

    def get_image_coordinates(self, pos):
        return pos

    def is_eraser_active(self):
        tablet_eraser = self.use_tablet and self.current_tablet_device == QTabletEvent.Eraser
        return self.eraser_key_pressed or self.right_button_pressed or tablet_eraser

    def mousePressEvent(self, event):
        if self.mode == 'spline':
            self.spline_manager.handle_mouse_press(event)
            self.update()
            return
        else:
            pos = self.get_image_coordinates(event.pos())
            if pos.x() >= 0 and pos.y() >= 0:
                button = event.button()
                pen_tool_button = self.main_window.mouse_config.get("Pen Tool", Qt.LeftButton)
                eraser_tool_button = self.main_window.mouse_config.get("Eraser Tool", Qt.RightButton)
                if pen_tool_button != Qt.NoButton and button == pen_tool_button:
                    self.drawing = True
                    self.last_point = pos
                    self.push_undo_stack()
                    self.redo_stack.clear()
                    self.draw_point(pos)
                    self.update_cursor()
                    self.point_buffer = []
                elif eraser_tool_button != Qt.NoButton and button == eraser_tool_button:
                    self.drawing = True
                    self.last_point = pos
                    self.right_button_pressed = True
                    self.redo_stack.clear()
                    self.draw_point(pos)
                    self.update_cursor()
                    self.point_buffer = []

    def mouseMoveEvent(self, event):
        if self.mode == 'spline':
            self.spline_manager.handle_mouse_move(event)
            self.update()
            return
        else:
            pos = self.get_image_coordinates(event.pos())
            if self.drawing and pos.x() >= 0 and pos.y() >= 0:
                if self.stabilization_degree > 0:
                    self.point_buffer.append(pos)
                    if len(self.point_buffer) > self.stabilization_degree:
                        self.point_buffer.pop(0)
                    avg_x = sum(p.x() for p in self.point_buffer) / len(self.point_buffer)
                    avg_y = sum(p.y() for p in self.point_buffer) / len(self.point_buffer)
                    stabilized_pos = QPoint(int(avg_x), int(avg_y))
                    self.draw_line(self.last_point, stabilized_pos)
                    self.last_point = stabilized_pos
                else:
                    self.draw_line(self.last_point, pos)
                    self.last_point = pos

    def mouseReleaseEvent(self, event):
        if self.mode == 'spline':
            self.spline_manager.handle_mouse_release(event)
            self.update()
            return
        else:
            button = event.button()
            pen_tool_button = self.main_window.mouse_config.get("Pen Tool", Qt.LeftButton)
            eraser_tool_button = self.main_window.mouse_config.get("Eraser Tool", Qt.RightButton)
            if button == pen_tool_button:
                self.drawing = False
            elif button == eraser_tool_button:
                self.drawing = False
                self.right_button_pressed = False
                self.update_cursor()

    def tabletEvent(self, event):
        if not self.use_tablet:
            event.ignore()
            return

        if self.mode == 'spline':
            event.accept()
            return

        pos = event.pos()
        img_pos = self.get_image_coordinates(pos)
        pressure = event.pressure()
        pressure_pen_size = max(1, self.pen_size * pressure)
        self.current_tablet_device = event.device()

        if event.device() == QTabletEvent.Stylus or event.device() == QTabletEvent.Eraser:
            if event.type() == QEvent.TabletPress:
                self.drawing = True
                self.last_point = img_pos
                self.push_undo_stack()
                self.redo_stack.clear()
                self.draw_point(img_pos, pressure_pen_size)
                self.update_cursor()
                self.point_buffer = []
                event.accept()
            elif event.type() == QEvent.TabletMove and self.drawing:
                if self.stabilization_degree > 0:
                    self.point_buffer.append(img_pos)
                    if len(self.point_buffer) > self.stabilization_degree:
                        self.point_buffer.pop(0)
                    avg_x = sum(p.x() for p in self.point_buffer) / len(self.point_buffer)
                    avg_y = sum(p.y() for p in self.point_buffer) / len(self.point_buffer)
                    stabilized_pos = QPoint(int(avg_x), int(avg_y))
                    self.draw_line(self.last_point, stabilized_pos, pressure_pen_size)
                    self.last_point = stabilized_pos
                else:
                    self.draw_line(self.last_point, img_pos, pressure_pen_size)
                    self.last_point = img_pos
                event.accept()
            elif event.type() == QEvent.TabletRelease:
                self.drawing = False
                event.accept()
            else:
                event.ignore()
        else:
            event.ignore()

    def draw_point(self, point, pen_size=None):
        if pen_size is None:
            pen_size = self.pen_size
        painter = QPainter(self.raster_layer)
        if self.is_eraser_active():
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            pen = QPen(Qt.transparent, pen_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        else:
            pen = QPen(self.colors[self.current_color_index], pen_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPoint(point)
        painter.end()
        self.update()

    def draw_line(self, start, end, pen_size=None):
        if pen_size is None:
            pen_size = self.pen_size
        painter = QPainter(self.raster_layer)
        if self.is_eraser_active():
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            pen = QPen(Qt.transparent, pen_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        else:
            pen = QPen(self.colors[self.current_color_index], pen_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(start, end)
        painter.end()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        widget_size = self.size()
        if self.original_pixmap:
            pixmap_size = self.original_pixmap.size()
        else:
            pixmap_size = self.raster_layer.size()

        scale_x = widget_size.width() / pixmap_size.width()
        scale_y = widget_size.height() / pixmap_size.height()

        painter.scale(scale_x, scale_y)

        if self.original_pixmap:
            painter.drawPixmap(0, 0, self.original_pixmap)
        else:
            painter.fillRect(self.rect(), self.background_color)

        painter.drawPixmap(0, 0, self.raster_layer)

        self.spline_manager.draw_paths(painter)

        painter.end()

    def keyPressEvent(self, event):
        key = event.key()
        toggle_tool_key = self.main_window.key_config.get("Toggle Tool", Qt.Key_Tab)
        if key == toggle_tool_key:
            if self.mode == 'draw':
                self.mode = 'spline'
                self.current_layer = self.vector_layer
                print("Mode switched to spline")
            else:
                self.mode = 'draw'
                self.current_layer = self.raster_layer
                print("Mode switched to draw")
            return

        # パスツールのモード切替を処理
        if self.mode == 'spline':
            toggle_path_mode_key = self.main_window.key_config.get("Toggle Path Mode", Qt.Key_Q)
            if key == toggle_path_mode_key:
                if self.spline_manager.mode == 'drawing':
                    self.spline_manager.mode = 'selection'
                    print("Path tool mode switched to selection")
                else:
                    self.spline_manager.mode = 'drawing'
                    print("Path tool mode switched to drawing")
                return

        if key == self.main_window.key_config.get("Next Color", Qt.Key_C):
            self.change_color(1)
            return
        elif key == self.main_window.key_config.get("Previous Color", Qt.Key_V):
            self.change_color(-1)
            return

        if key == self.main_window.key_config.get("Undo"):
            self.undo()
            return
        elif key == self.main_window.key_config.get("Redo"):
            self.redo()
            return

        if key == self.main_window.key_config.get("Eraser Tool"):
            self.eraser_key_pressed = True
            self.update_cursor()
            return

        toggle_fill_key = self.main_window.key_config.get("Toggle Fill", Qt.Key_F)
        if key == toggle_fill_key:
            if self.mode == 'spline' and self.spline_manager.selected_paths:
                for path in self.spline_manager.selected_paths:
                    path.fill_enabled = not path.fill_enabled
                    path.generate_path_from_bspline()
                self.update_vector_layer()
                self.update()
            else:
                self.spline_manager.default_fill_enabled = not self.spline_manager.default_fill_enabled
            return

        event.ignore()

    def setup_spline_manager_callbacks(self):
        pass

    def keyReleaseEvent(self, event):
        key = event.key()
        if key == self.main_window.key_config.get("Eraser Tool"):
            self.eraser_key_pressed = False
            self.update_cursor()
            return
        event.ignore()

    def update_cursor(self):
        cursor = self.create_cursor()
        self.setCursor(cursor)

    def create_cursor(self):
        if self.pen_size < 10:
            cursor_size = 15
            cursor_pixmap = QPixmap(cursor_size, cursor_size)
            cursor_pixmap.fill(Qt.transparent)
            painter = QPainter(cursor_pixmap)
            if self.is_eraser_active():
                pen_color = QColor(Qt.black)
            else:
                pen_color = self.colors[self.current_color_index]
            painter.setPen(QPen(pen_color, 1))
            painter.drawLine(cursor_size // 2, 0, cursor_size // 2, cursor_size)
            painter.drawLine(0, cursor_size // 2, cursor_size, cursor_size // 2)
            painter.end()
            return QCursor(cursor_pixmap, cursor_size // 2, cursor_size // 2)
        else:
            cursor_size = self.pen_size
            cursor_pixmap = QPixmap(cursor_size, cursor_size)
            cursor_pixmap.fill(Qt.transparent)
            if self.is_eraser_active():
                pen_color = QColor(Qt.black)
            else:
                pen_color = self.colors[self.current_color_index]
            painter = QPainter(cursor_pixmap)
            painter.setPen(QPen(pen_color, 1, Qt.SolidLine))
            painter.drawEllipse(0, 0, cursor_size - 1, cursor_size - 1)
            painter.end()
            return QCursor(cursor_pixmap, cursor_size // 2, cursor_size // 2)

    def change_color(self, direction):
        self.current_color_index = (self.current_color_index + direction) % len(self.colors)
        self.main_window.current_color_index = self.current_color_index
        self.update_cursor()
        if self.mode == 'spline':
            for vp in self.spline_manager.selected_paths:
                vp.pen_color = self.colors[self.current_color_index]
            self.update()

    def change_pen_size(self, delta):
        self.pen_size = max(1, min(50, self.pen_size + delta))
        self.update_cursor()

    def clear_paint_layer(self, push_undo=True):
        if push_undo:
            self.push_undo_stack()
        self.raster_layer.fill(Qt.transparent)
        self.update()

    def clear_vector_layer(self, push_undo=True):
        if push_undo:
            self.push_undo_stack()
        self.spline_manager.paths.clear()
        self.spline_manager.selected_paths.clear()
        self.update_vector_layer()
        self.update()

    def clear_all_layers(self):
        self.push_undo_stack()
        self.raster_layer.fill(Qt.transparent)
        self.spline_manager.paths.clear()
        self.spline_manager.selected_paths.clear()
        self.update_vector_layer()
        self.update()

    def save_state(self):
        state = {
            'raster_layer': self.raster_layer.copy(),
            'vector_layer': self.vector_layer.copy(),
            'spline_manager': self.spline_manager.copy()
        }
        self.undo_stack.append(state)
        if len(self.undo_stack) > 300:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def push_undo_stack(self):
        spline_manager_copy = self.spline_manager.copy()
        self.undo_stack.append({
            'raster_layer': self.raster_layer.copy(),
            'spline_manager': spline_manager_copy
        })
        if len(self.undo_stack) > 300:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
        state = self.undo_stack.pop()
        self.redo_stack.append({
            'raster_layer': self.raster_layer.copy(),
            'spline_manager': self.spline_manager.copy()
        })
        self.raster_layer = state['raster_layer']
        self.spline_manager = state['spline_manager']
        self.spline_manager.drawing_area = self
        for path in self.spline_manager.paths:
            path.drawing_area = self
        self.update_vector_layer()
        self.update()

    def redo(self):
        if not self.redo_stack:
            return
        state = self.redo_stack.pop()
        self.undo_stack.append({
            'raster_layer': self.raster_layer.copy(),
            'spline_manager': self.spline_manager.copy()
        })
        self.raster_layer = state['raster_layer']
        self.spline_manager = state['spline_manager']
        self.spline_manager.drawing_area = self
        self.update_vector_layer()
        self.update()

    def update_vector_layer(self):
        self.vector_layer.fill(Qt.transparent)
        painter = QPainter(self.vector_layer)
        painter.setRenderHint(QPainter.Antialiasing)

        for path in self.spline_manager.paths:
            pen = QPen(path.pen_color, path.pen_width)
            painter.setPen(pen)
            if path.fill_enabled:
                brush = QBrush(path.fill_color)
                painter.setBrush(brush)
            else:
                painter.setBrush(Qt.NoBrush)
            painter.drawPath(path.path)
        painter.end()
