# spline_manager.py

import math
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtWidgets import QApplication
from vector_path import VectorPath


class SplineManager:
    def __init__(self, drawing_area, control_point_size=10, scaling_sensitivity=0.002, hit_threshold=2.0):
        self.drawing_area = drawing_area
        self.paths = []
        self.selected_paths = []
        self.current_path = None
        self.hit_threshold = self.drawing_area.main_window.path_hit_threshold
        self.is_drawing = False
        self.current_scribble_points = []
        self.control_point_size = control_point_size
        self.scaling_sensitivity = scaling_sensitivity

        self.mode = 'drawing'  # <-- モードの追加

        self.on_change = None

        self.is_scaling = False
        self.scaling_start_pos = None
        self.scaling_mode = None
        self.proportional_scaling = True

        self.is_moving = False
        self.is_moving_control_point = False
        self.is_moving_path = False
        self.selected_control_point = None
        self.last_mouse_pos = None

        self.add_point_modifier = self.drawing_area.main_window.key_config.get("Add Control Point Modifier", Qt.ControlModifier)
        self.delete_point_modifier = self.drawing_area.main_window.key_config.get("Delete Control Point Modifier", Qt.AltModifier)
        self.rotate_modifier = Qt.ControlModifier
        self.scale_modifier = Qt.AltModifier

        self.default_fill_enabled = False
        self.freehand_path = None

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
            self.drawing_area.push_undo_stack()
            self.drawing_area.update_vector_layer()
            self.drawing_area.update()

    def handle_mouse_press(self, event):
        pos = self.drawing_area.get_image_coordinates(event.pos())
        modifiers = QApplication.keyboardModifiers()
        
        if event.button() == Qt.LeftButton:
            if self.mode == 'selection':
                # 選択モードの処理
                for path in reversed(self.paths):
                    index = path.get_control_point_at(pos, self.control_point_size)
                    if index is not None:
                        self.deselect_all_paths()
                        self.selected_paths = [path]
                        path.selected = True
                        self.selected_control_point = (path, index)
                        self.is_moving_control_point = True
                        self.drawing_area.push_undo_stack()
                        self.drawing_area.update()
                        return

                for path in reversed(self.paths):
                    if path.contains_point(pos, self.hit_threshold):
                        self.deselect_all_paths()
                        self.selected_paths = [path]
                        path.selected = True
                        self.is_moving_path = True
                        self.drawing_area.push_undo_stack()
                        self.drawing_area.update()
                        return

                if self.selected_paths:
                    clicked_inside_selection_rect = False
                    for path in self.selected_paths:
                        if path.get_selection_rect().contains(pos):
                            clicked_inside_selection_rect = True
                            break
                    if clicked_inside_selection_rect:
                        self.is_moving_path = True
                        self.drawing_area.push_undo_stack()
                        self.drawing_area.update()
                        return
                    else:
                        self.deselect_all_paths()
                        self.drawing_area.update()
                        return
            elif self.mode == 'drawing':
                # 描画モードの処理
                self.current_path = VectorPath(self.drawing_area)
                self.current_path.pen_color = self.drawing_area.colors[self.drawing_area.current_color_index]
                self.current_path.pen_width = self.drawing_area.pen_size
                self.current_path.fill_enabled = self.default_fill_enabled
                self.current_path.fill_color = self.drawing_area.colors[self.drawing_area.current_color_index]
                self.current_path.add_point(pos)
                self.is_drawing = True
                return
        # self.last_mouse_pos = pos
        # if event.button() == Qt.LeftButton:
        #     if modifiers & self.add_point_modifier:
        #         for path in self.paths:
        #             if path.contains_point(pos, self.hit_threshold):
        #                 self.drawing_area.push_undo_stack()
        #                 insertion_index = path.find_insertion_index(pos)
        #                 path.insert_control_point(insertion_index, pos)
        #                 self.drawing_area.update_vector_layer()
        #                 self.drawing_area.update()
        #                 break
        #         return
        #     elif modifiers & self.delete_point_modifier:
        #         for path in self.paths:
        #             index = path.get_control_point_at(pos, self.control_point_size)
        #             if index is not None:
        #                 self.drawing_area.push_undo_stack()
        #                 path.delete_control_point(index)
        #                 self.drawing_area.update_vector_layer()
        #                 self.drawing_area.update()
        #                 break
        #         return
        #     else:
        #         for path in reversed(self.paths):
        #             index = path.get_control_point_at(pos, self.control_point_size)
        #             if index is not None:
        #                 self.deselect_all_paths()
        #                 self.selected_paths = [path]
        #                 path.selected = True
        #                 self.selected_control_point = (path, index)
        #                 self.is_moving_control_point = True
        #                 self.drawing_area.push_undo_stack()
        #                 self.drawing_area.update()
        #                 return

        #         for path in reversed(self.paths):
        #             if path.contains_point(pos, self.hit_threshold):
        #                 self.deselect_all_paths()
        #                 self.selected_paths = [path]
        #                 path.selected = True
        #                 self.is_moving_path = True
        #                 self.drawing_area.push_undo_stack()
        #                 self.drawing_area.update()
        #                 return

        #         if self.selected_paths:
        #             clicked_inside_selection_rect = False
        #             for path in self.selected_paths:
        #                 if path.get_selection_rect().contains(pos):
        #                     clicked_inside_selection_rect = True
        #                     break
        #             if clicked_inside_selection_rect:
        #                 self.is_moving_path = True
        #                 self.drawing_area.push_undo_stack()
        #                 self.drawing_area.update()
        #                 return
        #             else:
        #                 self.deselect_all_paths()
        #                 self.drawing_area.update()
        #                 return

        #         self.current_path = VectorPath(self.drawing_area)
        #         self.current_path.pen_color = self.drawing_area.colors[self.drawing_area.current_color_index]
        #         self.current_path.pen_width = self.drawing_area.pen_size
        #         self.current_path.fill_enabled = self.default_fill_enabled
        #         self.current_path.fill_color = self.drawing_area.colors[self.drawing_area.current_color_index]
        #         self.current_path.add_point(pos)
        #         self.is_drawing = True
        #         return

    def handle_mouse_move(self, event):
        pos = self.drawing_area.get_image_coordinates(event.pos())
        if self.last_mouse_pos is None:
            self.last_mouse_pos = pos

        delta = pos - self.last_mouse_pos

        if self.mode == 'drawing':
            if self.is_drawing and self.current_path is not None:
                self.current_path.add_point(pos)
                self.drawing_area.update_vector_layer()
                self.drawing_area.update()
                self.last_mouse_pos = pos
                return
        elif self.mode == 'selection':
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
        self.last_mouse_pos = None

        if event.button() == Qt.LeftButton:
            if self.mode == 'drawing':
                if self.is_drawing:
                    if self.current_path:
                        self.current_path.finalize()
                        self.paths.append(self.current_path)
                        self.current_path = None
                        self.drawing_area.push_undo_stack()
                        self.drawing_area.update_vector_layer()
                        self.drawing_area.update()
                    self.is_drawing = False
            elif self.mode == 'selection':
                if self.is_moving_control_point:
                    self.is_moving_control_point = False
                    self.selected_control_point = None

                if self.is_moving_path:
                    self.is_moving_path = False

    def deselect_all_paths(self):
        for path in self.paths:
            path.selected = False
        self.selected_paths = []

    def draw_paths(self, painter):
        for vp in self.paths:
            vp.draw(painter, self.control_point_size)
        if self.is_drawing and self.current_path:
            self.current_path.draw(painter, self.control_point_size)

    def copy(self):
        new_manager = SplineManager(self.drawing_area)
        new_manager.paths = [path.copy() for path in self.paths]
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
        return new_manager
