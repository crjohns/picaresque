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
contacting me via e-mail at habilain@gmail.com. If you do not have in physical 
writing an alternative license agreement from me, you must use one of the 
licenses specified above when releasing work which makes use of this library.

hacks.py

Applies hacks to get PyGL3Display to run on known bad drivers.
applyHacks is called automatically on glInitEnvironment
"""

from OpenGL.GL import glGetString, GL_RENDERER

__all__ = ['applyHacks']

def applyHacks():
    """Applies hacks to PyGL3Display to allow it to work on bad drivers,
    whilst not impairing performance on good drivers.
    Current bad driver list:
        Virtualbox "Chromium" driver
    """
    renderer = glGetString(GL_RENDERER)
    if renderer == 'Chromium':
        # Virtualboxs Chromium driver allows the creation of large textures
        # that it can't support , causing crashes.
        # Compensate by reducing max texture size to 1024
        from twodtexture import TwoDTextureCommon
        TwoDTextureCommon.maxTextureSize = 1024
        
