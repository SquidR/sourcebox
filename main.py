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
# Start background music
pygame.mixer.music.load('assets/sound/sourcebox.wav')
pygame.mixer.music.set_volume(0.5)  # Optional: set volume (0.0 to 1.0)
pygame.mixer.music.play(-1)  # Loop forever
# window and display settings
WINDOWSIZE = (1600, 900)  # 16:9 aspect ratio for modern displays
MOVESPEED = 0            # base movement speed
MOUSESENSITIVITY = 0  # mouse sensitivity for camera control
TARGET_FPS = 144        # target frame rate
FRAME_TIME = 1.0 / TARGET_FPS  # time per frame in seconds
mouse_x = 0
mouse_y = 0

# texture management
background_texture = None         # main background texture
background_texture_alt = None     # alternative background texture
overlay_texture = None           # overlay texture for cone mode
cursor_texture = None           # cursor texture
texture_width = 0                 # texture width in pixels
texture_height = 0                # texture height in pixels

# interactive object states
cube_hover = False    # track if mouse is hovering over cube
sphere_hover = False  # track if mouse is hovering over sphere
cone_hover = False    # track if mouse is hovering over cone

# animation and timing
last_time = 0  # last frame timestamp
hover_scale = {'cube': 1.0, 'sphere': 1.0, 'cone': 1.0}  # current scale for each object
hover_timers = {'cube': 0, 'sphere': 0, 'cone': 0}       # animation timers
prev_hover_states = {'cube': False, 'sphere': False, 'cone': False}  # previous hover states

# object positioning
initial_positions = {}  # store initial positions of objects

# animation constants
HOVER_SCALE_MAX = 1.1     # maximum scale during pop animation
HOVER_SCALE_MIN = 1.0     # normal scale (no animation)
HOVER_POP_DURATION = 0.06 # duration of pop animation in seconds

blue_boxes = []
MAX_BLUE_BOXES = 5
BLUE_BOX_LIFETIME = 60 
BLUE_BOX_SPAWN_CHANCE = 0.1
def draw_cursor():
    global mouse_x, mouse_y, cursor_texture
    
    # Save current matrices and attributes
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    viewport = glGetIntegerv(GL_VIEWPORT)
    glOrtho(0, viewport[2], viewport[3], 0, -1, 1)  # 2D orthographic projection
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Save states and disable depth test for 2D drawing
    glPushAttrib(GL_ALL_ATTRIB_BITS)
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    # Enable blending for transparency
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Enable texturing
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, cursor_texture)
    
    # Set color to white to show texture as is
    glColor4f(1, 1, 1, 1)

    x = mouse_x
    y = mouse_y
    
    # Draw cursor quad
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(x, y)
    glTexCoord2f(1, 0); glVertex2f(x + 32, y)
    glTexCoord2f(1, 1); glVertex2f(x + 32, y + 32)
    glTexCoord2f(0, 1); glVertex2f(x, y + 32)
    glEnd()
    
    # Clean up
    glBindTexture(GL_TEXTURE_2D, 0)
    glDisable(GL_TEXTURE_2D)
    
    # Restore previous states
    glPopAttrib()
    
    # Restore matrices
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

class Camera:
    def __init__(self):
        self.pos = [0,0, 0]  # camera position in 3d space
        self.rot = [0,0,0]  # camera rotation (pitch, yaw, roll)
        self.move_speed = MOVESPEED  # camera movement speed
        self.mouse_sensitivity = MOUSESENSITIVITY  # mouse look sensitivity
        self.last_mouse = (WINDOWSIZE[0] / 2, WINDOWSIZE[1] / 2)  # previous mouse position
        self.keys_pressed = set()  # currently pressed keys
        self.first_mouse = True    # flag for first mouse movement
        self.window_center = (WINDOWSIZE[0] / 2, WINDOWSIZE[1] / 2)  # window center coordinates

    def update(self):
        # handle continuous keyboard movement
        forward = math.sin(math.radians(self.rot[1]))  # forward direction vector
        right = math.cos(math.radians(self.rot[1]))    # right direction vector
        
        # process movement based on pressed keys
        if b'w' in self.keys_pressed:  # move forward
            self.pos[0] -= forward * self.move_speed
            self.pos[2] -= right * self.move_speed
        if b's' in self.keys_pressed:  # move backward
            self.pos[0] += forward * self.move_speed
            self.pos[2] += right * self.move_speed
        if b'a' in self.keys_pressed:  # strafe left
            self.pos[0] -= right * self.move_speed
            self.pos[2] += forward * self.move_speed
        if b'd' in self.keys_pressed:  # strafe right
            self.pos[0] += right * self.move_speed
            self.pos[2] -= forward * self.move_speed
        if b' ' in self.keys_pressed:  # move up
            self.pos[1] += self.move_speed
        if b'z' in self.keys_pressed:  # move down
            self.pos[1] -= self.move_speed

    def handle_mouse(self, x, y):
        if self.first_mouse:
            self.last_mouse = (x, y)
            self.first_mouse = False
            return

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

        # handle mouse wrapping at window edges
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

    def apply(self):
        gl.glRotatef(-self.rot[0], 1, 0, 0)  # pitch rotation
        gl.glRotatef(-self.rot[1], 0, 1, 0)  # yaw rotation
        gl.glTranslatef(-self.pos[0], -self.pos[1], -self.pos[2])

