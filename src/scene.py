
import pygame
from pygame.locals import *
from pygame.surface import Surface
from pygame.color import Color

class Background:

    surface = None

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.initializeSurface()

    def initializeSurface(self):
        self.surface = Surface((self.width, self.height), flags=HWSURFACE|SRCALPHA)
        self.surface.fill(Color(255, 255, 255, 255))

    def render(self, screen):
        screen.blit(self.surface, (0,0))





class Grid:

    surface = None
    
    def __init__(self, width, height, spacing=20):
        self.width = width
        self.height = height
        self.spacing = spacing
        self.initializeSurface()

    def initializeSurface(self):
        self.surface = Surface((self.width, self.height), flags = HWSURFACE|SRCALPHA)
        self.surface.fill(Color(0,0,0,0))

        for i in range(0, self.width, self.spacing):
            pygame.draw.line(self.surface, Color(0,0,0,255), (i, 0), (i, self.height))

        
        for i in range(0, self.height, self.spacing):
            pygame.draw.line(self.surface, Color(0,0,0,255), (0, i), (self.width, i))
        
        pygame.draw.line(self.surface, Color(0,0,0,255), (self.width-1, 0), (self.width-1, self.height))
        pygame.draw.line(self.surface, Color(0,0,0,255), (0, self.height-1), (self.width, self.height-1))

    def render(self, screen):
        screen.blit(self.surface, (0,0))
        pass
