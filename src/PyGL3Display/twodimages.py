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

twodimages.py

Provides image functions for twodsprites
"""

from __future__ import division

from PyGL3Display.twodspriteinfrastructure import SpriteCommon, Image
from binascii import hexlify

__all__ = ['Surface', 'RawImage']

class RawImage(object):
    """A RawImage is an image before it has been uploaded. It provides
    information on the size of the image and a raw form of the image. This API
    should be replicated by the backends for their raw image representation"""
    def __init__(self, size, raw):
        """Initialise a raw image"""
        self.size = size
        self.raw = raw
        
    def getSize(self):
        """Return the size of the image"""
        return self.size
        
    def getSizeWrapped(self):
        """Return the size necessary to accommodate a wrapped image"""
        size = self.getSize()
        return (size[0] + 2, size[1] + 2)
        
    def getRaw(self):
        """Return an RGBA raw of the image"""
        return self.raw
        
    def getRawWrapped(self):
        """Return an RGBA raw of the image that is wrapped"""
        raw = self.getRaw()
        xsz, ysz = self.getSize()
        wrapRaw = []
        rowLength = xsz * 4
        for iter in (ysz-1,), xrange(ysz), (0,):
            for x in iter:
                base = xsz * x * 4
                wrapRaw.extend((raw[base+rowLength-4:base+rowLength], 
                                raw[base:base+rowLength], raw[base:base+4]))
        return ''.join(wrapRaw)
        
class Surface(Image):
    """A Image which is intended to be created by the user. Surfaces are HW
    accelerated."""
    def __init__(self, widthHeight, shader=None, wrapped = False):
        """Initialise the Gl3Surface. 
        Arguments:
          widthHeight: A tuple containing the width / height of the surface
          shader: The shader to use; defaults to shared sprite shader
          wrapped: If the sprite should be wrapped; this results in a different
                   image being uploaded to the shader than if it isn't.
        """
        width, height = widthHeight
        self.wrapped = wrapped
        manager = SpriteCommon.defaultShader if shader is None else shader
        manager.getBox(width, height, self, wrapped)
        self.reuploadData = None

