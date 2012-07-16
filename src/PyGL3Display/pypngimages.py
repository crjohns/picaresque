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

pypngimages.py

This file provides functions that let PyGL3Display use PyPNG for decoding 
images
"""

from png import Reader

from PyGL3Display.twodimages import Surface, RawImage

__all__ = ['PNGRawImage', 'PNGSurface', 'loadImage']

class PNGRawImage(RawImage):
    """A wrapper object to load raw data from a PNG file"""
    def __init__(self, fn):
        """Load data from the given file name"""
        reader = Reader(filename=fn)
        width, height, pixels, meta = reader.read_flat()
        self.size = (width, height)
        self.raw = list(pixels)
        
class PNGSurface(Surface):
    """A wrapper object to create a surface from a the given PNG filename"""
    def __init__(self, fn):
        """Setup a surface from the filename"""
        self.rawimage = PNGRawImage(fn)
        size = self.rawimage.getSize()
        Surface.__init__(self, size)
        self.upload(self.rawimage)

def loadImage(imagefn):
    """Load a PNG image to a new surface"""
    return PNGSurface(imagefn)
        
