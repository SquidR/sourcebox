import OpenGL.GL as gl
from OpenGL.GLUT import *
from OpenGL.GLU import *
from opengl import *
from texture import load_texture, draw_background_quad
import math
import sys
import random
import os
import numpy as np
import time
import pygame


pygame.mixer.init()
pygame.init()
# start background music
pygame.mixer.music.load('assets/sound/sourcebox.wav')
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)
# window and display settings
WINDOWSIZE = (1600, 900)       # 16:9

INTENDED = 1920
ACTUAL = pygame.display.Info().current_w
RATIO = ACTUAL/INTENDED

WINDOWSIZE = (int(WINDOWSIZE[0]*RATIO), int(WINDOWSIZE[1]*RATIO))


MOVESPEED = 0                  # base movement speed
MOUSESENSITIVITY = 0           # mouse sensitivity for camera control
TARGET_FPS = 144                # target frame rate
FRAME_TIME = 1.0 / TARGET_FPS  # time per frame in seconds
RATIO_TO_SIXTY = TARGET_FPS/60
DEBUG = False                  # debug mode flag
CUBESIZE = 8192
FARPLANE = 6000.0
mouse_x = 0
mouse_y = 0

# texture management
background_texture     = None    # main background texture
background_texture_alt = None    # alternative background texture
overlay_texture        = None    # overlay texture for cone mode
cursor_texture         = None    # cursor texture
grid_texture           = None

# interactive object states
cube_hover   = False    # track if mouse is hovering over cube
sphere_hover = False    # track if mouse is hovering over sphere
cone_hover   = False    # track if mouse is hovering over cone

# animation and timing
last_time = 0  # last frame timestamp
hover_scale       = {'cube': 1.0,   'sphere': 1.0,   'cone': 1.0}     # current scale for each object
hover_timers      = {'cube': 0,     'sphere': 0,     'cone': 0}       # animation timers
prev_hover_states = {'cube': False, 'sphere': False, 'cone': False}   # previous hover states

# object positioning
initial_positions = {}    # store initial positions of objects

# animation constants
HOVER_SCALE_MAX = 1.1     # maximum scale during pop animation
HOVER_SCALE_MIN = 1.0     # normal scale (no animation)
HOVER_POP_DURATION = 0.06 # duration of pop animation in seconds

blue_boxes = []
MAX_BLUE_BOXES = 20

floaters = []
MAX_FLOATERS = 50

# color constants (obsolete)
COLOR = {
    "RED":(1.0, 0.0, 0.0),
}
soundplay = False
metalreg = [
    'PLAT',
    'STOPREG_DIRTY',
    'SETREG',
    'THINK',
    'WAIT',
    'CPU_POP',
    'CPU_PUSH'
]
# --- HELPER FUNCTIONS ---
def point_in_cube(SIZE):
    HALFSIZE = SIZE/2
    x = random.uniform(-HALFSIZE, HALFSIZE)
    y = random.uniform(0, SIZE)
    z = random.uniform(-HALFSIZE, HALFSIZE)
    return (x, y, z)

def calculate_normals(vertices):
    normals = []
    for i in range(0, len(vertices), 3):
        v1 = vertices[i]
        v2 = vertices[i+1]
        v3 = vertices[i+2]
        
        # calculate vectors for cross product
        vec1 = [v2[0]-v1[0], v2[1]-v1[1], v2[2]-v1[2]]
        vec2 = [v3[0]-v1[0], v3[1]-v1[1], v3[2]-v1[2]]
        
        # calculate normal using cross product
        normal = [
            vec1[1]*vec2[2] - vec1[2]*vec2[1],
            vec1[2]*vec2[0] - vec1[0]*vec2[2],
            vec1[0]*vec2[1] - vec1[1]*vec2[0]
        ]
        
        # normalize the normal vector
        length = (normal[0]**2 + normal[1]**2 + normal[2]**2)**0.5
        if length != 0:
            normal = [n/length for n in normal]
        
        normals.extend([normal]*3)  # apply same normal to all vertices in triangle
    return normals
def rgb2color(r, g, b):
    return (r/255.0, g/255.0, b/255.0)

def magnitude(point1, point2):
    """Calculate the Euclidean distance between two points."""""
    return ((point1[0] - point2[0])**2 +
            (point1[1] - point2[1])**2 +
            (point1[2] - point2[2])**2)**0.5

def draw_cursor():
    global mouse_x, mouse_y, cursor_texture
    
    # save current matrices and attributes
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    viewport = glGetIntegerv(GL_VIEWPORT)
    glOrtho(0, viewport[2], viewport[3], 0, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # save states and disable depth test for 2D drawing
    glPushAttrib(GL_ALL_ATTRIB_BITS)
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    # enable blending for transparency
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # enable texturing
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, cursor_texture)
    
    # set color to white to show texture as is
    glColor4f(1, 1, 1, 1)

    x = mouse_x
    y = mouse_y
    
    # draw cursor quad
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(x,      y     )
    glTexCoord2f(1, 0); glVertex2f(x + 32, y     )
    glTexCoord2f(1, 1); glVertex2f(x + 32, y + 32)
    glTexCoord2f(0, 1); glVertex2f(x,      y + 32)
    glEnd()
    
    # clean up
    glBindTexture(GL_TEXTURE_2D, 0)
    glDisable(GL_TEXTURE_2D)
    
    # restore previous states
    glPopAttrib()
    
    # restore matrices
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

