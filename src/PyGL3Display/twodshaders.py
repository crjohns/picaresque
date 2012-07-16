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

twodshaders.py

Provides the functionality for 2d Cameras, and base functionality for 
2d shaders.
"""

from __future__ import division

import ctypes
import weakref
from PyGL3Display.infrastructure import GLCommon, GL3Shader
from PyGL3Display.shaderdata import UniformStore, Uniform
from OpenGL.GL import glUniform4fv, glGetIntegerv, glUniformMatrix4fv, \
                      GL_MAX_VERTEX_UNIFORM_COMPONENTS, GL_FALSE

__all__ = ['TwoDShaderCommon', 'TwoDCameraCommon', 'TwoDShader', 
           'TwoDVertexCamera', 'TwoDFragmentCamera']

class TwoDShaderCommon(object):
    """The base class for 2d Shaders. 
    applyTransformsSource is the base shader source for all 2d shaders
    2dShaders are mainly distinguished by thier use of this shader fragment
    and cameras."""
    
    class __metaclass__(type):
        def __getattr__(mcs, attr):
            if attr == 'defaultUniforms':
                mcs.defaultUniforms = UniformStore({})
                return mcs.defaultUniforms
            elif attr == 'defaultCameras':
                mcs.defaultCameras = TwoDCameraCommon(50)
                return mcs.defaultCameras        
                
    applyTransformSource = """
    vec2 applyTransform(in vec2 pos, in vec2 origin, in vec2 offset, 
                        in float xScale, in float yScale, in float rotation)
    {
        vec2 offsets = vec2 ((offset.x - origin.x) * xScale,
                             (offset.y - origin.y) * yScale);
        mat2 rotMatrix = mat2 (cos(rotation), sin(rotation),
                              -sin(rotation), cos(rotation));    
        offsets = (rotMatrix * offsets);
        vec2 ret = offsets + pos;
        return ret;
    }
    """
    dropSource = """
        bool drop(in vec2 pos)
        {
            return ((pos.x > 1.0) || (pos.x < -1.0) || 
                    (pos.y > 1.0) || (pos.y < -1.0));
        }"""
    
    twoDMatrix = None
    matrixRes = None
    
    @staticmethod
    def updateProjMatrix():
        """Update the shared projection matrix"""
        resolution = GLCommon.resolution
        TwoDShaderCommon.matrixRes = resolution
        if TwoDShaderCommon.twoDMatrix is None:
            matrixType = ctypes.c_float * 16
            projMatrix = matrixType()
        projMatrix[0] = 2 / resolution[0]
        projMatrix[5] = 2 / -resolution[1]
        projMatrix[12] = -1
        projMatrix[13] = 1
        projMatrix[15] = 1
        TwoDShaderCommon.twoDMatrix = Uniform('projMatrix', projMatrix, 
                                        glUniformMatrix4fv, [1, GL_FALSE])
        
    @staticmethod
    def getProjMatrix():
        """Return a 2d projection matrix"""
        if TwoDShaderCommon.matrixRes != GLCommon.resolution:
            TwoDShaderCommon.updateProjMatrix()
        return TwoDShaderCommon.twoDMatrix

        
class TwoDShader(GL3Shader):
    """A shared base for all 2D shaders"""
        

class TwoDCameraCommon(object):
    """A class to control camera state, and share it amongst shaders
    
    Cameras are numbered starting at 1. The 0'th is hard coded to do nothing,
    as it could get somewhat confusing if it is assigned to (as by default
    the 0'th camera is applied 8 times to everything).
    """
    
    def __init__(self, blockSize=None):
        """Initialise cameras
        Args:
         blockSize : The size of the block of uniforms to create. Defaults
         to maximum"""
        if blockSize is None:
            totalUniformSize = glGetIntegerv(GL_MAX_VERTEX_UNIFORM_COMPONENTS)
            blockSize = int(totalUniformSize) - 16 # 4 vec4s in ProjMatrix

        self.noOfCameras = int(blockSize / 8)
        self.cameraArray = (ctypes.c_float * blockSize)()
        self.cameraProxies = weakref.WeakValueDictionary()
       
        self.blockMap = [x for x in xrange(int(blockSize / 4))]
            
        self.shaderSource = """
        uniform vec4 cameraArray[""" + str(int(self.noOfCameras * 2)) + """];
        
        vec2 applyTransform(in vec2 pos, in vec2 origin, in vec2 offset, 
                            in float xScale, in float yScale, in float rotation);
        vec2 applyCamera(in float camera, in vec2 pos)
        { // Apply a camera to a position
          vec2 ret = pos;
          if (camera != 0.0) {
            int camBase = int(camera - 1.0);
            int camBase2 = camBase + 1;
            ret = applyTransform(cameraArray[camBase].xy, 
                        cameraArray[camBase].zw, pos, cameraArray[camBase2].x, 
                        cameraArray[camBase2].y, cameraArray[camBase2].z);
          } 
          return ret;
        }
        vec2 applyCameras(in vec4 cameras, in vec2 pos)
        { // Apply a vector of cameras to a position
          vec2 ret = applyCamera(cameras.x, pos);
          ret = applyCamera(cameras.y, ret);
          ret = applyCamera(cameras.z, ret);
          ret = applyCamera(cameras.w, ret);
          return ret;
        }
        """
        self.fragShaderSource = """
        uniform vec4 cameraArray[""" + str(int(self.noOfCameras * 2)) + """];
        
        vec4 applyFragCamera(in float camera, in vec4 fragColor)
        {
          vec4 ret = fragColor;
          if (camera != 0.0) {
             int camBase = int(camera - 1.0);
             ret = ret * cameraArray[camBase];
          }
          return ret;
        }
        vec4 applyFragCameras(in vec4 cameras, in vec4 fragColor)
        { 
          vec4 ret = applyFragCamera(cameras.x, fragColor);
          ret = applyFragCamera(cameras.y, ret);
          ret = applyFragCamera(cameras.z, ret);
          ret = applyFragCamera(cameras.w, ret);
          return ret;
        }
        """
        # Format: posx posy originx originy scalex scaley rotation blank

        self.cameraUniform = Uniform('cameraArray', self.cameraArray, 
                                    glUniform4fv, [int(self.noOfCameras*2)])
        self.cameraUniforms = set([self.cameraUniform])
        
    def getBlocks(self, n):
        """Get a block of memory of size n floats in the camera store"""
        x = 0
        found = False
        indicesList = self.blockMap
        indicesList.sort()
        length = len(indicesList) 
        while not found and x + n < length:
            if indicesList[x+n] - indicesList[x] == n:
                found = True
            else: 
                x += 1
        if not found:
            raise MemoryError('Ran out of space in cameraBlock')
        else:
            ret = [indicesList.pop(x) for _ in xrange(n)]
        return ret[0]
        
    def releaseBlocks(self, base, no):
        """Get blocks back from dead cameras"""
        for x in xrange(base, base+no):
            self.blockMap.append(x)
        
    def setCameraTuple(self, pos, tpl):
        """Sets a tuple of values in the cameras array"""
        self.cameraArray[pos:pos+len(tpl)] = tpl
        self.cameraUniform.dirty()
    
    def setCameraVal(self, pos, val):
        """Set the value of a position in the camera array"""
        self.cameraArray[pos] = val
        self.cameraUniform.dirty()

class TwoDFragmentCamera(object):
    """A fragment camera is an object that provides a fragment camera, i.e.
    a hardware accelerated method to set coloration on sprites. May be
    extended to provide other methods at somepoint
    """
    def __init__(self, camerasObj=None):
        """Initialise the camera"""
        if camerasObj is None:
            camerasObj = TwoDShaderCommon.defaultCameras
        self.camerasObj = camerasObj
        self.base = camerasObj.getBlocks(1)
        self.baseTimes4 = self.base * 4
        self.setCameraColor((1.0, 1.0, 1.0, 1.0))
        
    def __del__(self):
        """Release our camera block"""
        self.camerasObj.releaseBlocks(self.base, 1)
        
    def __int__(self):
        """Enable casting to an int, so a Camera can be used in a
        setCamera call"""
        return self.base + 1
        
    def setCameraColor(self, color):
        """Sets the coloration of the camera"""
        self.camerasObj.setCameraTuple(self.baseTimes4, color)
    
class TwoDVertexCamera(object):
    """A vertex camera is an provides a hardware accelrated set of transforms:
    scale (x and y independ), then rotate, then translate"""
    
    def __init__(self, camerasObj=None):
        """Initialise the camera proxy"""
        if camerasObj is None:
            camerasObj = TwoDShaderCommon.defaultCameras
        self.camerasObj = camerasObj
        self.base = camerasObj.getBlocks(2)
        self.baseTimes4 = self.base * 4
        self.setCameraScale(1)
        
    def __del__(self):
        """Release camera blocks"""
        self.camerasObj.releaseBlocks(self.base, 2)
        
    def __int__(self):
        """Enable casting to an int, so a Camera can be used in a
        setCamera call"""
        return self.base + 1
        
    def setCameraPosition(self, pos):
        """Set camera position"""
        self.camerasObj.setCameraTuple(self.baseTimes4, pos)
        
    def setCameraOrigin(self, origin):
        """Set the origin of the camera"""
        self.camerasObj.setCameraTuple(self.baseTimes4+2, origin)
        
    def setCameraScale(self, scale):
        """Set both X and Y scaling of the camera"""
        self.camerasObj.setCameraTuple(self.baseTimes4+4, (scale, scale))
        
    def setCameraScaleX(self, scale):
        """Set X scale of the camera"""
        self.camerasObj.setCameraVal(self.baseTimes4+4, scale)
        
    def setCameraScaleY(self, scale):
        """Set Y scale of the camera"""
        self.camerasObj.setCameraVal(self.baseTimes4+5, scale)
        
    def setCameraRotation(self, rotation):
        """Set camera rotation"""
        self.camerasObj.setCameraVal(self.baseTimes4+6, rotation)
