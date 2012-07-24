import pygame
import sys
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *


class Game:

    def __init__(self, dimensions=(800,600)):
        pygame.init()
        self.dimensions=dimensions
        self.screen = pygame.display.set_mode(dimensions, OPENGL|HWSURFACE|DOUBLEBUF)

        self.clock = pygame.time.Clock()
        print self.clock

        glViewport(0,0,dimensions[0], dimensions[1])
        glClearColor(1.,0.,0.,1.)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL) 

        glMatrixMode(GL_PROJECTION)
        gluOrtho2D(0, 100, 0, 100)

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT)

        glBegin(GL_TRIANGLES)
        glColor3f(1., 1., 0.)
        glVertex2f(10., 10.)
        glVertex2f(40., 10.)
        glVertex2f(40., 40.)
        glEnd()


    def mainLoop(self):
        while 1:
            for event in pygame.event.get():
                print event
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.KEYUP and event.key == K_ESCAPE:
                    sys.exit()
                 

            self.render()
            pygame.display.flip()

            self.clock.tick(60)
