import pygame
import sys
from pygame.locals import *


class InvalidType(Exception):
    pass


class Game:

    renderList = []

    def __init__(self, dimensions=(800, 600)):
        pygame.init()
        self.dimensions = dimensions
        self.screen = pygame.display.set_mode(dimensions, HWSURFACE | DOUBLEBUF)

        self.clock = pygame.time.Clock()

    def addRenderable(self, obj):
        if getattr(obj, 'render', None) == None:
            raise InvalidType

        self.renderList.append(obj)

    def mainLoop(self):
        while 1:
            for event in pygame.event.get():
                #print event
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.KEYUP and event.key == K_ESCAPE:
                    sys.exit()
                if event.type == pygame.KEYUP and event.key == K_a:
                    self.location.updateView((0,0), min(self.location.scale *10, 200))
                if event.type == pygame.KEYUP and event.key == K_z:
                    self.location.updateView((0,0), max(self.location.scale /10, 20))

            for obj in self.renderList:
                obj.render(self.screen)

            pygame.display.flip()

            self.clock.tick(60)
