import pygame
from pygame.locals import *
import sys

from game import Game
from scene import *


game = Game()

game.addRenderable(Background(800,600))
game.addRenderable(Grid(800,600))

game.mainLoop()


