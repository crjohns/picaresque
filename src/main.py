
from game import Game
from scene import LocationView, LocationTerrainHandler
import cloak

game = Game()


manager = cloak.Manager()

manager.addHandler("/location/terrain", LocationTerrainHandler())

locationView = LocationView(0, manager, (800, 600), (0,0), 20)

game.addRenderable(locationView)

game.location = locationView

game.mainLoop()
