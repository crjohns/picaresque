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

twodellipse.py

This file provides 2d ellipse drawing facilities.
"""

from __future__ import division
from ctypes import c_uint8
from OpenGL.GL import glUniformMatrix4fv, \
      GL_TRUE, GL_FALSE, GL_UNSIGNED_BYTE, GL_TRIANGLES
from PyGL3Display.infrastructure import GL3Client
from PyGL3Display.twodshaders import TwoDShaderCommon, TwoDShader
from PyGL3Display.twodbases import TwoDThing
from PyGL3Display.shaderdata import VertexArraySpec, UniformStore, Uniform

__all__ = ['TwoDEllipseCommon', 'TwoDEllipseRenderer', 
           'TwoDEllipseShader', 'Ellipse']
         
class TwoDEllipseCommon(object):
    """The shared state between 2d ellipse"""
    
    class __metaclass__(type):
        """Enables easy lazy creation of default objects
           by redefining the class __getattr__"""
        def __getattr__(cls, attr):
            if attr == 'defaultShader':
                cls.makeDefaultShader()
                return cls.defaultShader
            else:
                raise AttributeError('TwoDEllipseCommon does not have ' + attr)
        
    spec = VertexArraySpec('TwoDEllipseArrays')
    spec.addArray('pos')
    spec.addArray('rotozoom')
    spec.addArray('cameras1')
    spec.addArray('cameras2')
    spec.addArray('color', cType=c_uint8, 
                  glType=GL_UNSIGNED_BYTE, glNorm=GL_TRUE)
    spec.addArray('dimension')
    spec.addAttrib('pos', 'Position', 2, 0)
    spec.addAttrib('pos', 'Offset', 2, 2, True)
    spec.addAttrib('color', 'Color', 4, 0)
    spec.addAttrib('color', 'Color', 4, 0, True)
    spec.addAttrib('cameras1', 'Camera1', 1, None)
    spec.addAttrib('cameras2', 'Camera2', 1, None)
    spec.addAttrib('rotozoom', 'ScaleX', 1, 0)
    spec.addAttrib('rotozoom', 'ScaleY', 1, 1)
    spec.addAttrib('rotozoom', 'Rotation', 1, 2)
    spec.addAttrib('dimension', 'Dimension', 2, 0)
    spec.addAttrib('dimension', 'Antialiasing', 1, 2)

    @classmethod
    def makeDefaultShader(cls):
        """Create the default shader object"""
        cls.defaultShader = TwoDEllipseShader()

class TwoDEllipseShader(TwoDShader):
    """A shader for 2d lines"""
    
    def __init__(self, cameraObj=None):
        """Initialise the 2d Line Shader.
        Args:
         arrays: a VertexArrays object that contains render data
         cameraObj: A TwoDCameraManager object for camera state. Default to 
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
            attribute vec4 dimension;
            uniform mat4 projMatrix;
            varying vec4 v2fColor;
            varying vec4 v2fEllipse;
            varying vec4 v2fPos;
            void main()
            {   
                vec2 transform = applyTransform(pos.xy, vec2(0.0, 0.0), 
                                 pos.zw, rotozoom.x, rotozoom.y, rotozoom.z);
                transform = applyCameras(cameras1, transform);
                transform = applyCameras(cameras2, transform);
                gl_Position = projMatrix * vec4(transform.xy, 0.0, 1.0);
                v2fPos.xy = gl_Position.xy;
                v2fPos.z = dimension.z;
                v2fColor = color;
                v2fEllipse = vec4(pos.zw, dimension.xy);
            }"""
        fragmentProg = """
            varying vec4 v2fColor;
            varying vec4 v2fEllipse;
            varying vec4 v2fPos;
            bool drop(in vec2 pos);
            void main()
            {   
                if (drop(v2fPos.xy)) {discard;} 
                vec2 working = abs(v2fEllipse.xy);
                working = working / v2fEllipse.zw;
                working = working * working;
                float sum = working.x + working.y;
                if (sum <= (1.0 - v2fPos.z)) {
                  gl_FragColor = v2fColor;
                }
                else if (sum <= 1.0) {
                  gl_FragColor = vec4(v2fColor.xyz, v2fColor.w * (1.0 -(1.0 / v2fPos.z)*(sum - 1.0 + v2fPos.z)));
                }
                else {
                  gl_FragColor = vec4(0, 0, 0, 0);
                }
            }"""
                
        super(TwoDEllipseShader, self).__init__(
            vertexProgs= [TwoDShaderCommon.applyTransformSource, 
            cameraObj.shaderSource, vertexProg], 
            fragmentProgs=[TwoDShaderCommon.dropSource, fragmentProg])
            
        self.ellipseRenderer = TwoDEllipseRenderer(self)

    def getRenderer(self):
        """Get the renderer"""
        return self.ellipseRenderer

            
class TwoDEllipseRenderer(GL3Client):
    """A client for Ellipse the renderer"""
    
    def __init__(self, shader):
        """Initialise the Ellipse renderer.
        Args:
          shader: The shader to use; default to default ellipse shader
        """
        super(TwoDEllipseRenderer, self).__init__(GL_TRIANGLES, shader,
                            vertexArraySpec=TwoDEllipseCommon.spec)
        self.uniforms = UniformStore(set([
            TwoDShaderCommon.getProjMatrix(),
            TwoDShaderCommon.defaultCameras.cameraUniform,
            ]))

class Ellipse(TwoDThing):
    """The class that represents an ellipse drawn to screen"""
    
    def __init__(self, dx=1, dy=1, pos = (0, 0),
                 scalex = 1, scaley = 1, scale = None,
                 rotation = 0, color = (255, 255, 255, 255), colors = None, 
                 layer = 0, antialiasing = 0.0, shader = None):
        """Initialise the Ellipse object:
        Args:
          dx: The x ratio of the ellipse
          dy: The y ratio of the ellipse
          pos: The position on screen to draw the origin point to
          scalex: X scale of the line
          scaley: Y scale of the line
          scale: Scale of the line. Overrides scalex/scaley
          rotation: Rotation of the line
          color: A color for the entire line; 
          colors: A list of colors that match to the appropriate coordinates
                  Overrides color
           (default color: (255, 255, 255, 255)
          closed: If True, draw a line between the start vertex and the 
                  end vertex
                  Note: Cannot be changed after initialisation
          layer: The layer the line should render on (default: 0)
          antialiasing: The amount of antialiasing to use (default: 0.0)
          width: The width of the line (default: 2.0)
         Advanced:
          shader: The shader the line should use. Default to shared shader
        """
        if shader is not None:
            self._shader = shader
        else:
            self._shader = TwoDEllipseCommon.defaultShader
        
        self._layer = layer    
        
        if scale is not None:
            scalex, scaley = scale, scale

        if colors is None:
            colors = [color] * 4
                        
        self._renderer = self._shader.getRenderer()
        self._vertexArrays = self._renderer.getVertexArrays(4)
        self._slots = self._vertexArrays.getDataSlots(4)
        self._rslots, self._rindex = self._renderer.getRenderSlots(6, 
                                            self._layer, self._vertexArrays)
        
        self._rdata = [self._slots[0], self._slots[1], self._slots[2], 
                       self._slots[0], self._slots[2], self._slots[3]]
        self._renderer.uploadSlotData(self._rdata, self._rslots, self._layer, 
                                            self._rindex, self._vertexArrays)
        
        self.setDimensions(dx, dy)
        self.setPosition(pos)
        self.setColors(colors)
        self.setScaleX(scalex)
        self.setScaleY(scaley)
        self.setRotation(rotation)
        self.setAntialiasing(antialiasing)
        
    def setAntialiasing(self, amount):
        """Set the amount of antialisasing on the ellipse. This is a float
        between 0.0 and 1.0 that controls the proportion of the ellipse that
        should be antialisased"""
        self._vertexArrays.setAntialiasing(self._slots, amount)
        
    def setDimensions(self, dx, dy):
        """Set the dimensions of the ellipse"""
        newCoords = [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]
        self._vertexArrays.setOffsets(self._slots, newCoords)
        self._vertexArrays.setDimension(self._slots, (dx, dy))
            
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
