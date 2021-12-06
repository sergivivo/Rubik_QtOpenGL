import sys
import numpy as np

from PySide2.QtCore    import *
from PySide2.QtGui     import *
from PySide2.QtWidgets import *
from PySide2.QtOpenGL  import *

from OpenGL.GL  import *
from OpenGL.GLU import gluPickMatrix, gluUnProject
from rubik import Rubik

class RubikGL(QGLWidget):
    colors = {
            'white' : b'\xff\xff\xff\xff',
            'yellow': b'\xff\xff\x00\xff',
            'blue'  : b'\x00\x5f\xff\xff',
            'green' : b'\x00\xff\x00\xff',
            'red'   : b'\xff\x00\x00\xff',
            'orange': b'\xff\x8f\x00\xff'}

    initColors = {
            'up'   : 'white' ,
            'down' : 'yellow',
            'right': 'blue'  ,
            'left' : 'green' ,
            'front': 'red'   ,
            'back' : 'orange'}

    vertices = (
        ( 1,  1,  1), # 0
        ( 1,  1, -1), # 1
        ( 1, -1,  1), # 2
        ( 1, -1, -1), # 3
        (-1,  1,  1), # 4
        (-1,  1, -1), # 5
        (-1, -1,  1), # 6
        (-1, -1, -1)) # 7

    edges = (
        (2,3), (3,1), (1,0), (0,2),
        (0,4), (1,5), (2,6), (3,7),
        (4,5), (5,7), (7,6), (6,4))

    faces = ('right','left','up','down','front','back')

    facedict = {
        'right': (2,3,1,0), # Right
        'left' : (4,5,7,6), # Left
        'up'   : (0,1,5,4), # Up
        'down' : (6,7,3,2), # Down
        'front': (4,6,2,0), # Front
        'back' : (1,3,7,5)} # Back


    fps = 60

    def __init__(self,parent=None):
        super(RubikGL, self).__init__(parent)

        self.setMinimumSize(500,500)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.xRot = 0
        self.yRot = 0
        self.zRot = 0
        self.rotDuration = 0.2

        self.initPos = QPointF()
        self.lastPos = QPointF()

        self.picking = False
        self.shrink = 1

    def initCube(self, size):
        self.size = size
        self.cube = Rubik(size)

        self.layers = [True] + [False] * (size-1)
        self.beginGame = False

        self.rotating = 0
        self.repaint()

    def initializeGL(self):
        self.object = self.makeObject()
        self.hitbox = self.makeHitbox()
        glMatrixMode(GL_MODELVIEW)
        self.modelMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)

        glShadeModel(GL_FLAT) # Flat color, no lighting
        glEnable(GL_DEPTH_TEST) # Closer polygons paint over further
        glEnable(GL_CULL_FACE) # Don't render polygons facing oposite

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

        glPushMatrix()
        # {

        glLoadIdentity()

        glRotated(self.xRot * 0.3, 1.0, 0.0, 0.0)
        glRotated(self.yRot * 0.3, 0.0, 1.0, 0.0)
        self.xRot = 0
        self.yRot = 0
        self.zRot = 0

        glMultMatrixf(self.modelMatrix)
        self.modelMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)

        glLoadIdentity()
        glTranslated(0.0, 0.0, -10.0)

        glMultMatrixf(self.modelMatrix)

        self.drawCubies()

        # }
        glPopMatrix()

    def drawCubies(self):
        if self.picking:
            glCallList(self.hitbox)
        else:
            lst = np.linspace(1-1/self.size, -1+1/self.size, self.size)

            for i in range(self.size):
                for j in range(self.size):
                    for k in range(self.size):
                        glPushMatrix()

                        # Change angle while rotating layers
                        if 0 < self.rotating < self.rotNframes:
                            if   self.axis == 0 and self.mvlayers[i]:
                                glRotated(self.sign*self.rotFrames[self.rotating], 1.0, 0.0, 0.0)
                            elif self.axis == 1 and self.mvlayers[j]:
                                glRotated(self.sign*self.rotFrames[self.rotating], 0.0, 1.0, 0.0)
                            elif self.axis == 2 and self.mvlayers[k]:
                                glRotated(self.sign*self.rotFrames[self.rotating], 0.0, 0.0, 1.0)

                        glTranslated(lst[i],lst[j],lst[k])
                        glScaled(self.shrink/self.size, self.shrink/self.size, self.shrink/self.size)

                        # Aplies the inverse matrix representing the orientation of the cubie
                        glMultMatrixf(self.cube.getCubie(i,j,k).getGLInverseMatrix())

                        glCallList(self.object)

                        glPopMatrix()

    def rotate(self):
        self.rotNframes = int(self.fps*self.rotDuration)
        self.rotFrames = list(map(lambda x: (1-np.cos(x))*90/2, np.linspace(0, np.pi, self.rotNframes)))
        self.rotating = 1
        while self.rotating < self.rotNframes:
            self._delay(1000/self.fps)
            self.repaint()
            self.rotating += 1
        self.rotating = 0

    def resizeGL(self, width, height):
        side = min(width, height)
        glViewport(int((width - side) / 2), int((height - side) / 2), side, side)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glFrustum(-1.0, 1.0, -1.0, 1.0, 4.0, 15.0)
        glMatrixMode(GL_MODELVIEW)

    def mousePressEvent(self, event):
        self.initPos = event.pos()
        self.lastPos = event.pos()

    def mouseMoveEvent(self,event):
        self.xRot = 0
        self.yRot = 0
        self.zRoy = 0

        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()

        if event.buttons() in (Qt.LeftButton, Qt.RightButton):
            if event.buttons() == Qt.LeftButton:
                self.xRot = dy
                self.yRot = dx
            if event.buttons() == Qt.RightButton:
                self.zRot = dx + dy
            self.repaint()

        self.lastPos = event.pos()

    def mouseReleaseEvent(self, event):
        button = event.button()
        if self.rotating == 0 and button in (Qt.LeftButton, Qt.RightButton):
            dif = event.pos() - self.initPos
            if -5 < dif.x() < 5 and -5 < dif.y() < 5:
                posx = event.pos().x()
                posy = event.pos().y()
                face = self.pick(posx,posy)
                if face:
                    face = self.faces[face[0]]
                    if   button == Qt.LeftButton : rotDir = 0
                    elif button == Qt.RightButton: rotDir = 1

                    if face in self.faces[::2]:
                        self.sign =  1 if rotDir == 0 else -1
                        self.mvlayers = self.layers[:]
                    else:
                        self.sign = -1 if rotDir == 0 else  1
                        self.mvlayers = self.layers[::-1]
                    self.axis = int(self.faces.index(face) / 2)

                    self.rotate()
                    self.cube.moveRelativeToFace(face, self.layers, rotDir)

                    self.repaint()
                    self.checkSolved()

    def pick(self, x, y):
        BUFSIZE = 128
        viewport = glGetIntegerv(GL_VIEWPORT)
        projection = glGetFloatv(GL_PROJECTION_MATRIX)
        glSelectBuffer(BUFSIZE)

        glRenderMode(GL_SELECT)
        glInitNames()
        glPushName(0)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()

        # Create a 5x5 pixel picking region near cursor location.
        gluPickMatrix(x, (viewport[3] - y), 5, 5, viewport)
        glMultMatrixd(projection)
        glMatrixMode(GL_MODELVIEW)

        glPushMatrix()
        self.picking = True
        self.repaint()
        self.picking = False
        glPopMatrix()

        hits = glRenderMode(GL_RENDER)
        nearest = []
        minZ = None
        for hit in hits:
            if hit.names and (minZ is None or hit.near < minZ):
                nearest = hit.names
                minZ = hit.near

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

        glMatrixMode(GL_MODELVIEW)

        return nearest

    def checkSolved(self):
        if self.beginGame and self.cube.checkSolved():
            self.beginGame = False
            d = QMessageBox(parent=self)
            d.setWindowTitle("Congratulations!")
            d.setText("You solved the cube using {} movements.".format(self.cube.moves))
            d.show()

    def wheelEvent(self, event):
        if self.rotating == 0:
            if event.delta() > 0:
                if not self.layers[-1]: self.layers = [False] + self.layers[:-1]
            else:
                if not self.layers[0]: self.layers = self.layers[1:] + [False]

    def setLayers(self, layers):
        self.layers = layers

    def scramble(self):
        self.cube.scramble(self.size**3)
        self.beginGame = True
        self.repaint()

    def undo(self):
        self.cube.undo()
        self.repaint()

    def solve(self):
        self.initCube(self.size)

    def redo(self):
        self.cube.redo()
        self.repaint()

    def makeObject(self):
        genList = glGenLists(1)
        glNewList(genList, GL_COMPILE)

        i = 0
        for key, face in self.facedict.items():
            glBegin(GL_POLYGON)

            for vertex in face:
                glColor4ubv(self.colors[self.initColors[key]])
                glVertex3fv(self.vertices[vertex])

            glEnd()

            i+=1

        for edge in self.edges:
            glLineWidth(2.0)
            glBegin(GL_LINES)

            for vertex in edge:
                glColor3f(0,0,0)
                glVertex3fv(self.vertices[vertex])

            glEnd()

        glEndList()
        return genList

    def makeHitbox(self):
        genList = glGenLists(1)
        glNewList(genList, GL_COMPILE)
        i = 0
        for key, face in self.facedict.items():
            glLoadName(i)
            glBegin(GL_POLYGON)
            for vertex in face:
                glColor4f(0,0,0,0)
                glVertex3fv(self.vertices[vertex])
            glEnd()
            i+=1
        glEndList()
        return genList

    def _delay(self, milliseconds):
        loop = QEventLoop(self)
        t = QTimer(self)
        t.timeout.connect(loop.exit)
        t.start(milliseconds)
        loop.exec_()

if __name__ == "__main__":
    app = QApplication([])

    window = RubikGL()
    window.show()

    sys.exit(app.exec_())
