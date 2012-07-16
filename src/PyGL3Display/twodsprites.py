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

twodsprites.py

This file provides "oldschool style" 2d Sprite specific features, by collecting
things from other files.
"""

from PyGL3Display.twodspriteinfrastructure import GL3Rect, SpriteCommon
from PyGL3Display.twodimages import Surface
from PyGL3Display.twodspritesinterface import (Sprite, AttribSprite,
     SpriteBuffer, topLeftOffsets, topRightOffsets, bottomLeftOffsets, 
     bottomRightOffsets, centerOffsets, makeAdjacentSprites)
from PyGL3Display.twodspritegroups import SpriteGroup

PYGAMEENABLED = False
try:
    import pygame
    del pygame
    PYGAMEENABLED = True
except ImportError:
    pass
PNGENABLED = False
try:
    import png
    del png
    PNGENABLED = True
except ImportError:
    pass
    
if PYGAMEENABLED:
    # Prefer pygame...
    from PyGL3Display.pygameimages import loadImage, PygameSurface
elif PNGENABLED:
    # ... but fall back on PyPNG
    from PyGL3Display.pypngimages import loadImage, PNGSurface
