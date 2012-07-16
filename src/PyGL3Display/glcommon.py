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

glcommon.py

This file provides abstractions on the GL state
"""

from OpenGL.GL import \
     glViewport, glClearColor, glLineWidth, glHint, glBlendFunc, glEnable, \
     glClear, glCreateShader, glShaderSource, glCompileShader, glClearColor, \
     glGetShaderInfoLog, glUseProgram, glDisableVertexAttribArray, \
     glVertexAttribPointer, glGetShaderiv, glBindBuffer, \
     glEnableVertexAttribArray, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, \
     GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST, GL_LINE_SMOOTH_HINT, \
     GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_LINE_SMOOTH, GL_TEXTURE_2D, \
     GL_BLEND, GL_TRUE, GL_COMPILE_STATUS

import weakref, os
from hacks import applyHacks

__all__ = ['ShaderError', 'GLCommonClass', 'glConfigure']

class ShaderError(Exception):  
    """Error type for GL shader errors"""
    
class GLCommonClass(object):
    """The 'shared state' between other things, mainly to track the GL state"""
    def __init__(self):
        """Initialise the shared state"""
        self.shaders = weakref.WeakKeyDictionary()
        self.layers = []
        self.boundShader = None
        self.boundVertexArrays = None
        self.boundBuffers = {}
        self.boundUniformStore = weakref.WeakKeyDictionary()
        self.boundArrays = {}
        self.boundUniforms = {}
        self.lineWidth = 1.0
        self.shaderProgs = {}
        
    def bindBuffer(self, loc, bufferid):
        """Perform buffer binding only if necessary"""
        if self.boundBuffers.get(loc, None) != bufferid:
            glBindBuffer(loc, bufferid)
            self.boundBuffers[loc] = bufferid
    
    def getShader(self, shaderSource, shaderType):
        """Get the shader object for shaderSource. Compiles if necessary.
        Args:
         shaderSource: The source code of a shader
         shaderType: The type of the shader. Should be
                     GL_VERTEX_SHADER of GL_FRAGMENT_SHADER"""
        if (shaderSource, shaderType) not in self.shaderProgs:
            shader = glCreateShader(shaderType)
            glShaderSource(shader, [shaderSource])
            glCompileShader(shader)
            shaderCompiled = glGetShaderiv(shader, GL_COMPILE_STATUS) == GL_TRUE
            if not shaderCompiled:
                shaderLog = glGetShaderInfoLog(shader).strip()
                errorMessage = 'Shader Compile Error: \nSource:\n' + \
                               shaderSource + '\nError:\n' + shaderLog
                raise ShaderError(errorMessage)
            self.shaderProgs[(shaderSource, shaderType)] = shader
        return self.shaderProgs[(shaderSource, shaderType)]

    def useProgram(self, program):
        """Replaces calls to glUseProgram. Only changes the program as
        necessary, which is somewhat faster.
        Arguments:
         program: The program to use"""
        if self.boundShader is not program:
            self.boundShader = program
            glUseProgram(program.shaderProgram)
            
    def updateLayers(self, layer):
        """Add a new rendering layer"""
        if layer not in self.layers:
            self.layers.append(layer)
            self.layers.sort()
    
    def bindArray(self, glArgsList, force=False):
        """Replaces calls to glVertexAttribPointer, glEnableVertexAttribArray
        and glDisableVertexAttribArray. Performs the binding on an "as 
        necessary" basis, which is somewhat faster.
        Arguments:
         glArgsList: A list of arguments to pass to glEnableVertexAttribArray.
                     Arguments for other functions are extracted from the list.
         force: The detection is by index/array, not by any other arguments. On
         the off chance that someone wants to change the arguments on 
         glVertexAttribPointers (which I can't think of why you'd want to do)
         specifying force guarantees that the array will be rebound.
        """
        index = glArgsList[0]
        array = glArgsList[-1]
        if index == -1: 
            return # Short circuit if the GL compilers have decided not to
                   # allocate the array.
        elif ((type(array) == int and 
                    self.boundArrays.get(index, None) != array or force) or 
                (self.boundArrays.get(index, None) is not array or force)):
            self.boundArrays[index] = array
            glDisableVertexAttribArray(index)
            glVertexAttribPointer(*glArgsList)
            glEnableVertexAttribArray(index)
            
    def bindUniform(self, bindFunc, args, force=False):
        """Replaces calls to glUniform functions. Performs binding on an
           as necessary basis.
           Arguments:
             bindFunc: The OpenGL function that binds the uniform 
                       (e.g. glUniform1v)
             args    : A list of arguments to bindFunc which will bind the
                       uniform as desired.
             force   : Force, even if array already bound (to change arguments
                       on bindFunc)
        """
        if args[0] == -1:
            return # Short circuit if GL compiler decided not to allocate
        if self.boundUniforms.get(args[0], None) is not args[-1] or force:
            self.boundArrays[args[0]] = args[-1]
            bindFunc(*args)
    
    @staticmethod
    def createContext(resolution, doubleBuffer, fullscreen):
        """A dummy function to explain that something has gone wrong with
        backend configuration. Implementation should take given arguments
        and create a window matching them."""
        raise Exception('No backend has taken control of creating a context')
        
    @staticmethod
    def init():
        """A dummy function to explain that something has gone wrong with
        backend configuration. Implementation should set up backend 
        environment"""
        raise Exception('No backend has taken control of initialisaion')
        
    @staticmethod
    def decodeImage(image):
        """A dummy function to explain that something has gone wrong with
        backend configuration. Implementation should take a notional image
        and return an RGBA list of values"""
        raise Exception('No backend has taken control of image decoding')
        
    @staticmethod
    def redraw():
        """A dummy function to explain something has gone wrong with backend
        configuration. Implmentation should update the screen properly"""
        raise Exception('No backend has taken control of redrawing the screen')

                    
    def initEnvironment(self, resolution, doubleBuffer=True, fullscreen=False):
        """Initialise the OpenGL environment with the given flags
          Arguments:
            resolution: The resolution of the window
            doubleBuffer: Enable doublebuffering. Recommended
            fullscreen: Use full screen mode rather than windowed mode
        """
        
        self.createContext(resolution, doubleBuffer, fullscreen)
        
        glViewport(0, 0, resolution[0], resolution[1])
        glClearColor(0.0, 0.5, 1.0, 1.0)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_TEXTURE_2D) # Not necessary? Test on other drivers
        glEnable(GL_BLEND)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        
        self.resolution = resolution
        
        # Recreate the context as necessary
        if os.name in ('nt',):
            for ref in self.shaders.iterkeyrefs():
                if ref(): 
                    ref().rebind()
        
        # Apply hacks to compensate bad drivers
        applyHacks()
            
    def addShader(self, shader):
        """Register a shader with GLCommon"""
        self.shaders[shader] = True
            
    def doTasks(self):
        """Draw everything that GLCommon knows about"""
        self.clear()
        for layer in self.layers:
            for ref in self.shaders.iterkeyrefs():
                if ref(): 
                    shader = ref()
                    shader.doTasks(layer=layer)
        self.redraw()
        
    @staticmethod
    def clear():
        """Clears the screen"""
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT) 
    
    @staticmethod
    def setClearColour(color):
        """Set the colour to clear the screen with
        Args:
         color: An rgb or rgba color to clear the screen with"""
        if len(color) == 3: 
            color.append(255)
        normalised = [x/255 for x in color]
        glClearColor(*normalised)
        
    def setLineWidth(self, width):
        """Set the line width of any normal GL lines
        Args:
         width: width in pixels. Note that as things are smoothed
         by default, some widths are not distinguishable"""
        if self.lineWidth != width:
            glLineWidth(width)
            self.lineWidth = width
            
def glConfigure(glCommonInstance, glContextBackend=None, 
              spriteBackend=None):
    """Configure a GLCommon instance to use a given set of backends"""
    if glContextBackend is not None:
        if glContextBackend == 'pygame1.x':
            import PyGL3Display.backends.pygamebackend as glBackend
        elif glContextBackend == 'GLUT':
            import PyGL3Display.backends.glutbackend as glBackend
        else:
            raise Exception('No recognised backend for operation')
        glCommonInstance.createContext = glBackend.createContext
        glCommonInstance.redraw = glBackend.redraw
        glCommonInstance.init = glBackend.init
    #if spriteBackend is not None:
    #    if spriteBackend == 'pygame1.x':
    #        import pygameimages
    #    else:
    #        raise Exception('No recognised backend for operation')
    #    glCommonInstance.imageDecoder = imageBackend.imageDecoder

