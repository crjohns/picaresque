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

pygameimages.py

This file provides pygame specific implementations of image loading etc.
"""
from __future__ import division

import pygame

from PyGL3Display.twodspriteinfrastructure import Image
from PyGL3Display.twodimages import Surface, RawImage

__all__ = ['PygameSurface', 'PyGameRawImage', 'loadImage']

class PygameRawImage(RawImage):
    def __init__(self, surface):
        self.surface = surface
        self.size = self.surface.get_size()
        
    def getSize(self):
        return self.size
        
    def getRaw(self):
        return pygame.image.tostring(self.surface , "RGBA")

class PygameSurface(Surface):
    """A Wrapper around a Pygame surface. One thing to note is that this
    maintains a copy of the surface in main memory as well as in video RAM; it
    behaves just like a Pygame surface in most respects, uploading to VRAM
    where necessary. Note that uploading is a fairly slow operation,
    especially on large surfaces, so if using this class please refrain from
    modifying large surfaces. Whilst a surface is locked, uploading doesn't
    occur, so if you're doing lots of operations it might be a good idea
    to lock the surface even if you wouldn't normally.
    
    Due to me being lazy, the docstrings are not included. Consult the pygame
    docs instead.
    """
    def __init__(self, widthheight, shader=None, wrapped=False, blank=False,
                       *args, **kwargs):
        """Initialise the PygameSurface
        Arguments:
            widthheight: a tuple containing the width/height of the image
            other args as pygame surface.
        """
        Surface.__init__(self, widthheight, shader, wrapped)
        if not blank:
            self.surface = pygame.surface.Surface(widthheight, *args, **kwargs)
            self.rawimage = PygameRawImage(self.surface)
            self.upload(self.surface)
            self.parent = None

    def upload(self, surface):
        """Internal method; uploads changes in the soft-surface to the
        GL surface, when appropriate."""
        if not surface.get_locked(): 
            Image.upload(self, self.rawimage)
    
    @classmethod
    def loadImage(cls, *args, **kwargs):
        """Replacement for pygame.image.load"""
        if 'wrapped' in kwargs:
            wrapped = kwargs['wrapped']
            del kwargs['wrapped']
        else:
            wrapped = False
        return cls.surfaceify(pygame.image.load(*args, **kwargs), 
                              wrapped = wrapped)

    @classmethod
    def surfaceify(cls, pygameSurface, wrapped = False):
        """Convert a pygame Surface into a GL3pygameSurface"""
        ret = PygameSurface(pygameSurface.get_size(), wrapped=wrapped, 
                            blank=True)
        ret.surface = pygameSurface
        ret.rawimage = PygameRawImage(ret.surface)
        ret.upload(pygameSurface)
        return ret
    
    def blit(self, *args, **kwargs):
        self.surface.blit(*args, **kwargs)
        self.upload(self.surface)
    
    def convert(self, *args, **kwargs): 
        return self.surfaceify(self.surface.convert(*args, **kwargs))
    def convert_alpha(self, *args, **kwargs): 
        return self.surfaceify(self.surface.convert_alpha(*args, **kwargs))
    def copy(self): return self.GL3Surfacify(self.surface.copy(self))
    
    def fill(self, *args, **kwargs):
        self.surface.fill(*args, **kwargs)
        self.upload(self.surface)
    
    def scroll(self, dx, dy):
        self.surface.scroll(dx, dy)
        self.upload(self.surface)
        
    def set_colorkey(self, *args, **kwargs):
        self.surface.set_colorkey(*args, **kwargs)
        self.upload(self.surface)
        
    def get_colorkey(self): return self.surface.get_colorkey()
        
    def set_alpha(self, *args, **kwargs):
        self.surface.set_alpha(*args, **kwargs)
        self.upload(self.surface)
    
    def get_alpha(self): return self.surface.get_alpha()
    def lock(self): self.surface.lock()

    def unlock(self):
        self.surface.unlock()
        self.upload(self.surface)
            
    def mustlock(self): return True
    def get_locks(self): return self.surface.get_locks()
    def get_at(self, xy): return self.surface.get_at(xy)

    def set_at(self, xy, color): 
        self.surface.set_at(xy, color)
        self.upload(self.surface)
    
    def get_palette(self): return self.surface.get_palette()
    def get_palette_at(self, index): return self.surface.get_palette_at(index)
    
    def set_palette_at(self, index, rgb):
        self.surface.set_palette_at(index, rgb)
        self.upload(self.surface)
    
    def map_rgb(self, color): return self.surface.map_rgb(color)
    def unmap_rgb(self, mapped_int): return self.surface.unmap_rgb(mapped_int)
    def set_clip(self, rect): self.surface.set_clip(rect)
    def get_clip(self): return self.surface.get_clip()

    def subsurface(self, rect):
        # TODO: This will need to convert the Pygame rect to a GL rect 
        ret = PygameSurface(None)
        ret.surface = self.surface.subsurface(rect)
        ret.parent = self
        hwsubsurface = Image.subsurface(self, rect)
        ret.coords = hwsubsurface.coords
        ret.atlas = hwsubsurface.atlas
        ret.intCoords = hwsubsurface.intCoords
        return ret
    
    def get_parent(self): return self.parent
    
    def get_abs_parent(self):
        ret = self.parent
        while ret != None: ret = ret.parent
        return ret
    
    def get_offset(self): return self.surface.get_offset()
    def get_abs_offset(self): return self.surface.get_abs_offset()
    def get_size(self): return self.surface.get_size()
    def get_width(self): return self.surface.get_width()
    def get_height(self): return self.surface.get_height()
    def get_rect(self, **kwargs): return self.surface.get_rect(**kwargs)
    def get_bit_size(self): return self.surface.get_bit_size()
    def get_byte_size(self): return self.surface.get_byte_size()
    def get_flags(self): return self.surface.get_flags()
    def get_pitch(self): return self.surface.get_pitch()
    def get_masks(self): return self.surface.get_masks()
    
    def set_masks(self, *args, **kwargs): 
        self.surface.set_masks(*args, **kwargs)
        self.upload(self.surface)
        
    def get_shifts(self): return self.surface.get_shifts()
    
    def set_shifts(self, *args, **kwargs): 
        self.surface.set_shifts(*args, **kwargs)
        self.upload(self.surface)
        
    def get_losses(self): return self.surface.get_losses()
    def get_bounding_rect(self): return self.surface.get_bounding_rect()
    def get_buffer(self): return self.surface.get_buffer()
    
loadImage = PygameSurface.loadImage