# global variables
base_factor = 4
factor = base_factor
grid_size = 256 * int((factor/2))
grid_spacing = 128 * (1/factor)
# separate offsets for each grid plane
floor_offset = {'x': 0, 'y': 0, 'z': 0}
front_wall_offset = {'x': 0, 'y': 0, 'z': 0}
side_wall_offset = {'x': 0, 'y': 0, 'z': 0}

# list to store multiple grid offsets
grid_offsets = [
    {'x': 0, 'y': 0, 'z': 0},
    {'x': 0, 'y': 0, 'z': 0},
    {'x': 0, 'y': 0, 'z': 0}
]

camera = Camera()

def rgb2color(r, g, b):
    return (r/255.0, g/255.0, b/255.0)

def update_factor(value):
    global camera, factor, grid_size, grid_spacing, floor_offset, front_wall_offset, side_wall_offset, grid_offsets
    # get random factor between 1 and n
    factor = random.randint(1, 8)
    grid_size = 64 * int((factor/2))
    grid_spacing = 32 * factor*2
    
    # update random offsets for each grid independently (-50 to 50 units)
    offsetcap = 1000 * factor/2
    floor_offset.update({
        'x': random.uniform(-offsetcap, offsetcap),
        'y': random.uniform(-offsetcap, offsetcap),
        'z': random.uniform(-offsetcap, offsetcap)
    })
    front_wall_offset.update({
        'x': random.uniform(-offsetcap, offsetcap),
        'y': random.uniform(-offsetcap, offsetcap),
        'z': random.uniform(-offsetcap, offsetcap)
    })
    side_wall_offset.update({
        'x': random.uniform(-offsetcap, offsetcap),
        'y': random.uniform(-offsetcap, offsetcap),
        'z': random.uniform(-offsetcap, offsetcap)
    })

    # update offsets for each grid instance
    for offset in grid_offsets:
        offset.update({
            'x': random.uniform(-offsetcap*4, offsetcap*4),
            'y': random.uniform(-offsetcap*4, offsetcap*4),
            'z': random.uniform(-offsetcap*4, offsetcap*4)
        })
    update_coordinates()
    if cone:
        camera.rot = [random.randint(-180, 180), random.randint(-180, 180), random.randint(-180, 180)]
    glutTimerFunc(1000, update_factor, 0)

