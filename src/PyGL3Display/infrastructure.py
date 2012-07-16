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

infrastructure.py

This file provides the basic infrastructure of the PyGL3Display project.
"""

from __future__ import division
import ctypes, weakref
from PyGL3Display.glcommon import ShaderError
from PyGL3Display.glcommoninst import GLCommon
from PyGL3Display.slices import Slices
from OpenGL.GL import \
     glCreateProgram, glLinkProgram, glAttachShader, glDrawElements, \
     glGetAttribLocation, glGetUniformLocation, \
     glDeleteProgram, glDeleteShader, glGetProgramiv, glGetProgramInfoLog, \
     GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, GL_LINK_STATUS, GL_FALSE

__all__ = ['GL3Client', 'GL3Shader']

class GL3Client(object):
    """GL3Client is a base class for items which interact directly with the 
    manager. The clients track all GL state, and handle the actual drawing 
    of primitives to screen."""
    
    def __init__(self, glType, shader, vertexArraySpec):
        """Initialise the GL3Client.
        Args:
         glType : The GL Type of the data to be rendered (e.g. GL_LINES)
         shader : the shader which created this client
         vertexArraySpec : An array specification for the vertex arrays this
                           client will be drawing"""
        self.vertexArraySpec = vertexArraySpec
        self.vertexArraysD = {} 
        self.shader = shader
        self.layers = {}
        self.renderHooks = []
        self.glType = glType
        shader.addClient(self)
        
    def addRenderHook(self, callback):
        """Add a function to be called from the client when rendering."""
        self.renderHooks.append(callback)
            
    def doTasks(self, layer):
        """Instuct the client to draw everything it is responsible for to
        screen, for the given layer. 
        Will also perform housekeeping as necessary."""
        glType = self.glType
        for vertexArrays in self.layers:
            layerDict = self.layers[vertexArrays]
            if layer not in layerDict:
                pass
            else:
                for func in self.renderHooks:
                    func(layer)
                layerData = layerDict[layer]
                for indicesData in layerData[3]:
                    if indicesData[5] is True: 
                        self.clean(indicesData, layerData[2])
                    if indicesData[2] == 0: 
                        pass
                    else:
                        self.uniforms.bind()
                        vertexArrays.bind()
                        glDrawElements(glType, indicesData[2], 
                            vertexArrays.indicesType, indicesData[7])
                            
    def makeLayer(self, layer, vertexArrays):
        """Create a new layer
        Arguments:
         layer   : the layer to create
        Notes:
         The data format of the layer is a list, with items as follows:
         [0] indicesType: ctypes type for indices lists
         [1] indicesArrayLen: Length of indices array
         [2] indicesLength: The length of each index in bytes
         [3] indicesLists: List of lists made by makeLayerIndices
        This format is used over named tuples as named tuples do not have
        assignment to values (used on min, len, dirty) and lists are faster
        than dicts or objects (approx. 50%).
        """
        indicesLength = int(vertexArrays.noSlots * vertexArrays.slotMultiplier)
        indicesArrayType = vertexArrays.indicesCType * indicesLength
        sizeOfIndices = vertexArrays.sizeOfIndices
        GLCommon.updateLayers(layer)
        self.shader.addClientLayer(self, layer)
        layerData = [indicesArrayType, indicesLength, sizeOfIndices, []]
        if vertexArrays not in self.layers: 
            self.layers[vertexArrays] = {}
        self.layers[vertexArrays][layer] = layerData
    
    def makeLayerIndices(self, layer, vertexArrays):
        """Makes a list to store one set of indices on the given layer.
        Lists are of the following form:
         [0] indices: The ctypes array of indices
         [1] min: the index of the first element to draw of indices
         [2] len: the index of the last element to draw of indices - min
         [3] slots: a Slices object to handle slots to give out
         [4] allocated: a list of slots already allocated
         [5] dirty: flag to determine if housekeeping is necessary
         [6] pending: a list of slots (ungrouped) to reuse, 
                      but not sorted into [3]
         [7] startAddress: the address that relevant data starts at 
                           for a GL call
        """
        layerData = self.layers[vertexArrays][layer]
        newLayerIndices = [layerData[0](), 0, 0, Slices(0, layerData[1]), 
                           set(), False, [], 0]
        newLayerIndices[7] = (layerData[0].from_address(
                               ctypes.addressof(newLayerIndices[0])))
        layerData[3].append(newLayerIndices)
        return newLayerIndices, len(layerData[3]) - 1
        
    def getVertexArrays(self, n):
        """Return a vertex array that has at least n slots available"""
        ret = None
        for vertexArrays in self.vertexArraysD:
            if vertexArrays.canAllocDataSlots(n):
                ret = vertexArrays
                break
        if ret is None:
            ret = self.vertexArraySpec.makeArrays(65535)
            self.vertexArraysD[ret] = []
        return ret
        
    def getRenderSlots(self, n, layer, vertexArrays):
        """Get n slots in the render array
        Always returns adjacent items
        Arguments:
         image: The image to allocate slots to
         n: The number of slots needed
         layer: The layer the slots should be on
        """
        if (vertexArrays not in self.layers or 
           layer not in self.layers[vertexArrays]): 
            self.makeLayer(layer, vertexArrays)
        layerData = self.layers[vertexArrays][layer]
        indx = 0
        found = False
        while not found and indx < len(layerData[3]):
            indicesData = layerData[3][indx]
            slices = indicesData[3]
            found = indicesData[3].canAllocate(n)
            
        if not found:
            indicesData, indx = self.makeLayerIndices(layer, vertexArrays)
            slices = indicesData[3]
                
        ret = slices.allocate(n)
        layerData[3][indx][5] = True
        layerData[3][indx][4].update(ret)
        return ret, indx
        
    def releaseRenderSlots(self, slots, layer, indx, vertexArrays):
        """Release slots from a sprite
        Arguments:
         slots: the slots to release
         layer: the layer to release the slots from
        """
        indicesData = self.layers[vertexArrays][layer][3][indx]
        indicesData[5] = True
        indicesData[6].extend(slots)
        indicesData[3].release(slots)

    def uploadSlotData(self, data, slots, layer, indx, vertexArrays):
        """Upload some slots to be rendered.
        Arguments:
         data: the n slots corresponding to the vertex data indices
         slots: the n slots to upload to
         layer: the layer to upload to
        """
        if (vertexArrays not in self.layers or 
           layer not in self.layers[vertexArrays] or
           not (indx < len(self.layers[vertexArrays][layer]))): 
            raise ValueError('Layer does not exist on client')
        for x in xrange(len(slots)):
            self.layers[vertexArrays][layer][3][indx][0][slots[x]] = data[x]
    
    @staticmethod
    def clean(layerData, sizeOfIndices):
        """Perform housekeeping on a layerData;
        doTasks should call this if layerData[5] is True"""
        for slot in layerData[6]: 
            layerData[0][slot] = 0
        layerData[3].join()
        layerData[4].difference_update(layerData[6])
        layerData[6] = []
        layerData[5] = False
        if layerData[4]:
            layerData[1] = min(layerData[4])
            maximum = max(layerData[4])
            layerData[2] = maximum - layerData[1] + 1
            layerData[7] = type(layerData[0]).from_address(
                            ctypes.addressof(layerData[0]) +
                            (sizeOfIndices*layerData[1])
                           )
        else:
            layerData[1:3] = 0, 0        


class GL3Shader(object):
    """Abstraction of a shader program and the vertex arrays which 
    support it"""
    
    def __init__(self, vertexProgs, fragmentProgs, **kwargs):
        """Initialise the shader.
        Arguments:
         vertexProgs  : A list of vertex programs (source code)
         fragmentProgs: A list of fragment programs (source code)"""
        self.vertexProgs = vertexProgs
        self.fragmentProgs = fragmentProgs
        fullProg = '\n'.join(vertexProgs + fragmentProgs)
        arrays = set()
        uniforms = set()
        for line in fullProg.split('\n'):
            line = line.strip()
            if line.startswith('attribute'):
                arrays.add(line.partition(' ')[2].partition(' ')[2]
                    .partition(';')[0].partition('[')[0].strip())
            elif line.startswith('uniform'):
                uniforms.add(line.partition(' ')[2].partition(' ')[2]
                    .partition(';')[0].partition('[')[0].strip())
        self.arrayNames = arrays
        self.uniforms = uniforms
        self.setup()
        self.clientLayers = {}
        self.clients = weakref.WeakKeyDictionary()
        GLCommon.addShader(self)
        
    def addClient(self, client):
        """Add a client to the shader"""
        self.clients[client] = True
        
    def addClientLayer(self, client, layer):
        """Allow a client to draw on a layer
        Arguments:
         client : The client to allow
         layer : The layer to allow to draw on"""
        if layer not in self.clientLayers: 
            self.clientLayers[layer] = weakref.WeakKeyDictionary()
        self.clientLayers[layer][client] = True

    def removeClientLayer(self, client, layer):
        """Disallow a client to draw on a layer; this is for performance,
        if it gets used.
        Arguments:
         client: The client to disallow
         layer: The layer to disallow drawing onto"""
        if layer in self.clientLayers and client in self.clientLayers[layer]: 
            del self.clientLayers[layer][client]

    def setup(self):
        """Perform the setup of the actual shader program, and the necessary
        setup of data for binding arrays/uniforms."""
        
        self._vertexShaders = [
           GLCommon.getShader(vertexProg, GL_VERTEX_SHADER) for 
           vertexProg in self.vertexProgs]
        self._fragmentShaders = [
           GLCommon.getShader(fragmentProg, GL_FRAGMENT_SHADER) for 
           fragmentProg in self.fragmentProgs]
                                 
        self.shaderProgram = glCreateProgram()
        for vertexShader in self._vertexShaders:
            glAttachShader(self.shaderProgram, vertexShader)
        for fragmentShader in self._fragmentShaders:
            glAttachShader(self.shaderProgram, fragmentShader)
        glLinkProgram(self.shaderProgram)
        if glGetProgramiv(self.shaderProgram, GL_LINK_STATUS) == GL_FALSE:
            infoLog = glGetProgramInfoLog(self.shaderProgram)
            errorMessage = 'Shader Link Error:\n Error Message:' + infoLog
            raise ShaderError(errorMessage)
        
        GLCommon.useProgram(self)
        
        self.arrayLocs = dict([(key, 
            glGetAttribLocation(self.shaderProgram, key)) 
            for key in self.arrayNames])
        self.uniformLocs = dict([(key, 
                             glGetUniformLocation(self.shaderProgram, key)
                            ) for key in self.uniforms])

    def rebind(self):
        """Reset the shader, and all managers attached to it"""
        glDeleteProgram(self.shaderProgram)
        for shader in self._vertexShaders:
            glDeleteShader(shader)
        for shader in self._fragmentShaders:
            glDeleteShader(shader)
        self.setup()
        for ref in self.clients.iterkeyrefs():
            if ref(): 
                ref().rebind()      
            
    def doTasks(self, layer):
        """Perform all tasks on a given layer
        Arguments:
         layer : the layer to draw"""
        if layer in self.clientLayers:
            if GLCommon.boundShader is not self:
                GLCommon.useProgram(self)
            for client in self.clientLayers[layer]:
                client.doTasks(layer)
                
