import sys

from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *

from rubik import Rubik, Cubie

class Sticker(QGraphicsPolygonItem):
    colors = {
            'while' : QBrush(QColor(255,255,255,255)),
            'yellow': QBrush(QColor(255,255,0  ,255)),
            'blue'  : QBrush(QColor(0  ,95 ,255,255)),
            'green' : QBrush(QColor(0  ,255,0  ,255)),
            'red'   : QBrush(QColor(255,0  ,0  ,255)),
            'orange': QBrush(QColor(255,143,0  ,255))}
    initColors = {
            'up'   : 'while' ,
            'down' : 'yellow',
            'right': 'blue'  ,
            'left' : 'green' ,
            'front': 'red'   ,
            'back' : 'orange'}
    def __init__(self, faceSize, face, nlayers, vector, parent=None):
        super(Sticker, self).__init__()
        self.faceSize = faceSize
        self.nlayers = nlayers
        self.size = faceSize / nlayers
        self.face = face
        self.notVisible = nlayers-1 in vector
        self.vector = vector
        self._initFacePolygon(face)

    def _initFacePolygon(self, face):
        polygon = QPolygonF()
        fs = self.faceSize
        s = self.size
        fa = self.faceSize*3**0.5/2
        a = s*3**0.5/2
        i, j, k = self.vector

        if face in ('up','down'):
            polygon.append([QPointF(0,0),QPointF( a,-s/2),QPointF( 0,-s  ),QPointF(-a,-s/2)])
            if face == 'down' and j == self.nlayers-1:
                polygon.translate(QPointF(0, fs+s))
        elif face in ('right','left'):
            polygon.append([QPointF(0,0),QPointF( 0, s  ),QPointF( a, s/2),QPointF( a,-s/2)])
            if face == 'left' and i == self.nlayers-1:
                polygon.translate(QPointF(-(fa+a), -(fs+s)/2))
        elif face in ('front','back'):
            polygon.append([QPointF(0,0),QPointF(-a,-s/2),QPointF(-a, s/2),QPointF( 0, s  )])
            if face == 'back' and k == self.nlayers-1:
                polygon.translate(QPointF(fa+a, -(fs+s)/2))

        polygon.translate(QPointF(a*(k-i),s*(j-(i+k)/2)))

        self.setPolygon(polygon)
        self.setBrush(self.colors[self.initColors[self.face]])

    def getFace(self):
        return self.face

    def setColor(self, face):
        self.setBrush(self.colors[self.initColors[face]])

class RubikView(QGraphicsView):
    faceSize = 160
    apothem = faceSize*3**0.5/2
    margin = 20
    faces = ('right','left','up','down','front','back')
    def __init__(self, parent=None):
        super(RubikView, self).__init__()

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.Antialiasing)

        self.scene = QGraphicsScene(parent=self)
        self.setScene(self.scene)
        self.scene.setBackgroundBrush(QBrush(QColor(100,150,255,255)))

    def initCube(self, size):
        self.scene.clear()

        # Init cube object
        self.size = size
        self.rubik = Rubik(size)
        self.layers = [True] + [False] * (size-1)

        self.cubies = [[[{} for i in range(size)] for j in range(size)] for k in range(size)]
        self.pressing = False
        for i in list(range(size))[::-1]:
            for j in list(range(size))[::-1]:
                for k in list(range(size))[::-1]:
                    self.cubies[i][j][k]['left' ] = Sticker(self.faceSize, 'left',  size, (i,j,k), parent=self)
                    self.cubies[i][j][k]['down' ] = Sticker(self.faceSize, 'down',  size, (i,j,k), parent=self)
                    self.cubies[i][j][k]['back' ] = Sticker(self.faceSize, 'back',  size, (i,j,k), parent=self)
                    self.cubies[i][j][k]['right'] = Sticker(self.faceSize, 'right', size, (i,j,k), parent=self)
                    self.cubies[i][j][k]['up'   ] = Sticker(self.faceSize, 'up',    size, (i,j,k), parent=self)
                    self.cubies[i][j][k]['front'] = Sticker(self.faceSize, 'front', size, (i,j,k), parent=self)
                    self.scene.addItem(self.cubies[i][j][k]['left' ])
                    self.scene.addItem(self.cubies[i][j][k]['down' ])
                    self.scene.addItem(self.cubies[i][j][k]['back' ])
                    self.scene.addItem(self.cubies[i][j][k]['right'])
                    self.scene.addItem(self.cubies[i][j][k]['up'   ])
                    self.scene.addItem(self.cubies[i][j][k]['front'])
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def _updateStickers(self):
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    for origin in self.faces:
                        self.cubies[i][j][k][origin].setColor(self.rubik.getFace(origin, self.rubik.cube[i][j][k]))

    def mouseReleaseEvent(self, event):
        pos = self.mapToScene(event.pos())
        item = self.scene.itemAt(pos, QTransform())

        face = item.getFace()
        button = event.button()
        rotation = -1
        if button == Qt.LeftButton: rotation = 0
        elif button == Qt.RightButton: rotation = 1

        if rotation != -1:
            if self.pressing:
                self.rubik.rotateCubeRelativeToFace(face, rotation)
            else:
                self.rubik.moveRelativeToFace(face, self.layers, rotation)
            self._updateStickers()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Shift: self.pressing = True

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Shift: self.pressing = False

    def wheelEvent(self, event):
        if event.delta() > 0:
            if not self.layers[-1]: self.layers = [False] + self.layers[:-1]
        else:
            if not self.layers[0]: self.layers = self.layers[1:] + [False]

    def resizeEvent(self, event):
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

if __name__ == "__main__":
    app = QApplication([])
    window = RubikView()
    window.show()
    sys.exit(app.exec_())
