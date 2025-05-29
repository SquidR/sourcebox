import OpenGL.GL as gl
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math

def draw_line(start, end):
    gl.glBegin(gl.GL_LINES)
    gl.glVertex3f(start[0], start[1], start[2])
    gl.glVertex3f(end[0], end[1], end[2])
    gl.glEnd()

class Shape:
    def __init__(self, position=(0, 0, 0), size=1.0, color=(1, 1, 1)):
        self.position = list(position)
        self.size = size
        self.color = list(color)
        self.rotation = [0, 0, 0]  # rotation angles in degrees for x, y, z

    def set_position(self, x, y, z):
        self.position = [x, y, z]

    def set_color(self, r, g, b):
        self.color = [r, g, b]

    def set_rotation(self, x, y, z):
        self.rotation = [x, y, z]

    def _pre_render(self):
        gl.glPushMatrix()
        # first translate to the position
        gl.glTranslatef(*self.position)
        
        # for shapes that need center rotation, translate to center, rotate, translate back
        gl.glTranslatef(self.size/2, self.size/2, self.size/2)  # move to center
        gl.glRotatef(self.rotation[0], 1, 0, 0)  # rotate around x
        gl.glRotatef(self.rotation[1], 0, 1, 0)  # rotate around y
        gl.glRotatef(self.rotation[2], 0, 0, 1)  # rotate around z
        gl.glTranslatef(-self.size/2, -self.size/2, -self.size/2)  # move back
        
        gl.glColor3f(*self.color)

    def _post_render(self):
        gl.glPopMatrix()

class Cube(Shape):
    def __init__(self, position=(0, 0, 0), size=1.0, color=(1, 1, 1), rotation=[0,0,0]):
        super().__init__(position, size, color)
        self.rotation = rotation

    def render(self):
        self._pre_render()
        
        gl.glBegin(gl.GL_QUADS)
        # front face
        gl.glNormal3f(0, 0, -1)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(self.size, 0, 0)
        gl.glVertex3f(self.size, self.size, 0)
        gl.glVertex3f(0, self.size, 0)
        
        # back face
        gl.glNormal3f(0, 0, 1)
        gl.glVertex3f(0, 0, self.size)
        gl.glVertex3f(self.size, 0, self.size)
        gl.glVertex3f(self.size, self.size, self.size)
        gl.glVertex3f(0, self.size, self.size)
        
        # top face
        gl.glNormal3f(0, 1, 0)
        gl.glVertex3f(0, self.size, 0)
        gl.glVertex3f(self.size, self.size, 0)
        gl.glVertex3f(self.size, self.size, self.size)
        gl.glVertex3f(0, self.size, self.size)
        
        # bottom face
        gl.glNormal3f(0, -1, 0)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(self.size, 0, 0)
        gl.glVertex3f(self.size, 0, self.size)
        gl.glVertex3f(0, 0, self.size)
        
        # right face
        gl.glNormal3f(1, 0, 0)
        gl.glVertex3f(self.size, 0, 0)
        gl.glVertex3f(self.size, self.size, 0)
        gl.glVertex3f(self.size, self.size, self.size)
        gl.glVertex3f(self.size, 0, self.size)
        
        # left face
        gl.glNormal3f(-1, 0, 0)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(0, self.size, 0)
        gl.glVertex3f(0, self.size, self.size)
        gl.glVertex3f(0, 0, self.size)
        gl.glEnd()
        
        self._post_render()

class Sphere(Shape):
    def __init__(self, position=(0, 0, 0), radius=1.0, color=(1, 1, 1), slices=32, stacks=32):
        super().__init__(position, radius*2, color)  # size is diameter
        self.slices = slices
        self.stacks = stacks
        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)  # enable smooth normals

    def render(self):
        self._pre_render()
        gluSphere(self.quadric, self.size/2, self.slices, self.stacks)  # use radius
        self._post_render()

class Cylinder(Shape):
    def __init__(self, position=(0, 0, 0), radius=1.0, height=2.0, color=(1, 1, 1), slices=32):
        super().__init__(position, radius*2, color)  # size is diameter
        self.height = height
        self.slices = slices
        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)  # enable smooth normals

    def _pre_render(self):
        gl.glPushMatrix()
        gl.glTranslatef(*self.position)
        # move to center for rotation
        gl.glTranslatef(0, 0, self.height/2)
        gl.glRotatef(self.rotation[0], 1, 0, 0)
        gl.glRotatef(self.rotation[1], 0, 1, 0)
        gl.glRotatef(self.rotation[2], 0, 0, 1)
        gl.glTranslatef(0, 0, -self.height/2)
        gl.glColor3f(*self.color)

    def render(self):
        self._pre_render()
        gluCylinder(self.quadric, self.size/2, self.size/2, self.height, self.slices, 1)  # use radius
        self._post_render()