tracking_cone  =   Cone(position=(0.2, -0.1, -25), radius=0.3,  height=0.6, color=(1, 0, 0), rotation=[90, 0, 0])
tracked_sphere = Sphere(position=(0, -0.4, -25),   radius=0.03, color=(1, 0.7, 0.9))
cyan_cone      = Cone(position=(5, -3.5, -25), radius=0.7, height=1.4, color=(0, 1, 1), rotation=[90, -15, 30])
def draw_tracking_cone():
    gl.glPushMatrix()
    gl.glLoadIdentity()

    # Draw the cone
    tracking_cone.render()
    gl.glPopMatrix()

endpoint  = (random.uniform(-1000, 1000), random.uniform(-1000, 1000), random.uniform(-1000, 1000))
endpoint2 = (random.uniform(-1000, 1000), random.uniform(-1000, 1000), random.uniform(-1000, 1000))

basewobble = 0.003
wobblerate = basewobble
setwobble = False
sphererunning = False
runspeed = [random.uniform(-1, 1), random.uniform(-10, 1), random.uniform(-1, 1)]
def draw_tracked_sphere():
    global basewobble, wobblerate, setwobble, runspeed, sphererunning
    gl.glPushMatrix()
    gl.glLoadIdentity()

    # Draw the sphere
    tracked_sphere.position = [
        tracked_sphere.position[0] + random.uniform(-wobblerate, wobblerate) + (runspeed[0]/100 if sphererunning else 0),
        tracked_sphere.position[1] + random.uniform(-wobblerate, wobblerate) + (runspeed[1]/100 if sphererunning else 0),
        tracked_sphere.position[2] + random.uniform(-wobblerate, wobblerate) + (runspeed[2]/100 if sphererunning else 0),
    ]
    tracking_cone.position = [
        tracked_sphere.position[0] + 0.2,  # slightly in front of the sphere
        tracked_sphere.position[1] + 0.2,  # slightly above the sphere
        tracked_sphere.position[2]
    ]
    gl.glDisable(GL_LIGHTING)
    cyan_cone.render()
    if random.randint(0, 100)/100 < 0.01 and setwobble == False and sphererunning == False:  # 1% chance to schmoove faster
        setwobble  = True
        wobblerate = 0.05
        sphererunning = True
        runspeed = [random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-10, 10)]

    if wobblerate > basewobble:
        wobblerate -= 0.001
    else:
        setwobble  = False
        wobblerate = basewobble
    tracked_sphere.render()

    gl.glLineWidth(0.1)
    gl.glColor3f(1.0, 0.3, 0.3)
    gl.glBegin(gl.GL_LINES)

    #draw a line starting at the sphere and going to nowhere
    gl.glVertex3f(tracked_sphere.position[0], tracked_sphere.position[1], tracked_sphere.position[2])
    gl.glVertex3f(*endpoint)

    gl.glColor3f(0.0,0.0,1.0)
    gl.glVertex3f(tracked_sphere.position[0], tracked_sphere.position[1], tracked_sphere.position[2])
    gl.glVertex3f(*endpoint2)  # vertical line to the sky
    gl.glEnd()
    gl.glEnable(GL_LIGHTING)
    gl.glPopMatrix()

class Camera:
    def __init__(self):
        self.pos = [0,0, 0]  # in 3d
        self.rot = [0,0,0]  # (pitch, yaw, roll)
        if DEBUG:
            self.move_speed        = 5
            self.mouse_sensitivity = 0.1
        else:
            self.move_speed        = MOVESPEED
            self.mouse_sensitivity = MOUSESENSITIVITY
        self.last_mouse    = (WINDOWSIZE[0] / 2, WINDOWSIZE[1] / 2)
        self.keys_pressed  = set()  # currently pressed keys
        self.first_mouse   = True    # flag for first mouse movement
        self.window_center = (WINDOWSIZE[0] / 2, WINDOWSIZE[1] / 2)  # window center coordinates
        self.just_wrapped  = False  # flag to prevent immediate re-wrapping after first wrap

    def update(self):
        # handle continuous keyboard movement
        forward = math.sin(math.radians(self.rot[1]))  # forward direction vector
        right   = math.cos(math.radians(self.rot[1]))    # right direction vector
        
        # process movement based on pressed keys
        if b'w' in self.keys_pressed:  # move forward
            self.pos[0] -= forward * self.move_speed
            self.pos[2] -= right   * self.move_speed
        if b's' in self.keys_pressed:  # move backward
            self.pos[0] += forward * self.move_speed
            self.pos[2] += right   * self.move_speed
        if b'a' in self.keys_pressed:  # strafe left
            self.pos[0] -= right   * self.move_speed
            self.pos[2] += forward * self.move_speed
        if b'd' in self.keys_pressed:  # strafe right
            self.pos[0] += right   * self.move_speed
            self.pos[2] -= forward * self.move_speed
        if b' ' in self.keys_pressed:  # move up
            self.pos[1] += self.move_speed
        if b'z' in self.keys_pressed:  # move down
            self.pos[1] -= self.move_speed
        if b'e' in self.keys_pressed:  # log position
            print("Camera Pos")
            x, y, z = round(self.pos[0],1), round(self.pos[1],1), round(self.pos[2],1)
            print(f"X: {x}, Y: {y}, Z: {z}")

    def handle_mouse(self, x, y):
        if self.first_mouse:
            self.last_mouse = (x, y)
            self.first_mouse = False
            return
        if self.just_wrapped:
            self.last_mouse = (x, y)
            self.just_wrapped = False
            return  # skip frames movement

        # calculate mouse movement
        dx = x - self.last_mouse[0]
        dy = y - self.last_mouse[1]

        # update rotation
        self.rot[1] -= dx * self.mouse_sensitivity  # yaw (left/right)
        self.rot[0] -= dy * self.mouse_sensitivity  # pitch (up/down)
        
        # normalize yaw to stay within 0-360 degrees
        self.rot[1] = self.rot[1] % 360.0
        
        # clamp pitch to prevent over-rotation
        self.rot[0] = max(-89.0, min(89.0, self.rot[0]))

        # update last position
        self.last_mouse = (x, y)

        # handle mouse wrapping at window edges (kept for debugging)
        wrap_margin = 50  # pixels from edge to trigger wrap
        wrap_needed = False
        new_x, new_y = x, y

        if x < wrap_margin:
            new_x = self.window_center[0] * 2 - wrap_margin
            wrap_needed = True
        elif x > self.window_center[0] * 2 - wrap_margin:
            new_x = wrap_margin
            wrap_needed = True

        if y < wrap_margin:
            new_y = self.window_center[1] * 2 - wrap_margin
            wrap_needed = True
        elif y > self.window_center[1] * 2 - wrap_margin:
            new_y = wrap_margin
            wrap_needed = True
        
        #if wrap_needed:
        #    glutWarpPointer(int(new_x), int(new_y))
        #    self.last_mouse = (new_x, new_y)
        #    self.just_wrapped = True

    def apply(self):
        gl.glRotatef(-self.rot[0], 1, 0, 0)  # pitch rotation
        gl.glRotatef(-self.rot[1], 0, 1, 0)  # yaw rotation
        gl.glTranslatef(-self.pos[0], -self.pos[1], -self.pos[2])

