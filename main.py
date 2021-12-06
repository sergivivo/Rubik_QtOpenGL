import sys

from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *

#from rubikview import RubikView
from rubikgl import RubikGL

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Menu bar
        self.menu = self.menuBar()
        game = self.menu.addMenu("Game")
        size = QAction("Size",parent=self)
        size.triggered.connect(self.openSetSizeWindow)
        game.addAction(size)

        # Rubik's cube view
        self.size = 3
        self.cube = RubikGL(parent=self)
        self.cube.initCube(self.size)

        # Timer and move counter
        self.timer = DigitalClock(parent=self)

        # Control buttons
        undo     = QPushButton("Undo",     parent=self)
        redo     = QPushButton("Redo",     parent=self)
        solve    = QPushButton("Solve",    parent=self)
        scramble = QPushButton("Scramble", parent=self)
        undo    .clicked.connect(self.undo    )
        redo    .clicked.connect(self.redo    )
        solve   .clicked.connect(self.solve   )
        scramble.clicked.connect(self.scramble)

        # Layouts
        control = QWidget(parent=self)
        hblayout = QHBoxLayout()
        hblayout.addWidget(undo    )
        hblayout.addWidget(redo    )
        hblayout.addWidget(solve   )
        hblayout.addWidget(scramble)
        control.setLayout(hblayout)

        cwidget = QWidget(parent=self)
        vblayout = QVBoxLayout()
        vblayout.addWidget(self.timer)
        vblayout.addWidget(self.cube)
        vblayout.addWidget(control)
        cwidget.setLayout(vblayout)

        self.setCentralWidget(cwidget)

    def openSetSizeWindow(self):
        self.settings = SetSizeWindow()
        self.settings.sendSize.connect(self.setSize)
        self.settings.show()

    @Slot(int)
    def setSize(self, size):
        self.cube.initCube(size)
        self.resize(self.sizeHint())

    def undo(self):
        self.cube.undo()

    def redo(self):
        self.cube.redo()

    def solve(self):
        self.cube.solve()
        self.timer.stopTimer()
        self.timer.resetTime()

    def scramble(self):
        self.cube.scramble()
        self.timer.startTimer()

    @Slot()
    def solved(self):
        pass

    def setLayers(self):
        pass

    @Slot(list)
    def getLayers(self, layers):
        for i in range(len(layers)):
            pass

class MovesCounter(QLCDNumber):
    def __init__(self, parent=None):
        super(MovesCounter, self).__init__(parent)

        self.setSegmentStyle(QLCDNumber.Filled)


class DigitalClock(QLCDNumber):
    def __init__(self, parent=None):
        super(DigitalClock, self).__init__(parent)

        self.setSegmentStyle(QLCDNumber.Filled)
        self.setDigitCount(7)
        self.setMinimumSize(100,50)

        self.time = QTime()
        self.time.restart()
        self.timer = QTimer(self)

        self.displayTime()

    def stopTimer(self):
        self.timer.stop()

    def startTimer(self):
        self.connect(self.timer, SIGNAL('timeout()'), self.displayTime)
        self.time.start()
        self.timer.start(10)

    def resetTime(self):
        self.time.restart()
        self.displayTime()

    def displayTime(self):
        text = str(self.time.elapsed()).zfill(7)[:-1]
        formated = text[:-2] + '.' + text[-2:]
        self.display(formated)

class SetSizeWindow(QDialog):
    sendSize = Signal(int)
    def __init__(self, parent=None):
        super(SetSizeWindow, self).__init__(parent)

        twidget = QWidget(parent=self)
        label = QLabel("Size:", parent=self)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.spbox = QSpinBox(parent=self)
        self.spbox.setRange(2,100)
        self.spbox.setValue(3)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        hblayout = QHBoxLayout()
        hblayout.addWidget(label)
        hblayout.addWidget(self.spbox)
        twidget.setLayout(hblayout)

        vblayout = QVBoxLayout()
        vblayout.addWidget(twidget)
        vblayout.addWidget(buttonBox)

        self.setLayout(vblayout)

    def accept(self):
        self.sendSize.emit(self.spbox.value())
        self.close()

if __name__ == "__main__":
    app = QApplication([])

    mainwindow = MainWindow()
    mainwindow.show()

    sys.exit(app.exec_())
