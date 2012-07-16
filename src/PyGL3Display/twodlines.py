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

twodlines.py

This file provides 2d line drawing facilities.
"""

from __future__ import division
from ctypes import c_uint8
from PyGL3Display.infrastructure import GLCommon, GL3Client
from OpenGL.GL import glUniformMatrix4fv, \
     GL_TRUE, GL_FALSE, GL_UNSIGNED_BYTE, GL_LINES 
from PyGL3Display.twodshaders import TwoDShaderCommon, TwoDShader
from PyGL3Display.twodbases import TwoDThing
from PyGL3Display.shaderdata import VertexArraySpec, UniformStore, Uniform

__all__ = ['TwoDLineCommon', 'TwoDLineRenderer', 'TwoDLineShader', 'Lines']

class TwoDLineCommonMetaclass(type):
    """Enables easy lazy creation of default objects
       by redefining the class __getattr__"""
    def __getattr__(cls, attr):
        if attr == 'defaultShader':
            cls.makeDefaultShader()
            return cls.defaultShader
        else:
            raise AttributeError('TwoDLineCommon does not have ' + attr)


class TwoDLineCommon(object):
    """The shared state between 2d lines"""
    
    __metaclass__ = TwoDLineCommonMetaclass
        
    spec = VertexArraySpec('TwoDLinesArrays')
    spec.addArray('pos')
    spec.addArray('rotozoom')
    spec.addArray('cameras1')
    spec.addArray('cameras2')
    spec.addArray('color', cType=c_uint8, 
                  glType=GL_UNSIGNED_BYTE, glNorm=GL_TRUE)
    spec.addAttrib('pos', 'Position', 2, 0)
    spec.addAttrib('pos', 'Offset', 2, 2, True)
    spec.addAttrib('color', 'Color', 4, 0)
    spec.addAttrib('color', 'Color', 4, 0, True)
    spec.addAttrib('cameras1', 'Camera1', 1, None)
    spec.addAttrib('cameras2', 'Camera2', 1, None)
    spec.addAttrib('rotozoom', 'ScaleX', 1, 0)
    spec.addAttrib('rotozoom', 'ScaleY', 1, 1)
    spec.addAttrib('rotozoom', 'Rotation', 1, 2)

    @classmethod
    def makeDefaultShader(cls):
        """Create the default shader object"""
        cls.defaultShader = TwoDLineShader()        
        

class TwoDLineRenderer(GL3Client):
    """A client for Line renderer"""
    
    def __init__(self, shader, width):
        """Initialise the Line renderer.
        See GL3CLient for missing argument info
        Args:
         width: Width of lines the renderer should draw
        """
        super(TwoDLineRenderer, self).__init__(GL_LINES, shader,
                            vertexArraySpec=TwoDLineCommon.spec)
        self.width = width
        self.addRenderHook(self.setLineWidth)
        self.uniforms = UniformStore(set([
            TwoDShaderCommon.getProjMatrix(),
            TwoDShaderCommon.defaultCameras.cameraUniform,
            ]))
        
    def setLineWidth(self, layer):
        """Set the line width correctly for the layer"""
        GLCommon.setLineWidth(self.width)

class TwoDLineShader(TwoDShader):
    """A shader for 2d lines"""
    
    def __init__(self, cameraObj=None):
        """Initialise the 2d Line Shader.
        Args:
         arrays: a VertexArrays object that contains render data
         cameraObj: A TwoDCamerashader object for camera state. Default to 
                    shared camera state.
         projMatrix: a Projection matrix. Default to flat 2d grid matrix
         uniforms: a UniformStore. Default to the shared 2d store"""
        if cameraObj is None:
            cameraObj = TwoDShaderCommon.defaultCameras
        
        vertexProg = """
            vec2 applyTransform(in vec2 pos, in vec2 origin, in vec2 offset, 
                        in float xScale, in float yScale, in float rotation);
            vec2 applyCameras(in vec4 cameras, in vec2 pos);
            attribute vec4 pos;   
            attribute vec4 rotozoom;
            attribute vec4 cameras1;
            attribute vec4 cameras2;
            attribute vec4 color;
            attribute vec4 offsets;
            uniform mat4 projMatrix;
            varying vec4 v2fColor;
            varying vec4 v2fPos;
            void main()
            {   
                vec2 transform = applyTransform(pos.xy, vec2(0.0, 0.0), 
                                 pos.zw, rotozoom.x, rotozoom.y, rotozoom.z);
                transform = applyCameras(cameras1, transform);
                transform = applyCameras(cameras2, transform);
                gl_Position = projMatrix * vec4(transform.xy, 0.0, 1.0);
                v2fPos.xy = gl_Position.xy;
                v2fColor = color;
            }"""
        fragmentProg = """
            varying vec4 v2fColor;
            bool drop(in vec2 pos);
            varying vec4 v2fPos;
            void main()
            {
                if (drop(v2fPos.xy)) {discard;} 
                gl_FragColor = v2fColor;
            }"""
                        
        super(TwoDLineShader, self).__init__( 
            vertexProgs= [TwoDShaderCommon.applyTransformSource, 
            cameraObj.shaderSource, vertexProg], 
            fragmentProgs=[TwoDShaderCommon.dropSource, fragmentProg])
            
        self.lineRenderers = {}

    def getRenderer(self, width):
        """Get the appropriate renderer for a line of given width
        Args:
         width: the width of the line to draw"""
        if width not in self.lineRenderers:
            self.lineRenderers[width] = TwoDLineRenderer(shader = self, 
                                                         width = width)
        return self.lineRenderers[width]

class Lines(TwoDThing):
    """The class that represents a set of connected lines to be drawn"""
    
    def __init__(self, vertices, pos = (0, 0),
                 scalex = 1, scaley = 1, scale = None,
                 rotation = 0, color = (255, 255, 255, 255), colors = None, 
                 layer = 0, width = 2.0, closed=False,
                 shader = None):
        """Initialise the Lines object:
        Args:
          vertices: A list of coordinates relative to the origin. 
                    Lines will be drawn between these coordinates.
                    Note: Whilst the positions of each vertex can be changed,
                    the number of points cannot be changed
          pos: The position on screen to draw the origin point to
          scalex: X scale of the line
          scaley: Y scale of the line
          scale: Scale of the line. Overrides scalex/scaley
          rotation: Rotation of the line
          color: A color for the entire line; (default color: white) 
          colors: A list of colors that match to the appropriate coordinates
                  Overrides color 
          closed: If True, draw a line between the start vertex and the 
                  end vertex
                  Note: Cannot be changed after initialisation
          layer: The layer the line should render on (default: 0)
          width: The width of the line (default: 2.0)
         Advanced:
          shader: The shader the line should use. Default to shared shader
        """
        if shader is not None:
            self._shader = shader
        else:
            self._shader = TwoDLineCommon.defaultShader

        self._layer = layer
        self._width = width    
    
        verticesLen = len(vertices)    
        
        if scale is not None:
            scalex, scaley = scale, scale

        if colors is None:
            colors = [color] * verticesLen
        
        if verticesLen <= 2:
            renderLen = 2
        elif closed:
            renderLen = 2 * verticesLen 
        else:
            renderLen = 2 * verticesLen - 2
            
        self._renderer = self._shader.getRenderer(self._width)
        self._vertexArrays = self._renderer.getVertexArrays(verticesLen)
        self._slots = self._vertexArrays.getDataSlots(verticesLen)
        self._rslots, self._rindex = self._renderer.getRenderSlots(renderLen, 
                                            self._layer, self._vertexArrays)
        if verticesLen == 2:
            slotsList = self._slots
        else:
            slotLists = [[self._slots[x], self._slots[(x+1) % verticesLen]] 
                     for x in xrange(verticesLen)]
            slotsList = []
            for x in slotLists:
                slotsList.extend(x)
        self._rdata = slotsList
        self._renderer.uploadSlotData(slotsList, self._rslots, self._layer, 
                                      self._rindex, self._vertexArrays)
        self.__verticesLen = verticesLen
        self.__renderLen = renderLen
        
        self.setVertices(vertices)
        self.setPosition(pos)
        self.setColors(colors)
        self.setScaleX(scalex)
        self.setScaleY(scaley)
        self.setRotation(rotation)
            
    def setWidth(self, width):
        """Set the width of the lines. This is a potentially slow operation."""
        if width != self._width:
            if self._rslots:
                self._renderer.releaseRenderSlots(self._rslots, self._layer, 
                                            self._rindex, self._vertexArrays)
            self._width = width
            self._renderer = self._shader.getRenderer(self._width)
            self._rslots, self._rindex = self._renderer.getRenderSlots(
                            self.__renderLen, self._layer, self._vertexArrays)
            self._renderer.uploadSlotData(self._rdata, self._rslots, 
                                self._layer, self._rindex,self._vertexArrays)

    setScaleX = TwoDThing.setScaleX
    setColor = TwoDThing.setColor
    setCameras = TwoDThing.setCameras
    setVisibility = TwoDThing.setVisibility
    setScaleY = TwoDThing.setScaleY
    setVertices = TwoDThing.setVertices
    setLayer = TwoDThing.setLayer
    setVertex = TwoDThing.setVertex
    setScale = TwoDThing.setScale
    setRotation = TwoDThing.setRotation
    setPosition = TwoDThing.setPosition
    setCamera = TwoDThing.setCamera
    setColors = TwoDThing.setColors
    setVertexColor = TwoDThing.setVertexColor
