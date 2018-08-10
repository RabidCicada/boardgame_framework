
class Cell():
    """
    Be the representation of regions of the gamespace.

    A Cell is a representation of physical space in the game.  This can be squares
    in chess and checkers, regions like playfield etc for magic the gathering,
    hexes in terra mystica, settlers of catan, etc.
    """

    def __init__(self, name=None, coord, ):

        self.name = name
        self.coord = coord
        self.connections = list()
        #self.children