def draw_grid():
    global metalreg, metal_reg_display_2
    # temporarily disable lighting for grid lines
    gl.glDisable(gl.GL_LIGHTING)
    if random.randint(0,5) == 2:
        metal_reg_display_2.text = metalreg[random.randint(0, len(metalreg)-1)]
    
    # set initial line properties
    gl.glColor3f(0.5, 0.5, 0.5)  # set default grid color to gray
    blank = gl.glColor4f(0, 0, 0, 0)
    def set_line_width(n):
        # set line width and color based on grid subdivision
        if not n % 128 * factor/2:
            gl.glLineWidth(4.0)  # major grid lines
            gl.glColor3f(*rgb2color(101,55,0))  # red color
        elif not n % 64 * factor/2:
            gl.glLineWidth(3.0)  # medium grid lines
            gl.glColor3f(*rgb2color(164, 49, 28))  # green color
        elif not n % 32 * factor/2:
            gl.glLineWidth(2.0)  # minor grid lines
            gl.glColor3f(*rgb2color(100, 21, 13))  # blue color
        else:
            gl.glLineWidth(1.0)  # smallest grid lines
            gl.glColor4f(0, 0, 0, 0)  # black color with 0 alpha
    
    # draw horizontal grid (floor)
    def create_floor_lines(offset):
        for i in range(-grid_size, grid_size + 1):  # create x-axis lines
            if i % 32 * factor/2 == 0:  # only draw lines that aren't the smallest subdivision
                set_line_width(i)
                draw_line((i * grid_spacing + floor_offset['x'] + offset['x'], floor_offset['y'] + offset['y'], -grid_size * grid_spacing + floor_offset['z'] + offset['z']), 
                        (i * grid_spacing + floor_offset['x'] + offset['x'], floor_offset['y'] + offset['y'], grid_size * grid_spacing + floor_offset['z'] + offset['z']))

        for i in range(-grid_size, grid_size + 1):  # create z-axis lines
            if i % 32 * factor/2 == 0:  # only draw lines that aren't the smallest subdivision
                set_line_width(i)
                draw_line((-grid_size * grid_spacing + floor_offset['x'] + offset['x'], floor_offset['y'] + offset['y'], i * grid_spacing + floor_offset['z'] + offset['z']), 
                        (grid_size * grid_spacing + floor_offset['x'] + offset['x'], floor_offset['y'] + offset['y'], i * grid_spacing + floor_offset['z'] + offset['z']))

    # draw vertical grid (front wall)
    def create_front_wall_lines(offset):
        for i in range(-grid_size, grid_size + 1): # create vertical lines
            if i % 32 * factor/2 == 0:  # only draw lines that aren't the smallest subdivision
                set_line_width(i)
                draw_line((front_wall_offset['x'] + offset['x'], -grid_size * grid_spacing + front_wall_offset['y'] + offset['y'], i * grid_spacing + front_wall_offset['z'] + offset['z']), 
                        (front_wall_offset['x'] + offset['x'], grid_size * grid_spacing + front_wall_offset['y'] + offset['y'], i * grid_spacing + front_wall_offset['z'] + offset['z']))

        for i in range(-grid_size, grid_size + 1): # create horizontal lines
            if i % 32 * factor/2 == 0:  # only draw lines that aren't the smallest subdivision
                set_line_width(i)
                draw_line((front_wall_offset['x'] + offset['x'], i * grid_spacing + front_wall_offset['y'] + offset['y'], -grid_size * grid_spacing + front_wall_offset['z'] + offset['z']), 
                        (front_wall_offset['x'] + offset['x'], i * grid_spacing + front_wall_offset['y'] + offset['y'], grid_size * grid_spacing + front_wall_offset['z'] + offset['z']))

    # draw vertical grid (side wall)
    def create_side_wall_lines(offset):
        for i in range(-grid_size, grid_size + 1): # create vertical lines
            if i % 32 * factor/2 == 0:  # only draw lines that aren't the smallest subdivision
                set_line_width(i)
                draw_line((i * grid_spacing + side_wall_offset['x'] + offset['x'], -grid_size * grid_spacing + side_wall_offset['y'] + offset['y'], side_wall_offset['z'] + offset['z']), 
                        (i * grid_spacing + side_wall_offset['x'] + offset['x'], grid_size * grid_spacing + side_wall_offset['y'] + offset['y'], side_wall_offset['z'] + offset['z']))

        for i in range(-grid_size, grid_size + 1): # create horizontal lines
            if i % 32 * factor/2 == 0:  # only draw lines that aren't the smallest subdivision
                set_line_width(i)
                draw_line((-grid_size * grid_spacing + side_wall_offset['x'] + offset['x'], i * grid_spacing + side_wall_offset['y'] + offset['y'], side_wall_offset['z'] + offset['z']), 
                        (grid_size * grid_spacing + side_wall_offset['x'] + offset['x'], i * grid_spacing + side_wall_offset['y'] + offset['y'], side_wall_offset['z'] + offset['z']))

    # draw multiple grids using the stored offsets
    for offset in grid_offsets:
        create_front_wall_lines(offset)
        create_side_wall_lines(offset)
        create_floor_lines(offset)
    
    # re-enable lighting after grid drawing
    gl.glEnable(gl.GL_LIGHTING)

