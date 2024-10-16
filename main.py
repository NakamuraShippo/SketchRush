import sys
import os
import yaml
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QSlider, QColorDialog, QDialog, QTabWidget,
                            QSpinBox, QDoubleSpinBox, QAction, QGridLayout, QFileDialog,
                            QListWidget, QListWidgetItem, QAbstractItemView, QComboBox,
                            QMessageBox, QLineEdit, QSizePolicy)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QCursor, QImage, QTabletEvent, QPainterPath, QPainterPathStroker, QBrush
from PyQt5.QtCore import Qt, QPoint, QSize, QEvent, QTimer, QPointF, QRectF
import math
from scipy.interpolate import splprep, splev
from shapely.geometry import LineString
import numpy as np

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
            self.main_window.delete_mode = self.settings.get('delete_mode', 'Delete Current Tool')  # 新しい設定項目
            # 手ブレ補正の読み込み
            self.main_window.stabilization_degree = self.settings.get('stabilization_degree', 0)
            self.main_window.drawing_area.set_stabilization_degree(self.main_window.stabilization_degree)
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
            'delete_mode': self.main_window.delete_mode,  # 保存
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

class VectorPath:
    def __init__(self, drawing_area):
        self.points = []
        self.drawing_area = drawing_area
        self.control_points = []  # 制御点のリストを初期化
        self.qt_path = QPainterPath()
        self.pen_color = drawing_area.colors[drawing_area.current_color_index]
        self.pen_width = drawing_area.pen_size
        self.fill_color = QColor(255, 255, 255)
        self.fill_enabled = False
        self.spline_control_points = []
        self.path = QPainterPath()
        self.selected = False  # パスが選択されているかどうか
        self.is_closed = False  # パスが閉じているかどうか

    def add_point(self, point):
        self.points.append(point)
        if len(self.points) == 1:
            self.path.moveTo(point)
        else:
            self.path.lineTo(point)

    def generate_path_from_bspline(self):
        """
        Bスプライン制御点からQPainterPathを生成します。
        """
        if len(self.spline_control_points) < 2:
            self.path = QPainterPath()
            return

        self.path = QPainterPath()
        points = [QPointF(x, y) for x, y in self.spline_control_points]
        if len(points) >= 4:
            b_spline = self.calculate_bspline(points)
            self.path.moveTo(b_spline[0])
            for point in b_spline[1:]:
                self.path.lineTo(point)
        else:
            # 制御点が少ない場合は直線を描画
            self.path.moveTo(points[0])
            for point in points[1:]:
                self.path.lineTo(point)

        self.qt_path = QPainterPath()
        if self.control_points:
            self.qt_path.moveTo(self.control_points[0])
            if len(self.control_points) == 1:
                self.qt_path.lineTo(self.control_points[0])
            elif len(self.control_points) == 2:
                self.qt_path.lineTo(self.control_points[1])
            else:
                # Bスプライン曲線の生成
                spline_points = bspline_curve(self.control_points)
                for point in spline_points:
                    self.qt_path.lineTo(point)

            # ここで、fill_enabled が True の場合、パスを閉じる
            if self.fill_enabled:
                self.qt_path.closeSubpath()

    def draw(self, painter, control_point_size=0):
        if not self.path.isEmpty():
            # パスの描画
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)

            if self.fill_enabled:
                # 塗りつぶしが有効な場合
                brush = QBrush(self.fill_color)
                painter.setBrush(brush)
                painter.drawPath(self.path)
            else:
                # 塗りつぶしが無効な場合
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(self.path)

            # 選択されている場合、選択矩形を描画
            if self.selected:
                self.draw_selection_rectangle(painter)

            # 選択されている場合のみ、制御点を描画
            if self.selected and control_point_size > 0:
                self.draw_control_points(painter, control_point_size)

    def draw_control_points(self, painter: QPainter, control_point_size: int):
        """
        制御点を描画します。
        """
        painter.setBrush(QColor(255, 0, 0))  # 赤色
        painter.setPen(Qt.NoPen)
        for cp in self.spline_control_points:
            rect = QRectF(cp[0] - control_point_size / 2, cp[1] - control_point_size / 2,
                          control_point_size, control_point_size)
            painter.drawRect(rect)

    def draw_selection_rectangle(self, painter: QPainter):
        """
        選択されたパスを囲む矩形を描画します。
        """
        bounding_rect = self.path.boundingRect().adjusted(-10, -10, 10, 10)

        # 点線の矩形
        pen = QPen(QColor(0, 120, 215), 1, Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(bounding_rect)

        # ハンドルの描画
        handle_size = 10
        corners = [
            bounding_rect.topLeft(),
            bounding_rect.topRight(),
            bounding_rect.bottomLeft(),
            bounding_rect.bottomRight(),
        ]

        handle_pen = QPen(QColor(0, 120, 215), 1, Qt.SolidLine)
        handle_brush = QBrush(QColor(0, 120, 215))
        painter.setPen(handle_pen)
        painter.setBrush(handle_brush)
        for corner in corners:
            handle_rect = QRectF(corner.x() - handle_size / 2, corner.y() - handle_size / 2,
                                handle_size, handle_size)
            painter.drawRect(handle_rect)

    def get_selection_rect(self):
        # 選択矩形を返す
        return self.path.boundingRect().adjusted(-10, -10, 10, 10)

    def contains_control_point(self, pos: QPointF, control_point_size: int) -> bool:
        for x, y in self.spline_control_points:
            rect = QRectF(
                x - control_point_size / 2,
                y - control_point_size / 2,
                control_point_size,
                control_point_size
            )
            if rect.contains(pos):
                return True
        return False

    def get_control_point_at(self, pos: QPointF, control_point_size: int):
        for index, (x, y) in enumerate(self.spline_control_points):
            rect = QRectF(
                x - control_point_size / 2,
                y - control_point_size / 2,
                control_point_size,
                control_point_size
            )
            if rect.contains(pos):
                return index
        return None

    def move_control_point(self, index: int, delta: QPointF):
        x, y = self.spline_control_points[index]
        self.spline_control_points[index] = (x + delta.x(), y + delta.y())
        self.generate_path_from_bspline()

    def contains_point(self, point, threshold):
        stroker = QPainterPathStroker()
        stroker.setWidth(threshold)
        stroke = stroker.createStroke(self.path)
        return stroke.contains(point)

    def contains(self, pos: QPointF, hit_threshold: float = 2.0) -> bool:
        """
        指定された位置がパスの近くにあるかどうかを判定します。
        """
        stroker = QPainterPathStroker()
        stroker.setWidth(hit_threshold * 2)
        stroked_path = stroker.createStroke(self.path)
        return stroked_path.contains(pos)

    def find_insertion_index(self, click_pos: QPointF) -> int:
        """
        クリック位置に最も近いセグメントのインデックスを返します。
        """
        min_distance = float('inf')
        insertion_index = None
        for i in range(len(self.spline_control_points) - 1):
            cp1 = self.spline_control_points[i]
            cp2 = self.spline_control_points[i + 1]
            p1 = QPointF(cp1[0], cp1[1])
            p2 = QPointF(cp2[0], cp2[1])
            distance = self.point_to_segment_distance(click_pos, p1, p2)
            if distance < min_distance:
                min_distance = distance
                insertion_index = i + 1  # 新しい制御点を挿入する位置
                min_distance = distance
        return insertion_index

    @staticmethod
    def point_to_segment_distance(p: QPointF, p1: QPointF, p2: QPointF) -> float:
        """
        点pから線分p1-p2への最小距離を計算します。
        """
        if p1 == p2:
            return math.hypot(p.x() - p1.x(), p.y() - p1.y())
        else:
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            t = ((p.x() - p1.x()) * dx + (p.y() - p1.y()) * dy) / (dx * dx + dy * dy)
            t = max(0, min(1, t))
            nearest_x = p1.x() + t * dx
            nearest_y = p1.y() + t * dy
            return math.hypot(p.x() - nearest_x, p.y() - nearest_y)

    def calculate_bspline(self, points):
        """
        Bスプライン曲線を計算します。
        """
        x = [p.x() for p in points]
        y = [p.y() for p in points]
        tck, u = splprep([x, y], s=0)
        unew = np.linspace(0, 1.0, num=100)
        out = splev(unew, tck)
        bspline_points = [QPointF(out[0][i], out[1][i]) for i in range(len(out[0]))]
        return bspline_points

    def finalize(self):
        # ポイントから制御点を生成
        self.spline_control_points = [(p.x(), p.y()) for p in self.points]
        # パスのスムージングと単純化を実行
        self.smooth_and_simplify()
        # スムージング・単純化後の制御点からパスを生成
        self.generate_path_from_bspline()

    def smooth_and_simplify(self):
        # PaintAppインスタンスから設定値を取得
        simplify_tolerance = self.drawing_area.main_window.default_simplify_tolerance
        smooth_strength = self.drawing_area.main_window.default_smooth_strength

        # パスの単純化
        self.simplify_path(simplify_tolerance)
        # パスのスムージング
        self.smooth_path(smooth_strength)

    def simplify_path(self, tolerance):
        """
        パスを単純化して制御点の数を減らします。
        """
        if tolerance <= 0:
            return  # 単純化をスキップ

        if len(self.spline_control_points) < 2:
            return  # 制御点が2つ未満の場合は単純化をスキップ

        coords = [(x, y) for x, y in self.spline_control_points]
        line = LineString(coords)
        simplified_line = line.simplify(tolerance, preserve_topology=False)
        self.spline_control_points = list(simplified_line.coords)

    def smooth_path(self, strength):
        """
        パスを滑らかにします。
        """
        if strength <= 0:
            return  # 滑らか化をスキップ

        if len(self.spline_control_points) < 3:
            return  # 制御点が3つ未満の場合は滑らか化をスキップ

        coords = np.array(self.spline_control_points)
        smoothed_coords = coords.copy()

        for _ in range(strength):
            smoothed_coords[1:-1] = (smoothed_coords[:-2] + smoothed_coords[1:-1] + smoothed_coords[2:]) / 3

        self.spline_control_points = [tuple(coord) for coord in smoothed_coords]

    def copy(self):
        new_path = VectorPath(self.drawing_area)
        # new_path.points = list(self.points)
        new_path.control_points = list(self.control_points)
        new_path.spline_control_points = list(self.spline_control_points)
        new_path.pen_color = QColor(self.pen_color)
        new_path.pen_width = self.pen_width
        new_path.fill_color = QColor(self.fill_color)
        new_path.fill_enabled = self.fill_enabled
        # new_path.selected = self.selected
        new_path.is_closed = self.is_closed
        # パスオブジェクトをコピー
        new_path.path = QPainterPath(self.path)
        new_path.qt_path = QPainterPath(self.qt_path)
        return new_path

    def move_by(self, delta: QPointF):
        # 制御点を移動
        self.spline_control_points = [
            (x + delta.x(), y + delta.y()) for x, y in self.spline_control_points
        ]
        self.generate_path_from_bspline()

    def path_to_svg_d(self):
        elements = []
        for i in range(self.path.elementCount()):
            elem = self.path.elementAt(i)
            if elem.type == QPainterPath.ElementType.MoveToElement:
                elements.append(f"M {elem.x} {elem.y}")
            elif elem.type == QPainterPath.ElementType.LineToElement:
                elements.append(f"L {elem.x} {elem.y}")
            elif elem.type == QPainterPath.ElementType.CurveToElement:
                cp1 = elem
                cp2 = self.path.elementAt(i + 1)
                end = self.path.elementAt(i + 2)
                elements.append(f"C {cp1.x} {cp1.y} {cp2.x} {cp2.y} {end.x} {end.y}")
                i += 2  # Skip control points
            elif elem.type == QPainterPath.ElementType.CurveToDataElement:
                continue  # Handled in CurveToElement
        return ' '.join(elements)

    def insert_control_point(self, index: int, pos: QPointF):
        self.spline_control_points.insert(index, (pos.x(), pos.y()))

    def delete_control_point(self, index: int):
        if len(self.spline_control_points) > 2:
            del self.spline_control_points[index]

class SplineManager:
    def __init__(self, drawing_area, control_point_size=10, scaling_sensitivity=0.002, hit_threshold=2.0):
        self.drawing_area = drawing_area  # DrawingArea インスタンス
        self.paths = []
        self.selected_paths = []
        self.current_path = None
        self.hit_threshold = self.drawing_area.main_window.path_hit_threshold
        self.is_drawing = False
        self.current_scribble_points = []
        self.control_point_size = control_point_size
        self.scaling_sensitivity = scaling_sensitivity

        self.on_change = None  # コールバック関数

        # スケーリング関連
        self.is_scaling = False
        self.scaling_start_pos = None
        self.scaling_mode = None  # 'expand' or 'shrink'
        self.proportional_scaling = True

        # 操作関連
        self.is_moving = False
        self.is_moving_control_point = False  # 制御点を移動中かどうか
        self.is_moving_path = False           # パスを移動中かどうか
        self.selected_control_point = None    # 選択された制御点
        self.last_mouse_pos = None            # マウスの前回位置を初期化

        # 修飾キーの設定（キーコード）
        self.add_point_modifier = self.drawing_area.main_window.key_config.get("Add Control Point Modifier", Qt.ControlModifier)
        self.delete_point_modifier = self.drawing_area.main_window.key_config.get("Delete Control Point Modifier", Qt.AltModifier)
        # self.add_point_modifier = Qt.ControlModifier
        # self.delete_point_modifier = Qt.AltModifier
        self.rotate_modifier = Qt.ControlModifier
        self.scale_modifier = Qt.AltModifier
        
        self.default_fill_enabled = False  # 新しく追加
        self.freehand_path = None  # フリーハンドの軌跡表示用

    def notify_change(self):
        if self.on_change:
            self.on_change()
        self.drawing_area.update()

    def delete_selected_paths(self):
        if self.selected_paths:
            for path in self.selected_paths:
                if path in self.paths:
                    self.paths.remove(path)
            self.selected_paths.clear()
            # 削除後に状態を保存
            self.drawing_area.push_undo_stack()
            self.drawing_area.update_vector_layer()
            self.drawing_area.update()

    def handle_mouse_press(self, event):
        pos = self.drawing_area.get_image_coordinates(event.pos())
        modifiers = QApplication.keyboardModifiers()

        self.last_mouse_pos = pos  # マウス押下時に現在の位置を記録
        self.drawing_area.push_undo_stack()
        if event.button() == Qt.LeftButton:
            if modifiers & self.add_point_modifier:
                # 制御点の追加
                for path in self.paths:
                    if path.contains_point(pos, self.hit_threshold):
                        # 操作開始時に状態を保存
                        self.drawing_area.push_undo_stack()
                        # 挿入位置を計算
                        insertion_index = path.find_insertion_index(pos)
                        # 制御点を追加
                        path.insert_control_point(insertion_index, pos)
                        path.generate_path_from_bspline()
                        self.drawing_area.update_vector_layer()
                        self.drawing_area.update()
                        break  # 一つのパスにのみ追加
                return
            elif modifiers & self.delete_point_modifier:
                # 制御点の削除
                for path in self.paths:
                    index = path.get_control_point_at(pos, self.control_point_size)
                    if index is not None:
                        # 操作開始時に状態を保存
                        self.drawing_area.push_undo_stack()
                        path.delete_control_point(index)
                        path.generate_path_from_bspline()
                        self.drawing_area.update_vector_layer()
                        self.drawing_area.update()
                        break  # 一つのパスからのみ削除
                return
            else:
                # まず制御点の選択・移動を確認
                for path in reversed(self.paths):
                    index = path.get_control_point_at(pos, self.control_point_size)
                    if index is not None:
                        self.deselect_all_paths()
                        self.selected_paths = [path]
                        path.selected = True
                        self.selected_control_point = (path, index)
                        self.is_moving_control_point = True
                        # 操作開始時に状態を保存
                        self.drawing_area.push_undo_stack()
                        self.drawing_area.update()
                        return

                # 次にパス上をクリックした場合、パスの選択と移動を開始
                for path in reversed(self.paths):
                    if path.contains_point(pos, self.hit_threshold):
                        self.deselect_all_paths()
                        self.selected_paths = [path]
                        path.selected = True
                        self.is_moving_path = True  # パスの移動を開始
                        # 操作開始時に状態を保存
                        self.drawing_area.push_undo_stack()
                        self.drawing_area.update()
                        return

                # 選択されたパスがあり、その選択矩形内をクリックした場合、パスの移動を開始
                if self.selected_paths:
                    clicked_inside_selection_rect = False
                    for path in self.selected_paths:
                        if path.get_selection_rect().contains(pos):
                            clicked_inside_selection_rect = True
                            break
                    if clicked_inside_selection_rect:
                        self.is_moving_path = True  # パスの移動を開始
                        # 操作開始時に状態を保存
                        self.drawing_area.push_undo_stack()
                        self.drawing_area.update()
                        return
                    else:
                        # 選択矩形の外側をクリックした場合、選択を解除
                        self.deselect_all_paths()
                        self.drawing_area.update()
                        return

            # 新しいパスの描画開始
            self.current_path = VectorPath(self.drawing_area)
            self.current_path.pen_color = self.drawing_area.colors[self.drawing_area.current_color_index]
            self.current_path.pen_width = self.drawing_area.pen_size
            self.current_path.fill_enabled = self.default_fill_enabled  # デフォルトの fill_enabled を適用
            self.current_path.fill_color = self.drawing_area.colors[self.drawing_area.current_color_index]  # 塗りつぶし色を設定
            self.current_path.add_point(pos)
            self.is_drawing = True
            # 操作開始時に状態を保存（削除）
            # self.drawing_area.push_undo_stack()
            return

    def handle_mouse_move(self, event):
        pos = self.drawing_area.get_image_coordinates(event.pos())
        if self.last_mouse_pos is None:
            self.last_mouse_pos = pos

        delta = pos - self.last_mouse_pos

        if self.is_drawing and self.current_path is not None:
            self.current_path.add_point(pos)
            # 描画中のパスにも単純化とスムージングを適用
            # self.current_path.finalize()
            self.drawing_area.update_vector_layer()
            self.drawing_area.update()
            self.last_mouse_pos = pos
            return

        if self.is_moving_control_point and self.selected_control_point:
            path, index = self.selected_control_point
            path.move_control_point(index, delta)
            self.drawing_area.update_vector_layer()
            self.drawing_area.update()
            self.last_mouse_pos = pos
            return

        if self.is_moving_path and self.selected_paths:
            for path in self.selected_paths:
                path.move_by(delta)
            self.drawing_area.update_vector_layer()
            self.drawing_area.update()
            self.last_mouse_pos = pos
            return

    def handle_mouse_release(self, event):
        pos = self.drawing_area.get_image_coordinates(event.pos())
        self.last_mouse_pos = None  # マウスリリース時に位置をリセット

        if event.button() == Qt.LeftButton:
            if self.is_drawing:
                if self.current_path:
                    # パスの作成を終了
                    self.current_path.finalize()
                    self.paths.append(self.current_path)
                    self.current_path = None
                    # 操作終了時に状態を保存
                    self.drawing_area.push_undo_stack()
                    self.drawing_area.update_vector_layer()
                    self.drawing_area.update()
                self.is_drawing = False

            if self.is_moving_control_point:
                self.is_moving_control_point = False
                self.selected_control_point = None

            if self.is_moving_path:
                self.is_moving_path = False  # パスの移動を終了

    def deselect_all_paths(self):
        for path in self.paths:
            path.selected = False
        self.selected_paths = []

    def scale_selected_paths(self, scale_x: float, scale_y: float):
        """
        選択されたパスの制御点をスケーリングします。
        """
        center = self.scaling_start_pos
        for vp in self.selected_paths:
            new_control_points = []
            for (x, y) in vp.spline_control_points:
                new_x = center.x() + (x - center.x()) * scale_x
                new_y = center.y() + (y - center.y()) * scale_y
                new_control_points.append((new_x, new_y))
            vp.spline_control_points = new_control_points
            vp.generate_path_from_bspline()

    def draw_paths(self, painter):
        for vp in self.paths:
            vp.draw(painter, self.control_point_size)
        # 現在描画中のパスも描画
        if self.is_drawing and self.current_path:
            self.current_path.draw(painter, self.control_point_size)

    def move_selected_paths(self, delta: QPointF):
        for path in self.selected_paths:
            path.move_by(delta)
        self.drawing_area.update_vector_layer()
        self.drawing_area.update()

    def rotate_selected_paths(self, angle_degrees: float, center: QPointF):
        """
        選択されたパスを回転します。
        """
        angle_radians = math.radians(angle_degrees)
        cos_theta = math.cos(angle_radians)
        sin_theta = math.sin(angle_radians)
        for vp in self.selected_paths:
            new_control_points = []
            for x, y in vp.spline_control_points:
                dx = x - center.x()
                dy = y - center.y()
                new_x = center.x() + dx * cos_theta - dy * sin_theta
                new_y = center.y() + dx * sin_theta + dy * cos_theta
                new_control_points.append((new_x, new_y))
            vp.spline_control_points = new_control_points
            vp.generate_path_from_bspline()

    def scale_selected_paths(self, scale_x: float, scale_y: float, center: QPointF):
        """
        選択されたパスを拡大縮小します。
        """
        for vp in self.selected_paths:
            new_control_points = []
            for x, y in vp.spline_control_points:
                new_x = center.x() + (x - center.x()) * scale_x
                new_y = center.y() + (y - center.y()) * scale_y
                new_control_points.append((new_x, new_y))
            vp.spline_control_points = new_control_points
            vp.generate_path_from_bspline()

    def get_selected_paths_center(self):
        """
        選択されたパスの中心座標を取得します。
        """
        min_x, min_y, max_x, max_y = None, None, None, None
        for vp in self.selected_paths:
            rect = vp.path.boundingRect()
            if min_x is None or rect.left() < min_x:
                min_x = rect.left()
            if min_y is None or rect.top() < min_y:
                min_y = rect.top()
            if max_x is None or rect.right() > max_x:
                max_x = rect.right()
            if max_y is None or rect.bottom() > max_y:
                max_y = rect.bottom()
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        return QPointF(center_x, center_y)

    def is_point_within_selected_paths(self, pos: QPointF) -> bool:
        """
        指定された位置が選択されたパスの内側にあるかを判定します。
        """
        for vp in self.selected_paths:
            if vp.path.contains(pos):
                return True
        return False

    def is_over_control_point(self, pos):
        for vp in self.selected_paths:
            for cp in vp.spline_control_points:
                rect_cp = QRectF(cp[0] - self.control_point_size / 2,
                                cp[1] - self.control_point_size / 2,
                                self.control_point_size,
                                self.control_point_size)
                if rect_cp.contains(pos):
                    return True
        return False

    def copy(self):
        # SplineManagerのコピーを作成
        new_manager = SplineManager(self.drawing_area)
        # パスのコピーを作成
        new_manager.paths = [path.copy() for path in self.paths]
        # selected_paths を新しいパスのコピーに更新
        new_manager.selected_paths = []
        for path in self.selected_paths:
            index = self.paths.index(path)
            new_manager.selected_paths.append(new_manager.paths[index])
            new_manager.paths[index].selected = True
        new_manager.current_path = self.current_path.copy() if self.current_path else None
        new_manager.is_drawing = self.is_drawing
        new_manager.is_moving_control_point = self.is_moving_control_point
        new_manager.is_moving_path = self.is_moving_path
        new_manager.hit_threshold = self.hit_threshold
        new_manager.control_point_size = self.control_point_size
        new_manager.last_mouse_pos = self.last_mouse_pos
        new_manager.default_fill_enabled = self.default_fill_enabled
        # 他の必要な属性もコピー
        return new_manager


class PathToolSettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Path Tool Settings")
        self.main_window = parent

        layout = QVBoxLayout()

        # 線の太さ設定
        pen_width_label = QLabel("Pen Width")
        self.pen_width_slider = QSlider(Qt.Horizontal)
        self.pen_width_slider.setMinimum(1)
        self.pen_width_slider.setMaximum(20)
        self.pen_width_slider.setValue(self.main_window.pen_size)
        self.pen_width_slider.valueChanged.connect(self.change_pen_width)

        layout.addWidget(pen_width_label)
        layout.addWidget(self.pen_width_slider)

        # 色の選択
        pen_color_label = QLabel("Pen Color")
        self.pen_color_button = QPushButton()
        self.pen_color_button.setStyleSheet(f"background-color: {self.main_window.colors[self.main_window.current_color_index].name()}")
        self.pen_color_button.clicked.connect(self.change_pen_color)

        layout.addWidget(pen_color_label)
        layout.addWidget(self.pen_color_button)

        # 単純化の度合い設定
        simplify_label = QLabel("Simplification Tolerance")
        self.simplify_slider = QSlider(Qt.Horizontal)
        self.simplify_slider.setMinimum(0)
        self.simplify_slider.setMaximum(10)
        self.simplify_slider.setValue(self.main_window.default_simplify_tolerance)
        self.simplify_slider.valueChanged.connect(self.change_simplify_tolerance)

        layout.addWidget(simplify_label)
        layout.addWidget(self.simplify_slider)

        # 滑らかさの度合い設定
        smooth_label = QLabel("Smoothing Strength")
        self.smooth_slider = QSlider(Qt.Horizontal)
        self.smooth_slider.setMinimum(0)
        self.smooth_slider.setMaximum(5)
        self.smooth_slider.setValue(self.main_window.default_smooth_strength)
        self.smooth_slider.valueChanged.connect(self.change_smooth_strength)

        layout.addWidget(smooth_label)
        layout.addWidget(self.smooth_slider)

        self.setLayout(layout)

    # 設定変更のメソッド
    def change_pen_width(self, value):
        self.main_window.pen_size = value
        self.main_window.drawing_area.pen_size = value
        for vp in self.main_window.drawing_area.spline_manager.selected_paths:
            vp.pen_width = value
            vp.generate_path_from_bspline()
        self.main_window.drawing_area.update()

    def change_pen_color(self):
        color = QColorDialog.getColor(initial=self.main_window.colors[self.main_window.current_color_index],
                                    title="Select Pen Color")
        if color.isValid():
            self.main_window.colors[self.main_window.current_color_index] = color
            self.pen_color_button.setStyleSheet(f"background-color: {color.name()}")
            for vp in self.main_window.drawing_area.spline_manager.selected_paths:
                vp.pen_color = color
            self.main_window.drawing_area.update()

    def change_simplify_tolerance(self, value):
        self.main_window.default_simplify_tolerance = value
        for vp in self.main_window.drawing_area.spline_manager.selected_paths:
            vp.simplify_path(value)
            vp.generate_path_from_bspline()
        self.main_window.drawing_area.update()

    def change_smooth_strength(self, value):
        self.main_window.default_smooth_strength = value
        for vp in self.main_window.drawing_area.spline_manager.selected_paths:
            vp.smooth_path(value)
            vp.generate_path_from_bspline()
        self.main_window.drawing_area.update()

class DrawingArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAttribute(Qt.WA_StaticContents)
        self.setTabletTracking(True)

        # レイヤーの初期化
        initial_size = self.main_window.default_canvas_size
        self.raster_layer = QPixmap(initial_size)
        self.raster_layer.fill(Qt.transparent)

        self.vector_layer = QPixmap(initial_size)
        self.vector_layer.fill(Qt.transparent)

        self.current_layer = self.raster_layer  # 初期はペンツール用のラスターレイヤー

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

        self.stabilization_degree = self.main_window.stabilization_degree  # 手ブレ補正の度合い
        self.point_buffer = []  # 補正に使用するポイントのバッファ

        # Set the size of the DrawingArea widget
        self.setFixedSize(initial_size)

        # スプライン関連
        self.spline_manager = SplineManager(self)
        self.mode = 'draw'  # 'draw' or 'spline'
        self.setup_spline_manager_callbacks()  # コールバックを設定


    def set_stabilization_degree(self, degree):
        self.stabilization_degree = degree
        self.point_buffer = []  # バッファをリセット

    def set_image(self, pixmap):
        self.original_pixmap = pixmap
        new_size = self.original_pixmap.size()
        # Resize raster_layer and vector_layer to match the image size
        self.raster_layer = QPixmap(new_size)
        self.raster_layer.fill(Qt.transparent)
        self.vector_layer = QPixmap(new_size)
        self.vector_layer.fill(Qt.transparent)
        # Set the size of the DrawingArea widget
        self.setFixedSize(new_size)
        self.update()
        # Optionally resize the main window to fit the image
        self.main_window.resize(self.main_window.sizeHint())

    def resize_canvas(self, new_size):
        self.raster_layer = self.raster_layer.scaled(new_size)
        self.vector_layer = self.vector_layer.scaled(new_size)
        self.paint_layer = self.paint_layer.scaled(new_size)

        if self.original_pixmap:
            self.original_pixmap = self.original_pixmap.scaled(new_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        else:
            self.create_default_image(new_size)

        new_paint_layer = QPixmap(new_size)
        new_paint_layer.fill(Qt.transparent)
        painter = QPainter(new_paint_layer)
        painter.drawPixmap(0, 0, self.paint_layer)
        painter.end()
        self.paint_layer = new_paint_layer
        self.update_cursor()
        self.update()
        self.main_window.resize(new_size)

    def create_default_image(self, size):
        self.raster_layer = QPixmap(size)
        self.raster_layer.fill(Qt.transparent)
        self.vector_layer = QPixmap(size)
        self.vector_layer.fill(Qt.transparent)

        self.setFixedSize(size)
        self.update()

        # self.paint_layer = QPixmap(size)
        # self.paint_layer.fill(Qt.transparent)

        # self.update()

    def get_image_coordinates(self, pos):
        return pos
        # widget_size = self.size()
        # if self.original_pixmap:
        #     pixmap_size = self.original_pixmap.size()
        # else:
        #     pixmap_size = self.raster_layer.size()
        # if pixmap_size.width() == 0 or pixmap_size.height() == 0:
        #     return QPoint(-1, -1)
        # scale_x = pixmap_size.width() / widget_size.width()
        # scale_y = pixmap_size.height() / widget_size.height()
        # x = pos.x() * scale_x
        # y = pos.y() * scale_y
        # return QPoint(int(x), int(y))

    def resizeEvent(self, event):
        self.update()
        super().resizeEvent(event)

    def is_eraser_active(self):
        tablet_eraser = self.use_tablet and self.current_tablet_device == QTabletEvent.Eraser
        return self.eraser_key_pressed or self.right_button_pressed or tablet_eraser

    def mousePressEvent(self, event):
        if self.mode == 'spline':
            self.spline_manager.handle_mouse_press(event)
            # 操作開始時に状態を保存
            # if event.button() == Qt.LeftButton:
            #     self.push_undo_stack()
            self.update()
            return
        else:
            # 既存のペンツールの処理
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
                    self.right_button_pressed = True  # 右ボタンが押されたことを記録
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
                self.right_button_pressed = False  # 右ボタンが離されたことを記録
                self.update_cursor()

    def tabletEvent(self, event):
        if not self.use_tablet:
            event.ignore()
            return

            # 現在のモードが 'spline'（パスツール）の場合、ペンツールの描画を行わない
        if self.mode == 'spline':
        # パスツール用のタブレットイベント処理を行う場合は、ここに実装
        # 必要に応じて、self.spline_manager.handle_tablet_event(event) を実装して呼び出す
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
            # 消しゴムの場合、目的の領域を透明にする
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
            # 消しゴムの場合、目的の領域を透明にする
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

        # ラスターレイヤーの描画
        painter.drawPixmap(0, 0, self.raster_layer)

        # ベクターレイヤーの描画
        self.spline_manager.draw_paths(painter)

        # フリーハンドの軌跡の描画
        if self.spline_manager.freehand_path:
            pen = QPen(self.colors[self.current_color_index], self.pen_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawPath(self.spline_manager.freehand_path)

        painter.end()

    def keyPressEvent(self, event):
        key = event.key()
        toggle_tool_key = self.main_window.key_config.get("Toggle Tool", Qt.Key_Tab)
        if key == toggle_tool_key:
            # モード切替
            if self.mode == 'draw':
                self.mode = 'spline'
                self.current_layer = self.vector_layer
                print("Mode switched to spline")
            else:
                self.mode = 'draw'
                self.current_layer = self.raster_layer
                print("Mode switched to draw")
            return

        if self.mode == 'spline':
            clear_key = self.main_window.key_config.get("Clear", Qt.Key_Delete)
            if key == clear_key:
                if self.spline_manager.selected_paths:
                    # パス選択中にClearキーで削除
                    self.spline_manager.delete_selected_paths()
                    return
                else:
                    # 選択されたパスがない場合はイベントを親に伝播させる
                    event.ignore()
                    return
            # 他のキーイベント処理を追加可能

        # 色変更のキー処理
        if key == self.main_window.key_config.get("Next Color", Qt.Key_C):
            self.change_color(1)
            return
        elif key == self.main_window.key_config.get("Previous Color", Qt.Key_V):
            self.change_color(-1)
            return

        # アンドゥ・リドゥのキー処理
        if key == self.main_window.key_config.get("Undo"):
            self.undo()
            return
        elif key == self.main_window.key_config.get("Redo"):
            self.redo()
            return

        # 消しゴムモードの切替
        if key == self.main_window.key_config.get("Eraser Tool"):
            self.eraser_key_pressed = True
            self.update_cursor()
            return

        toggle_fill_key = self.main_window.key_config.get("Toggle Fill", Qt.Key_F)
        if key == toggle_fill_key:
            # 塗りつぶしの有効/無効を切り替える
            if self.mode == 'spline' and self.spline_manager.selected_paths:
                for path in self.spline_manager.selected_paths:
                    path.fill_enabled = not path.fill_enabled
                    # パスを再生成
                    path.generate_path_from_bspline()
                # ベクターレイヤーを更新
                self.update_vector_layer()
                self.update()
            else:
                # 選択されたパスがない場合、新しいパスに対してデフォルトの fill_enabled を設定
                self.spline_manager.default_fill_enabled = not self.spline_manager.default_fill_enabled
            return

        # その他のキーイベント処理
        event.ignore()

    # パスツールの操作時にスタックを保存するために、SplineManagerにコールバックを設定
    def setup_spline_manager_callbacks(self):
        # 必要に応じてスプラインマネージャーのコールバックを設定
        pass  # 現在のところ、特定のコールバックは必要ありません

    def keyReleaseEvent(self, event):
        key = event.key()
        if key == self.main_window.key_config.get("Eraser Tool"):
            self.eraser_key_pressed = False
            self.update_cursor()
            return
        # super().keyReleaseEvent(event) を以下に置き換え
        event.ignore()

    def update_cursor(self):
        cursor = self.create_cursor()
        self.setCursor(cursor)

    def create_cursor(self):
        if self.pen_size < 10:
            # カスタムのクロスカーソルを作成
            cursor_size = 15  # 適切なサイズを設定
            cursor_pixmap = QPixmap(cursor_size, cursor_size)
            cursor_pixmap.fill(Qt.transparent)
            painter = QPainter(cursor_pixmap)
            if self.is_eraser_active():
                pen_color = QColor(Qt.black)
            else:
                pen_color = self.colors[self.current_color_index]
            painter.setPen(QPen(pen_color, 1))
            # 縦線
            painter.drawLine(cursor_size // 2, 0, cursor_size // 2, cursor_size)
            # 横線
            painter.drawLine(0, cursor_size // 2, cursor_size, cursor_size // 2)
            painter.end()
            # ホットスポットをカーソルの中心に設定
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
            # ホットスポットをカーソルの中心に設定
            return QCursor(cursor_pixmap, cursor_size // 2, cursor_size // 2)

    def change_color(self, direction):
        self.current_color_index = (self.current_color_index + direction) % len(self.colors)
        self.main_window.current_color_index = self.current_color_index
        self.update_cursor()
        # パスツールの場合、選択されたパスの色を更新
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
        self.spline_manager.selected_paths.clear()  # 選択されたパスもクリア
        self.update_vector_layer()
        self.update()

    def clear_all_layers(self):
        self.push_undo_stack()
        self.raster_layer.fill(Qt.transparent)
        self.spline_manager.paths.clear()
        self.spline_manager.selected_paths.clear()
        self.update_vector_layer()
        self.update()

    def clear_raster_layer(self):
        self.undo_stack.append((self.raster_layer.copy(), self.vector_layer.copy()))
        self.redo_stack.clear()
        self.clear_paint_layer()

    def save_state(self):
        """現在の状態をスタックに保存する"""
        # レイヤーとスプラインマネージャーのコピーを保存
        state = {
            'raster_layer': self.raster_layer.copy(),
            'vector_layer': self.vector_layer.copy(),
            'spline_manager': self.spline_manager.copy()
        }
        self.undo_stack.append(state)
        if len(self.undo_stack) > self.max_stack_size:
            self.undo_stack.pop(0)
        # Redoスタックをクリア
        self.redo_stack.clear()

    def push_undo_stack(self):
        # SplineManagerのディープコピーを作成
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
        # 現在の状態を redo スタックに保存
        self.redo_stack.append({
            'raster_layer': self.raster_layer.copy(),
            'spline_manager': self.spline_manager.copy()
        })
        # 保存された状態を復元
        self.raster_layer = state['raster_layer']
        self.spline_manager = state['spline_manager']
        # drawing_area の参照を更新
        self.spline_manager.drawing_area = self
        # 各パスの drawing_area 参照を更新
        for path in self.spline_manager.paths:
            path.drawing_area = self
        self.update_vector_layer()
        self.update()

    def redo(self):
        if not self.redo_stack:
            return
        state = self.redo_stack.pop()
        # 現在の状態を undo スタックに保存
        self.undo_stack.append({
            'raster_layer': self.raster_layer.copy(),
            'spline_manager': self.spline_manager.copy()
        })
        # 保存された状態を復元
        self.raster_layer = state['raster_layer']
        self.spline_manager = state['spline_manager']
        # drawing_area の参照を更新
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
            # パスを描画
            painter.drawPath(path.path)
        painter.end()

    def load_next_image(self):
        if self.image_files:
            next_index = (self.current_image_index + 1) % len(self.image_files)
            self.load_image(next_index)

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

    def setup_path_tool_tab(self):
        layout = QVBoxLayout()

        # 単純化の度合い設定
        simplify_label = QLabel(self.main_window.translations.get('Default Simplification Tolerance', 'Simplification Tolerance'))
        self.simplify_slider = QSlider(Qt.Horizontal)
        self.simplify_slider.setMinimum(0)
        self.simplify_slider.setMaximum(10)
        self.simplify_slider.setValue(self.main_window.default_simplify_tolerance)
        simplify_value_label = QLabel(str(self.main_window.default_simplify_tolerance))
        self.simplify_slider.valueChanged.connect(lambda value: simplify_value_label.setText(str(value)))
        layout.addWidget(simplify_label)
        simplify_layout = QHBoxLayout()
        simplify_layout.addWidget(self.simplify_slider)
        simplify_layout.addWidget(simplify_value_label)
        layout.addLayout(simplify_layout)

        # 滑らかさの度合い設定
        smooth_label = QLabel(self.main_window.translations.get('Default Smoothing Strength', 'Smoothing Strength'))
        self.smooth_slider = QSlider(Qt.Horizontal)
        self.smooth_slider.setMinimum(0)
        self.smooth_slider.setMaximum(5)
        self.smooth_slider.setValue(self.main_window.default_smooth_strength)
        smooth_value_label = QLabel(str(self.main_window.default_smooth_strength))
        self.smooth_slider.valueChanged.connect(lambda value: smooth_value_label.setText(str(value)))
        layout.addWidget(smooth_label)
        smooth_layout = QHBoxLayout()
        smooth_layout.addWidget(self.smooth_slider)
        smooth_layout.addWidget(smooth_value_label)
        layout.addLayout(smooth_layout)

        # パスの当たり判定の設定
        hit_threshold_label = QLabel(self.main_window.translations.get('Path Hit Detection Threshold', 'Path Hit Detection Threshold (px)'))
        self.hit_threshold_slider = QSlider(Qt.Horizontal)
        self.hit_threshold_slider.setMinimum(1)
        self.hit_threshold_slider.setMaximum(200)
        self.hit_threshold_slider.setValue(int(self.main_window.path_hit_threshold * 10))
        hit_threshold_value_label = QLabel(f"{self.main_window.path_hit_threshold:.1f}")
        self.hit_threshold_slider.valueChanged.connect(lambda value: hit_threshold_value_label.setText(f"{value / 10:.1f}"))
        layout.addWidget(hit_threshold_label)
        hit_threshold_layout = QHBoxLayout()
        hit_threshold_layout.addWidget(self.hit_threshold_slider)
        hit_threshold_layout.addWidget(hit_threshold_value_label)
        layout.addLayout(hit_threshold_layout)

        self.path_tool_tab.setLayout(layout)

    def save_settings(self):
        # パスツール設定の保存
        self.main_window.default_simplify_tolerance = self.simplify_spinbox.value()
        self.main_window.default_smooth_strength = self.smooth_spinbox.value()
        self.main_window.path_hit_threshold = self.hit_threshold_spinbox.value()

        # スプラインマネージャーに適用
        self.main_window.drawing_area.spline_manager.hit_threshold = self.main_window.path_hit_threshold

        self.accept()

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
        layout.addWidget(QLabel(self.main_window.translations['Delete Mode']),row,0)
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

        self.basic_settings_tab.setLayout(layout)

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

        self.basic_settings_tab.setLayout(layout)

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

        key_actions = ["Undo", "Redo", "Clear", "Next Color", "Previous Color", "Save", "Next Image",
                    "Previous Image", "Eraser Tool", "Increase Pen Size", "Decrease Pen Size", "Merged Save",
                    "Toggle Tool", "Toggle Fill"]  # "Toggle Fill" を追加
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
            "Delete Control Point Modifier": Qt.AltModifier
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    paint_app = PaintApp()
    paint_app.show()
    sys.exit(app.exec_())
