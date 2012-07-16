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

shaderdata.py

This file provides the base classes which hold data for consumption by shaders
(the vertex arrays and the uniforms).
"""

from PyGL3Display.glcommoninst import GLCommon
from PyGL3Display.slices import Slices
from OpenGL.GL import (glGenBuffers, glBindBuffer, glBufferData, glBufferSubData,
    GL_FLOAT, GL_FALSE, GL_UNSIGNED_INT, GL_ARRAY_BUFFER, GL_STATIC_DRAW, 
    GL_DYNAMIC_DRAW)
from ctypes import c_float
import ctypes, weakref

__all__ = ['VertexArraySpec', 'Uniform', 'UniformStore']

class VertexArraySpec(object):
    """Defines a specification for a class of vertex arrays"""
    def __init__(self, name, slotMultiplier=1.0):
        """Initialise the VertexArraySpec
        Args:
          name: The name of the class of vertex arrays to create
                (as would be used in documentation)
          slotMultiplier: A multiplier to give an idea of how many render
                          slots are needed per data point. For example, on a
                          sprite 4 data points are needed per sprite, but to
                          draw two triangles 6 render points are needed, so
                          the multiplier is 1.5. This is only a guide, can be
                          ignored if OpenGL wouldn't support a long enough 
                          array, and shouldn't result in too big a performance
                          hit even if it is completely ignored. Default: 1.0
        """
        
        self.name = name
        self.spec = {}
        self.attribs = []
        self.swappers = []
        self.vertexArraysClass = None
        self.slotMultiplier = slotMultiplier
        
    def copy(self, newName):
        """Return a copy of the vertex arrays spec, but this copy
        will always be unfrozen"""
        copy = type(self)(newName, self.slotMultiplier)
        copy.spec = self.spec.copy()
        copy.attribs = self.attribs[:]
        copy.swappers = self.swappers[:]
        return copy
        
    def addArray(self, name, cType=c_float, glType=GL_FLOAT, 
                       noAttribs=4, glNorm=GL_FALSE, glStride=0,
                       dynamic=True):
        """Add an array to the specification. Defaults to float vec4s"""
        if self.vertexArraysClass is None:
            self.spec[name] = (cType, (noAttribs, glType, glNorm, glStride),
                                dynamic)
        else:
            raise Exception('VertexArraySpec has been frozen')
    
    def addAttrib(self, arrayName, attribName, attribSize, attribOffset,
                  attribBatched=False):
        """Add an attribute which will gain a setter function
        If attribOffset is None, the offset is an argument to the setter 
        function
        The functions added to the class are as follows:
        (with attribName == 'Attrib'; replace Attrib with the actual
         attribName for an actual usage')
        setAttribs(slots, values): 
          take two lists, slots and values, and set the value of slot[x] to
          values[x]
        setAttrib(slots, value, offset): 
          For each slot in slots, set the value of slot + offset to value
        setAttrib(slots, value): 
          For each slot in slots, set the value of the slot to value"""
        if self.vertexArraysClass is None:
            self.attribs.append((attribName, arrayName, attribSize, 
                                 attribOffset, attribBatched))
        else:
            raise Exception('VertexArraySpec has become frozen')
            
    def addSwapper(self, name, docstring, swaps):
        """Add an array swapper to the spec"""
        if self.vertexArraysClass is None:
            self.swappers.append((name, docstring, swaps))
        else:
            raise Exception('VertexArraySpec has become frozen')
            
    # Index format for setterMaker keys:
    # (attribBatched, singleAttrib, offsetIsNone, dynamic)
    setterMakers = {
        (True, False, False, False): 'makeBatchSetter',
        (False, True, True, False): 'makeVariableValSetter',
        (False, True, False, False): 'makeValSetter',
        (False, False, False, False): 'makeSetter',
        (True, False, False, True): 'makeBatchSetterDyn',
        (False, True, True, True): 'makeVariableValSetterDyn',
        (False, True, False, True): 'makeValSetterDyn',
        (False, False, False, True): 'makeSetterDyn',
    }            
    
    def makeVertexClass(self):
        """Create and metaprogram a class that matches the current spec"""
        class VertexArrayClass(VertexArrays):
            pass
        self.vertexArraysClass = VertexArrayClass
        VertexArrayClass.__name__ = self.name
        VertexArrayClass.__doc__ = "Stores and manages vertex arrays"""
        VertexArrayClass.slotMultiplier = self.slotMultiplier
        for attribName, arrayName, attribSize, attribOffset, attribBatched \
        in self.attribs:
            itemSize = self.spec[arrayName][1][0]
            setterName = 'set' + attribName
            if attribBatched:
                setterName += 's'
            offsetIsNone = attribOffset is None
            singleAttrib = attribSize == 1
            dynamic = self.spec[arrayName][2]
            
            signature = (attribBatched, singleAttrib, offsetIsNone, dynamic)
            if signature not in self.setterMakers:
                raise Exception('No valid setter maker')
            
            setterMakerName = self.setterMakers[signature]
            setterMaker = getattr(VertexArrayClass, setterMakerName)
            setterMaker(setterName, attribName, arrayName, itemSize, 
                        attribSize, attribOffset)
                                
        for swapperArgs in self.swappers:
            VertexArrayClass.makeSwapper(*swapperArgs)
            
    def makeArrays(self, length):
        """Freeze the spec and return a VertexArrays object of the class
        defined by the spec."""
        if self.vertexArraysClass is None:
            self.makeVertexClass()
        arrays = {}
        for name in self.spec:
            arraySpec = self.spec[name]
            cArray = (arraySpec[0] * (arraySpec[1][0] * length))()
            arrays[name] = [cArray, arraySpec[1], arraySpec[2]] 
        return self.vertexArraysClass(length, arrays)
        

class VertexArraysMetaclass(type):
    """A Metaclass providing factory functionality for setters on shaders.
    Arguments to the functions:
      name: the name the function should be given
      docdtype: the type of data (e.g. position coords) for documentation
      arrayName: the name of the attribute of the array 
            (i.e. getattr(self, array) = array on an instance of the class)
      itemSize: the number of elements in each item
      itemLen (not for makeValSetter): the number of elements in an item
      offset: An offset to apply (i.e. if packing scaleX, scaleY into a 2 float
              array, then scaleX has offset 0, scaleY has offset 1)
      """
      
    def finaliseFunc(cls, name, doc, func):
        """Finalises a metaprogrammed function by assigning its name, docstring
        and assigning it to the class"""
        func.__name__ = name
        func.__doc__ = doc
        setattr(cls, name, func)
      
    def makeValSetterDyn(cls, name, docdtype, arrayName, itemSize, itemLen, offset):
        """Makes a single value setter for a dynamic VBO"""
        doc = "Sets each slot in slots to " + docdtype + " specified"
        def setter(self, slots, val):
            array = self.arraysR[arrayName]
            dirtyElems = self.dirtyRange[arrayName]
            dirtyElems[0].add(slots[0] * itemSize + offset)
            dirtyElems[1].add(slots[-1] * itemSize + offset)
            self.dirty.add(arrayName)
            for pos in slots:
                array[pos*itemSize+offset] = val
        
        cls.finaliseFunc(name, doc, setter)
    
    def makeValSetter(cls, name, docdtype, arrayName, itemSize, itemLen, offset):
        """Makes a single value setter for a static VBO"""
        doc = "Sets each slot in slots to " + docdtype + " specified"
        def setter(self, slots, val):
            array = self.arraysR[arrayName]
            self.dirty.add(arrayName)
            for pos in slots:
                array[pos*itemSize+offset] = val
        
        cls.finaliseFunc(name, doc, setter)
        
    def makeSetterDyn(cls, name, docdtype, arrayName, itemSize, itemLen, offset):
        """Make a tuple value setter for a dynamic VBO"""
        doc = "Sets each slot in slots to " + docdtype + " specified"
        itemLenPlusOffset = itemLen + offset
        def setter(self, slots, val):
            array = self.arraysR[arrayName]
            dirtyElems = self.dirtyRange[arrayName]
            dirtyElems[0].add(slots[0] * itemSize + offset)
            dirtyElems[1].add(slots[-1] * itemSize + itemLenPlusOffset)
            self.dirty.add(arrayName)
            for pos in slots:
                array[pos*itemSize+offset:pos*itemSize+itemLenPlusOffset] = val
        
        cls.finaliseFunc(name, doc, setter)
        
    def makeSetter(cls, name, docdtype, arrayName, itemSize, itemLen, offset):
        """Make a tuple value setter for a static VBO"""
        doc = "Sets each slot in slots to " + docdtype + " specified"
        itemLenPlusOffset = itemLen + offset
        def setter(self, slots, val):
            array = self.arraysR[arrayName]
            self.dirty.add(arrayName)
            for pos in slots:
                array[pos*itemSize+offset:pos*itemSize+itemLenPlusOffset] = val
        
        cls.finaliseFunc(name, doc, setter)
    
    def makeBatchSetterDyn(cls, name, docdtype, arrayName, itemSize, itemLen, 
                        offset): 
        """Makes a batch tuple setter for a dynamic VBO"""
        doc = ("Set each slot to the " + docdtype + " value corresponding to" +
               " its position in vals")
        lenplusOffset = itemLen+offset
        def batchSetter(self, slots, vals):
            array = self.arraysR[arrayName]
            dirtyElems = self.dirtyRange[arrayName]
            dirtyElems[0].add(slots[0] * itemSize + offset)
            dirtyElems[1].add(slots[-1] * itemSize + lenplusOffset)
            self.dirty.add(arrayName)
            for pos, val in zip(slots, vals):
                pos = pos*itemSize
                array[pos+offset:pos+lenplusOffset] = val
            
        cls.finaliseFunc(name, doc, batchSetter)
        
    def makeBatchSetter(cls, name, docdtype, arrayName, itemSize, itemLen, 
                        offset): 
        """Makes a batch tuple setter for a static VBO"""
        doc = ("Set each slot to the " + docdtype + " value corresponding to" +
               " its position in vals")
        lenplusOffset = itemLen+offset
        def batchSetter(self, slots, vals):
            array = self.arraysR[arrayName]
            self.dirty.add(arrayName)
            for pos, val in zip(slots, vals):
                pos = pos*itemSize
                array[pos+offset:pos+lenplusOffset] = val
            
        cls.finaliseFunc(name, doc, batchSetter)
        
    def makeVariableValSetterDyn(cls, name, docdtype, arrayName, itemSize, 
                              itemLen, offset):
        """Makes a single value setter that takes an offset for a dynamic 
        VBO"""
        doc = "Sets one of the " + docdtype + " of slots specified, as" + \
              "given by offset"
        def setter(self, slots, offset, val):
            array = self.arraysR[arrayName]
            dirtyElems = self.dirtyRange[arrayName]
            dirtyElems[0].add(slots[0] * itemSize + offset)
            dirtyElems[1].add(slots[-1] * itemSize + offset)
            self.dirty.add(arrayName)
            for pos in slots:
                array[pos*itemSize+offset] = val
            
        cls.finaliseFunc(name, doc, setter)
        
    def makeVariableValSetter(cls, name, docdtype, arrayName, itemSize, 
                              itemLen, offset):
        """Makes a single value setter that takes an offset for a static VBO"""
        doc = "Sets one of the " + docdtype + " of slots specified, as" + \
              "given by offset"
        def setter(self, slots, offset, val):
            array = self.arraysR[arrayName]
            self.dirty.add(arrayName)
            for pos in slots:
                array[pos*itemSize+offset] = val
            
        cls.finaliseFunc(name, doc, setter)
        
    def makeSwapper(cls, funcName, docstring, swaps):
        """Make an array swapper"""
        def swapper(self):
            for oldName, newName in swaps:
                temp = self.arraysR[oldName]
                self.arraysR[oldName] = self.arraysR[newName]
                self.arraysR[newName] = temp
        
        cls.finaliseFunc(name, docstring, swapper)

        
class VertexArrays(object):
    """Handles Vertex arrays, so that they can be shared amongst
    shaders as necessary. This class should not be initialised directly;
    instead, use VertexArraySpec to create a subclass which has all the
    appropriate setter methods already created."""
    __metaclass__ = VertexArraysMetaclass
    
    def __init__(self, noSlots, arrays):
        """Initialise the vertex array container
        Arguments:
         noSlots: The total number of slots (i.e. length of the arrays)
         arrays : A Dictionary mapping array names (as in the shader program)
                  to a list containing the array itself as first element,
                  and as second element a list of the arguments to 
                  glVertexAttribPointer, without the first (location) or 
                  last (the actual array) argument
                  e.g. [someCTypesArray, [4, GL_FLOAT, GL_FALSE, 0]]"""
        
        self.positions = Slices(0, noSlots)
        self.arrays = arrays
        self.arraysR = dict([(key, self.arrays[key][0]) 
                              for key in self.arrays])
        self.shaderBindArgs = weakref.WeakKeyDictionary()
        self.dirty = set()
        self.dirtyRange = dict([(key, (set(), set())) for key in self.arrays])
        self.noSlots = noSlots
        self.indicesType = GL_UNSIGNED_INT
        self.indicesCType = ctypes.c_uint32
        self.indicesArrayType = ctypes.c_uint32 * noSlots
        self.sizeOfIndices = 4
        
        buffers = [int(x) for x in glGenBuffers(len(arrays))]
        self.arrayBuffers = dict(zip(arrays.keys(), buffers))
        for key in self.arrayBuffers:
            bufferID = self.arrayBuffers[key]
            data = self.arraysR[key]
            GLCommon.bindBuffer(GL_ARRAY_BUFFER, bufferID)
            bufferType = (GL_DYNAMIC_DRAW if self.arrays[key][2] 
                          else GL_STATIC_DRAW)
            glBufferData(GL_ARRAY_BUFFER, len(data), data, bufferType)
                          
    def bind(self, force=False):
        """Bind the arrays as necessary, using the currently bound shader
        to determine locations"""
        shader = GLCommon.boundShader
        if shader not in self.shaderBindArgs:
            bindArgs = {}
            for key in self.arrays:
                if key in shader.arrayLocs:
                    bindArrayArgs = ((shader.arrayLocs[key],) + 
                        self.arrays[key][1] + (ctypes.c_void_p(0),))
                    bindArgs[key] = bindArrayArgs
            self.shaderBindArgs[shader] = bindArgs
        bindArgs = self.shaderBindArgs[shader]
        if GLCommon.boundVertexArrays is not self or force:
            GLCommon.boundVertexArrays = self
            bind = bindArgs
        else:
            bind = self.dirty

        for array in bind:
            bufferID = self.arrayBuffers[array]
            data = self.arraysR[array]
            dynamic = self.arrays[array][2]
            GLCommon.bindBuffer(GL_ARRAY_BUFFER, bufferID)
            if array in self.dirty:
                if dynamic:
                    dirtyElems = self.dirtyRange[array]
                    mn, mx = min(dirtyElems[0]), max(dirtyElems[1])
                    mult = int(ctypes.sizeof(data) / len(data))
                    sz = (mx - mn + 1) * mult
                    mn *= mult
                    glBufferSubData(GL_ARRAY_BUFFER, mn, sz, 
                                    ctypes.byref(data, mn))
                    dirtyElems[0].clear()
                    dirtyElems[1].clear()
                else:
                    glBufferData(GL_ARRAY_BUFFER, len(data), data, GL_STATIC_DRAW)
            GLCommon.bindArray(bindArgs[array])
        self.dirty.clear()
        
    def canAllocDataSlots(self, no):
        """Returns True if the VertexArrays have no or more slots remaining"""
        return self.positions.canAllocate(no) 
        
    def getDataSlots(self, no):
        """Get slots for storing vertex information
        Arguments:
         no: The number of slots to get"""
        return self.positions.allocate(no)
        
    def releaseDataSlots(self, slots):
        """Release slots to be reused
        Arguments:
         slots: The slots to be released"""
        self.positions.release(slots)

class Uniform(object):
    """Represents a Uniform"""
    def __init__(self, name, data, func, args):
        """Initialise the Uniform"""
        self.name = name
        self.data = data
        self.func = func
        self.args = args
        self.shaderBindArgs = weakref.WeakKeyDictionary()
        
    def dirty(self):
        """Mark the uniform as dirty"""
        for shader in self.shaderBindArgs:
            self.shaderBindArgs[shader][0] = True
        
    def genBindArgs(self, shader):
        """Generate arguments for binding the uniform on a shader"""
        location = shader.uniformLocs[self.name]
        self.shaderBindArgs[shader] = [True, [location] + self.args + 
                                              [self.data]]
        
    def bind(self, shader, force):
        """Bind the uniform"""
        shaderBindArgs = self.shaderBindArgs[shader]
        if shaderBindArgs[0] or force:
            GLCommon.bindUniform(self.func, shaderBindArgs[1], 
                                force=shaderBindArgs[0])
            shaderBindArgs[0] = False
        
class UniformStore(object):
    """A UniformStore handles the storing and binding of Uniforms for a 
    shader"""
    def __init__(self, uniforms=None):
        """Initalise the uniform store.
        Args: 
          uniforms: A set of Uniform objects
        """
        self.uniforms = uniforms if uniforms is not None else set()
        self.shaderBindArgs = weakref.WeakKeyDictionary()
             
    def bind(self):
        """Bind the uniforms in this store"""
        shader = GLCommon.boundShader
        if shader not in self.shaderBindArgs:
            for uniform in self.uniforms:
                uniform.genBindArgs(shader)
            self.shaderBindArgs[shader] = True 
            
        boundUniformStore = GLCommon.boundUniformStore
        if (shader not in boundUniformStore or 
           boundUniformStore[shader] is not self):
            boundUniformStore[shader] = self
            force = True
        else:
            force = False
        for uniform in self.uniforms:
            uniform.bind(shader, force)
                    
    def update(self, uniforms):
        """Update uniforms set"""
        self.uniforms.update(uniforms)
