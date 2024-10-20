from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QSlider, QPushButton, QColorDialog
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

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
