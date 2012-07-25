
from game import Game
from scene import Background, Grid


game = Game()

game.addRenderable(Background(800, 600))
game.addRenderable(Grid(800, 600))

game.mainLoop()