# separate offsets for each grid plane
camera = Camera()
camera_rot_offsets = {
    'x':0.0,
    'y':0.0,
    'z':0.0
}
tracker_active =  True


class BlueBox:
    def __init__(self):
        self.position = point_in_cube(CUBESIZE)
        self.rotation = [0,0,0]  # random rotation on all axes
        self.x = self.position[0]
        self.y = self.position[1]
        self.z = self.position[2]
        self.size = {
            'x':random.uniform(20, 200),
            'y':random.uniform(20, 200),
            'z':random.uniform(20, 200)
        }
        self.alpha = 0.3
    
    def render(self):
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        gl.glPushMatrix()
        # move to position
        gl.glTranslatef(self.x, self.y, self.z)
        # apply rotation
        gl.glRotatef(self.rotation[0], 1, 0, 0)
        gl.glRotatef(self.rotation[1], 0, 1, 0)
        gl.glRotatef(self.rotation[2], 0, 0, 1)

        gl.glColor4f(0.0, 0.0, 1.0, self.alpha)  # blue color with alpha
        
        sx = self.size['x']
        sy = self.size['y']
        sz = self.size['z']

        # Half-sizes for centering
        hx, hy, hz = sx / 2, sy / 2, sz / 2

        # FRONT face (+Z)
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f(-hx, -hy,  hz)
        gl.glVertex3f( hx, -hy,  hz)
        gl.glVertex3f( hx,  hy,  hz)
        gl.glVertex3f(-hx,  hy,  hz)
        gl.glEnd()

        # BACK face (-Z)
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f( hx, -hy, -hz)
        gl.glVertex3f(-hx, -hy, -hz)
        gl.glVertex3f(-hx,  hy, -hz)
        gl.glVertex3f( hx,  hy, -hz)
        gl.glEnd()

        # LEFT face (-X)
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f(-hx, -hy, -hz)
        gl.glVertex3f(-hx, -hy,  hz)
        gl.glVertex3f(-hx,  hy,  hz)
        gl.glVertex3f(-hx,  hy, -hz)
        gl.glEnd()

        # RIGHT face (+X)
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f( hx, -hy,  hz)
        gl.glVertex3f( hx, -hy, -hz)
        gl.glVertex3f( hx,  hy, -hz)
        gl.glVertex3f( hx,  hy,  hz)
        gl.glEnd()

        # TOP face (+Y)
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f(-hx,  hy,  hz)
        gl.glVertex3f( hx,  hy,  hz)
        gl.glVertex3f( hx,  hy, -hz)
        gl.glVertex3f(-hx,  hy, -hz)
        gl.glEnd()

        # BOTTOM face (-Y)
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f(-hx, -hy, -hz)
        gl.glVertex3f( hx, -hy, -hz)
        gl.glVertex3f( hx, -hy,  hz)
        gl.glVertex3f(-hx, -hy,  hz)
        gl.glEnd()
        
        gl.glPopMatrix()
        gl.glDisable(gl.GL_BLEND)

class Floater:
    def __init__(self):
        self.pos          = point_in_cube(CUBESIZE)
        self.original_pos = self.pos
        self.baseradius   = random.uniform(5, 20)
        self.object       = Sphere(self.pos, self.baseradius, (1, 0.7, 0.9))
        self.run_x        = random.randint(-10, 10)
        self.run_y        = random.randint(-10, 10)
        self.run_z        = random.randint(-10, 10)
        self.lifetime     = 10
        self.running      = False
    def update(self):
        if self.running:
            self.pos = (
                self.pos[0] + self.run_x,
                self.pos[1] + self.run_y,
                self.pos[2] + self.run_z
            )
            self.object.position = self.pos
        else:
            if random.random() < 0.01:
                self.running = True
        distance = magnitude(camera.pos, self.pos)
        self.object.size = self.baseradius * (distance/CUBESIZE)
        gl.glLineWidth(0.1)
        gl.glColor4f(1.0, 0.3, 0.3, 0.5)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        draw_line(
            self.original_pos,
            self.pos
        )
        gl.glDisable(gl.GL_BLEND)
