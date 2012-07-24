import pygame
import sys
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

class InvalidType:
    pass

class Game:

    renderList = []

    def __init__(self, dimensions=(800,600)):
        pygame.init()
        self.dimensions=dimensions
        self.screen = pygame.display.set_mode(dimensions, HWSURFACE|DOUBLEBUF)

        self.clock = pygame.time.Clock()

    def addRenderable(self, obj):
        try:
            obj.render
        except AttributeError:
            raise InvalidType

        self.renderList.append(obj)

    def mainLoop(self):
        while 1:
            for event in pygame.event.get():
                print event
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.KEYUP and event.key == K_ESCAPE:
                    sys.exit()
             
            for obj in self.renderList:
                obj.render(self.screen)

            pygame.display.flip()

            self.clock.tick(60)
