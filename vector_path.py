# vector_path.py

import math
import numpy as np
from scipy.interpolate import splprep, splev
from shapely.geometry import LineString
from PyQt5.QtGui import QPainterPath, QPainter, QPen, QColor, QBrush, QPainterPathStroker
from PyQt5.QtCore import QPointF, QRectF, Qt


class VectorPath:
    def __init__(self, drawing_area):
        self.points = []
        self.drawing_area = drawing_area
        self.control_points = []
        self.qt_path = QPainterPath()
        self.pen_color = drawing_area.colors[drawing_area.current_color_index]
        self.pen_width = drawing_area.pen_size
        self.fill_color = QColor(255, 255, 255)
        self.fill_enabled = False
        self.spline_control_points = []
        self.path = QPainterPath()
        self.selected = False
        self.is_closed = False

    def add_point(self, point):
        self.points.append(point)
        if len(self.points) == 1:
            self.path.moveTo(point)
        else:
            self.path.lineTo(point)

    def generate_path_from_bspline(self):
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
            self.path.moveTo(points[0])
            for point in points[1:]:
                self.path.lineTo(point)

        if self.fill_enabled:
            self.path.closeSubpath()

    def draw(self, painter, control_point_size=0):
        if not self.path.isEmpty():
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)

            if self.fill_enabled:
                brush = QBrush(self.fill_color)
                painter.setBrush(brush)
                painter.drawPath(self.path)
            else:
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(self.path)

            if self.selected:
                self.draw_selection_rectangle(painter)

            if self.selected and control_point_size > 0:
                self.draw_control_points(painter, control_point_size)

    def draw_control_points(self, painter: QPainter, control_point_size: int):
        painter.setBrush(QColor(255, 0, 0))
        painter.setPen(Qt.NoPen)
        for cp in self.spline_control_points:
            rect = QRectF(cp[0] - control_point_size / 2, cp[1] - control_point_size / 2,
                          control_point_size, control_point_size)
            painter.drawRect(rect)

    def draw_selection_rectangle(self, painter: QPainter):
        bounding_rect = self.path.boundingRect().adjusted(-10, -10, 10, 10)

        pen = QPen(QColor(0, 120, 215), 1, Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(bounding_rect)

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
        stroker = QPainterPathStroker()
        stroker.setWidth(hit_threshold * 2)
        stroked_path = stroker.createStroke(self.path)
        return stroked_path.contains(pos)

    def find_insertion_index(self, click_pos: QPointF) -> int:
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
                insertion_index = i + 1
        return insertion_index

    @staticmethod
    def point_to_segment_distance(p: QPointF, p1: QPointF, p2: QPointF) -> float:
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
        x = [p.x() for p in points]
        y = [p.y() for p in points]
        tck, u = splprep([x, y], s=0)
        unew = np.linspace(0, 1.0, num=100)
        out = splev(unew, tck)
        bspline_points = [QPointF(out[0][i], out[1][i]) for i in range(len(out[0]))]
        return bspline_points

    def finalize(self):
        self.spline_control_points = [(p.x(), p.y()) for p in self.points]
        self.smooth_and_simplify()
        self.generate_path_from_bspline()

    def smooth_and_simplify(self):
        simplify_tolerance = self.drawing_area.main_window.default_simplify_tolerance
        smooth_strength = self.drawing_area.main_window.default_smooth_strength

        self.simplify_path(simplify_tolerance)
        self.smooth_path(smooth_strength)

    def simplify_path(self, tolerance):
        if tolerance <= 0:
            return

        if len(self.spline_control_points) < 2:
            return

        coords = [(x, y) for x, y in self.spline_control_points]
        line = LineString(coords)
        simplified_line = line.simplify(tolerance, preserve_topology=False)
        self.spline_control_points = list(simplified_line.coords)

    def smooth_path(self, strength):
        if strength <= 0:
            return

        if len(self.spline_control_points) < 3:
            return

        coords = np.array(self.spline_control_points)
        smoothed_coords = coords.copy()

        for _ in range(strength):
            smoothed_coords[1:-1] = (smoothed_coords[:-2] + smoothed_coords[1:-1] + smoothed_coords[2:]) / 3

        self.spline_control_points = [tuple(coord) for coord in smoothed_coords]

    def copy(self):
        new_path = VectorPath(self.drawing_area)
        new_path.control_points = list(self.control_points)
        new_path.spline_control_points = list(self.spline_control_points)
        new_path.pen_color = QColor(self.pen_color)
        new_path.pen_width = self.pen_width
        new_path.fill_color = QColor(self.fill_color)
        new_path.fill_enabled = self.fill_enabled
        new_path.is_closed = self.is_closed
        new_path.path = QPainterPath(self.path)
        new_path.qt_path = QPainterPath(self.qt_path)
        return new_path

    def move_by(self, delta: QPointF):
        self.spline_control_points = [
            (x + delta.x(), y + delta.y()) for x, y in self.spline_control_points
        ]
        self.generate_path_from_bspline()

    def path_to_svg_d(self):
        elements = []
        i = 0
        while i < self.path.elementCount():
            elem = self.path.elementAt(i)
            if elem.type == QPainterPath.ElementType.MoveToElement:
                elements.append(f"M {elem.x} {elem.y}")
            elif elem.type == QPainterPath.ElementType.LineToElement:
                elements.append(f"L {elem.x} {elem.y}")
            elif elem.type == QPainterPath.ElementType.CurveToElement:
                cp1 = elem
                i += 1
                cp2 = self.path.elementAt(i)
                i += 1
                end = self.path.elementAt(i)
                elements.append(f"C {cp1.x} {cp1.y} {cp2.x} {cp2.y} {end.x} {end.y}")
            elif elem.type == QPainterPath.ElementType.CurveToDataElement:
                pass
            i += 1
        return ' '.join(elements)

    def insert_control_point(self, index: int, pos: QPointF):
        self.spline_control_points.insert(index, (pos.x(), pos.y()))
        self.generate_path_from_bspline()

    def delete_control_point(self, index: int):
        if len(self.spline_control_points) > 2:
            del self.spline_control_points[index]
            self.generate_path_from_bspline()
