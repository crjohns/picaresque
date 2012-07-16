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

glutbackend.py

This file provides functions that let PyGL3Display use GLUT for its backend
"""
from OpenGL.GL import glFlush
from OpenGL.GLUT import glutInitWindowSize, glutInitWindowSize, \
    glutSwapBuffers, glutInit, glutFullScreen, glutInitDisplayMode, \
    glutCreateWindow, GLUT_RGB, GLUT_DOUBLE

__all__ = ['createContext', 'redraw', 'init']

def createContext(resolution, doubleBuf, fullScreen):
    """Create a GLUT window on screen"""
    glutInitWindowSize(resolution[0], resolution[1])
    glutCreateWindow("PyGL3Display Window")
    params = GLUT_RGB
    if doubleBuf:
        params |= GLUT_DOUBLE
    glutInitDisplayMode(params)
    if fullScreen:
        glutFullScreen()

def redraw():
    """Flush and swap buffers if necessary"""
    glFlush()
    glutSwapBuffers()

init = glutInit

    
    
