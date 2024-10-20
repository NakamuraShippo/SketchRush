import sys
from PyQt5.QtWidgets import QApplication
from paint_app import PaintApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    paint_app = PaintApp()
    paint_app.show()
    sys.exit(app.exec_())