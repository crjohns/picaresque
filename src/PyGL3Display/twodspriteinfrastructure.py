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

twodspriteinfrastructure.py

Provides the infrastructure for twodsprites
"""
from __future__ import division

import ctypes
from ctypes import c_uint8
from collections import namedtuple
from weakref import WeakKeyDictionary
from PyGL3Display.infrastructure import GL3Client
from PyGL3Display.shaderdata import VertexArraySpec, UniformStore
from PyGL3Display.twodshaders import TwoDShaderCommon, TwoDShader
from twodtexture import TwoDTextureCommon, TwoDTexture
from OpenGL.GL import (glUniformMatrix4fv,  
    GL_TRUE, GL_UNSIGNED_BYTE, GL_TRIANGLES)

__all__ = ['SpriteCommon', 'SpriteShader', 'TextureAtlas2dshader',
           'TextureAtlas2d', 'Image', 'linearFiltering', 'noFiltering']

GL3Rect = namedtuple('GL3Rect', ('x', 'y', 'width', 'height', 'area'))
FloatCoords = namedtuple('FloatCoords', ('left', 'top', 'width', 'height'))

class SpriteCommonMetaclass(type):
    """Enables easy lazy creation of default objects
       by redefining the class __getattr__"""
    def __getattr__(cls, attr):
        if attr == 'defaultShader':
            cls.makeDefaultShader()
            return cls.defaultShader
        else:
            raise AttributeError('SpriteCommon does not have ' + attr)
            
class SpriteCommon(object):
    """The shared state between 2d sprites
    Variables:
      spec: a vertex array specification for sprite shaders
      maxTextureSize: The maximum edge size of a texture. Default is 4096,
                      but bad OpenGL drivers might necessitate lowering it.
                      (Example of known bad OpenGL driver: VirtualBox)
      minTextureSize: If a texture of this size cannot be created, assume that
                      there isn't much benefit in hardware acceleration and 
                      raise an error. Can be set arbitarily low, but as it gets
                      lower you cannot guarantee as much functionality.
                      Default is 512.
    """
    
    __metaclass__ = SpriteCommonMetaclass

    spec = VertexArraySpec('TwoDSpritesArray', slotMultiplier=1.5)
    spec.addArray('pos')
    spec.addArray('color', cType=c_uint8, 
                  glType=GL_UNSIGNED_BYTE, glNorm=GL_TRUE)
    spec.addArray('cameras1')
    spec.addArray('cameras2')
    spec.addArray('fragCameras')
    spec.addArray('texCoords', dynamic=False)
    spec.addArray('texRatios', dynamic=False)
    spec.addArray('rotozoom')
    spec.addArray('filters')
    spec.addAttrib('pos', 'Position', 2, 0)
    spec.addAttrib('pos', 'Offset', 2, 2, True)
    spec.addAttrib('texCoords', 'TexCoord', 4, 0)
    spec.addAttrib('texRatios', 'TexRatio', 2, 0, True)
    spec.addAttrib('color', 'Color', 4, 0)
    spec.addAttrib('color', 'Color', 4, 0, True)
    spec.addAttrib('cameras1', 'Camera1', 1, None)
    spec.addAttrib('cameras2', 'Camera2', 1, None)
    spec.addAttrib('fragCameras', 'FragCamera', 1, None)
    spec.addAttrib('rotozoom', 'ScaleX', 1, 0)
    spec.addAttrib('rotozoom', 'ScaleY', 1, 1)
    spec.addAttrib('rotozoom', 'Rotation', 1, 2)
    spec.addAttrib('filters', 'FilterType', 1, 0)
    
    @classmethod
    def makeDefaultShader(cls):
        """Create the default shader object"""
        cls.defaultShader = SpriteShader()
            
    @classmethod
    def setDefaultFilter(cls, filter):
        """Set default filter for the the default shader"""
        cls.defaultShader.setDefaultFilter(filter)


class SpriteShader(TwoDShader):
    """Shader for Two-D sprite shaders"""
    
    def __init__(self, defaultFilter = 'bilinear', cameraObj = None):
        """Initialise the 2d sprite shader
        Args:
         defaultFilter: the default filter to apply
         cameraObj: A TwoDCamerashader object for camera state. Default to 
                    shared camera state.
         projMatrix: a Projection matrix. Default to flat 2d grid matrix
         uniforms: a GL3UniformStore. Default to the shared 2d store"""
        if cameraObj is None:
            cameraObj = TwoDShaderCommon.defaultCameras
            
        vertexProg = """
            vec2 applyTransform(in vec2 pos, in vec2 origin, in vec2 offset, 
                       in float xScale, in float yScale, in float rotation);
            vec2 applyCameras(in vec4 camera, in vec2 pos);
            attribute vec4 pos;   // x,y = position, z,w offset 
            attribute vec4 texCoords; // x,y = x0, y0, z,w = x1-x0, y1-y0
            attribute vec4 texRatios; // x,y = texture ratio
            attribute vec4 color; 
            attribute vec4 rotozoom; // x = scaleX, y = scaleY, z = rotation
            attribute vec4 cameras1;
            attribute vec4 cameras2;
            attribute vec4 fragCameras;
            attribute vec4 filters;
            uniform mat4 projMatrix;
            varying vec4 v2fColor;
            varying vec4 v2fTex;
            varying vec4 v2fTilingPos;
            varying vec4 v2fCameras;
            varying vec4 v2fFilters;
            void main()
            {   
                vec2 transform = applyTransform(pos.xy, vec2(0, 0), 
                                 pos.zw, rotozoom.x, rotozoom.y, rotozoom.z);
                transform = applyCameras(cameras1, transform);
                transform = applyCameras(cameras2, transform);
                gl_Position = projMatrix * vec4 (transform.xy, 0, 1);
                v2fTilingPos.zw = gl_Position.xy;
                v2fTex = texCoords; 
                v2fTilingPos.xy = texRatios.xy;
                v2fColor = color;
                v2fCameras = fragCameras;
                v2fFilters = filters;
            }"""

        fragmentProg = """
            vec4 applyFragCameras(in vec4 cameras, in vec4 fragColor);
            bool drop(in vec2 pos);
            uniform sampler2D tex;
            uniform float texelSize;
            uniform float texSize;
            varying vec4 v2fColor;
            varying vec4 v2fTex;
            varying vec4 v2fTilingPos;
            varying vec4 v2fCameras;
            varying vec4 v2fFilters; // x = type, yzw = params

            void main()
            {   
                if (drop(v2fTilingPos.zw)) {discard;} 
                vec2 texP = 
                   vec2(v2fTex.x + mod((v2fTilingPos.x * v2fTex.z), v2fTex.z),
                        v2fTex.y + mod((v2fTilingPos.y * v2fTex.w), v2fTex.w));
                vec4 texColor;
                if (v2fFilters.x == 0.0) {
                    texColor = texture2D(tex, texP);
                }
                else if (v2fFilters.x == 1.0) {
                    vec4 tl = texture2D(tex, texP);
                    vec4 tr = texture2D(tex, texP + vec2(texelSize, 0));
                    vec4 bl = texture2D(tex, texP + vec2(0, texelSize));
                    vec4 br = texture2D(tex, texP + vec2(texelSize , texelSize));
                    vec2 mixVals = fract( texP * texSize );
                    vec4 texColorT = mix( tl, tr, mixVals.x );
                    vec4 texColorB = mix( bl, br, mixVals.x );
                    texColor = mix(texColorT, texColorB, mixVals.y);
                }
                
                gl_FragColor = applyFragCameras(v2fCameras, 
                              v2fColor * texColor);
            }"""
        
        super(SpriteShader, self).__init__(
            vertexProgs= [TwoDShaderCommon.applyTransformSource, 
            cameraObj.shaderSource, vertexProg], 
            fragmentProgs=[TwoDShaderCommon.dropSource, 
            cameraObj.fragShaderSource, fragmentProg])
            
        self.atlases = []
        self.defaultFilter = defaultFilter
        self.findAtlasSize()
        
    def setDefaultFilter(self, filter):
        """Set the default filter for sprites on this shader"""
        self.defaultFilter = filter
        
    def rebind(self):
        """Rebind all atlases in the shader"""
        for atlas in self.atlases: 
            atlas.unbind()
        for atlas in self.atlases: 
            atlas.rebind()
        
    def findAtlasSize(self):
        """Function to determine maximum atlas size"""
        self.atlasSize = TwoDTextureCommon.findTextureSize()

    def makeNewAtlas(self):
        """Create a new atlas of maximum possible size"""
        self.findAtlasSize()
        temp = TextureAtlas2d(size=self.atlasSize, shader = self)
        self.atlases.append(temp)        

    def getBox(self, width, height, image = None, wrapped = False):
        """Get a box in a texture atlas.
        Arguments:
         width  : width needed
         height : height needed
         image  : a Image object; if not specified, create a new Image 
        """
        if width >= self.atlasSize or height >= self.atlasSize:
            raise CannotAllocateError('Cannot allocate area of size ' +
                                      str(width) + 'x' + str(height))
        x = None
        n = len(self.atlases) - 1
        while not x and n != -1:
            x = self.atlases[n].getBox(width, height, image, wrapped)
            n -= 1
        if x is None:
            self.makeNewAtlas()
            x = self.atlases[-1].getBox(width, height, image, wrapped)
        return x        
        

class CannotAllocateError(Exception):
    """Exception raised when a rectangle cannot be allocated in an atlas"""


class CannotBlitIntoError(Exception):
    """Exception raised when a rectangle is larger than the area that it is
    attempting to upload into."""


class TextureAtlas2d(GL3Client):
    """A 2d texture atlas. These are responsible for storing images, and for
    drawing to screen any sprite using an image they contain. Configured for
    optimal use when rendering squares; triangles can be rendered as well, but
    they'll be overallocated slots in the texture atlas."""
    def __init__(self, size, shader, wasteWidth=10, border=1):
        """Initialise the texture array
        Arguments:
         size          : the size of the texture atlas to create
         shader        : the shader which created this atlas
         wasteWidth    : the wasted width tolerable
         border        : the border to give sprites
        """
        super(TextureAtlas2d, self).__init__(GL_TRIANGLES, shader,
                            vertexArraySpec=SpriteCommon.spec)
        
        self.border = border
        self.wasteWidth = wasteWidth
        
        self.texture = TwoDTexture(size)
        self.size = self.texture.size # Useful to guarantee consistency 
                                      # when debugging
        self.addRenderHook(self.texture.bindTexture)
        
        self.rects = [GL3Rect(0, 0, self.size, self.size, 
                      self.size*self.size)]
        self.images = WeakKeyDictionary()
        
        self.uniforms = UniformStore(set([
            TwoDShaderCommon.getProjMatrix(),
            TwoDShaderCommon.defaultCameras.cameraUniform,
            self.texture.texelUniform, self.texture.sizeUniform,
            ]))
    
    def unbind(self):
        """Destroy the gl texture"""
        self.texture.unbind()
        
    def rebind(self):
        """Recreates the atlas"""
        self.texture.rebind()
        for ref in self.images.iterkeyrefs():
            if ref(): 
                ref().reupload()
   
    def getAtlasImage(self, top=0.0, bottom=1.0, left=0.0, right=1.0):
        """Get an image of the atlas for debug purposes.
        Arguments:
          top, bottom, left, right: Floats between 0 and 1 describing
                                    the rectangle to view. Defaults to
                                    entire atlas.
        """
        floatCoords = FloatCoords(
                            top = top, left = left,
                            width = right - left,
                            height = bottom - top            
                      )
        leftEdge, topEdge = left * self.size, top * self.size
        width, height = (right - left) * self.size, \
                        (bottom - top) * self.size
        redrawData = GL3Rect(leftEdge, topEdge, width, height, width * height)
        return Image(self, redrawData, floatCoords)
            
    def getBox(self, width, height, image=None, wrapped=False):
        """Try to get a Box in this atlas. Returns None if it can't be
        allocated. 
        
        Arguments:
         width: The width to find
         height: The height to find
         image : a Image to use; if None create a new Image
         wrapped: If the image should be wrapped
        """
        
        if wrapped:
            width += 2
            height += 2
        
        findWidth = width + self.border
        findHeight = height + self.border
        findSize = findWidth * findHeight
        
        foundRect = None
        bestWastage = self.size * self.size + 1 
        for rect in self.rects:
            if rect.width > findWidth and rect.height > findHeight:
                thisWastage = rect.area - findSize
                if thisWastage < bestWastage:
                    foundRect = rect
                    bestWastage = thisWastage
        if foundRect is None:
            return None
        else:
            # We found a rect to upload to, so split it appropriately
            newX = foundRect.x + findWidth
            remainingX = foundRect.width - findWidth
            newY = foundRect.y + findHeight
            remainingY = foundRect.height - findHeight
            self.rects.remove(foundRect)
            ## Keep as large a box available as possible
            bigBox1 = GL3Rect(newX, foundRect.y, remainingX, foundRect.height,
                              remainingX * foundRect.height)
            bigBox2 = GL3Rect(foundRect.x, newY, foundRect.width, remainingY, 
                              foundRect.width * remainingY)
            if bigBox1.area > bigBox2.area:
                bigBox = bigBox1
                smallBox = GL3Rect(foundRect.x, newY, findWidth, remainingY, 
                                   findWidth * remainingY)
            else:
                bigBox = bigBox2
                smallBox = GL3Rect(newX, foundRect.y, remainingX, findHeight, 
                                   remainingX * findHeight)
            
            if bigBox.area > 0: 
                self.rects.append(bigBox)
            if smallBox.area > 0: 
                self.rects.append(smallBox)
            redrawData = GL3Rect(foundRect.x, foundRect.y, findWidth, 
                                 findHeight, findWidth * findHeight)
            topInt, leftInt, rightInt, bottomInt = \
                    foundRect.y, foundRect.x, newX-1, newY-1
                    
            if wrapped: 
                topInt += 1
                leftInt += 1
                rightInt -= 1
                bottomInt -= 1
                
            top = topInt / self.size
            left = leftInt / self.size
            right = rightInt / self.size
            bottom = bottomInt / self.size
                
            floatCoords = FloatCoords(
                            top = top, left = left,
                            width = right - left,
                            height = bottom - top            
                        )
                        
        if not image:
            ret = Image(self, redrawData, floatCoords, wrapped)
            self.images[ret] = True
            return ret
        else:
            Image.__init__(image, self, redrawData, floatCoords, wrapped)
            self.images[image] = True
            return image
            
    def deallocateImage(self, image):
        """Deallocates an image. This returns the box of the image
           to the pool. It does not defragment so fragmentation will
           happen."""
        self.rects.append(image.intCoords)

    def uploadToBox(self, image, rect, wrapped = False):
        """Put an image into a rectangle in the atlas
        Arguments:
         image: an image to upload; must be recognised by the decoder
         rect:  the rect inside the atlas to upload to
         wrapped: Should be true if the image is going to be wrapped
        """
        x, y = rect.x, rect.y
        if wrapped:
            size = image.getSizeWrapped()
            data = image.getRawWrapped()
        else:
            size = image.getSize()
            data = image.getRaw()
        if size > (rect.width, rect.height):
            raise CannotBlitIntoError('Image is bigger than allocated area.')
        self.texture.upload((x, y), size, data)
                        
    def getDefaultFilter(self):
        """Returns the default filter of the shader"""
        return self.shader.defaultFilter
                        

