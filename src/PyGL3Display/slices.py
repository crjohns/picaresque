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

slices.py

Provides a class for efficiently representing an integer number line (for
allocating slots in the various data structures)
"""

__all__ = ['Slices']

class Slices(object):
    """Class for efficiently representing slices of a number line"""
    def __init__(self, start, end):
        """Initialise the slices object"""
        self.slices = [[start, end]]
        self.allocating = None
        self.foundSlice = None
        
    def canAllocate(self, n):
        """Return true if the object slices object could allocate a 
        slice of size n. Sets up allocate for this slice."""
        for slice in self.slices:
            if slice[1] - slice[0] > n:
                self.allocating = n
                self.foundSlice = slice
                return True
        self.join()
        for slice in self.slices:
            if slice[1] - slice[0] > n:
                self.allocating = n
                self.foundSlice = slice
                return True
        return False
        
    def allocate(self, n):
        """Allocate a slice of size n"""
        if n != self.allocating and not self.canAllocate(n):
            raise Exception('Cannot allocate enough numbers from this slice')
        ret = [y for y in xrange(self.foundSlice[0], self.foundSlice[0]+n)]
        self.foundSlice[0] += n
        self.foundSlice = None
        self.allocating = None
        return ret
        
    def release(self, numbers):
        """Release some numbers back to the number line"""
        mn, mx = min(numbers), max(numbers)
        if len(numbers) - 1 == mx - mn:
            self.slices.append([mn, mx+1])
        else:
            self.slices.extend(([number, number+1] for number in numbers))
            
    def join(self):
        """Join up slices to reduce fragmentation"""
        slices = self.slices
        slices.sort()
        length = len(slices)
        indx = 1
        while indx < length:
            if slices[indx-1][1] == slices[indx][0]:
                slices[indx-1][1] = slices[indx][1]
                slices.pop(indx)
                length -= 1
            else:
                indx += 1

