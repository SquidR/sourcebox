import OpenGL.GL as gl
from OpenGL.GLUT import GLUT_DOUBLE, GLUT_RGB, GLUT_DEPTH
import OpenGL.GLUT as glut
from OpenGL.GLU import *
import math
import sys

# Define colors (R, G, B)
COLOR_GRID_MAJOR = (1.0, 0.4, 0.0)  # Bright Orange/Red for major lines
COLOR_GRID_MINOR = (0.7, 0.2, 0.0)  # Darker Orange/Red for minor lines
COLOR_TEXT_HEADER = (1.0, 1.0, 0.0)  # Yellow for header text
COLOR_TEXT_COORD = (1.0, 0.0, 0.0)   # Red for coordinate text
COLOR_TEXT_STATUS = (1.0, 1.0, 0.0) # Yellow for status text


# Window settings
WINDOW_SIZE = (800, 800)
MOVE_SPEED = 2.0
MOUSE_SENSITIVITY = 0.1

class Camera:
    def __init__(self):
        self.pos = [200.0, 150.0, 200.0]  # Pulled camera back for larger grid
        self.rot = [-30.0, 45.0, 0.0]  # Kept similar angle
        self.move_speed = MOVE_SPEED
        self.mouse_sensitivity = MOUSE_SENSITIVITY
        self.last_mouse = (WINDOW_SIZE[0]/2, WINDOW_SIZE[1]/2)
        self.keys_pressed = set()
        self.first_mouse = True

    def update(self):
        # Calculate movement direction based on camera rotation
        forward = math.sin(math.radians(self.rot[1]))
        right = math.cos(math.radians(self.rot[1]))
        
        if b'w' in self.keys_pressed:
            self.pos[0] -= forward * self.move_speed
            self.pos[2] -= right * self.move_speed
        if b's' in self.keys_pressed:
            self.pos[0] += forward * self.move_speed
            self.pos[2] += right * self.move_speed
        if b'a' in self.keys_pressed:
            self.pos[0] -= right * self.move_speed
            self.pos[2] += forward * self.move_speed
        if b'd' in self.keys_pressed:
            self.pos[0] += right * self.move_speed
            self.pos[2] -= forward * self.move_speed
        if b' ' in self.keys_pressed:  # Space to move up
            self.pos[1] += self.move_speed
        if b'z' in self.keys_pressed:  # Z to move down
            self.pos[1] -= self.move_speed

    def handle_mouse(self, x, y):
        if self.first_mouse:
            self.last_mouse = (x, y)
            self.first_mouse = False
            return

        dx = x - self.last_mouse[0]
        dy = y - self.last_mouse[1]

        self.rot[1] -= dx * self.mouse_sensitivity
        self.rot[0] -= dy * self.mouse_sensitivity
        
        # Clamp vertical rotation
        self.rot[0] = max(-89.0, min(89.0, self.rot[0]))
        
        # Keep horizontal rotation in [0, 360)
        self.rot[1] = self.rot[1] % 360.0
        
        self.last_mouse = (x, y)

    def apply(self):
        gl.glRotatef(-self.rot[0], 1, 0, 0)
        gl.glRotatef(-self.rot[1], 0, 1, 0)
        gl.glTranslatef(-self.pos[0], -self.pos[1], -self.pos[2])


camera = Camera()

def init():
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glClearColor(0.0, 0.0, 0.0, 1.0)
    
    # Enable line smoothing
    gl.glEnable(gl.GL_LINE_SMOOTH)
    gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST)
    # Enable blending for text and lines
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    
    # Set up projection
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gluPerspective(45, (WINDOW_SIZE[0]/WINDOW_SIZE[1]), 0.1, 1000.0)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    
    # Hide cursor
    glut.glutSetCursor(glut.GLUT_CURSOR_NONE)

def display():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glLoadIdentity()
    
    camera.update()
    camera.apply()
    
    draw_subdivided_grid()
    draw_ui_text()
    
    glut.glutSwapBuffers()

def draw_text(text, x, y, color, font=glut.GLUT_BITMAP_9_BY_15):
    gl.glColor3fv(color)
    gl.glRasterPos2f(x, y)
    for character in text:
        glut.glutBitmapCharacter(font, ord(character))

def draw_ui_text():
    # To draw text in screen space, we need to set up an ortho projection
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    gluOrtho2D(0, WINDOW_SIZE[0], 0, WINDOW_SIZE[1])
    
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    
    # Disable depth test for 2D text rendering
    gl.glDisable(gl.GL_DEPTH_TEST)

    text_y_start = WINDOW_SIZE[1] - 20
    line_height = 18 # Adjusted line height

    draw_text("LOCATED WFA3Y-A [INTERLOPE.DME]", 10, text_y_start, COLOR_TEXT_HEADER)
    text_y_start -= line_height
    draw_text("VALIDATORS HAVE NOT BEEN VERIFIED, PLEASE", 10, text_y_start, COLOR_TEXT_HEADER)
    text_y_start -= line_height * 1.5 # Extra space for clarity

    draw_text("X6 9,   8 2 7,   3 0 1,   3 6", 10, text_y_start, COLOR_TEXT_COORD)
    text_y_start -= line_height
    draw_text("Y2 9,   1 4 9,   5 1 6,   8 9", 10, text_y_start, COLOR_TEXT_COORD)
    text_y_start -= line_height
    draw_text("Z2 0,   0 1 4,   0 7 1,   0 3", 10, text_y_start, COLOR_TEXT_COORD)
    text_y_start -= line_height * 1.5

    # METAL_REG-STOPREG_DIRTY
    draw_text("METAL_REG-STOPREG_DIRTY", 10, text_y_start, COLOR_TEXT_STATUS)

    # Restore depth test and matrices
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPopMatrix()
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPopMatrix()


