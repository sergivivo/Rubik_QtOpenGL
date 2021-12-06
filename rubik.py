import numpy as np
import random as rnd

class Cubie:
    def __init__(self):
        self.x = np.array([1,0,0])
        self.y = np.array([0,1,0])
        self.z = np.array([0,0,1])

    def getX(self):
        return self.x

    def getY(self):
        return self.y

    def getZ(self):
        return self.z

    def rotate(self, axis, rotation):
        rmatrix = np.identity(3)
        ch = [[0,-1],[ 1,0]] if (rotation + axis) % 2 == 0 else [[0, 1],[-1,0]]
        for i in range(2):
            for j in range(2):
                iinc = i
                jinc = j
                if i >= axis:
                    iinc += 1
                if j >= axis:
                    jinc += 1
                rmatrix[iinc,jinc] = ch[i][j]
        self.x = np.matmul(rmatrix, self.x)
        self.y = np.matmul(rmatrix, self.y)
        self.z = np.matmul(rmatrix, self.z)

    def multiplyMatrix(self, matrix):
        self.x = np.matmul(matrix, self.x)
        self.y = np.matmul(matrix, self.y)
        self.z = np.matmul(matrix, self.z)

    def getMatrix(self):
        return np.concatenate((self.x, self.y, self.z)).reshape((3,3)).transpose()

    def getGLInverseMatrix(self):
        f = np.concatenate((self.x, self.y, self.z)).reshape((3,3))
        n = np.identity(4)
        n[:3,:3] = f
        return n.flatten()

    def __repr__(self):
        return "{}{}{}".format(self.x, self.y, self.z)

