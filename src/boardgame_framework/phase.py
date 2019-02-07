

class Phase():
    """
    Be the representation of phases of gametime.

    A Phase is a representation of periods of play in the game.  This can be
    turns of individuals in chess/checkers.  It can be phases within turns like
    magic the gathering, or a simultaneous phase/turn as in seven wondersself.

    Phases can be nested and in general the turn mechanics of an entire game should
    break down into nested phases.  For example from Magic The Gatherig, there
    would be a game phase with turn phases that each contain subphases like upkeep,
    untap,draw,1st main phase,attack, 2nd main phase etc.
    """