def draw_subdivided_grid():
    grid_extent = 150  # How far the grid extends from origin (Increased size)
    major_step = 70   # Every 10 units for major lines
    minor_step = 10    # Every 10 units for minor lines (Changed from 5 to make subdivided squares larger)
    y_extent = grid_extent # For a cubic grid volume

    # --- Draw Major Lines ---
    gl.glLineWidth(1.5) # Thicker lines for major grid
    gl.glColor3fv(COLOR_GRID_MAJOR) # Use unified major color

    # Major lines parallel to X-axis
    gl.glBegin(gl.GL_LINES)
    for y_coord in range(-y_extent, y_extent + 1, major_step):
        for z_coord in range(-grid_extent, grid_extent + 1, major_step):
            gl.glVertex3f(float(-grid_extent), float(y_coord), float(z_coord))
            gl.glVertex3f(float(grid_extent), float(y_coord), float(z_coord))
    gl.glEnd()

    # Major lines parallel to Y-axis
    gl.glBegin(gl.GL_LINES)
    for x_coord in range(-grid_extent, grid_extent + 1, major_step):
        for z_coord in range(-grid_extent, grid_extent + 1, major_step):
            gl.glVertex3f(float(x_coord), float(-y_extent), float(z_coord))
            gl.glVertex3f(float(x_coord), float(y_extent), float(z_coord))
    gl.glEnd()

    # Major lines parallel to Z-axis
    gl.glBegin(gl.GL_LINES)
    for x_coord in range(-grid_extent, grid_extent + 1, major_step):
        for y_coord in range(-y_extent, y_extent + 1, major_step):
            gl.glVertex3f(float(x_coord), float(y_coord), float(-grid_extent))
            gl.glVertex3f(float(x_coord), float(y_coord), float(grid_extent))
    gl.glEnd()

    # --- Draw Minor Lines (on principal planes only: Y=0, X=0, Z=0) ---
    gl.glLineWidth(0.5) # Thinner lines for minor grid
    gl.glColor3fv(COLOR_GRID_MINOR) # Use unified minor color

    # Minor lines on XZ plane (Y=0)
    # Parallel to X
    gl.glBegin(gl.GL_LINES)
    for z_coord in range(-grid_extent, grid_extent + 1, minor_step):
        if z_coord % major_step == 0: continue # Avoid drawing over major lines
        gl.glVertex3f(float(-grid_extent), 0.0, float(z_coord))
        gl.glVertex3f(float(grid_extent), 0.0, float(z_coord))
    gl.glEnd()
    # Parallel to Z
    gl.glBegin(gl.GL_LINES)
    for x_coord in range(-grid_extent, grid_extent + 1, minor_step):
        if x_coord % major_step == 0: continue # Avoid drawing over major lines
        gl.glVertex3f(float(x_coord), 0.0, float(-grid_extent))
        gl.glVertex3f(float(x_coord), 0.0, float(grid_extent))
    gl.glEnd()

    # Minor lines on XY plane (Z=0)
    # Parallel to X
    gl.glBegin(gl.GL_LINES)
    for y_coord in range(-y_extent, y_extent + 1, minor_step):
        if y_coord % major_step == 0: continue # Avoid drawing over major lines
        gl.glVertex3f(float(-grid_extent), float(y_coord), 0.0)
        gl.glVertex3f(float(grid_extent), float(y_coord), 0.0)
    gl.glEnd()
    # Parallel to Y
    gl.glBegin(gl.GL_LINES)
    for x_coord in range(-grid_extent, grid_extent + 1, minor_step):
        if x_coord % major_step == 0: continue # Avoid drawing over major lines
        gl.glVertex3f(float(x_coord), float(-y_extent), 0.0)
        gl.glVertex3f(float(x_coord), float(y_extent), 0.0)
    gl.glEnd()

    # Minor lines on YZ plane (X=0)
    # Parallel to Y
    gl.glBegin(gl.GL_LINES)
    for z_coord in range(-grid_extent, grid_extent + 1, minor_step):
        if z_coord % major_step == 0: continue # Avoid drawing over major lines
        gl.glVertex3f(0.0, float(-y_extent), float(z_coord))
        gl.glVertex3f(0.0, float(y_extent), float(z_coord))
    gl.glEnd()
    # Parallel to Z
    gl.glBegin(gl.GL_LINES)
    for y_coord in range(-y_extent, y_extent + 1, minor_step):
        if y_coord % major_step == 0: continue # Avoid drawing over major lines
        gl.glVertex3f(0.0, float(y_coord), float(-grid_extent))
        gl.glVertex3f(0.0, float(y_coord), float(grid_extent))
    gl.glEnd()

def keyboard(key, x, y):
    if key == b'\x1b':  # ESC
        sys.exit(0)
    else:
        camera.keys_pressed.add(key)

def keyboard_up(key, x, y):
    camera.keys_pressed.discard(key)

def mouse_motion(x, y):
    camera.handle_mouse(x, y)

def update(value):
    glut.glutPostRedisplay()
    glut.glutTimerFunc(16, update, 0)

def main():
    glut.glutInit()
    glut.glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glut.glutInitWindowSize(WINDOW_SIZE[0], WINDOW_SIZE[1])
    glut.glutCreateWindow(b"Subdivided Cube Grid")
    
    init()
    glut.glutDisplayFunc(display)
    glut.glutKeyboardFunc(keyboard)
    glut.glutKeyboardUpFunc(keyboard_up)
    glut.glutPassiveMotionFunc(mouse_motion)
    glut.glutMotionFunc(mouse_motion)
    glut.glutTimerFunc(0, update, 0)
    glut.glutMainLoop()

if __name__ == "__main__":
    main()