class Rubik:
    vmapping = {'up': np.array([0,1,0]), 'down': np.array([0,-1,0]),
            'right': np.array([1,0,0]), 'left': np.array([-1,0,0]),
            'front': np.array([0,0,1]), 'back': np.array([0,0,-1])}
    HISTORYSIZE = 20
    def __init__(self, size):
        self.size = size
        self.orientation = Cubie()
        self.cube = np.array([[[Cubie() for i in range(size)]
                for j in range(size)] for k in range(size)])

        self.moves = 0
        self.hidx = 0
        self.history = []

    def move(self, axis, layers, rotation, register=True):
        for i in range(self.size):
            if layers[i]:
                self._rotateSlice(axis, i, rotation)
                self._rotateCubies(axis, i, rotation)

        if register:
            self.moves += 1

            # Move after undo
            if self.hidx < len(self.history):
                self.history = self.history[:self.hidx]

            # Buffer is full
            if self.hidx == self.HISTORYSIZE:
                self.history.pop(0)
            else:
                self.hidx += 1
            self.history.append((axis, layers, rotation))

    def rotateCube(self, axis, rotation):
        axes = [i for i in range(3) if i != axis]
        if (axis + rotation) % 2 == 1: axes.reverse()
        self.cube = np.rot90(self.cube, axes=axes)
        np.vectorize(lambda c: c.rotate(axis,rotation), [Cubie])(self.cube)

    def rotateCubeRelativeToFace(self, face, rotation):
        axis, sign = self.getAxisSign(face, self.orientation)
        if sign < 0:
            rotation = 1 if rotation == 0 else 0
        self.rotateCube(axis, rotation)

    def _rotateSlice(self, axis, layer, rotation):
        if (axis + rotation) % 2 == 0: axes = (0,1)
        else: axes = (1,0)

        if axis == 0:
            self.cube[layer,:,:] = np.rot90(np.copy(self.cube[layer,:,:]),
                    axes=axes)
        elif axis == 1:
            self.cube[:,layer,:] = np.rot90(np.copy(self.cube[:,layer,:]),
                    axes=axes)
        elif axis == 2:
            self.cube[:,:,layer] = np.rot90(np.copy(self.cube[:,:,layer]),
                    axes=axes)

    def _rotateCubies(self, axis, layer, rotation):
        function = np.vectorize(lambda c: c.rotate(axis,rotation), [Cubie])
        if axis == 0:
            function(self.cube[layer,:,:])
        elif axis == 1:
            function(self.cube[:,layer,:])
        elif axis == 2:
            function(self.cube[:,:,layer])

    def checkSolved(self):
        reference = self.cube[0,0,0]
        compareX = np.vectorize(lambda e: (e.getX()==reference.getX()).all(),
                [Cubie])
        compareY = np.vectorize(lambda e: (e.getY()==reference.getY()).all(),
                [Cubie])
        compareZ = np.vectorize(lambda e: (e.getZ()==reference.getZ()).all(),
                [Cubie])

        # I will not explain the magnificence of this solution
        functions = (compareX, compareY, compareZ)
        _, laxis = np.where(reference.getMatrix().transpose())

        # Axis 0
        faces = np.concatenate((self.cube[0,:,:], self.cube[-1,:,:]))
        if not functions[laxis[0]](faces).all(): return False

        # Axis 1
        faces = np.concatenate((self.cube[:,0,:], self.cube[:,-1,:]))
        if not functions[laxis[1]](faces).all(): return False

        # Axis 2
        faces = np.concatenate((self.cube[:,:,0], self.cube[:,:,-1]))
        if not functions[laxis[2]](faces).all(): return False

        return True

    def checkCenterSolved(self):
        # Check only for unambiguous centers
        reference = self.cube[0,0,0]
        compareAll = np.vectorize(lambda e:
                (e.getX()==reference.getX()).all() and
                (e.getY()==reference.getY()).all() and
                (e.getZ()==reference.getZ()).all(), [Cubie])

        # Compare orientation on each face center
        xfaces = np.concatenate((self.cube[0,1:-1,1:-1],
            self.cube[self.size-1,1:-1,1:-1]))
        if not compareAll(xfaces).all(): return False

        yfaces = np.concatenate((self.cube[1:-1,0,1:-1],
            self.cube[1:-1,self.size-1,1:-1]))
        if not compareAll(yfaces).all(): return False

        zfaces = np.concatenate((self.cube[1:-1,1:-1,0],
            self.cube[1:-1,1:-1,self.size-1]))
        if not compareAll(zfaces).all(): return False

        return True

    def checkSuperSolved(self):
        # Include inner cubies
        reference = self.cube[0,0,0]
        compareAll = np.vectorize(lambda e:
                (e.getX()==reference.getX()).all() and
                (e.getY()==reference.getY()).all() and
                (e.getZ()==reference.getZ()).all(), [Cubie])

        return compareAll(self.cube).all()

    def moveRelativeToFace(self, face, layers, rotation):
        axis, sign = self.getAxisSign(face, self.orientation)
        layerscp = layers[:]
        if sign < 0:
            rotation = 1 if rotation == 0 else 0
            layerscp.reverse()
        self.move(axis, layerscp, rotation)

    def getAxisSign(self, face, cubie):
        v = self.vmapping[face]
        v = np.matmul(cubie.getMatrix().transpose(), v)
        for i in range(len(v)):
            if v[i] != 0:
                axis = i
                sign = int(v[i])
                break
        return axis, sign

    def getFace(self, face, cubie):
        axis, sign = self.getAxisSign(face, cubie)
        m = (('right','left'), ('up','down'), ('front','back'))
        idx = 0 if sign > 0 else 1
        return m[axis][idx]

    def getAxisSignFromFace(self, face):
        axis, sign = self.getAxisSign(face, self.orientation)
        lyridx = 0 if sign > 0 else self.size-1
        if   axis == 0: layer = self.cube[lyridx,:,:]
        elif axis == 1: layer = self.cube[:,lyridx,:]
        elif axis == 2: layer = self.cube[:,:,lyridx]
        asarr = np.vectorize(lambda c: self.getAxisSign(face,c),[Cubie])(layer)
        return asarr.tolist()

    def getCubie(self, i, j, k):
        return self.cube[i, j, k]

    def scramble(self, moves):
        self.hidx = 0
        self.history = []
        for _ in range(moves):
            axis = rnd.randrange(3)
            layers = []
            while not any(layers) or all(layers):
                layers = [rnd.random() < 0.5 for _ in range(self.size)]
            rotation = rnd.randrange(2)
            self.move(axis, layers, rotation, register=False)

    def undo(self):
        if self.hidx > 0:
            self.moves -= 1

            self.hidx -= 1 # Predecrement
            axis, layers, rotation = self.history[self.hidx]

            rotation = 1 if rotation == 0 else 0 # Invert
            self.move(axis, layers, rotation, register=False)

    def redo(self):
        if self.hidx < len(self.history):
            self.moves += 1

            axis, layers, rotation = self.history[self.hidx]
            self.hidx += 1 # Postincrement

            self.move(axis, layers, rotation, register=False)

    def __str__(self):
        return str(self.cube)

if __name__ == "__main__":
    c = Rubik(3)
    print(c.getAxisSignFromFace('right'))
