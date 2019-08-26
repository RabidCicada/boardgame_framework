#!/usr/bin/env python
"""
Module that provides a simple example of loading and using boardgame_framework.

To run it, change directory into src/ and  use something like
'PYTHONPATH=./ python ../examples/driver.py' so that it can find the codebase.
"""
import logging
from logging_tree import printout

import argparse

import math
import pathlib
import sys

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
import pygame
import pygame.freetype
from boardgame_framework.cell import Cell, CellMgr
from boardgame_framework.coord import (
    CoordinateSystem,
    CoordinateSystemMgr,
    CubedCoord,
    HexCoord,
    HexCoordinateSystem,
    RectCoord,
    RectCoordinateSystem
)
from boardgame_framework.serializers.yaml import yaml

# from asphalt.serialization.serializers.yaml import YAMLSerializer
# yamlserializer = YAMLSerializer()

# from asphalt.serialization.serializers.json import JSONSerializer
# jsonserializer = JSONSerializer()

# from asphalt.serialization.serializers.msgpack import MsgpackSerializer
# serializer = MsgpackSerializer()
# from preserialize.json import JsonPreserializer
# preserializer = JsonPreserializer()

logger = logging.getLogger(__name__)

SQRT3 = math.sqrt( 3 )
NUM_COLS = 20
NUM_ROWS = 20


BLACK = (0,0,0)
WHITE = (255,255,255)
RED = (255,0,0)


# @dataclass(eq=True, frozen=True)
# class Orientation:
# 	"""
# 	Represent the forward and back matrix and starting angle for hex rendering
# 	"""
# 	f0: float
# 	f1: float
# 	f2: float
# 	f3: float
# 	b0: float
# 	b1: float
# 	b2: float
# 	b3: float
# 	start_angle: int

class Layout:
    """
    Represent the Layout of the objects

    Any coordinates passed through this layout have the following operations applied
    - The coordinate is adjusted so that the specified origin would be 0,0
    - The cooridnate is then shifted by the flat amount.
    - The coordinate is then scaled for x and y by the specified units
    """
    #orientation: Orientation
    # scale: RectCoord #scales the incoming coordinates by the amount specified
    # origin: RectCoord #represents which point in the coordinate system should be considered the origin
    # shift: RectCoord #shifts the entire system by the specified number of units

    def __init__(self, scale: RectCoord, origin: RectCoord):
        self.origin = origin #represents which point in the coordinate system should be considered the origin
        self.scale = scale #scales the incoming coordinates by the amount specified

    # def process_coord(self, coord: RectCoord, coordsys: CoordinateSystem):
    #     newcoord = coordsys.coord(x=(coord.x - self.origin.x)*self.scale.x + self.shift.x,y=(coord.y - self.origin.y)*self.scale.y+ self.shift.y)
    #     #logger.debug("Coord: %s --> AdjustedCoord: %s", coord, newcoord)
    #     return newcoord

# def hex_to_pixel(layout: Layout, h):
#     M = layout.orientation;
#     x = (M.f0 * h.q + M.f1 * h.r) * layout.scale.x;
#     y = (M.f2 * h.q + M.f3 * h.r) * layout.scale.y;
#     return RectCoord(x + layout.origin.x, y + layout.origin.y);

#
# def text_objects(text, font):
#     textSurface , rect= font.render(text, (255,255,255))
#     logger.debug("textSurface type: %s",type(textSurface))
#     return textSurface, rect

def display_in_bounds(lines,locx,locy,bndx,bndy, display):
    font = pygame.freetype.SysFont('comicsansms',10)
    surfsandrects = list()
    #currlocx = locx
    currlocy = locy
    for line in lines:
        #logger.debug("Drawing %s at (%s,%s)", line, locx, currlocy)
        TextSurf, TextRect = font.render(line, pygame.Color('black'))
        TextRect.left=locx
        TextRect.top=currlocy
        surfsandrects.append((TextSurf, TextRect))
        currlocy = currlocy + TextRect.height
        if currlocy > bndy:
            logger.error("currlocy %s bndy %s",currlocy, bndy)
            raise ValueError("Lines exceed vertical size")

    for TextSurf, TextRect in surfsandrects:
        #logger.debug("blitting at (%s,%s)",TextRect.left, TextRect.top)
        display.blit(TextSurf, TextRect)