def toggle_tracker(value):
    global tracker_active
    tracker_active = not tracker_active
def update_factor(value):
    global camera, endpoint, wobblerate, setwobble, basewobble, endpoint2, camera_rot_offsets, cone, tracking_cone, sphererunning
    offsetcap = CUBESIZE/2
    wobblerate = basewobble
    setwobble = False
    update_coordinates()
    if cone:
        if not DEBUG:
            regen_floaters()
            sphererunning = False
            camera_rot_offsets.update({
                'x': random.uniform(-3, 3)/60,
                'y': random.uniform(-3, 3)/60,
                'z': random.uniform(-3, 3)/60
            })
            camera.rot = [random.randint(-180, 180), random.randint(-180, 180), random.randint(-180, 180)]
            camera.pos = [
                0 + random.uniform(-offsetcap, offsetcap),
                0 + random.uniform(-offsetcap, offsetcap),
                0 + random.uniform(-offsetcap, offsetcap)
            ]
            tracking_cone.rotation = [
                90,
                -24, 
                0
            ]
        tracked_sphere.position = (0.2, -0.1, -25)
        endpoint  = (random.uniform(-1000, 1000), random.uniform(-1000, 1000), random.uniform(-1000, 1000))
        endpoint2 = (random.uniform(-1000, 1000), random.uniform(-1000, 1000), random.uniform(-1000, 1000))
    glutTimerFunc(2000, update_factor, 0)
    glutTimerFunc(100, toggle_tracker, 0)
def draw_grid():
    global metalreg, metal_reg_display_2, MOVESPEED, MOUSESENSITIVITY, grid_texture, CUBESIZE
    MOVESPEED        = 5
    MOUSESENSITIVITY = 0.1
    # enable blending for transparency
    camera.rot = [
        camera.rot[0] + camera_rot_offsets['x'],
        camera.rot[1] + camera_rot_offsets['y'],
        camera.rot[2] + camera_rot_offsets['z']
    ]
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    
    if random.randint(0,5) == 2:
        metal_reg_display_2.text = metalreg[random.randint(0, len(metalreg)-1)]

    def render_grid_3d():
        gl.glEnable(gl.GL_LIGHTING)
        gl.glDisable(gl.GL_LIGHTING)
        size              = CUBESIZE
        halfsize          = size/2
        GridCube.size     = size
        GridCube.position = [-halfsize, 0, -halfsize]
        quads = [
            Quad((-halfsize, 0,                -0.01    ), size, rotation=[0, 0, 0] , textureid=grid_texture),      # front face (XY)
            Quad((-halfsize, -(halfsize+0.01), -halfsize), size, rotation=[90, 0, 0], textureid=grid_texture),     # XZ
            Quad((-0.01    , 0,                -halfsize), size, rotation=[0, 90, 0], textureid=grid_texture),     # YZ
        ]
        gl.glDisable(gl.GL_DEPTH_TEST)
        for quad in quads:
            quad.render()
        GridCube.render()
        gl.glEnable(gl.GL_DEPTH_TEST)
        

    render_grid_3d()
    gl.glEnable(gl.GL_LIGHTING)

def init():
    global background_texture, background_texture_alt, overlay_texture, last_frame_time, cursor_texture, grid_texture
    
    # initialize frame timing
    last_frame_time = time.time()
    
    # load both background textures and get dimensions
    background_texture, _, _     = load_texture('assets/img/checkerboard.png')
    background_texture_alt, _, _ = load_texture('assets/img/checkerboardmissing.png')
    overlay_texture, _, _        = load_texture('assets/img/checkerboardoverlay.png')
    grid_texture, _, _           = load_texture('assets/img/grid.png')
    cursor_texture, _, _         = load_texture('assets/img/cursor.png')

    # store initial positions
    initial_positions['cube'] = list(ButtonCube.position)
    GridCube.textureid = grid_texture
    # enable rendering features
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glEnable(gl.GL_LINE_SMOOTH)
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    
    # enable lighting
    gl.glEnable(gl.GL_LIGHTING)
    gl.glEnable(gl.GL_LIGHT0)
    gl.glEnable(gl.GL_COLOR_MATERIAL)
    gl.glColorMaterial(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE)
    
    # set up light properties
    gl.glLight(gl.GL_LIGHT0, gl.GL_POSITION, (0.0, 0.0, -100.0, 1.0))
    gl.glLight(gl.GL_LIGHT0, gl.GL_AMBIENT,  (0.0, 0.0, 0.0, 1.0))
    gl.glLight(gl.GL_LIGHT0, gl.GL_DIFFUSE,  (0.6, 0.6, 0.6, 1.0))
    gl.glLight(gl.GL_LIGHT0, gl.GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))
    
    # set up material properties
    gl.glMaterial(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))
    gl.glMaterial(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, 0.0)


cone   = False
cube   = False
sphere = False

ButtonCube   =   Cube(position=(-1.3,-0.5,-9),    size=1.25,             color=(0.5,0.5,0.5), rotation=[15, -25, -21])
GridCube     =   Cube(position=(-1.3,2,-9),       size=1.25,             color=(1,0,0),       rotation=[0,0,0])
ButtonSphere = Sphere(position=(0.7,-0.2,-8.5),   radius=0.85,           color=(0.5,0.5,0.5))
ButtonCone   =   Cone(position=(6,-3.5,-10),      radius=.5,   height=1, color=(0.5,0.5,0.5), rotation=[-120,23,-35])

