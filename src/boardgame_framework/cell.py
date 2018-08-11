import itertools

class Cell():
    """
    Be the representation of regions of the gamespace.

    A Cell is a representation of physical space in the game.  This can be squares
    in chess and checkers, regions like playfield etc for magic the gathering,
    hexes in terra mystica, settlers of catan, etc.
    """

    new_uid = itertools.count().next

    def __init__(self, uid=None, name=None, attributes=None ):

        self.name = name
        self.uid = new_uid() if uid is None else uid
        self.coord = coord
        self.connections = list()
        self.attributes = dict()
        #self.children

    def __str__(self):
        return F"{type(self).__name__}-{self.uid}"

    def __repr__(self):
        return F"{type(self).__name__}-{self.uid}"