def message_display(text, locx, locy, display):
    font = pygame.freetype.SysFont('comicsansms',10)
    TextSurf, TextRect = font.render(text, pygame.Color('black'))
    TextRect.center = locx,locy
    display.blit(TextSurf, TextRect)


# orient_pointy = Orientation(SQRT3, SQRT3 / 2.0, 0.0, 3.0 / 2.0,
# 				SQRT3 / 3.0, -1.0 / 3.0, 0.0, 2.0 / 3.0,
# 				0.5)
#
# orient_flat = Orientation(3.0 / 2.0, 0.0, SQRT3 / 2.0, SQRT3,
#                 2.0 / 3.0, 0.0, -1.0 / 3.0, SQRT3 / 3.0,
#                 0.0)

class Render( pygame.Surface ):

    __metaclass__ = ABCMeta

    def __init__( self, cellmgr, radius=24, primary_coord_sys= "Global", *args, **keywords ):
        self.cellmgr = cellmgr
        self.primary_coord_sys = primary_coord_sys
        self.radius = radius
        self.cols = NUM_COLS
        self.rows = NUM_ROWS
        self.hex_width = SQRT3 * self.radius
        self.hex_height = 2 * self.radius
        self.xycoordsys = CoordinateSystemMgr.create_coord_system("oddr","renderxy")
        self.layout = None
        self._stats_by_coord_tuple = dict()

        P_TL_COORD = ( 0, .5 * self.radius ) # Pointy -- Top Left most point
        P_TM_COORD = ( SQRT3 * self.radius / 2, 0 ) # Pointy -- Top most point (Middle)
        P_TR_COORD = ( SQRT3 * self.radius, .5 * self.radius ) # Pointy -- Top Right most point
        P_BR_COORD = ( SQRT3 * self.radius, 1.5 * self.radius ) # Pointy -- Bottom Right most point
        P_BM_COORD = ( SQRT3 * self.radius / 2, 2 * self.radius ) # Pointy -- Bottom most point (Middle)
        P_BL_COORD = ( 0, 1.5 * self.radius ) # Pointy -- Bottom Left most point

        # Colors for the map
        self.GRID_COLOR = pygame.Color( 50, 50, 50 )

        super( Render, self ).__init__( ( self.width, self.height ), *args, **keywords )

        self.cell = [P_TL_COORD,
                     P_TM_COORD,
                     P_TR_COORD,
                     P_BR_COORD,
                     P_BM_COORD,
                     P_BL_COORD
                     ]



    @property
    def width( self ):
        return	self.cols * self.hex_width + self.hex_width/ 2.0
    @property
    def height( self ):
        return ( self.rows + .5 ) * self.hex_height

    def get_surface( self, row, col ):
        """
        Returns a subsurface corresponding to the surface, hopefully with trim_cell wrapped around the blit method.
        """
        width = SQRT3 * self.radius
        height = 2 * self.radius

        top = ( row - math.ceil( col / 2.0 ) ) * height + ( height / 2 if col % 2 == 1 else 0 )
        left = 1.5 * self.radius * col

        return self.subsurface( pygame.Rect( left, top, width, height ) )

    # Draw methods
    @abstractmethod
    def draw( self ):
        """
        An abstract base method for various render objects to call to paint
        themselves.  If called via super, it fills the screen with the colorkey,
        if the colorkey is not set, it sets the colorkey to magenta (#FF00FF)
        and fills this surface.
        """
        color = self.get_colorkey()
        if not color:
            magenta = pygame.Color( 255, 0, 255 )
            self.set_colorkey( magenta )
            color = magenta
        self.fill( color )

    # Identify cell
    def get_cell( self,  x, y  ):
        """
        Identify the cell clicked in terms of row and column
        """
        # Identify the square grid the click is in.
        row = math.floor( y / ( SQRT3 * self.radius ) )
        col = math.floor( x / ( 1.5 * self.radius ) )

        # Determine if cell outside cell centered in this grid.
        x = x - col * 1.5 * self.radius
        y = y - row * SQRT3 * self.radius

        # Transform row to match our hex coordinates, approximately
        row = row + math.floor( ( col + 1 ) / 2.0 )

        # Correct row and col for boundaries of a hex grid
        if col % 2 == 0:
            if 	y < SQRT3 * self.radius / 2 and x < .5 * self.radius and \
                y < SQRT3 * self.radius / 2 - x:
                row, col = row - 1, col - 1
            elif y > SQRT3 * self.radius / 2 and x < .5 * self.radius and \
                y > SQRT3 * self.radius / 2 + x:
                row, col = row, col - 1
        else:
            if 	x < .5 * self.radius and abs( y - SQRT3 * self.radius / 2 ) < SQRT3 * self.radius / 2 - x:
                row, col = row - 1 , col - 1
            elif y < SQRT3 * self.radius / 2:
                row, col = row - 1, col


        return ( row, col ) if self.map.valid_cell( ( row, col ) ) else None

    def fit_window( self, window ):
        top = max( window.get_height() - self.height, 0 )
        left = max( window.get_width() - map.width, 0 )
        return ( top, left )

    def track_coord_stats(self, cell, coord):
        """Record information in the renderspace coordinate system when passed the coordinate
         of the boardgame coordinate system

         This stat tracker is used primarily for tracking xy coordinate equivalents
         for any incoming coordinate system so that it is easy to feed information
         to a renderer, but may be used to track any information as coordinates
         are assigned.
         """
        xy_coord = self.xycoordsys.from_other_system(coord)
        if coord.system.system_tuple not in self._stats_by_coord_tuple:
            self._stats_by_coord_tuple[coord.system.system_tuple] = dict()

        if ('min_x' not in self._stats_by_coord_tuple[coord.system.system_tuple]
        or xy_coord.x < self._stats_by_coord_tuple[coord.system.system_tuple]['min_x']
           ):
           self._stats_by_coord_tuple[coord.system.system_tuple]['min_x'] = xy_coord.x

        if ('max_x' not in self._stats_by_coord_tuple[coord.system.system_tuple]
        or xy_coord.x > self._stats_by_coord_tuple[coord.system.system_tuple]['max_x']
           ):
           self._stats_by_coord_tuple[coord.system.system_tuple]['max_x'] = xy_coord.x

        if ('min_y' not in self._stats_by_coord_tuple[coord.system.system_tuple]
        or xy_coord.y < self._stats_by_coord_tuple[coord.system.system_tuple]['min_y']
           ):
           self._stats_by_coord_tuple[coord.system.system_tuple]['min_y'] = xy_coord.y

        if ('max_y' not in self._stats_by_coord_tuple[coord.system.system_tuple]
        or xy_coord.y > self._stats_by_coord_tuple[coord.system.system_tuple]['max_y']
           ):
           self._stats_by_coord_tuple[coord.system.system_tuple]['max_y'] = xy_coord.y

    def get_known_coordsys_stats(self):
        """Return the keys of all the known coordinate systems for stat tracking"""
        return self._stats_by_coord_tuple.keys()


    def get_coordsys_stats(self,sysid):
        """Return stats tracked for a coordinate system"""
        if sysid not in self._stats_by_coord_tuple:
            raise ValueError("No tracked stats for that system")

        # Lazy calculate size of X for the coordinate system
        self._stats_by_coord_tuple[sysid]['xsize'] = (
        self._stats_by_coord_tuple[sysid]['max_x']
        - self._stats_by_coord_tuple[sysid]['min_x']
        + 1
        )

        # Lazy calculate size of Y for the coordinate system
        self._stats_by_coord_tuple[sysid]['ysize'] = (
        self._stats_by_coord_tuple[sysid]['max_y']
        - self._stats_by_coord_tuple[sysid]['min_y']
        + 1
        )

        return self._stats_by_coord_tuple[sysid]

    def resolve_layout(self):
        logger.debug("**Resolving Layout**")
        stats = self.get_coordsys_stats(self.primary_coord_sys)

        #Generate a layout that shifts all coordinates so they start at 0 and flip
        #the y axis so that +y points up (like real life)  instead of down (like screens)
        self.layout = Layout(scale=self.xycoordsys.coord(x=1,y=1),
         origin=self.xycoordsys.coord(0,0),
         #shift=self.xycoordsys.coord(200,35)
        )

