
import pygame

from pygame.locals import *
from pygame.color import THECOLORS
from pygame.surface import Surface
from pygame.color import Color
import cloak

class LocationTerrainHandler(cloak.Handler):

    def handle(self, requested, attrs):

        locid = attrs['id']
        x,y = (attrs['x'], attrs['y'])
        size = (attrs['size'])

        locw , loch = (100,100)

        surface = Surface((size, size))
        if x < 0 or x >= locw or y < 0 or y >= loch:
            surface.fill(THECOLORS['black'])
        else:
            surface.fill(THECOLORS['white'])

        return surface



class LocationView:

    surface = None

    def __init__(self, locationId, manager, dimensions, topLeft, scale = 20):
        """
            Create a view of the terrain for a location

            locationId is the identifier for the location
            being displayed.

            manager is a cloak manager object

            dimensions is the size of this view in pixels.

            topLeft is the top left corner of the view in
            cell coordinates.

            scale is the size of each cell in pixels
            scale must divide dimensions perfectly
        """

        self.locationId = locationId
        self.manager = manager

        if len(dimensions) != 2 or len(topLeft) != 2:
            raise Exception("Arguments must be 2-tuples")

        self.width, self.height = dimensions

        self.updateView(topLeft, scale)


    def updateView(self, topLeft, scale):

        if self.width % scale != 0 or self.height % scale != 0:
            raise Exception("Dimensions %s not divisible by scale %d" % ((self.width, self.height), scale))

        self.scale = scale
        self.topLeft = topLeft
        cellwidth = self.width / scale
        cellheight = self.height / scale
        self.bottomRight = (topLeft[0]+cellwidth, topLeft[1]+cellheight)

        self.updateSurface()


    def updateSurface(self):
        self.surface = Surface((self.width, self.height), flags=HWSURFACE | SRCALPHA)
        self.surface.fill(Color(255, 0, 0, 255))

        for x in range(self.topLeft[0], self.bottomRight[0]):
            for y in range(self.topLeft[1], self.bottomRight[1]):
                cellbg = self.manager.get("/location/terrain", {'id': 0,
                                                                'x': x,
                                                                'y': y,
                                                                'size': self.scale})
                self.surface.blit(cellbg, (x*self.scale, y*self.scale))

        # Render the grid on this map
        grid = Grid(self.width, self.height, self.scale)
        grid.render(self.surface)



    def render(self, screen):
        screen.blit(self.surface, (0, 0))


class Grid:

    surface = None

    def __init__(self, width, height, spacing=20):
        self.width = width
        self.height = height
        self.spacing = spacing
        self.initializeSurface()

    def initializeSurface(self):
        self.surface = Surface((self.width, self.height), flags=HWSURFACE | SRCALPHA)
        self.surface.fill(Color(0, 0, 0, 0))

        for i in range(0, self.width, self.spacing):
            pygame.draw.line(self.surface, Color(0, 0, 0, 255), (i, 0), (i, self.height))

        for i in range(0, self.height, self.spacing):
            pygame.draw.line(self.surface, Color(0, 0, 0, 255), (0, i), (self.width, i))

        pygame.draw.line(self.surface,
                Color(0, 0, 0, 255),
                (self.width - 1, 0),
                (self.width - 1, self.height))
        pygame.draw.line(self.surface, Color(0, 0, 0, 255),
                (0, self.height - 1), (self.width, self.height - 1))

    def render(self, screen):
        screen.blit(self.surface, (0, 0))
        pass
