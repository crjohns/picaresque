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

twodspritegroups.py

This file provides the old, software driven, sprite group class. 
"""

__all__ = ['SpriteGroup']

class SpriteGroup(object):
    """An object to group together Sprites, like a Pygame group.
    SpriteGroup present a similar API to a Sprite, with an operation
    applied to the group being applied to all contained sprites. Because
    the SpriteGroup does some caching, this normally means that the operations
    on the SpriteGroup are faster than what you'd get if you iterated over
    any old container of sprites.
    
    SpriteGroup do not implement setImage, as it doesn't make too much sense.
    SpriteGroup currently don't implement flipping.
    
    SpriteGroup are (essentially) a software implementation of Cameras.
    In most cases it is more advantageous to use Cameras, as these are fully
    hardware accelerated. However, in some cases Groups would be preferable,
    for example for a large number of small blocks of text.
    
    There is no way to remove a Sprite from a SpriteGroup at present.
    """
    def __init__(self, sprites=None):
        """Create a SpriteGroup
           Arguments:
                sprites: The sprite or sprites to be in the group initially
        """
        self._vertexArrays = None 
        self._spritesByAtlas = {}
        self._slots = set()
        self._dirtyAtlases = {}
        self._deletedRenderSlots = set()
        self._deletedSprites = set()
        self._sprites = set()
        
        if sprites is not None:
            for container in sprites: 
                self.add(container)
        
    def __iter__(self):
        """Make the SpriteGroup an iterable"""
        self.clean()
        return self._sprites.__iter__()
        
    def __len__(self):
        """Provide a way of determining the number of elements in the group"""
        return self._sprites.__len__()
    
    def clean(self):
        """Remove any sprites which have been removed from the group"""
        if self._dirtyAtlases:
            for atlas in self._dirtyAtlases:
                self._spritesByAtlas[atlas][0].difference_update(
                                                  self._dirtyAtlases[atlas][0])
                self._spritesByAtlas[atlas][1].difference_update(
                                                  self._dirtyAtlases[atlas][1]) 
            self._slots.difference_update(self._deletedRenderSlots)
            self._sprites.difference_update(self._deletedSprites)
            self._dirtyAtlases.clear()
            self._deletedRenderSlots.clear()
            self._deletedSprites.clear()
            
    def add(self, container):
        """Add a sprite or iterable container of sprites to the group
        Arguments:
         container: the sprite or container to add"""
        for sprite in container:
            if self._vertexArrays is None:
                self._vertexArrays = sprite._vertexArrays
            elif sprite._vertexArrays != self._vertexArrays:
                raise Exception('Tried to add something to a group which' + \
                                ' does not share the groups vertexArrays')
            if sprite not in self._sprites:
                spriteAtlas = sprite._renderer
                if spriteAtlas not in self._spritesByAtlas:
                    self._spritesByAtlas[spriteAtlas] = [set(), set()]
                self._spritesByAtlas[spriteAtlas][0].update(
                                                        sprite._rdata)
                self._spritesByAtlas[spriteAtlas][1].update(sprite._rslots)
                self._sprites.add(sprite)
                self._slots.update(sprite._rslots)
                spritePosX, spritePosY = sprite._position
                sprite._baseOffsets = [(offsetX+spritePosX, offsetY+spritePosY) 
                                for offsetX, offsetY in sprite._baseOffsets]
                sprite._position = (0, 0)
                sprite._vertexArrays.setPosition(sprite._slots, 
                                                 sprite._position)
                sprite._vertexArrays.setOffsets(sprite._slots, 
                                                sprite._baseOffsets)
            
    def setPosition(self, newPos):
        """Set the position of all sprites in the group."""
        for sprite in self: 
            sprite._position = newPos
        self._vertexArrays.setPosition(self._slots, newPos)
    
    def setLayer(self, layer):
        """Set the layer of all sprites in the group. This is not a
        very fast operation at present."""
        for sprite in self:
            if sprite._layer != layer:
                sprite._renderer.releaseRenderSlots(
                            sprite._rslots, sprite._layer, 
                            sprite._rindex, sprite._vertexArrays)
                sprite._layer = layer
                sprite._rslots, sprite._rindex = (
                        sprite._renderer.getRenderSlots(6, 
                        sprite._layer, sprite._vertexArrays))
                sprite._renderer.uploadSlotData(sprite._rdata, sprite._rslots, 
                        sprite._layer, sprite._rindex, sprite._vertexArrays)
                
    def setScale(self, scale):
        """Set the scale of all sprites in the group."""
        for sprite in self:
            sprite._scalex = scale
            sprite._scaley = scale
        self._vertexArrays.setScaleX(self._slots, scale)
        self._vertexArrays.setScaleY(self._slots, scale)
    
    def setScaleY(self, scaley):
        """Set the Y scale of all sprites in the group."""
        for sprite in self: 
            sprite._scaley = scaley
        self._vertexArrays.setScaleY(self._slots, scaley)
    
    def setScaleX(self, scalex):
        """Set the X scale of all sprites in the group."""
        for sprite in self: 
            sprite._scalex = scalex
        self._vertexArrays.setScaleX(self._slots, scalex)
        
    def setRotation(self, rotation):
        """Set the rotation of all sprites in the group."""
        for sprite in self: 
            sprite._rotation = rotation
        self._vertexArrays.setRotation(self._slots, rotation)
        
#    def setCamera(self, camera):
        # TODO: Fix for new system
#        """Set the camera of all sprites in the group."""
#        for sprite in self: 
#            sprite._camera = camera
#        self._vertexArrays.setCamera(self._slots, camera)
                            
    def setColoration(self, color):
        """Set the coloration of all sprites in the group."""
        for sprite in self: 
            sprite._color = color
        self._vertexArrays.setColor(self._slots, color)
        
    def setVisibility(self, visibility):
        """Set the visibility of all sprites in the group."""
        self.clean()
        visibility = True if visibility else False
        zeros = (0, 0, 0, 0, 0, 0)
        for sprite in self: 
            sprite._visible = visibility
            uploadSlots = sprite._rdata if visibility else zeros
            sprite._renderer.uploadSlotData(uploadSlots, sprite._rslots, 
                        sprite._layer, sprite._rindex, sprite._vertexArrays)

        