class RenderGrid( Render ):

    def hex_to_tl_anchor(self, coord, indent):
        """
        Returns the top left corner of a bounding square drawn around the hex.

        This allows mathy calculation of the actual corner points
        """

        offset = SQRT3 * self.radius * self.layout.scale.x / 2 if indent else 0

        top = (1.5 * self.radius * coord.y) * self.layout.scale.y + self.layout.origin.y
        left = (offset + SQRT3 * self.radius * coord.x) * self.layout.scale.x + self.layout.origin.x

        #logging.debug(f"({offset} + {SQRT3} * {self.radius} * {coord.x}) * {self.layout.scale.x} + {self.layout.origin.x})")

        #logging.debug("htla: scoord: (%s,%s), tl: (%s,%s)",coord.x,coord.y,left,top)
        return (top,left)
        #
        #newcoord = coordsys.coord(x=(coord.x - self.origin.x)*self.scale.x + self.shift.x,y=(coord.y - self.origin.y)*self.scale.y+ self.shift.y)

    def draw( self):
        """
        Draws a hex grid, based on the map object, onto this Surface
        """
        super( RenderGrid, self ).draw()
        # A point list describing a single cell, based on the radius of each hex
        if not self.layout:
            raise RuntimeError("Layout not initialized.  Must be initialized with"
             "resolve_layout() before drawing")

        cells = cellmgr.by_coord_id(self.primary_coord_sys)
        stats = self.get_coordsys_stats(self.primary_coord_sys)

        for cell in cells:
            hexorigin = self.xycoordsys.coord(stats['min_x'],stats['min_y'])

            #coordinates with reference to 0,0 of the anchoring map tile
            xycoord = self.xycoordsys.from_other_system(cell.coord)

            #coordinates with respect to the players point of view 0,0 in bottom left of entire map
            playerxy = xycoord - hexorigin # pure poitive xy axes

            #coordinates in terms of screen (y flipped over x axis and slid down so 0,0 is top left corner)
            screenxy = self.xycoordsys.coord(playerxy.x,playerxy.y*-1+stats['max_y']-stats['min_y'])

            # # Create coordinate that maps the coordinate system into completely positive space
            # # So that it can be rendered to the screen easily
            # screenxycoord = self.layout.process_coord(xycoord, self.xycoordsys)
            # # for col in range( 0, stats['xsize'] ):
            # # 	for row in range( 0, stats['ysize'] ):
            #
            # # Alternate the offset of the cells based on column
            # #offset = SQRT3 * self.radius / 2 if row % 2 else 0
            # offset = SQRT3 * self.radius / 2 if screenxycoord.y % 2 else 0
            #
            # # Calculate the offset of the cell
            # # top = 1.5 * self.radius * row
            # # left = offset + SQRT3 * self.radius * col
            #
            # top = 1.5 * self.radius * screenxycoord.y
            # left = offset + SQRT3 * self.radius * screenxycoord.x

            #top,left = self.hex_to_tl_anchor(screenxy, playerxy.y % 2)

            # TODO: Encapsulate the indentation calculation in the coordinate system

            #top,left = self.hex_to_tl_anchor(screenxy, cell.auto_coord.y % 2 )

            top,left = self.hex_to_tl_anchor(screenxy, xycoord.y % 2 )

            # Create a point list to draw the hex.
            # It is anchored at the top left corner and scaled
            points = [( x*self.layout.scale.x + left, y*self.layout.scale.y + top ) for ( x, y ) in self.cell]

            # Draw the polygon onto the surface
            pygame.draw.polygon( self, self.GRID_COLOR, points, 1 )

            #Create location strings
            lines = list()
            # for k,v in cell.coords.items():
            #     lines.append(f"{v}")
            lines.append(f" p {playerxy}")
            lines.append(f" o {xycoord}")
            #lines.append(f" s {screenxy}")
            lines.append(f" a {cell.auto_coord}")
            #lines.append(f" ind l-{cell.auto_coord.y % 2} g-{playerxy.y % 2}")
            lines.append(f" hex {cell.coord}")
            #lines.append(f" {cell.name}")
            #logging.debug("%s\n\tpxy %s \n\torigin %s\n\tscreen %s\n\tcell.coord %s",cell._str_with_coords(), playerxy, xycoord, screenxy, cell.coord)
            display_in_bounds(lines,left,top + .5 * self.radius*self.layout.scale.y, 300, top + 2 * self.radius *self.layout.scale.y, self)