def init():
    global background_texture, background_texture_alt, overlay_texture, texture_width, texture_height, last_frame_time, cursor_texture
    
    # initialize frame timing
    last_frame_time = time.time()
    
    # load both background textures and get dimensions
    background_texture, texture_width, texture_height = load_texture('assets/img/checkerboard.png')
    background_texture_alt, _, _ = load_texture('assets/img/checkerboardmissing.png')
    overlay_texture, _, _ = load_texture('assets/img/checkerboardoverlay.png')
    
    # Load cursor texture and verify it loaded correctly
    try:
        cursor_texture, cursor_width, cursor_height = load_texture('assets/img/cursor.png')
        print(f"Cursor texture loaded successfully: ID={cursor_texture}, Size={cursor_width}x{cursor_height}")
    except Exception as e:
        print(f"Error loading cursor texture: {e}")
        # Fallback to a simple generated texture if loading fails
        cursor_texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, cursor_texture)
        # Create a simple white texture as fallback
        pixel_data = [255, 255, 255, 255] * 16 * 16  # 16x16 white texture with alpha
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, 16, 16, 0,
                     gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, pixel_data)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        print("Created fallback cursor texture")
    # store initial positions
    initial_positions['cube'] = list(ButtonCube.position)
    
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
    
    # set up light 0 properties
    gl.glLight(gl.GL_LIGHT0, gl.GL_POSITION, (0.0, 0.0, -100.0, 1.0))
    gl.glLight(gl.GL_LIGHT0, gl.GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
    gl.glLight(gl.GL_LIGHT0, gl.GL_DIFFUSE, (0.6, 0.6, 0.6, 1.0))
    gl.glLight(gl.GL_LIGHT0, gl.GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))
    
    # set up material properties
    gl.glMaterial(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))
    gl.glMaterial(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, 0.0)


cone = False
cube = False
sphere = False

ButtonCube = Cube(position=(-1.3,-0.5,-9), size=1.25, color=(0.5,0.5,0.5), rotation=[15, -25, -21])
ButtonSphere = Sphere(position=(0.7,-0.2,-8.5), radius=0.85, color=(0.5,0.5,0.5))
ButtonCone = Cone(position=(6,-3.5,-10), radius=.5, height=1, color=(0.5,0.5,0.5), rotation=[-120,23,-35])

def check_hover(x, y):
    global cube_hover, sphere_hover, cone_hover
    
    # get ray from mouse position
    ray_origin, ray_dir = get_ray_from_mouse(x, y)
    
    # check cube
    cube_pos = ButtonCube.position
    cube_size = 1.25
    box_min = np.array([cube_pos[0], cube_pos[1], cube_pos[2]])
    box_max = np.array([cube_pos[0] + cube_size, cube_pos[1] + cube_size, cube_pos[2] + cube_size])
    cube_hover = aabb_ray_intersection(ray_origin, ray_dir, box_min, box_max)
    
    # check sphere
    sphere_pos = ButtonSphere.position
    sphere_radius = 0.85
    box_min = np.array([sphere_pos[0], sphere_pos[1], sphere_pos[2]])
    box_max = np.array([sphere_pos[0] + sphere_radius, sphere_pos[1] + sphere_radius, sphere_pos[2] + sphere_radius])
    sphere_hover = aabb_ray_intersection(ray_origin, ray_dir, box_min, box_max)
    
    # check cone
    cone_pos = ButtonCone.position
    cone_radius = 0.5
    cone_height = 1
    box_min = np.array([cone_pos[0], cone_pos[1], cone_pos[2]])
    box_max = np.array([cone_pos[0] + cone_radius, cone_pos[1] + cone_height, cone_pos[2] + cone_radius])
    cone_hover = aabb_ray_intersection(ray_origin, ray_dir, box_min, box_max)

def motion_func(x, y):
    global mouse_x, mouse_y
    mouse_x = x
    mouse_y = y
    global sphere
    if not sphere:
        camera.handle_mouse(x, y)
        check_hover(x, y)

def update_hover_animations():
    global last_time, prev_hover_states
    current_time = glutGet(GLUT_ELAPSED_TIME)
    delta_time = (current_time - last_time) / 1000.0  # convert to seconds
    last_time = current_time
    
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

