"""
PyGL3Display
(C) David Griffin (2010-present)
"Habilain" is a pseudonym used by David Griffin in a number of places.

A high performance Pygame OpenGL library, capable of handling 1000s of sprites

Requirements: Python, Pygame, PyOpenGL, Open GL 2.0 graphics hardware

Licensed under GPLv2 or GPLv3. You should have received a copy of both of these
licenses in the files GPLv2.txt and GPLv3.txt. If not these licenses can be
found at http://www.gnu.org/licenses/gpl-2.0.html (GPLv2) and
http://www.gnu.org/licenses/gpl-3.0.html (GPLv3). By using this file you agree
to be bound by at least one of these licenses.

Other licenses, including commercial/proprietary licenses, can be arranged by 
contacting me via e-mail at habilain@gmail.com. If you do not have in 
writing an alternative license agreement from me, you must use one of the 
licenses specified above when releasing work which makes use of this library.

twodtexture.py

Provides TwoDTexture, an abstraction of a 2d texture, as well as some support
classes
"""

import ctypes
from array import array
from itertools import chain
from PyGL3Display.shaderdata import Uniform
import struct
from OpenGL.GL import (glTexImage2D, glGetTexLevelParameteriv,
    glGenTextures, glBindTexture, glTexParameteri, glTexSubImage2D,
    glGetIntegerv, glGetTexImage, glUniform1f,
    GL_PROXY_TEXTURE_2D, GL_TEXTURE_2D, GL_RGBA, GL_UNSIGNED_BYTE,
    GL_TEXTURE_WIDTH, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER,
    GL_NEAREST, GL_MAX_TEXTURE_SIZE, GL_FLOAT)
    
class TwoDTextureCommon(object):
    maxTextureSize = 4096
    minTextureSize = 512
    
    @classmethod
    def findTextureSize(cls, minsize=None, maxsize=None):
        """Function to determine maximum atlas size presently possible; 
        can specify a range that this has to be in as well."""
        if minsize is None: 
            minsize = cls.minTextureSize
        if maxsize is None: 
            maxsize = min(glGetIntegerv(GL_MAX_TEXTURE_SIZE), 
                          cls.maxTextureSize)
        size = maxsize
        while not cls.testSize(size):
            size >>= 1
        while not cls.testSize2(size):
            size >>= 1
        if size <= minsize:
            raise MemoryError('Cannot create an atlas of minimum size')        
        return size
            
    @staticmethod
    def testSize(texsize):
        """Helper function to determine maximum atlas size
        Arguments:
         texsize : test if an atlas of texsizextexsize can be created"""
        try:
            glTexImage2D(GL_PROXY_TEXTURE_2D, 0, GL_RGBA, 
                         texsize, texsize, 0,
                         GL_RGBA, GL_UNSIGNED_BYTE, None)
            return glGetTexLevelParameteriv(GL_PROXY_TEXTURE_2D, 
                        0, GL_TEXTURE_WIDTH)
        except GLError:
            return False
            
    @staticmethod
    def testSize2(texsize):
        """Helper function to determine maximum atlas size.
        Some (bad) GL drivers want some dummy data, it seems,
        so this version gives dummy data. It's in a seperate function because
        for compliant systems creating a ctypes array for each texsize would
        give a high performance overhead. With this, there is low overhead
        on a compliant system as it minimises the number of different types
        of call.
        Arguments:
         texsize : test if an atlas of texsizextexsize can be created"""
        try:
            glTexImage2D(GL_PROXY_TEXTURE_2D, 0, GL_RGBA, 
                         texsize, texsize, 0,
                         GL_RGBA, GL_UNSIGNED_BYTE, 
                         (ctypes.c_int * texsize * texsize)())
            return glGetTexLevelParameteriv(GL_PROXY_TEXTURE_2D, 
                        0, GL_TEXTURE_WIDTH)
        except GLError:
            return False    
    
class TwoDTexture(object):
    """A Two D Hardware accelerated texture"""
    def __init__(self, size):
        """Initialise a texture of given size. Will raise errors if texture
        of given size cannot be created; use the functions in TwoDTextureCommon
        to determine possible texture sizes"""
        
        self.size = size
        
        self.sizeUniform = Uniform('texSize', self.size, glUniform1f, [])
        self.texelUniform = Uniform('texelSize', 1.0 / self.size, 
                                    glUniform1f, [])

        self.surface = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.surface)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.size, self.size, 
                     0, GL_RGBA, GL_UNSIGNED_BYTE, 
                     (ctypes.c_int * self.size * self.size)())
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        
    def unbind(self):
        """Destroy the gl texture"""
        glDeleteTextures(self.surface)
        self.surface = None
        
    def rebind(self):
        """Recreates the atlas"""
        self.surface = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.surface)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.size, self.size, 
                     0, GL_RGBA, GL_UNSIGNED_BYTE, 
                     (ctypes.c_int * self.size * self.size)())
                     
    def upload(self, pos, size, data):
        """Upload to a area on the texture
        Arguments:
         pos: The x,y coordinates of the top left of the area
         size: The width, height of the area
         data: The data to upload; must be size[0]*size[1]*4 bytes long
        """
        glBindTexture(GL_TEXTURE_2D, self.surface)
        glTexSubImage2D(GL_TEXTURE_2D, 0, pos[0], pos[1], size[0], size[1], 
                        GL_RGBA, GL_UNSIGNED_BYTE, data)
                        
    def bindTexture(self, layer):
        """Callback to bind the texture to the texture unit"""
        glBindTexture(GL_TEXTURE_2D, self.surface)
        
    def readPixels(self):
        """Dump pixels from texture to a 3d numpy array. This is not
        really ideal, but alternatives are slow - this will be subject
        to change should I implement my own GL bindings."""
        self.bindTexture(0)
        pixels = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_FLOAT)
        return pixels
        
    def readPixelsToArrays(self):
        """Wrestles pixels out of numpy arrays into python arrays, but this
        is slow, and probably should be avoided"""
        npyarray = self.readPixels()
        stringres = npyarray.tostring()
        res = [array('f', struct.unpack('f' * self.size * 4, 
                stringres[(x * self.size * 16):((x+1) * self.size * 16)])) 
                for x in xrange(self.size)]
        return res