class Pyramid(Shape):
    def __init__(self, position=(0, 0, 0), size=1.0, color=(1, 1, 1), rotation=[0,0,0]):
        super().__init__(position, size, color)
        self.rotation = rotation

    def render(self):
        self._pre_render()
        
        # calculate normal vectors for each face
        front_normal = self._calculate_normal(
            [0, 0, 0],
            [self.size, 0, 0],
            [self.size/2, self.size, self.size/2]
        )
        right_normal = self._calculate_normal(
            [self.size, 0, 0],
            [self.size, 0, self.size],
            [self.size/2, self.size, self.size/2]
        )
        back_normal = self._calculate_normal(
            [self.size, 0, self.size],
            [0, 0, self.size],
            [self.size/2, self.size, self.size/2]
        )
        left_normal = self._calculate_normal(
            [0, 0, self.size],
            [0, 0, 0],
            [self.size/2, self.size, self.size/2]
        )
        
        gl.glBegin(gl.GL_TRIANGLES)
        # front face
        gl.glNormal3f(*front_normal)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(self.size, 0, 0)
        gl.glVertex3f(self.size/2, self.size, self.size/2)
        
        # right face
        gl.glNormal3f(*right_normal)
        gl.glVertex3f(self.size, 0, 0)
        gl.glVertex3f(self.size, 0, self.size)
        gl.glVertex3f(self.size/2, self.size, self.size/2)
        
        # back face
        gl.glNormal3f(*back_normal)
        gl.glVertex3f(self.size, 0, self.size)
        gl.glVertex3f(0, 0, self.size)
        gl.glVertex3f(self.size/2, self.size, self.size/2)
        
        # left face
        gl.glNormal3f(*left_normal)
        gl.glVertex3f(0, 0, self.size)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(self.size/2, self.size, self.size/2)
        gl.glEnd()
        
        # base
        gl.glBegin(gl.GL_QUADS)
        gl.glNormal3f(0, -1, 0)  # base normal points down
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(self.size, 0, 0)
        gl.glVertex3f(self.size, 0, self.size)
        gl.glVertex3f(0, 0, self.size)
        gl.glEnd()
        
        self._post_render()

    def _calculate_normal(self, p1, p2, p3):
        """Calculate normal vector for a triangle face."""
        v1 = [p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]]
        v2 = [p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2]]
        
        # cross product
        normal = [
            v1[1] * v2[2] - v1[2] * v2[1],
            v1[2] * v2[0] - v1[0] * v2[2],
            v1[0] * v2[1] - v1[1] * v2[0]
        ]
        
        # normalize
        length = (normal[0]**2 + normal[1]**2 + normal[2]**2)**0.5
        if length != 0:
            normal = [n/length for n in normal]
        
        return normal

class Cone(Shape):
    def __init__(self, position=(0, 0, 0), radius=1.0, height=2.0, color=(1, 1, 1), slices=32, rotation=[0,0,0]):
        super().__init__(position, radius*2, color)  # size is diameter
        self.height = height
        self.slices = slices
        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)  # enable smooth normals
        self.rotation = rotation

    def render(self):
        self._pre_render()
        
        # draw the cone body
        gluCylinder(self.quadric, self.size/2, 0, self.height, self.slices, 1)  # use radius
        
        # draw the base circle
        gl.glPushMatrix()
        gl.glRotatef(180, 1, 0, 0)  # flip normal to point outward
        gluDisk(self.quadric, 0, self.size/2, self.slices, 1)  # draw filled circle
        gl.glPopMatrix()
        
        self._post_render()


class Text2D(Shape):
    def __init__(self, position=(0, 0, 0), text="", color=(1, 1, 1), scale=1.0, center=False, font=GLUT_STROKE_ROMAN):
        super().__init__(position, scale, color)
        self.text = text
        self.center = center
        self.font = font

    def render(self):
        # save matrices and attributes
        gl.glPushAttrib(gl.GL_ALL_ATTRIB_BITS)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glOrtho(0, 1600, 0, 900, -1, 1)  # match window size
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        
        # disable lighting and depth test for 2d text
        gl.glDisable(gl.GL_LIGHTING)
        gl.glDisable(gl.GL_DEPTH_TEST)
        
        # enable line smoothing for better looking text
        gl.glEnable(gl.GL_LINE_SMOOTH)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        # set color
        gl.glColor3f(*self.color)
        
        # set line width for thicker characters
        gl.glLineWidth(2.0)  # increase this value for thicker letters
        
        # calculate total width for centering
        total_width = 0
        for c in self.text:
            total_width += glutStrokeWidth(self.font, ord(c))
        total_width = total_width * 0.1 * self.size  # scale factor for reasonable size
        
        # position text
        gl.glPushMatrix()
        if self.center:
            gl.glTranslatef(self.position[0] - total_width/2, self.position[1], 0)
        else:
            gl.glTranslatef(self.position[0], self.position[1], 0)
        gl.glScalef(0.1 * self.size, 0.1 * self.size, 1.0)  # scale the stroke font
        
        # draw characters
        for c in self.text:
            glutStrokeCharacter(self.font, ord(c))
        
        gl.glPopMatrix()
        
        # restore state
        gl.glLineWidth(1.0)  # reset line width
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopAttrib()

    def set_text(self, text):
        self.text = text

def init():
    gl.glClearColor(0.0, 0.0, 0.0, 1.0)
    gl.gluOrtho2D(0.0, 500.0, 0.0, 500.0)

def display():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    gl.glColor3f(1.0, 1.0, 1.0)
    gl.glBegin(gl.GL_POLYGON)
    gl.glVertex2f(100, 100)
    gl.glEnd()
    gl.glFlush()

