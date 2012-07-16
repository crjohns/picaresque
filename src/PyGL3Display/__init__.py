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
"""

#TODO: Render to texture support. Should create a texture buffer object that is
#    : a subclass of a Texture, and some kind of "targetting" framework so that
#    : doTasks can be pointed at a specific target.

import OpenGL
OpenGL.FORWARD_COMPATIBLE_ONLY = True

from PyGL3Display.glcommoninst import *
from PyGL3Display.infrastructure import *
from PyGL3Display.twodshaders import *
from PyGL3Display.twodsprites import *
from PyGL3Display.twodlines import *
from PyGL3Display.twodtriangles import *
from PyGL3Display.twodellipse import *


