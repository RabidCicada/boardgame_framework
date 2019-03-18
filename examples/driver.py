#!/usr/bin/env python
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
import pygame
import logging
import math
import io
import pathlib
from boardgame_framework.cell import CellMgr, Cell
from boardgame_framework.coord import CoordinateSystem, CoordinateSystemMgr, RectCoord, CubedCoord, HexCoord, HexCoordinateSystem, RectCoordinateSystem
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


@dataclass(eq=True, frozen=True)
class Point():
	"""
	Represent 3 element coordinate primitive including providing support functions
	"""
	x: float
	y: float

	def __add__(self, thing):
		if not isinstance(thing, type(self)):
			raise ValueError(f"Cannot add {thing} to {self} because "
							 f"they are not the same type")
		return CubedCoord(x=self.x+thing.x, y=self.y+thing.y, z=self.z+thing.z)

	def __sub__(self, thing):
		if not isinstance(thing, type(self)):
			raise ValueError(f"Cannot add {thing} to {self} because "
							 f"they are not the same type")
		return CubedCoord(x=self.x-thing.x, y=self.y-thing.y, z=self.z-thing.z)

	def __mul__(self, multiplier):
		if not isinstance(multiplier, int):
			raise ValueError(f"The multiplier must be an integer")
		return CubedCoord(x=self.x*multiplier, y=self.y*multiplier,
						  z=self.z*multiplier)

	def __getitem__(self, idx):

		if idx == 0:
			return self.x
		if idx == 1:
			return self.y

		raise ValueError(f"Index must be 0, 1")

@dataclass(eq=True, frozen=True)
class Orientation:
	"""
	Represent the forward and back matrix and starting angle for hex rendering
	"""
	f0: float
	f1: float
	f2: float
	f3: float
	b0: float
	b1: float
	b2: float
	b3: float
	start_angle: int




@dataclass(eq=True, frozen=True)
class Layout:
	"""
	Represent the Layout of the objects
	"""
	orientation: Orientation
	scale: Point
	origin: Point

def hex_to_pixel(layout: Layout, h):
	M = layout.orientation;
	x = (M.f0 * h.q + M.f1 * h.r) * layout.scale.x;
	y = (M.f2 * h.q + M.f3 * h.r) * layout.scale.y;
	return Point(x + layout.origin.x, y + layout.origin.y);


def text_objects(text, font):
	textSurface = font.render(text, True, black)
	return textSurface, textSurface.get_rect()

def message_display(text):
	largeText = pygame.freetype.SysFont('comicsansms',10)
	TextSurf, TextRect = text_objects(text, largeText)
	TextRect.center = ((display_width/2),(display_height/2))
	gameDisplay.blit(TextSurf, TextRect)


orient_pointy = Orientation(SQRT3, SQRT3 / 2.0, 0.0, 3.0 / 2.0,
				SQRT3 / 3.0, -1.0 / 3.0, 0.0, 2.0 / 3.0,
				0.5)

orient_flat = Orientation(3.0 / 2.0, 0.0, SQRT3 / 2.0, SQRT3,
                2.0 / 3.0, 0.0, -1.0 / 3.0, SQRT3 / 3.0,
                0.0)

class Render( pygame.Surface ):

	__metaclass__ = ABCMeta

	def __init__( self, cellmgr, radius=24, *args, **keywords ):
		self.cellmgr = cellmgr
		self.radius = radius
		self.cols = NUM_COLS
		self.rows = NUM_ROWS
		self.hex_width = SQRT3 * self.radius
		self.hex_height = 2 * self.radius
		self.xycoordsys = CoordinateSystemMgr.create_coord_system("oddr","renderxy")

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

class RenderGrid( Render ):
	def draw( self, cells):
		"""
		Draws a hex grid, based on the map object, onto this Surface
		"""
		super( RenderGrid, self ).draw()
		# A point list describing a single cell, based on the radius of each hex

		cells = cellmgr.by_coord_id("Global")
		stats = cellmgr.get_coordsys_stats("Global")

		for cell in cells:

			xycoord = self.xycoordsys.from_other_system(cell.coord)
			mxycoord = self.xycoordsys.coord(x=xycoord.x-stats['min_x'],y=xycoord.y-stats['min_y'])
		# for col in range( 0, stats['xsize'] ):
		# 	for row in range( 0, stats['ysize'] ):

			# Alternate the offset of the cells based on column
			#offset = SQRT3 * self.radius / 2 if row % 2 else 0
			offset = SQRT3 * self.radius / 2 if mxycoord.y % 2 else 0

			# Calculate the offset of the cell
			# top = 1.5 * self.radius * row
			# left = offset + SQRT3 * self.radius * col

			top = 1.5 * self.radius * mxycoord.y
			left = offset + SQRT3 * self.radius * mxycoord.x

			# Create a point list containing the offset cell
			points = [( x + left, y + top ) for ( x, y ) in self.cell]
			# Draw the polygon onto the surface
			pygame.draw.polygon( self, self.GRID_COLOR, points, 1 )


def trim_cell( surface ):
	pass

if __name__ == '__main__':

	import sys
	cellmgr = CellMgr()

	cellmgr.load_cells("gloomhaven_scenario1.yml",basedir=pathlib.Path('..','tests','data_files','gloomhaven'))
	cells = cellmgr.by_coord_id("Global")


	grid = RenderGrid( cellmgr, radius=32 )
	#print( m.ascii() )
	#myfont = pygame.font.SysFont('Comic Sans MS', 30)

	logger.error("Known systems: %s", list(CoordinateSystemMgr.get_known_systems()))
	logger.error("Known sys_stats: %s", list(cellmgr.get_known_coordsys_stats()))
	stats = cellmgr.get_coordsys_stats("Global")
	logger.error("Global Coordinate System is %s xunits and %s yunits, minx %s maxx %s, miny %s maxy %s", stats['xsize'], stats['ysize'], stats['min_x'], stats['max_x'], stats['min_y'], stats['max_y'])
	logger.error("%s\n\n%s ", orient_pointy,orient_flat)

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
	yamloutput = yaml.dump(cells)
	#print(yamloutput)


	# serialized = yamlserializer.serialize(cells)
	# with open("serialized.yml","w") as ofile:
	# 	ofile.write(yamloutput)

	results = yaml.load(yamloutput)
	print(results)

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
			grid.draw(cellmgr)
			# units.draw()
			# fog.draw()
			window.blit( grid, ( 0, 0 ) )
			# window.blit( units, ( 0, 0 ) )
			# window.blit( fog, ( 0, 0 ) )
			pygame.display.update()
			fpsClock.tick( 10 )
	finally:
		pygame.quit()
