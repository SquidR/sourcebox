import OpenGL.GL as gl
from PIL import Image
import numpy as np

def load_texture(image_path):
    img = Image.open(image_path).convert("RGBA")

    image_data = img.tobytes("raw", "RGBA")
    width, height = img.size

    texid = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texid)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0,
                 gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, image_data)

    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

    return texid, width, height

def draw_background_quad(texture_id, apply_scale=True):
    # save current matrix mode and attributes
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    
    # save states
    gl.glPushAttrib(gl.GL_ALL_ATTRIB_BITS)
    
    # disable depth testing and lighting for background
    gl.glDisable(gl.GL_DEPTH_TEST)
    gl.glDisable(gl.GL_LIGHTING)
    
    # enable texturing
    gl.glEnable(gl.GL_TEXTURE_2D)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
    
    gl.glColor4f(1.3, 1.3, 1.3, 1.0)
    
    gl.glBegin(gl.GL_QUADS)
    if apply_scale:
        # original scaled version with proper aspect ratio
        target_aspect_ratio = 16.0 / 9.0
        tex_height = 1.1
        tex_width = tex_height * target_aspect_ratio
        
        left = 0.5 - (tex_width / 2)
        right = 0.5 + (tex_width / 2)
        bottom = 0.5 - (tex_height / 2)
        top = 0.5 + (tex_height / 2)
        
        # scale factor for the quad
        scale = 3
        
        gl.glTexCoord2f(left, top); gl.glVertex2f(-scale, -scale)
        gl.glTexCoord2f(right, top); gl.glVertex2f(scale, -scale)
        gl.glTexCoord2f(right, bottom); gl.glVertex2f(scale, scale) 
        gl.glTexCoord2f(left, bottom); gl.glVertex2f(-scale, scale)
    else:
        gl.glTexCoord2f(0.0, 1.0); gl.glVertex3f(-1.0, -1.0, -1.0)
        gl.glTexCoord2f(1.0, 1.0); gl.glVertex3f(1.0, -1.0, -1.0)
        gl.glTexCoord2f(1.0, 0.0); gl.glVertex3f(1.0, 1.0, -1.0)
        gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(-1.0, 1.0, -1.0)
    gl.glEnd()
    
    # restore states
    gl.glPopAttrib()
    
    # restore matrices
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPopMatrix()
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPopMatrix() 