class Image(object):
    """Images are internal things, mainly. Image handles the storing
    of a texture in GPU memory.
    """
    def __init__(self, atlas, intCoords, floatCoords, wrapped):
        """Initialise the image
        Args:
          atlas: the texture atlas the image is on
          intCoords: integer coordinates of the region on the texture atlas
          floatCoords: float coordinates of the region on the texture atlas
          wrapped: If the image is wrapped or not"""
          
        self.atlas = atlas
        self.intCoords = intCoords
        self.coords = floatCoords
        self.rawImage = None
        self.wrapped = wrapped
        
    def getSize(self):
        """Returns the size of the image, not including wrapped area"""
        if self.rawImage is not None:
            return self.rawImage.getSize()
        else:
            return (0, 0)
    
    def __del__(self):
        """Deallocates the image from the texture atlas"""
        self.atlas.deallocateImage(self)
        
    def reupload(self):
        """Reuploads the image to the texture atlas"""
        if self.rawImage: 
            self.atlas.uploadToBox(self.rawImage, self.intCoords, 
                                   self.wrapped)
        
    def upload(self, image):
        """Upload an image to the atlas
        Arguments:
          image: a RawImage to upload"""
        self.rawImage = image
        self.atlas.uploadToBox(image, self.intCoords, self.wrapped)
        
    def subsurface(self, rect):
        """Return a subsurface of the image
           Arguments:
             rect: a Rect indicating the area to become the subsurface
        """
        # TODO: Test new code
        dx, dy = rect.x, rect.y
        rx, ry = self.intCoords.x + dx, self.intCoords.y + dy
        rwidth = min(dx + rect.width, self.intCoords.width) - dx
        rheight = min(dy + rect.height, self.intCoords.height) - dy
        childIntCoords = GL3Rect(rx, ry, rwidth, rheight, rwidth * rheight)
        
        atlasWidth, atlasHeight = self.atlas.size
        top = childIntCoords.y / atlasHeight
        bottom = (childIntCoords.y + childIntCoords.height) / atlasHeight
        left = childIntCoords.x / atlasWidth
        right = (childIntCoords.x + childIntCoords.width) / atlasWidth
        
        floatCoords = FloatCoords(
                      tl = (left, top),
                      tr = (right, top),
                      br = (right, bottom),
                      bl = (left, bottom)
                      )
        
        return Image(self.atlas, childIntCoords, floatCoords)