def check_hover(x, y):
    global cube_hover, sphere_hover, cone_hover
    
    # get ray from mouse position
    ray_origin, ray_dir = get_ray_from_mouse(x, y)
    
    # check cube
    cube_pos   = ButtonCube.position
    cube_size  = 1.25
    box_min    = np.array([cube_pos[0], cube_pos[1], cube_pos[2]])
    box_max    = np.array([cube_pos[0] + cube_size, cube_pos[1] + cube_size, cube_pos[2] + cube_size])
    cube_hover = aabb_ray_intersection(ray_origin, ray_dir, box_min, box_max)
    
    # check sphere
    sphere_pos    = ButtonSphere.position
    sphere_radius = 0.85
    box_min       = np.array([sphere_pos[0], sphere_pos[1], sphere_pos[2]])
    box_max       = np.array([sphere_pos[0] + sphere_radius, sphere_pos[1] + sphere_radius, sphere_pos[2] + sphere_radius])
    sphere_hover  = aabb_ray_intersection(ray_origin, ray_dir, box_min, box_max)
    
    # check cone
    cone_pos    = ButtonCone.position
    cone_radius = 0.5
    cone_height = 1
    box_min     = np.array([cone_pos[0], cone_pos[1], cone_pos[2]])
    box_max     = np.array([cone_pos[0] + cone_radius, cone_pos[1] + cone_height, cone_pos[2] + cone_radius])
    cone_hover  = aabb_ray_intersection(ray_origin, ray_dir, box_min, box_max)

def motion_func(x, y):
    global mouse_x, mouse_y, sphere
    mouse_x = x
    mouse_y = y
    if not sphere:
        camera.handle_mouse(x, y)
        check_hover(x, y)

def update_hover_animations():
    global last_time, prev_hover_states
    current_time = glutGet(GLUT_ELAPSED_TIME)
    delta_time   = (current_time - last_time) / 1000.0  # convert to seconds
    last_time    = current_time
    
    # update cube animation
    if cube_hover != prev_hover_states['cube']:  # hover state changed
        if cube_hover and not cone:  # just started hovering
            # play click sound
            pygame.mixer.Sound('assets/sound/click.wav').play()
            hover_timers['cube'] = 0  # reset timer
            hover_scale['cube'] = HOVER_SCALE_MAX  # start at max scale
        prev_hover_states['cube'] = cube_hover
    
    if cube_hover and not cube:
        hover_timers['cube'] += delta_time
        # smoothly return to normal scale over the duration
        progress = min(1.0, hover_timers['cube'] / HOVER_POP_DURATION)
        hover_scale['cube'] = HOVER_SCALE_MAX + (HOVER_SCALE_MIN - HOVER_SCALE_MAX) * progress
    else:
        hover_scale['cube'] = HOVER_SCALE_MIN
    
    # update sphere animation
    if sphere_hover != prev_hover_states['sphere']:
        if sphere_hover and not cone:
            pygame.mixer.Sound('assets/sound/click.wav').play()
            hover_timers['sphere'] = 0
            hover_scale['sphere'] = HOVER_SCALE_MAX
        prev_hover_states['sphere'] = sphere_hover
    
    if sphere_hover:
        hover_timers['sphere'] += delta_time
        progress = min(1.0, hover_timers['sphere'] / HOVER_POP_DURATION)
        hover_scale['sphere'] = HOVER_SCALE_MAX + (HOVER_SCALE_MIN - HOVER_SCALE_MAX) * progress
    else:
        hover_scale['sphere'] = HOVER_SCALE_MIN
    
    # update cone animation
    if cone_hover != prev_hover_states['cone']:
        if cone_hover and not cone:
            pygame.mixer.Sound('assets/sound/click.wav').play()
            hover_timers['cone'] = 0
            hover_scale['cone'] = HOVER_SCALE_MAX
        prev_hover_states['cone'] = cone_hover
    
    if cone_hover:
        hover_timers['cone'] += delta_time
        progress = min(1.0, hover_timers['cone'] / HOVER_POP_DURATION)
        hover_scale['cone'] = HOVER_SCALE_MAX + (HOVER_SCALE_MIN - HOVER_SCALE_MAX) * progress
    else:
        hover_scale['cone'] = HOVER_SCALE_MIN

graphicsdriver = Text2D(position=(WINDOWSIZE[0]/2,WINDOWSIZE[1]/2,0), text="WARNING: NO GRAPHICS DRIVER DETECTED PLEASE ENABLE A VALID GRAPHICS DRIVER", color=(1,0,0), scale=2.0, center=True, font=GLUT_STROKE_ROMAN) # type: ignore

def generate_coords():
    coords = []
    for i in range(3):
        # generate 3 groups of numbers spaced with two spaces between each character
        groups = []
        for i in range(3):  # 3 groups per coordinate
            # generate a random number between 0-999 and convert to string
            if i == 0:
                num = str(random.randint(0, 99))
            else:
                num = str(random.randint(0, 999))
            # split into individual digits and remove leading zeros
            digits = list(num.lstrip('0') if num != '0' else '0')
            # join digits with two spaces between them
            group = "  ".join(digits)
            groups.append(group)
        
        # join groups with comma and space
        coord = "  ,  ".join(groups)
        # add decimal point and two random digits at the end
        decimal = f"  .  {random.randint(0, 9)}  {random.randint(0, 9)}"
        coords.append(coord + decimal)
    
    return coords

headeryellow = rgb2color(204, 195, 50)
lightyellow  = rgb2color(224, 201, 94)
burntorange  = rgb2color(197, 92 , 43)
displayred   = rgb2color(185, 6  , 30)