def trim_cell( surface ):
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A Sample Game Client using BoardGameFramework')
    parser.add_argument("-l", "--loglevel", type=str,
                        help="set log level")
    parser.add_argument("-r", "--radius", type=int, default=32,
                        help="radius in pixels of the outer most corners of the hexes")
    parser.add_argument("-t", "--target", type=str,
                        help="Name of the cell to render")
    parser.add_argument("-f", "--file", type=str,
                        help="Name of the cell file to load")

    args = parser.parse_args()

    if args.loglevel:
        caps_log_level = args.loglevel.upper()

        numeric_level = getattr(logging, caps_log_level, None) #Get numeric value form logging module
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)
        #logger.setLevel(numeric_level)
        logging.basicConfig(level=numeric_level)
        print(f"Logging Level:{caps_log_level} numeric:{numeric_level}")

    if args.target:
        sysid = (args.target, "Local")
        #target = args.target
        infile = args.file
    else:
        sysid = "Global"
        #target = args.target
        infile = args.file


    cellmgr = CellMgr()
    grid = RenderGrid( cellmgr, radius=args.radius, primary_coord_sys=sysid )
    #grid = RenderGrid( cellmgr, radius=32, primary_coord_sys=("Global") )

    cellmgr.register_coord_reg_callback(grid.track_coord_stats)
    cellmgr.load_cells(infile,basedir=pathlib.Path('..','tests','data_files','gloomhaven'))
    grid.resolve_layout()
    cells = cellmgr.by_coord_id(grid.primary_coord_sys)


    #print( m.ascii() )
    #myfont = pygame.font.SysFont('Comic Sans MS', 30)

    logging.debug("Known systems: %s", list(CoordinateSystemMgr.get_known_systems()))
    logging.debug("Known sys_stats: %s", list(grid.get_known_coordsys_stats()))
    stats = grid.get_coordsys_stats(grid.primary_coord_sys)
    logging.debug("%s Coordinate System is %s xunits and %s yunits, minx %s maxx %s, miny %s maxy %s",grid.primary_coord_sys, stats['xsize'], stats['ysize'], stats['min_x'], stats['max_x'], stats['min_y'], stats['max_y'])

    for cell in cells:
        logging.debug("%s",cell._str_with_coords())
    #logger.error("%s\n\n%s ", orient_pointy,orient_flat)

    # preserializer.register(Cell)
    # preserializer.register(CubedCoord)
    # preserializer.register(CellMgr)
    # preserializer.register(HexCoord)
    # preserializer.register(RectCoord)
    # preserializer.register(CoordinateSystem)
    # preserializer.register(CoordinateSystemMgr)
    # preserializer.register(HexCoordinateSystem)
    # preserializer.register(RectCoordinateSystem)
    # data = preserializer.preserialize(cells)

    # serialized = jsonserializer.serialize(data)
    # with open("serialized.json","wb") as ofile:
    # 	ofile.write(serialized)
    #yamloutput = yaml.dump(cells)
    #print(yamloutput)


    # serialized = yamlserializer.serialize(cells)
    # with open("serialized.yml","w") as ofile:
    # 	ofile.write(yamloutput)

    #results = yaml.load(yamloutput)
    #print(results)

    try:
        pygame.init()
        fpsClock = pygame.time.Clock()

        window = pygame.display.set_mode( ( 1280, 960 ), 1 )
        from pygame.locals import QUIT, MOUSEBUTTONDOWN

        #Leave it running until exit
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
            # if event.type == MOUSEBUTTONDOWN:
            # 	print( units.get_cell( event.pos ) )

            window.fill( pygame.Color( 'white' ) )
            grid.draw()
            # units.draw()
            # fog.draw()
            window.blit( grid, ( 0, 0 ) )
            # window.blit( units, ( 0, 0 ) )
            # window.blit( fog, ( 0, 0 ) )
            pygame.display.update()
            fpsClock.tick( 10 )
    finally:
        logging.debug("%s Coordinate System is %s xunits and %s yunits, minx %s maxx %s, miny %s maxy %s", grid.primary_coord_sys, stats['xsize'], stats['ysize'], stats['min_x'], stats['max_x'], stats['min_y'], stats['max_y'])
        pygame.quit()
