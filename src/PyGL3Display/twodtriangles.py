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

twodtriangles.py

This file provides 2d triangle drawing facilities.
"""

from __future__ import division
from ctypes import c_uint8
from PyGL3Display.infrastructure import GL3Client
from OpenGL.GL import glUniformMatrix4fv, \
     GL_TRUE, GL_FALSE, GL_UNSIGNED_BYTE, GL_TRIANGLES
from PyGL3Display.twodshaders import TwoDShaderCommon, TwoDShader
from PyGL3Display.twodbases import TwoDThing
from PyGL3Display.shaderdata import VertexArraySpec, UniformStore, Uniform

__all__ = ['TwoDTriangleCommon', 'TwoDTriangleRenderer', 
           'TwoDTriangleShader', 'Triangles']
           
class TwoDTriangleCommonMetaclass(type):
    """Enables easy lazy creation of default objects
       by redefining the class __getattr__"""
    def __getattr__(cls, attr):
        if attr == 'defaultShader':
            cls.makeDefaultShader()
            return cls.defaultShader
        else:
            raise AttributeError('TwoDTriangleCommon does not have ' + attr)
            
            
class TwoDTriangleCommon(object):
    """The shared state between 2d triangles"""
    
    __metaclass__ = TwoDTriangleCommonMetaclass
        
    spec = VertexArraySpec('TwoDTriangleArrays')
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
        cls.defaultShader = TwoDTriangleShader()

class TwoDTriangleShader(TwoDShader):
    """A shader for 2d triangles"""
    
    def __init__(self, cameraObj=None):
        """Initialise the 2d Triangle Shader.
        Args:
         arrays: a VertexArrays object that contains render data
         cameraObj: A TwoDCameraManager object for camera state. Default to shared
                    camera state."""
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
            bool drop(in vec2 pos);
            varying vec4 v2fColor;
            varying vec4 v2fPos;
            void main()
            {
                if (drop(v2fPos.xy)) {discard;} 
                gl_FragColor = v2fColor;
            }"""
        
        super(TwoDTriangleShader, self).__init__(
            vertexProgs= [TwoDShaderCommon.applyTransformSource, 
            cameraObj.shaderSource, vertexProg], 
            fragmentProgs=[TwoDShaderCommon.dropSource, fragmentProg])
            
        self.triangleRenderer = TwoDTriangleRenderer(self)

    def getRenderer(self):
        """Get the appropriate renderer for triangles"""
        return self.triangleRenderer

            
class TwoDTriangleRenderer(GL3Client):
    """A client for Triangle renderer"""
    
    def __init__(self, shader):
        """Initialise the Triangle renderer.
        See GL3CLient for missing argument info
        """
        super(TwoDTriangleRenderer, self).__init__(GL_TRIANGLES, shader,
                            vertexArraySpec=TwoDTriangleCommon.spec)
        self.uniforms = UniformStore(set([
            TwoDShaderCommon.getProjMatrix(),
            TwoDShaderCommon.defaultCameras.cameraUniform,
            ]))

class Triangles(TwoDThing):
    """The class that represents a group of triangles drawn to screen"""
    
    def __init__(self, vertices, pos = (0, 0),
                 scalex = 1, scaley = 1, scale = None,
                 rotation = 0, color = (255, 255, 255, 255), colors = None, 
                 layer = 0, shader = None):
        """Initialise the Triangles object:
        Args:
          vertices: A list of coordinates relative to the origin. 
                    Triangles will be drawn between these coordinates.
                    Note: Whilst the positions of each vertex can be changed,
                    the number of points cannot be changed
          pos: The position on screen to draw the origin point to
          scalex: X scale of the triangle
          scaley: Y scale of the triangle
          scale: Scale of the triangle. Overrides scalex/scaley
          rotation: Rotation of the triangle
          color: A color for the entire triangle; 
          colors: A triangle of colors that match to the appropriate 
                  coordinates; Overrides color
           (default color: (255, 255, 255, 255)
          layer: The layer the triangle should render on (default: 0)
         Advanced:
          shader: The shader the triangle should use. Default to shared manager
        """
        if shader is not None:
            self._shader = shader
        else:
            self._shader = TwoDTriangleCommon.defaultShader
        
        verticesLen = len(vertices)    
        if verticesLen % 3:
            raise ValueError("Need to pass in a multiple of 3 vertices" +
                             "for triangles")

        self._layer = layer    
        
        if scale is not None:
            scalex, scaley = scale, scale

        if colors is None:
            colors = [color] * verticesLen
            
        renderLen = verticesLen
            
        self._renderer = self._shader.getRenderer()
        self._vertexArrays = self._renderer.getVertexArrays(verticesLen)
        self._slots = self._vertexArrays.getDataSlots(verticesLen)
        self._rslots, self._rindex = self._renderer.getRenderSlots(renderLen, 
                                            self._layer, self._vertexArrays)
        
        self._rdata = self._slots
        self._renderer.uploadSlotData(self._rdata, self._rslots, self._layer, 
                                            self._rindex, self._vertexArrays)
        self.__verticesLen = verticesLen
        self.__renderLen = renderLen
        
        self.setVertices(vertices)
        self.setPosition(pos)
        self.setColors(colors)
        self.setScaleX(scalex)
        self.setScaleY(scaley)
        self.setRotation(rotation)
                    
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