x_display           = Text2D(position=(740/2,  (WINDOWSIZE[1]-120)/RATIO, 0), text="X",                                                        color=lightyellow , scale=1.5, thickness=2.0*RATIO, font=GLUT_STROKE_MONO_ROMAN) # type: ignore
y_display           = Text2D(position=(740/2,  (WINDOWSIZE[1]-145)/RATIO, 0), text="Y",                                                        color=lightyellow , scale=1.5, thickness=2.0*RATIO, font=GLUT_STROKE_MONO_ROMAN) # type: ignore
z_display           = Text2D(position=(740/2,  (WINDOWSIZE[1]-170)/RATIO, 0), text="Z",                                                        color=lightyellow , scale=1.5, thickness=2.0*RATIO, font=GLUT_STROKE_MONO_ROMAN) # type: ignore
xcoord_display      = Text2D(position=(790/2,  (WINDOWSIZE[1]-125)/RATIO, 0), text="0  0  ,  0  0  0  ,  0  0  0  .  0  0",                    color=displayred  , scale=1.9, thickness=3.0*RATIO, font=GLUT_STROKE_MONO_ROMAN) # type: ignore
ycoord_display      = Text2D(position=(790/2,  (WINDOWSIZE[1]-150)/RATIO, 0), text="0  0  ,  0  0  0  ,  0  0  0  .  0  0",                    color=displayred  , scale=1.9, thickness=3.0*RATIO, font=GLUT_STROKE_MONO_ROMAN) # type: ignore
zcoord_display      = Text2D(position=(790/2,  (WINDOWSIZE[1]-175)/RATIO, 0), text="0  0  ,  0  0  0  ,  0  0  0  .  0  0",                    color=displayred  , scale=1.9, thickness=3.0*RATIO, font=GLUT_STROKE_MONO_ROMAN) # type: ignore
connecting_display  = Text2D(position=(215  ,   WINDOWSIZE[1]/2   /RATIO, 0), text="CHECKING CONNECTION...",                                   color=displayred  , scale=2.0, thickness=3.0*RATIO, font=GLUT_STROKE_MONO_ROMAN) # type: ignore
location_display    = Text2D(position=(730/2,  (WINDOWSIZE[1]-40 )/RATIO, 0), text="LOCATED WFA3Y-A [INTERLOPE.DME]",                          color=headeryellow, scale=2.0, thickness=2.5*RATIO, font=GLUT_STROKE_MONO_ROMAN) # type: ignore
validator_display   = Text2D(position=(740/2,  (WINDOWSIZE[1]-80 )/RATIO, 0), text="VALIDATORS HAVE NOT BEEN VERIFIED, PLEASE CONTACT YOUR S", color=lightyellow , scale=1.5, thickness=2.0*RATIO, font=GLUT_STROKE_MONO_ROMAN) # type: ignore
metal_reg_display   = Text2D(position=(740/2,  (WINDOWSIZE[1]-200)/RATIO, 0), text="METAL_REG-",                                               color=lightyellow , scale=1.5, thickness=2.0*RATIO, font=GLUT_STROKE_MONO_ROMAN) # type: ignore
metal_reg_display_2 = Text2D(position=(1050/2, (WINDOWSIZE[1]-200)/RATIO, 0), text="NONE",                                                     color=burntorange , scale=1.3, thickness=2.0*RATIO, font=GLUT_STROKE_MONO_ROMAN) # type: ignore

def update_coordinates():
    coords = generate_coords()
    xcoord_display.text = coords[0]
    ycoord_display.text = coords[1]
    zcoord_display.text = coords[2]

if len(blue_boxes) < MAX_BLUE_BOXES:
    while len(blue_boxes) < MAX_BLUE_BOXES:
        blue_boxes.append(BlueBox())

def regen_floaters():
    for floater in floaters:
        floaters.remove(floater)
    while len(floaters) < MAX_FLOATERS:
        floaters.append(Floater())