# add text objects after the graphicsdriver definition
graphicsdriver = Text2D(position=(WINDOWSIZE[0]/2,WINDOWSIZE[1]/2,0), text="WARNING: NO GRAPHICS DRIVER DETECTED PLEASE ENABLE A VALID GRAPHICS DRIVER", color=(1,0,0), scale=2.0, center=True, font=GLUT_STROKE_ROMAN)

# add cone mode text objects with adjusted positions and larger scale
location_display = Text2D(position=(750/2, WINDOWSIZE[1]-40, 0), text="LOCATED WFA3Y-A [INTERLOPE.DME]", color=(1,1,0), scale=1.5, font=GLUT_STROKE_MONO_ROMAN)
validator_display = Text2D(position=(750/2, WINDOWSIZE[1]-80, 0), text="VALIDATORS HAVE NOT BEEN VERIFIED, PLEASE CONTACT YOUR S", color=(1,1,0), scale=1.5, font=GLUT_STROKE_MONO_ROMAN)
metal_reg_display = Text2D(position=(750/2, WINDOWSIZE[1]-200, 0), text="METAL_REG-", color=(1,1,0), scale=1.5, font=GLUT_STROKE_MONO_ROMAN)
metal_reg_display_2 = Text2D(position=(1060/2, WINDOWSIZE[1]-200, 0), text="NONE", color=(1,0.6,0), scale=1.3, font=GLUT_STROKE_MONO_ROMAN)

# coordinate displays with adjusted positions and larger scale
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

# create coordinate displays
x_display = Text2D(position=(750/2, WINDOWSIZE[1]-120, 0), text="X", color=(1,1,0), scale=1.5, font=GLUT_STROKE_MONO_ROMAN)
y_display = Text2D(position=(750/2, WINDOWSIZE[1]-145, 0), text="Y", color=(1,1,0), scale=1.5, font=GLUT_STROKE_MONO_ROMAN)
z_display = Text2D(position=(750/2, WINDOWSIZE[1]-170, 0), text="Z", color=(1,1,0), scale=1.5, font=GLUT_STROKE_MONO_ROMAN)
xcoord_display = Text2D(position=(800/2, WINDOWSIZE[1]-125, 0), text="2  2  ,  4  0  8  ,  0  6  9  .  2  9", color=(1,0,0), scale=1.9, font=GLUT_STROKE_MONO_ROMAN)
ycoord_display = Text2D(position=(800/2, WINDOWSIZE[1]-150, 0), text="2  7  ,  5  7  2  ,  9  8  4  .  2  1", color=(1,0,0), scale=1.9, font=GLUT_STROKE_MONO_ROMAN)
zcoord_display = Text2D(position=(800/2, WINDOWSIZE[1]-175, 0), text="4  4  ,  6  9  0  ,  6  7  9  .  1  7", color=(1,0,0), scale=1.9, font=GLUT_STROKE_MONO_ROMAN)

def update_coordinates():
    coords = generate_coords()
    xcoord_display.text = coords[0]
    ycoord_display.text = coords[1]
    zcoord_display.text = coords[2]

class BlueBox:
    def __init__(self):
        self.reset_position()
        self.rotation = [0,0,0]  # random rotation on all axes
    
    def reset_position(self):
        # position relative to camera
        distance = random.uniform(500, 2000)  # distance from camera
        angle_h = random.uniform(0, 360)  # horizontal angle
        angle_v = random.uniform(-45, 45)  # vertical angle
        
        # convert spherical coordinates to cartesian
        self.x = distance * math.cos(math.radians(angle_v)) * math.cos(math.radians(angle_h))
        self.y = distance * math.sin(math.radians(angle_v))
        self.z = distance * math.cos(math.radians(angle_v)) * math.sin(math.radians(angle_h))
        
        self.size = random.uniform(50, 200)
        self.alpha = 0.3
    
    def update(self, camera_pos):        
        # check if box is too far from camera
        distance = math.sqrt((self.x - camera_pos[0])**2 + 
                           (self.y - camera_pos[1])**2 + 
                           (self.z - camera_pos[2])**2)
        
        if distance > 3000:  # if too far, reset position
            self.reset_position()
            # add camera position to new coordinates
            self.x += camera_pos[0]
            self.y += camera_pos[1]
            self.z += camera_pos[2]
    
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
        
        # draw cube
        gl.glColor4f(0.0, 0.0, 1.0, self.alpha)
        
        # front face
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(self.size, 0, 0)
        gl.glVertex3f(self.size, self.size, 0)
        gl.glVertex3f(0, self.size, 0)
        gl.glEnd()
        
        # back face
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f(0, 0, self.size)
        gl.glVertex3f(self.size, 0, self.size)
        gl.glVertex3f(self.size, self.size, self.size)
        gl.glVertex3f(0, self.size, self.size)
        gl.glEnd()
        
        # right face
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f(self.size, 0, 0)
        gl.glVertex3f(self.size, 0, self.size)
        gl.glVertex3f(self.size, self.size, self.size)
        gl.glVertex3f(self.size, self.size, 0)
        gl.glEnd()
        
        # left face
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(0, 0, self.size)
        gl.glVertex3f(0, self.size, self.size)
        gl.glVertex3f(0, self.size, 0)
        gl.glEnd()
        
        # top face
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f(0, self.size, 0)
        gl.glVertex3f(self.size, self.size, 0)
        gl.glVertex3f(self.size, self.size, self.size)
        gl.glVertex3f(0, self.size, self.size)
        gl.glEnd()
        
        # bottom face
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(self.size, 0, 0)
        gl.glVertex3f(self.size, 0, self.size)
        gl.glVertex3f(0, 0, self.size)
        gl.glEnd()
        
        gl.glPopMatrix()
        gl.glDisable(gl.GL_BLEND)

