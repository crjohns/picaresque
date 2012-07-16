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

twodbases.py

Provides base classes that 2d implementations can derive from
"""

__all__ = ['TwoDThing']

class TwoDThing(object):
    """A TwoDThing is anything that should have access to this common set of
    functions."""
    def __init__(self):
        """Initialises all variables for the twodthing"""
        self._slots = None
        self._rslots = None
        self._rindex = None
        self._vertexArrays = None
        self._layer = None
        self._rdata = None
        self._renderer = None
        
    def __del__(self):
        """Perform cleanup by releasing the renderer and shader slots"""
        self._renderer.releaseRenderSlots(self._rslots, self._layer, 
                                          self._rindex, self._vertexArrays)
        self._vertexArrays.releaseDataSlots(self._slots)
        
    def setScale(self, scale):
        """Set the scale of the sprite"""
        self._vertexArrays.setScaleX(self._slots, scale)
        self._vertexArrays.setScaleY(self._slots, scale)
        self._scalex = scale
        self._scaley = scale
        
    def setScaleX(self, scale):
        """Set the X scale of the sprite; scaling applied before rotation"""
        self._vertexArrays.setScaleX(self._slots, scale)
        self._scalex = scale

    def setScaleY(self, scale):
        """Set the Y scale of the sprite; scaling applied before rotation"""
        self._vertexArrays.setScaleY(self._slots, scale)
        self._scaley = scale
        
    def setCamera(self, n, camera):
        """Set the nth camera applied to the sprite"""
        if n < 4:
            self._vertexArrays.setCamera1(self._slots, n, int(camera))
        else:
            self._vertexArrays.setCamera2(self._slots, n - 4, int(camera))
        
    def setFragCamera(self, n, camera):
        """Set the nth fragment camera applied to the sprite"""
        self._vertexArrays.setFragCamera(self._slots, n, int(camera))
        
    def setCameras(self, cameras):
        """Set multiple cameras in one function call.
        If the cameras argument is a list or tuple, the first len(cameras) 
        cameras of the sprite are set. If the list has length > 8, only the 
        first 8 are used. 
        If the cameras argument is a dict, it should map a subset of the
        values 1-8 to cameras. Keys not in the range 1-8 are ignored"""
        if isinstance(cameras, (list, tuple)):
            for x in xrange(min(len(cameras), 8)):
                if x < 4:
                    self._vertexArrays.setCamera1(self._slots, x, 
                                                  int(cameras[x]))
                else:
                    self._vertexArrays.setCamera2(self._slots, x-4, 
                                                  int(cameras[x]))
        elif isinstance(cameras, dict):
            for x in cameras:
                if 1 <= x < 4:
                    self._vertexArrays.setCamera1(self._slots, x, 
                                                  int(cameras[x]))
                elif 4 <= x < 8:
                    self._vertexArrays.setCamera2(self._slots, x-4, 
                                                  int(cameras[x]))
        else:
            raise ValueError('cameras should be specified as a list or dict')
            
    def setFragCameras(self, cameras):
        """Set multiple fragment cameras in one function call.
        If the cameras argument is a list or tuple, the first len(cameras) 
        cameras of the sprite are set. If the list has length > 4, only the 
        first 4 are used. 
        If the cameras argument is a dict, it should map a subset of the
        values 1-4 to cameras. Keys not in the range 1-8 are ignored"""

        if isinstance(cameras, (list, tuple)):
            for x in xrange(min(len(cameras), 4)):
                self._vertexArrays.setFragCamera(self._slots, x, 
                                                 int(cameras[x]))
        elif isinstance(cameras, dict):
            for x in cameras:
                if 1 <= x <= 4:
                    self._vertexArrays.setFragCamera(self._slots, x, 
                                                     int(cameras[x]))
        else:
            raise ValueError('cameras should be specified as a list or dict')
            
    def setColor(self, color):
        """Set the coloration of the sprite"""
        self._color = color
        self._vertexArrays.setColor(self._slots, color)

    def setRotation(self, rotation):
        """Set the rotation of the sprite"""
        self._rotation = rotation
        self._vertexArrays.setRotation(self._slots, self._rotation)

    def setPosition(self, newpos):
        """Set the position of the sprite"""
        self._position = newpos
        self._vertexArrays.setPosition(self._slots, self._position)

    def setVisibility(self, visibility):
        """Set the visibility of the sprite"""
        self._visible = True if visibility else False
        if self._rslots:
            uploadData = self._rdata if visibility \
                         else [0] * len(self._rdata)
            self._renderer.uploadSlotData(uploadData, self._rslots, 
                            self._layer, self._rindex, self._vertexArrays)
                
    def setLayer(self, layer):
        """Set the layer of the sprite"""
        if layer != self._layer:
            if self._rslots:
                self._renderer.releaseRenderSlots(self._rslots, self._layer, 
                                            self._rindex, self._vertexArrays)
            self._layer = layer
            self._rslots, self._rindex = self._renderer.getRenderSlots(6, 
                                                    layer, self._vertexArrays)
            self._renderer.uploadSlotData(self._rdata, self._rslots, layer, 
                                            self._rindex, self._vertexArrays)

    def setColors(self, colors):
        """Set all the vertice colors of a lines
        Args:
          colors: A list of coordinates for the vertices of the lines
          WARNING: This trusts that the number of colors is the same as
          the number of vertices in the lines, otherwise this will fail
          with a cryptic error message"""
        self._colors = colors
        self._vertexArrays.setColors(self._slots, self._colors)
        
    def setVertexColor(self, n, color):
        """Set the color of the nth vertex in the lines
        Args:
          n: The number of the vertex to set
          color: The new color to set the vertex to
        """
        self._colors[n] = color
        self._vertexArrays.setColors(self._slots, self._colors)

    def setVertices(self, vertices):
        """Set all the vertices of the lines
        Args:
          vertices: A list of coordinates for the vertices of the lines
          WARNING: This trusts that the number of vertices is the same as
          previous, otherwise this will fail with a cryptic error message"""
        self._vertices = vertices
        self._vertexArrays.setOffsets(self._slots, self._vertices)
                
    def setVertex(self, n, pos):
        """Set the position of the nth vertex in the lines
        Args:
          n: The number of the vertex to set
          pos: The new position to set the vertex to
        """
        self._vertices[n] = pos
        self._vertexArrays.setOffsets(self._slots, self._vertices)

class TwoDLerper(TwoDThing):
    """A lerper has binds onto two arrays for every attribute.
    The values used in rendering are lerped between the two"""
    
    
if __name__ == '__main__':
    for attr in TwoDThing.__dict__.values():
        if isinstance(attr, type(lambda: 0)):
            print attr.__name__ + ' = TwoDThing.' + attr.__name__
            
        
