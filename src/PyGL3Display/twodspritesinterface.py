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

twodspritesinterface.py

This file provides "oldschool style" 2d Sprite specific features.

Constants:

topLeftOffsets, topRightOffsets, bottomLeftOffsets, bottomRightOffsets
centerOffsets:
  These offsets, if passed to a sprite as the offsets argument with
  the offsets given as relative will cause the named corner (or middle) 
  to be positioned at (0, 0)
"""

from __future__ import division
from PyGL3Display.twodbases import TwoDThing

__all__ = ['Sprite', 'AttribSprite', 'SpriteBuffer',
           'centerOffsets', 'topRightOffsets', 'topLeftOffsets',
           'bottomRightOffsets', 'bottomLeftOffsets',
           'makeAdjacentSprites']

bottomLeftOffsets = (0, 0), (1, 0), (1, -1), (0, -1)
bottomRightOffsets = (-1, 0), (0, 0), (0, -1), (-1, -1)
topLeftOffsets = (0, 1), (1, 1), (1, 0), (0, 0)
topRightOffsets = (-1, 1), (0, 1), (0, 0), (-1, 0)
centerOffsets = (-0.5, 0.5), (0.5, 0.5), (0.5, -0.5), (-0.5, -0.5)
        
    
class Sprite(TwoDThing):
    """A Sprite is primarily an Image and the information needed
    to draw it to screen."""
    
    filters = {'nearest': 0, 'bilinear': 1}
    
    def __init__(self, image, position=(0, 0), layer=0, 
                 flipx=False, flipy=False,
                 scalex=1, scaley=1, scale=None, rotation=0, visible=True,
                 tiling=(1, 1), filter=None,
                 color=(255, 255, 255, 255),
                 offsets=topLeftOffsets, offsetsRel=True, 
                 cameras=None, fragCameras=None,
                 spriteBuffer=None, 
                 renderer=None, rslots = None, rindex = None, 
                 vertexArrays = None):
        """Initialise the Sprite. Arguments (all optional):
           image: a Image to use as the sprites image.
           position: The (x, y) coordinate for the sprite.
                     Default (0, 0)
           offsets: A list/tuple of the offsets of the four corners of the 
                    sprite from position. Defaults to topLeftOffsets.
           offsetsRel: If True, multiply each of the offsets by the
                       sprites (width, height). This is needed for the preset
                       values of offsets. Defaults to True
           layer: The layer of the sprite. Default 0
           flipx: If the surface should be initially flipped X-axis. 
                  Default False
           flipy: If the surface should be initially flipped Y-axis. 
                  Default False
           visible: If the sprite should be visible. Default True
           filter: The filtering the sprite should use. 
                   Default to value from SpriteCommon
           rotation: The rotation of the sprite in radians. Default 0
           scalex: The x scaling of the sprite. Default 1.
           scaley: The y scaling of the sprite. Default 1.
           scale: The scale of the sprite. Default (not specified). 
                  Overrides scalex and scaley.
           tiling: If given, sprite will be tiled the number of time specified
                   the x and y directions.
                   NOTE1: If using Linear Filtering, the image should be loaded
                   as tiled or you will get a transparent line problem.
           color: The coloration of the sprite. Uses normal pygame RGBA color
                  values. Each pixel in the image is "multiplied" by this
                  color, so it's very useful for doing fading with the alpha
                  component. Default White with full opacity (255,255,255,255)
           spriteBuffer: optional SpriteBuffer for recycling the sprite
           cameras: A list of length < 8 or a dict with keys from a subset of 
                    1-8. In each case, values should be integers or camera
                    proxies. If a list, the first len(cameras) of the sprite 
                    will be set to the cameras specified. If a dict, the keys
                    are used to determine which cameras are set.
           fragCameras: as cameras, but length 4 and for fragment cameras
           renderer, rslots, rindex, vertexArrays: 
                If all are specified, use the given renderer etc. 
                For use internally be makeAdjacentSprites; not recommended for
                external use.
                             
           Notes:
            As a small note, Sprites are iterable. Iterating over them gives
            the sprite itself. This is done for the sake of Sprite and
            SpriteGroup having a common interface.
        """        
        
        if renderer and rslots and vertexArrays and rindex is not None:
            self._renderer = renderer
            self._rslots = rslots
            self._rindex = rindex
            self._layer = layer
            self._vertexArrays = vertexArrays
            self._slots = self._vertexArrays.getDataSlots(4)
            self._rdata = [self._slots[0], self._slots[1], self._slots[2], 
                           self._slots[0], self._slots[2], self._slots[3]]
            self._renderer.uploadSlotData(self._rdata, self._rslots, 
                                self._layer, self._rindex, self._vertexArrays)
        else:
            self._renderer = None
            self._vertexArrays = None
            self._slots = []
            self._rslots = []
        
        self._layer = layer
        self._flipx = False
        self._flipy = False
        self._buffer = spriteBuffer

        self.setVisibility(visible)
        
        if image is not None: 
            self.setImage(image)
        else:
            self._image = None
            self._width, self._height = 0, 0
            self._baseOffsets = ((0, 0), (0, 0), (0, 0), (0, 0))
            self._unmodOffsets = self._baseOffsets
            self._vertexArrays.setOffsets(self._slots, self._baseOffsets)

        if scale is None:
            self.setScaleX(scalex)
            self.setScaleY(scaley)
        else:
            self.setScale(scale)
            
        if cameras is not None:
            self.setCameras(cameras)
        if fragCameras is not None:
            self.setFragCameras(fragCameras)
            
        if filter is None:
            if self._renderer is not None:
                filter = self._renderer.getDefaultFilter()
            else:
                filter = 'bilinear'
        
        self.setTiling(tiling, updateSize=False)    
        self.setOffsets(offsets, relative=offsetsRel)
        self.setColor(color)
        self.setPosition(position)
        self.setLayer(layer)
        self.setRotation(rotation)
        self.flipX(flipx)
        self.flipY(flipy)
        self.setFilter(filter)
        
    def reset(self):
        """Resets the sprite to default configuration"""
        self._vertexArrays.setOffsets(self._slots, 
                                ((0, 0), (0, 0), (0, 0), (0, 0)))
        self._color = (255, 255, 255, 255)
        self._vertexArrays.setColor(self._slots, self._color)
        self._position = (0, 0)
        self._visible = True
        if self._rslots:
            self._renderer.uploadSlotData(self._rdata, self._rslots, 
                            self._layer, self._rindex, self._vertexArrays)
        self._vertexArrays.setScaleX(self._slots, 1)
        self._vertexArrays.setScaleY(self._slots, 1)
        self._scalex = 1
        self._scaley = 1        
        self._flipx = False
        self._flipy = False
        if self._layer:
            self._layer = 0
            if self._rslots:
                self._renderer.releaseRenderSlots(self._rslots, self._layer, 
                                            self._rindex, self._vertexArrays)
                self._rslots, self._rindex = self._renderer.getRenderSlots(6, 
                                            self._layer, self._vertexArrays)
                self._renderer.uploadSlotData(self._rdata, self._rslots, 
                                self._layer, self._rindex, self._vertexArrays)
                
    def __iter__(self):
        """Sprites are iterable as SpriteGroups are, and it's desirable to have
        both share the same interface."""
        return (self,).__iter__()
        
    def __len__(self):
        """Sprites share the same API as SpriteGroups, so..."""
        return 1
    
    def __del__(self):
        """Release the slots so they can be used by other things.
        Alternatively, if the sprite is registered with a buffer and the buffer
        is not yet full, return the sprite to the buffer."""
        destroy = self._buffer.releaseSprite(self) if self._buffer else True
        if destroy:
            try: 
                self._vertexArrays.releaseDataSlots(self._slots)
            except AttributeError: 
                pass
            try: 
                self._renderer.releaseRenderSlots(self._rslots, self._layer, 
                                            self._rindex, self._vertexArrays)
            except AttributeError: 
                pass
                
    def setTiling(self, tiling, updateSize=True):
        """Set the tiling on the sprite.
        Arguments:
           tiling: Tile the sprite the given amount of time in the x and y
                   directions.
                   e.g. (2, 1) tiles the sprite twice in the x direction.
           updateSize: If True, the size of the sprite will be changed to
                       allow the tiles to be full size. If False, the size
                       of the sprite will remain the same.
                       
           IMPORTANT: If using filtering, the image should be loaded
           as tiled or you will get a transparent line problem.
        """
        self._tiling = tiling
        self._vertexArrays.setTexRatios(self._slots, 
            ((0, tiling[1]), (tiling[0], tiling[1]), (tiling[0], 0), (0, 0)))
        if updateSize:
            self.setOffsets(self._unmodOffsets, self._originRel)
            
    def setFilter(self, filter):
        """Sets the filtering on the sprite.
           Filter should be from the following table:
           0 / 'nearest' : Use nearest neighbour
           1 / 'bilinear': Use bilinear filtering
        """
        self._filter = filter
        if filter in type(self).filters:
            filter = type(self).filters[filter]
        self._vertexArrays.setFilterType(self._slots, filter)
        
    def setOffsets(self, offsets, relative=True):
        """Set the coordinates of each of the sprites coordinates
        Arguments:
         offsets: A list containing the top-left, top-right, 
                  bottom-right, bottom-left coordinates of the sprite
         relative: If true, multiple each coordinate tuple by current image
                   width and height"""
        if relative is True:
            width, height = self._width, self._height
            baseOffsets = [(width*ox, height*oy) for ox, oy in offsets]
        else:
            baseOffsets = offsets
        
        tilesX, tilesY = self._tiling
        self._baseOffsets = [(ox * tilesX, oy * tilesY) 
                              for ox, oy in baseOffsets]
        
        self._unmodOffsets = offsets
        self._originRel = relative
        self._vertexArrays.setOffsets(self._slots, self._baseOffsets)
        
                
    def setImage(self, image):
        """Set the image of the sprite
        Arguments:
         image: An Image (or subclass, eg. Surface).
        """
        
        self._image = image
        
        self._width, self._height = self._image.getSize()
        
        if self._renderer != self._image.atlas:
            if self._vertexArrays is not None:
                if self._renderer is not None:
                    self._renderer.releaseRenderSlots(self._rslots, 
                            self._layer, self._rindex, self._vertexArrays)
                self._vertexArrays.releaseDataSlots(self._slots)
            self._renderer = self._image.atlas
            self._vertexArrays = self._renderer.getVertexArrays(4)
            self._slots = self._vertexArrays.getDataSlots(4)
            self._rslots, self._rindex = self._renderer.getRenderSlots(6, 
                                            self._layer, self._vertexArrays)
            self._rdata = [self._slots[0], self._slots[1], self._slots[2], 
                           self._slots[0], self._slots[2], self._slots[3]]
            if self._visible is True:
                self._renderer.uploadSlotData(self._rdata, self._rslots, 
                                 self._layer, self._rindex, self._vertexArrays)
        
        self._vertexArrays.setTexCoord(self._slots, self._image.coords)
        
    def flipX(self, flipped = None):
        """Flip the sprite horizontally"""
        if flipped != self._flipx:
            self._flipx = not self._flipx
            self._baseOffsets = [self._baseOffsets[3], self._baseOffsets[2], 
                                self._baseOffsets[1], self._baseOffsets[0]]
            self._vertexArrays.setOffsets(self._slots, self._baseOffsets)
            
    def flipY(self, flipped = None):
        """Flip the sprite vertically"""
        if flipped != self._flipy:
            self._flipy = not self._flipy
            self._baseOffsets = [self._baseOffsets[1], self._baseOffsets[0], 
                                self._baseOffsets[3], self._baseOffsets[2]]
            self._vertexArrays.setOffsets(self._slots, self._baseOffsets)
            
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

def makeAdjacentSprites(images, layer, spriteclass=Sprite):
    """Make some sprites which are guanteed to be adjacent within the layer.
    Notes: All images must be on the same atlas. This can be accomplished by
    subsurfaces. None of the sprites may change layer."""
    if not images: return []
    atlas = images[0].atlas
    if not all([image.atlas == atlas for image in images]):
        raise Exception('For adjacent sprites, all images must ' + \
                        'be on the same atlas')
    vertexArrays = atlas.getVertexArrays(4 * len(images))
    adjSlots, rindex = atlas.getRenderSlots(6 * len(images), layer, 
                                            vertexArrays)
    divadjSlots = [adjSlots[6*x:6*x+6] for x in xrange(int(len(adjSlots)/6))]
    return [spriteclass(image=image, layer=layer, renderer=atlas, 
                        rslots=rslots, rindex=rindex, 
                        vertexArrays=vertexArrays)
            for image, rslots in zip(images, divadjSlots)]

class AttribSprite(Sprite):
    """An AttribSprite is a sprite with the feature that setting its attributes
    will call the relevant functions to set the sprite data properly.
    For example:
     "attribSprite.position = (0, 0)" == "gl3sprite.setPosition((0,0))" 
    
    However, the caveat is that each operation is slower (all attribute writes
    on the sprite incur an additional function call overhead; this can add up
    quite quickly given it also applies internally!)
    
    In summary, this type of sprite is easier to program but carries a
    performance penalty. 
    
    One important note: As x and y scale can be set independently, there is
    no real "good" value to return for overall scale. So if reading the
    scale attribute, you get the x scale. If you're not setting the x or y 
    scaling independently, this is always correct. If you are, then don't
    read from the scale attribute.
    
    Magic attributes are as follows:
    image    = a GL3 image to use as the sprites image
    layer    = sprite layer
    flipx    = if the sprite should be flipped in x axis
    flipy    = if the sprite should be flipped in y axis
    scale    = scale the sprite by this amount
    scalex   = scale the sprite in the x direction by this amount
    scaley   = scale the sprite in the y direction by this amount
    visible  = if the sprite should be visible or not
    rotation = rotate this sprite about its origin by this amount
    """
    
    __init__ = Sprite.__init__
    magicVars = {'position':Sprite.setPosition, 'layer':Sprite.setLayer,
                 'flipx':Sprite.flipX, 'flipy':Sprite.flipY, 
                 'scale':Sprite.setScale, 'scalex':Sprite.setScaleX,
                 'scaley':Sprite.setScaleY, 'camera':Sprite.setCamera,
                 'visibile':Sprite.setVisibility, 
                 'rotation':Sprite.setRotation, 
                 'image':Sprite.setImage, 'offsets':Sprite.setOffsets
                 }
    magicStore = {'position':'_position', 'layer':'_layer', 'flipx':'_flipx',
                  'flipy':'_flipy', 'scale':'_scalex', 'scalex':'_scalex',
                  'scaley':'_scaley', 'visible':'_visible', 
                  'rotation':'_rotation', 'camera':'_camera',
                  '_image':'_image', 'offsets':'_unmodOffsets'}
    
    def __setattr__(self, attr, val):
        """Used to implement 'magic' variables"""
        if attr in type(self).magicVars:
            type(self).magicVars[attr](self, val)
        else:
            object.__setattr__(self, attr, val)
    
    def __getattr__(self, attr):
        """Used to get the value of 'magic' variables"""
        if attr in type(self).magicStore:
            return getattr(self, type(self).magicStore[attr])
        else: 
            raise AttributeError(str(type(self)) + ' has no attribute ' + attr)


class SpriteBuffer(object):
    """A buffer for sprites. Creating and deleting sprites is quite taxing
    on the CPU. If a Sprite is allocated a SpriteBuffer, then instead of
    being deleted it may be reset and placed in the buffer for later user.
    The buffer creates sprites as necessary, but will not let sprites which
    are still useful go to waste. To use the sprite buffer, just create one
    and use the createSprite method to create sprites. Then use setX on the
    returned sprite to control the Sprite.
    """
    def __init__(self, length=100, spriteClass=Sprite, 
                 resetFunc = Sprite.reset):
        """Initialise the Sprite Buffer.
         Arguments:
          length: The max number of sprites to keep in the buffer
          spriteClass: the sprites class
          resetFunc: The function to call which resets the sprite to its
                     default state."""
        self.spriteBuffer = []
        self.length = length
        self.spriteClass = spriteClass
        self.resetFunc = resetFunc

    def createSprite(self, *args, **kwargs):
        """Create or get a sprite which is associated with this buffer"""
        kwargs['spriteBuffer'] = self
        return self.spriteBuffer.pop() if self.spriteBuffer else \
               self.spriteClass(*args, **kwargs)
        
    def releaseSprite(self, sprite):
        """Called when a sprite is deleted. If the buffer isn't full
        the sprite is kept. Otherwise, the sprite buffer tells the sprite
        to fully kill itself.
        Arguments:
         sprite: the sprite to potentially save for later"""
        if len(self.spriteBuffer) < self.length: 
            self.spriteBuffer.append(sprite)
            self.resetFunc(sprite)
            return False
        else:
            return True

    