def update_blue_boxes():
    global blue_boxes
    
    # initialize boxes if empty
    if len(blue_boxes) < MAX_BLUE_BOXES:
        while len(blue_boxes) < MAX_BLUE_BOXES:
            blue_boxes.append(BlueBox())
    
    # update existing boxes
    for box in blue_boxes:
        box.update(camera.pos)

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
def display():
    global last_frame_time, soundplay
    
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
    
    # draw background based on sphere state
    if not cone and not sphere:  # only draw normal background if neither cone nor sphere is active
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
    ButtonCone.color = (1.0, 0.0, 0.0) if cone_hover else (0.5, 0.5, 0.5)
    
    # update cube position based on state
    if cube and not cone:
        # move up when clicked
        if not soundplay:
            pygame.mixer.Sound('assets/sound/friend_join.wav').play()
            soundplay = True
        ButtonCube.position = (
            initial_positions['cube'][0]+0.4,
            initial_positions['cube'][1] + 0.5,
            initial_positions['cube'][2]-1
        )
        ButtonCube.rotation = [
            ButtonCube.rotation[0],
            ButtonCube.rotation[1]+0.3,
            ButtonCube.rotation[2]
        ]
        # save original size for hover animation
        orig_cube_size = ButtonCube.size
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
            orig_cube_size = ButtonCube.size
            ButtonCube.size = orig_cube_size * hover_scale['cube']
            ButtonCube.render()
            # restore original size
            ButtonCube.size = orig_cube_size
    
    orig_cube_size = ButtonCube.size
    orig_sphere_size = ButtonSphere.size
    orig_cone_size = ButtonCone.size
    orig_cone_height = ButtonCone.height
    
    ButtonCube.size = orig_cube_size * hover_scale['cube']
    ButtonSphere.size = orig_sphere_size * hover_scale['sphere']
    ButtonCone.size = orig_cone_size * hover_scale['cone']
    ButtonCone.height = orig_cone_height * hover_scale['cone']
    if not cone or sphere:
        ButtonSphere.render()
        ButtonCone.render()
    
    ButtonCube.size = orig_cube_size
    ButtonSphere.size = orig_sphere_size
    ButtonCone.size = orig_cone_size
    ButtonCone.height = orig_cone_height
    
    if cone:
        camera.move_speed = 0
        camera.mouse_sensitivity = 0
        
        viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
        
        # calculate dimensions for 1:1 aspect ratio
        size = min(viewport[2], viewport[3])
        x_offset = (viewport[2] - size) // 2
        y_offset = (viewport[3] - size) // 2
        
        # set viewport for grid
        gl.glViewport(x_offset, y_offset, size, size)
        
        # draw grid
        draw_grid()
        
        # update and render blue boxes
        update_blue_boxes()
        
        # render all active blue boxes
        for box in blue_boxes:
            box.render()
        
        # restore full viewport for overlay and text
        gl.glViewport(viewport[0], viewport[1], viewport[2], viewport[3])
        
        # draw black bars
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glOrtho(0, viewport[2], viewport[3], 0, -1, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        
        gl.glDisable(gl.GL_LIGHTING)
        gl.glDisable(gl.GL_DEPTH_TEST)
        
        # draw black letterboxing bars
        gl.glColor3f(0.0, 0.0, 0.0)
        
        # left black bar
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex2f(0, 0)
        gl.glVertex2f(x_offset, 0) 
        gl.glVertex2f(x_offset, viewport[3])
        gl.glVertex2f(0, viewport[3])
        gl.glEnd()
        
        # right black bar
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex2f(viewport[2] - x_offset, 0)
        gl.glVertex2f(viewport[2], 0)
        gl.glVertex2f(viewport[2], viewport[3])
        gl.glVertex2f(viewport[2] - x_offset, viewport[3])
        gl.glEnd()
        
        # draw overlay texture
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glBindTexture(gl.GL_TEXTURE_2D, overlay_texture)
        gl.glColor4f(1.0, 1.0, 1.0, 0.05)
        
        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord2f(0, 0); gl.glVertex2f(x_offset, viewport[3])
        gl.glTexCoord2f(1, 0); gl.glVertex2f(viewport[2] - x_offset, viewport[3])
        gl.glTexCoord2f(1, 1); gl.glVertex2f(viewport[2] - x_offset, 0)
        gl.glTexCoord2f(0, 1); gl.glVertex2f(x_offset, 0)
        gl.glEnd()
        
        gl.glDisable(gl.GL_TEXTURE_2D)
        
        # render text overlays using text2d
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
        gl.glDisable(gl.GL_BLEND)
        
        # restore 3d state
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_LIGHTING)
        
        # restore original matrices
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
    gluPerspective(45.0, float(width)/float(height), 0.1, 100000.0)
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
    viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
    projection = gl.glGetDoublev(gl.GL_PROJECTION_MATRIX)
    modelview = gl.glGetDoublev(gl.GL_MODELVIEW_MATRIX)
    
    # convert window coordinates to normalized device coordinates
    y = viewport[3] - y - 1  # flip y coordinate to match opengl coordinate system
    
    # calculate world space coordinates for near and far points
    near = gluUnProject(x, y, 0.0, modelview, projection, viewport)
    far = gluUnProject(x, y, 1.0, modelview, projection, viewport)
    
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
        
        # check intersection with all interactive objects
        cube_pos = ButtonCube.position
        cube_size = 1.25
        box_min = np.array([cube_pos[0], cube_pos[1], cube_pos[2]])
        box_max = np.array([cube_pos[0] + cube_size, cube_pos[1] + cube_size, cube_pos[2] + cube_size])
        
        # handle cube interaction
        if aabb_ray_intersection(ray_origin, ray_dir, box_min, box_max):
            if not cube:
                cube = True
            else:
                ButtonCube.rotation = [15, -25, -21]  # reset cube rotation
            return
        
        # handle sphere interaction
        sphere_pos = ButtonSphere.position
        sphere_radius = 0.85
        box_min = np.array([sphere_pos[0], sphere_pos[1], sphere_pos[2]])
        box_max = np.array([sphere_pos[0] + sphere_radius, sphere_pos[1] + sphere_radius, sphere_pos[2] + sphere_radius])
        
        if aabb_ray_intersection(ray_origin, ray_dir, box_min, box_max):
            sphere = not sphere  # toggle sphere state
            return

        # handle cone interaction
        cone_pos = ButtonCone.position
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
    screen_width = glutGet(GLUT_SCREEN_WIDTH)
    screen_height = glutGet(GLUT_SCREEN_HEIGHT)
    window_x = (screen_width - WINDOWSIZE[0]) // 2
    window_y = (screen_height - WINDOWSIZE[1]) // 2
    
    # set window properties
    glutInitWindowSize(*WINDOWSIZE)
    glutInitWindowPosition(window_x, window_y)
    glutCreateWindow(b"sourcebox.exe")
    
    # initialize opengl state and resources
    init()
    
    # Hide the cursor
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
    
    # start the factor update timer
    glutTimerFunc(5000, update_factor, 0)
    # set background color and start main loop
    gl.glClearColor(0,0,0, 1.0)  # black background
    glutMainLoop()

if __name__ == "__main__":
    main()

# helper function for calculating vertex normals
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