connected = False
connectedbuffer = 0
completeconnection = False
shapen = False
def display():
    global last_frame_time, soundplay, connected, connectedbuffer, completeconnection, shapen
    
    # fps limiting
    current_time = time.time()
    delta = current_time - last_frame_time
    if delta < FRAME_TIME:
        time.sleep(FRAME_TIME - delta)
    last_frame_time = time.time()
    
    # clear buffers with black background
    gl.glClearColor(0.0, 0.0, 0.0, 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glLoadIdentity()
    
    # draw background based on sphere/cone state
    if not cone and not sphere:
        draw_background_quad(background_texture, apply_scale=True)
    
    # update light position to move with camera
    gl.glLight(gl.GL_LIGHT0, gl.GL_POSITION, (camera.pos[0] + 100, camera.pos[1] + 100, camera.pos[2] + 100, 1.0))
    
    camera.update()
    camera.apply()
    
    # update hover animations
    update_hover_animations()
    
    # update colors based on hover state
    if cube:
        ButtonCube.color = (0.0, 1.0, 1.0)
    elif cube_hover:
        ButtonCube.color = (1.0,0,0)
    else:
        ButtonCube.color = (0.5, 0.5, 0.5)
    ButtonSphere.color = (1.0, 0.0, 0.0) if sphere_hover else (0.5, 0.5, 0.5)
    ButtonCone.color   = (1.0, 0.0, 0.0) if cone_hover   else (0.5, 0.5, 0.5)
    
    # update cube position based on state
    if cube and not cone:
        # move up when clicked
        if not soundplay:
            pygame.mixer.Sound('assets/sound/friend_join.wav').play()
            soundplay = True
        ButtonCube.position = (
            initial_positions['cube'][0] + 0.4,
            initial_positions['cube'][1] + 0.5,
            initial_positions['cube'][2] - 1
        )
        ButtonCube.rotation = [
            ButtonCube.rotation[0],
            ButtonCube.rotation[1] + 0.3,
            ButtonCube.rotation[2]
        ]
        # save original size for hover animation
        orig_cube_size  = ButtonCube.size
        ButtonCube.size = orig_cube_size * hover_scale['cube']
        # disable lighting for cube
        gl.glDisable(gl.GL_LIGHTING)
        ButtonCube.render()
        gl.glEnable(gl.GL_LIGHTING)
        # restore original size
        ButtonCube.size = orig_cube_size
    else:
        # return to original position
        ButtonCube.rotation = [15, -25, -21]
        if not cone or sphere:
            # save original size for hover animation
            orig_cube_size  = ButtonCube.size
            ButtonCube.size = orig_cube_size * hover_scale['cube']
            ButtonCube.render()
            # restore original size
            ButtonCube.size = orig_cube_size
    
    orig_cube_size   = ButtonCube.size
    orig_sphere_size = ButtonSphere.size
    orig_cone_size   = ButtonCone.size
    orig_cone_height = ButtonCone.height
    
    ButtonCube.size   = orig_cube_size   * hover_scale['cube']
    ButtonSphere.size = orig_sphere_size * hover_scale['sphere']
    ButtonCone.size   = orig_cone_size   * hover_scale['cone']
    ButtonCone.height = orig_cone_height * hover_scale['cone']
    if not cone or sphere:
        ButtonSphere.render()
        ButtonCone.render()
    
    ButtonCube.size   = orig_cube_size
    ButtonSphere.size = orig_sphere_size
    ButtonCone.size   = orig_cone_size
    ButtonCone.height = orig_cone_height
    


    if cone:
        viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
        connectedbuffer += 1
        if random.random() > 0.66 and connectedbuffer < 450 * RATIO_TO_SIXTY:
            connected = False
        else:
            connected = True
        
        if connectedbuffer < 15:
            reshape(WINDOWSIZE[1], WINDOWSIZE[1])
            shapen = True
        else:
            reshape(*WINDOWSIZE)
            shapen = False
        print(connectedbuffer)
        if connectedbuffer > 450 * RATIO_TO_SIXTY:
            completeconnection = True

        # draw grid
        if connected:
            draw_grid()
            draw_tracked_sphere()
            gl.glDisable(gl.GL_LIGHTING)
            if tracker_active:
                draw_tracking_cone()
            draw_tracked_sphere()
            gl.glEnable(gl.GL_LIGHTING)
            # render all active blue boxes
            for box in blue_boxes:
                box.render()
            for floater in floaters:
                floater.update()
                floater.object.render()

            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glPushMatrix()
            gl.glLoadIdentity()
            gl.glOrtho(0, viewport[2], 0, viewport[3], -1, 1)

            # save modelview matrix and reset it
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glPushMatrix()
            gl.glLoadIdentity()

            # disable depth test so quad draws on top
            gl.glDisable(gl.GL_DEPTH_TEST)
            gl.glDisable(gl.GL_LIGHTING)
            

            # enable blending for transparency
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

            # enable and bind the texture
            gl.glEnable(gl.GL_TEXTURE_2D)
            gl.glBindTexture(gl.GL_TEXTURE_2D, overlay_texture)

            # make overlay transparent
            gl.glColor4f(1.0, 1.0, 1.0, 0.05)

            gl.glBegin(gl.GL_QUADS)
            gl.glTexCoord2f(0.0, 0.0); gl.glVertex2f(0, 0)
            gl.glTexCoord2f(1.0, 0.0); gl.glVertex2f(viewport[2], 0)
            gl.glTexCoord2f(1.0, 1.0); gl.glVertex2f(viewport[2], viewport[3])
            gl.glTexCoord2f(0.0, 1.0); gl.glVertex2f(0, viewport[3])
            gl.glEnd()

            # draw letterbox bars on top of the overlay
            screen_width = viewport[2]
            screen_height = viewport[3]

            # render text overlays using text2d
            gl.glDisable(gl.GL_TEXTURE_2D)
            if completeconnection:
                location_display.render()
                validator_display.render()
                x_display.render()
                y_display.render()
                z_display.render()
                xcoord_display.render()
                ycoord_display.render()
                zcoord_display.render()
                metal_reg_display.render()
                metal_reg_display_2.render()
            else:
                if random.random() > 0.5:
                    connecting_display.render()

            # solid black bars (adjust alpha here if needed)
            
            gl.glColor4f(0.0, 0.0, 0.0, 1.0)
            gl.glBegin(gl.GL_QUADS)
            pad = (screen_width - screen_height) // 2
            if connectedbuffer > 15 * RATIO_TO_SIXTY and not shapen:
                # left bar
                gl.glVertex2f(0, 0)
                gl.glVertex2f(pad, 0)
                gl.glVertex2f(pad, screen_height)
                gl.glVertex2f(0, screen_height)
                # right bar  
                gl.glVertex2f(screen_width - pad, 0)
                gl.glVertex2f(screen_width, 0)
                gl.glVertex2f(screen_width, screen_height)
                gl.glVertex2f(screen_width - pad, screen_height)
            gl.glEnd()

            gl.glDisable(gl.GL_TEXTURE_2D)
            # clean up
            gl.glDisable(gl.GL_TEXTURE_2D)
            gl.glDisable(gl.GL_BLEND)
            gl.glEnable(gl.GL_DEPTH_TEST)

            # restore projection and modelview matrices
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glPopMatrix()
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glPopMatrix()

        
    if sphere:
        draw_background_quad(background_texture_alt, apply_scale=False)
        pygame.mixer.music.set_volume(0)
        if random.randint(0, 60) > 50:
            graphicsdriver.render()
    draw_cursor()
    glutSwapBuffers()
    glutPostRedisplay()

def reshape(width, height):
    if height == 0:
        height = 1
    
    # update viewport and projection
    gl.glViewport(0, 0, width, height)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gluPerspective(45.0, float(width)/float(height), 0.1, FARPLANE)
    gl.glMatrixMode(gl.GL_MODELVIEW)

def keyboard(key, x, y):
    if key == b'\x1b':  # escape key
        sys.exit(0)
    else:
        camera.keys_pressed.add(key)

def keyboard_up(key, x, y):
    if key in camera.keys_pressed:
        camera.keys_pressed.remove(key)

def get_ray_from_mouse(x, y):
    # get the viewport and projection matrix for ray calculation
    viewport   = gl.glGetIntegerv(gl.GL_VIEWPORT)
    projection = gl.glGetDoublev(gl.GL_PROJECTION_MATRIX)
    modelview  = gl.glGetDoublev(gl.GL_MODELVIEW_MATRIX)
    
    # convert window coordinates to normalized device coordinates
    y = viewport[3] - y - 1  # flip y coordinate to match opengl coordinate system
    
    # calculate world space coordinates for near and far points
    near = gluUnProject(x, y, 0.0, modelview, projection, viewport)
    far  = gluUnProject(x, y, 1.0, modelview, projection, viewport)
    
    # calculate normalized ray direction
    ray_dir = np.array(far) - np.array(near)
    ray_dir = ray_dir / np.linalg.norm(ray_dir)
    
    return np.array(near), ray_dir

def aabb_ray_intersection(ray_origin, ray_dir, box_min, box_max):
    # calculate intersection with axis-aligned bounding box
    t_min = float('-inf')
    t_max = float('inf')
    
    for i in range(3):
        if abs(ray_dir[i]) < 1e-8:
            if ray_origin[i] < box_min[i] or ray_origin[i] > box_max[i]:
                return False
        else:
            t1 = (box_min[i] - ray_origin[i]) / ray_dir[i]
            t2 = (box_max[i] - ray_origin[i]) / ray_dir[i]
            
            if t1 > t2:
                t1, t2 = t2, t1
                
            t_min = max(t_min, t1)
            t_max = min(t_max, t2)
            
            if t_min > t_max:
                return False
    
    return True

def mouse_click(button, state, x, y):
    global cube, sphere, cone
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not sphere and not cone:
        # get ray from mouse position for intersection testing
        ray_origin, ray_dir = get_ray_from_mouse(x, y)
        
        # check intersection with all objects
        cube_pos  = ButtonCube.position
        cube_size = 1.25
        box_min   = np.array([cube_pos[0], cube_pos[1], cube_pos[2]])
        box_max   = np.array([cube_pos[0] + cube_size, cube_pos[1] + cube_size, cube_pos[2] + cube_size])
        
        # handle cube interaction
        if aabb_ray_intersection(ray_origin, ray_dir, box_min, box_max):
            if not cube:
                cube = True
            else:
                ButtonCube.rotation = [15, -25, -21]  # reset cube rotation
            return
        
        # handle sphere interaction
        sphere_pos    = ButtonSphere.position
        sphere_radius = 0.85

        box_min = np.array([sphere_pos[0], sphere_pos[1], sphere_pos[2]])
        box_max = np.array([sphere_pos[0] + sphere_radius, sphere_pos[1] + sphere_radius, sphere_pos[2] + sphere_radius])
        
        if aabb_ray_intersection(ray_origin, ray_dir, box_min, box_max):
            sphere = not sphere  # toggle sphere state
            return

        # handle cone interaction
        cone_pos    = ButtonCone.position
        cone_radius = 0.5
        cone_height = 1

        box_min = np.array([cone_pos[0], cone_pos[1], cone_pos[2]])
        box_max = np.array([cone_pos[0] + cone_radius, cone_pos[1] + cone_height, cone_pos[2] + cone_radius])
        
        if aabb_ray_intersection(ray_origin, ray_dir, box_min, box_max):
            pygame.mixer.Sound('assets/sound/cone.wav').play()
            time.sleep(2)
            cone = not cone  # toggle cone state
            return

def main():
    # initialize opengl and create window
    glutInit()
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    
    # calculate window position for center placement
    screen_width  = glutGet(GLUT_SCREEN_WIDTH)
    screen_height = glutGet(GLUT_SCREEN_HEIGHT)
    window_x      = (screen_width - WINDOWSIZE[0]) // 2
    window_y      = (screen_height - WINDOWSIZE[1]) // 2
    
    # set window properties
    glutInitWindowSize(*WINDOWSIZE)
    glutInitWindowPosition(window_x, window_y)
    glutCreateWindow(b"sourcebox.exe")
    
    # initialize opengl state and resources
    init()
    
    # hide the cursor
    glutSetCursor(GLUT_CURSOR_NONE)
    
    # register callback functions
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutPassiveMotionFunc(motion_func)
    glutMotionFunc(motion_func)
    glutMouseFunc(mouse_click)  # register mouse click handler
    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # start timers
    glutTimerFunc(5000, update_factor, 0)
    # set background color and start main loop
    gl.glClearColor(0,0,0, 1.0)  # black background
    glutMainLoop()

if __name__ == "__main__":
    main()

