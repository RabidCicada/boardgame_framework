"""
This module provides coordinate system support for the boardgame_framework
"""
import logging
from dataclasses import dataclass

from .utils import checkallequal

logger = logging.getLogger(__name__)


def distance(self, coord1, coord2):
    """Calculate distance of the coord2 from coord1"""
    return (abs(coord1.x - coord2.x) + abs(coord1.y - coord2.y) + abs(coord1.z - coord2.z))//2

class CoordinateSystemMgr():
    """
    Manage the various coordinate systems available to boardgame_framework.

    Supports registering and tracking of different coordinate systems.  Some
    coordinate systems may be similar or use similar underlying geometry but,
    nonetheless have different algorithms for generating coordinates.  This includes
    Hex coordinate systems which come in many flavors (<x,y,z>, <oddr:x,y>,
    <oddq:x,y> etc.)
    """
    system_type_classes = dict()
    coord_systems = dict()

    #The following uses decorator syntax to perform processing
    #on the function but doesn't actually wrap it.
    @classmethod
    def register_coordsystem_type(cls, system_type):
        """Register the coordinate system type so that the coordinate system may be
         instantiated
        """
        def anon_reg_func(coord_system):
            if not issubclass(coord_system, CoordinateSystem):
                raise ValueError((f"Passed class {coord_system.__name__} not of"
                                  f" type CoordinateSystem"))

            cls.system_type_classes[system_type] = coord_system
            return coord_system
        return anon_reg_func

    @classmethod
    def get_known_systems(cls):
        """Return the known coordinate systems"""
        return cls.coord_systems.keys()

    @classmethod
    def get_system_type_class(cls, system_type):
        """Get the coordinate class registered to the system_type
        """
        if system_type not in cls.system_type_classes:
            raise ValueError(f"No coordinate system of type {system_type} registered!")

        return cls.system_type_classes[system_type]

    @classmethod
    def create_coord_system(cls, system_type, system_tuple):
        """Instantiate coordinate class registered to the system_type with an system_tuple
        as the identifier
        """
        if system_type not in cls.system_type_classes:
            raise ValueError(f"No coordinate system of type {system_type} registered!")

        coord_system = cls.system_type_classes[system_type]
        instance = coord_system(system_tuple=system_tuple, system_type=system_type)
        cls.coord_systems[system_tuple] = instance
        return instance

    @classmethod
    def get_coord_system(cls, system_tuple):
        """Get the instantiated coordinate system by it's tuple id
        """
        if system_tuple not in cls.coord_systems:
            raise ValueError(f"No coordinate system with id {system_tuple} created!")
        return cls.coord_systems[system_tuple]

    @classmethod
    def delete_coord_system(cls, system_tuple):
        """Delete the coordinate system by it's tuple id
        """
        if system_tuple not in cls.coord_systems:
            raise ValueError(f"No coordinate system with id {system_tuple} created!")

        del cls.coord_systems[system_tuple]

class CoordinateSystem():
    """
    Represent a coordinate system and handle/generate coordinate system algorithms
    and transforms
    """
    to_other_conversions = {}
    from_other_conversions = {}

    def __str__(self):
        return f"{self.system_type}-{self.system_tuple}"

    def __repr__(self):
        return f"{type(self).__name__}-{id(self)}-{self.system_type}-{self.system_tuple}"

    def __init__(self, system_tuple, system_type, **kwargs):
        if not system_tuple:
            raise ValueError(f"Attempt to create system missing system_tuple parameter")
        if not system_type:
            raise ValueError(f"Attempt to create system missing system_type parameter")
        self.system_tuple = system_tuple
        self.system_type = system_type

    def __hash__(self):
        return hash(self.system_tuple)

    @classmethod
    def register_to_converter(cls, coord_system):
        """Register a new converter function for transforming from this coordinate
        system to another system
        """
        print(f"Registering to converter for {coord_system} in {cls.__name__}")
        def anon_reg_func(callback):
            cls.to_other_conversions[coord_system] = callback
            return callback
        return anon_reg_func

    @classmethod
    def register_from_converter(cls, coord_system):
        """Register a new converter function for transforming to this coordinate
        system from another system
        """
        print(f"Registering from converter for {coord_system} in {cls.__name__}")
        def anon_reg_func(callback):
            cls.from_other_conversions[coord_system] = callback
            return callback
        return anon_reg_func

    def to_other_system(self, system_tuple, coord):
        """Converts a coordinate from this system to another system identified by
        the system id tuple.
        """
        if coord.system != self:
            raise ValueError(f"Coordinate not a member of this system")
        #logger.debug(f"to_other_conversions:{self.to_other_conversions}")
        #logger.debug(f"Converting from {self.system_tuple} to {name}")

        if system_tuple not in self.to_other_conversions:
            raise ValueError(f"No Converter from {self.system_tuple} to {system_tuple} Found")

        system = CoordinateSystemMgr.get_coord_system(system_tuple)
        return self.to_other_conversions[system](system, coord)

    def from_other_system(self, coord):
        """Converts from another system system_tuple is the tuple that identifies
        the other system being converted from coord is the coordinate of that system.
        """
        #logger.debug(f"from_other_conversions:{self.from_other_conversions}")
        #logger.debug(f"Converting to {self.system_tuple} from {name}")
        if coord.system.system_type not in self.from_other_conversions:
            raise ValueError((f"No Converter from {coord.system.system_type}"
                              f"{coord.system.system_tuple} to {self.system_type}"
                              f"{self.system_tuple} Found"))

        return self.from_other_conversions[coord.system.system_type](self, coord)

@dataclass(eq=True, frozen=True)
class CubedCoord():
    """
    Represent 3 element coordinate primitive including providing support functions
    """
    x: int
    y: int
    z: int
    system: CoordinateSystem

    def __add__(self, coord):
        if not isinstance(coord, type(self)):
            raise ValueError(f"Cannot add Coordinate {coord} to {self} because "
                             f"they are not the same type")
        if self.system != coord.system:
            raise ValueError(f"The coordinates must belong to the same system")
        return CubedCoord(x=self.x+coord.x, y=self.y+coord.y, z=self.z+coord.z,
                          system=self.system)

    def __sub__(self, coord):
        if not isinstance(coord, type(self)):
            raise ValueError(f"Cannot add Coordinate {coord} to {self} because "
                             f"they are not the same type")
        if self.system != coord.system:
            raise ValueError(f"The coordinates must belong to the same system")
        return CubedCoord(x=self.x-coord.x, y=self.y-coord.y, z=self.z-coord.z,
                          system=self.system)

    def __mul__(self, multiplier):
        if not isinstance(multiplier, int):
            raise ValueError(f"The multiplier must be an integer")
        return CubedCoord(x=self.x*multiplier, y=self.y*multiplier,
                          z=self.z*multiplier, system=self.system)

    def __getitem__(self, idx):

        if idx == 0:
            return self.x
        if idx == 1:
            return self.y
        if idx == 2:
            return self.z

        raise ValueError(f"Index must be 0, 1, or 2")


@dataclass(eq=True, frozen=True)
class HexCoord(CubedCoord):
    """
    Provide a 3 element coordinate primitive including support functions, specifically
    for hexagonal coordinate systems.  This one provides a guarantee that the hex
    system coordinates obey the constraint (x+y+z=0).
    """
    def __post_init__(self):
        if self.x+self.y+self.z == 0:
            raise ValueError(f"The coordinates do not conform to the hexagonal"
                             f"constraint of x+y+z=0")


@dataclass(eq=True, frozen=True)
class RectCoord():
    """
    Represent 2 element coordinate primitive including providing support functions
    """
    x: int
    y: int
    system: CoordinateSystem

    def __add__(self, coord):
        if not isinstance(coord, type(self)):
            raise ValueError(f"Cannot add Coordinate {coord} to {self} because "
                             f"they are not the same type")
        if self.system != coord.system:
            raise ValueError(f"The coordinates must belong to the same system")
        return RectCoord(x=self.x+coord.x, y=self.y+coord.y, system=self.system)

    def __sub__(self, coord):
        if not isinstance(coord, type(self)):
            raise ValueError(f"Cannot add Coordinate {coord} to {self} because "
                             f"they are not the same type")
        if self.system != coord.system:
            raise ValueError(f"The coordinates must belong to the same system")
        return RectCoord(x=self.x-coord.x, y=self.y-coord.y, system=self.system)

    def __mul__(self, multiplier):
        if not isinstance(multiplier, int):
            raise ValueError(f"The multiplier must be an integer")
        return RectCoord(x=self.x*multiplier, y=self.y*multiplier, system=self.system)

    def __getitem__(self, idx):
        if idx == 0:
            return self.x
        if idx == 1:
            return self.y

        raise ValueError(f"Index must be 0 or 1")

@CoordinateSystemMgr.register_coordsystem_type('hex')
class HexCoordinateSystem(CoordinateSystem):
    """
    Represent a hexagonal coordinate system and handle/generate coordinate system algorithms
    and transforms
    """
    dimensionality = 3
    dimension_req_keys = ['x', 'y', 'z']
    to_other_conversions = {}
    from_other_conversions = {}
    sides = 6
    coord_cls = CubedCoord

    def __init__(self, **kwargs):
        #logger.debug("%s: __init__ %s", type(self).__name__, kwargs)
        super().__init__(**kwargs)
        #[(x, y, z)]
        #On pointy top [Left, upleft, upright, right, downright, downleft]
        #Need self for coordinates

        #We must declare dirs here because coordinates require an owning
        #coordinate system
        self.dirs = [self.coord_cls(-1, 1, 0, self), self.coord_cls(0, 1, -1, self),
                     self.coord_cls(+1, 0, -1, self), self.coord_cls(1, -1, 0, self),
                     self.coord_cls(0, -1, 1, self), self.coord_cls(-1, 0, 1, self)]

    def coord(self, *args, **kwargs):
        """Generate a coordinate from passed through arguments, and assign this
        system as the coordinate's system"""
        return self.coord_cls(system=self, *args, **kwargs)

    def get_origin(self):
        """Return origin of the coordinate system"""
        return self.coord_cls(x=0, y=0, z=0, system=self)



    def coords_in_range(self, anchor, steps):
        """Return coordinates within x steps from a coordinate anchorpoint"""
        coords = list()
        x_low = -steps
        x_high = steps

        #Generate using an axial formula to make it easier
        #calculate z via the other two and throw away ones that aren't in bounds
        for x in range(x_low, x_high+1):
            for y in range(max(-steps, -x-steps), min(steps, -x+steps)+1):
                z = -x - y
                coords.append(anchor+self.coord(x, y, z))
        return coords

    def coords_reachable(self, start, distance): # TODO: Accept a lambda that
                                                 # determines blocked or not
        """Returns a set of those coordinates that are reachable within x steps"""
        visited = set() # set of hexes
        visited.add(start)
        fringes = list() # array of arrays of hexes
        fringes.append([start])

        for idx in range(1, distance+1):
            fringes.append([])
            for coord in fringes[idx-1]:
                for direction in self.dirs:
                    neighbor = coord+direction
                    if neighbor not in visited: # TODO: add exemptions (impassable)
                                                #or mandatory neighbors (direct
                                                #connections)
                        visited.add(neighbor)
                        fringes[idx].append(neighbor)

        return visited



    #assuming 60 degree rotations(edge-to-edge)..hence cnt of rotations
    def make_rotation_transform(self, cnt):
        """Use cnt to generate transform which is used to rotate a map of
        coordinates around an anchor"""
        neg = -1 if (cnt&1) else 1 #flip signs on negatives
        rotate = cnt % len(self.dirs) % 3

        def transform(vec):
            newvec = self.coord_cls(system=self, x=neg*vec[(0+rotate)%3],
                                    y=neg*vec[(1+rotate)%3], z=neg*vec[(2+rotate)%3])
            #logger.debug("Cnt: %s Rot#: %s, Neg: %s, Src Vec: %s, Rotated Vec: %s",
            #             cnt, rotate, neg, vec, newvec)
            return newvec

        return transform

    def get_mapping_offset(self, selfedge_idx, otheredge_idx):
        """Given adjacent edge indexes from the self system and other system, return
        the rotation count that, when applied to an edge index from the other system
        , results in the edge that faces the same direction in the self system (positive nt)"""
        cnt = selfedge_idx - ((otheredge_idx + len(self.dirs)//2) % len(self.dirs))
        if cnt < 0:
            return cnt + len(self.dirs)

        return cnt



    def gen_rotated_coords(self, anchor, coords, cnt):
        """Rotate a set of coordinates around a chosen anchor point.  It first
         makes a transform, then applies it to all the coordinates"""
        newcoords = set()
        xform = self.make_rotation_transform(cnt)

        for coord in coords:
            #create directional vector based on center
            pos_minus_anchor = coord - anchor
            #rotate directional vector
            rot_vec = xform(pos_minus_anchor)
            #concretize back to coordinate
            final_coord = rot_vec + anchor
            newcoords.add(final_coord)

        return newcoords

    def coords_in_ring(self, anchor, radius):
        """Return the coordinates one the ring shape at a distance, radius, from
        the anchor point"""
        if radius == 0:
            return [anchor]

        results = list()
        # this code doesn't work for radius == 0; can you see why?
        coord = anchor + self.dirs[4] * radius

        for i in range(0, 6):
            for _ in range(0, radius):
                results.append(coord)
                coord = coord + self.dirs[i]
        return results

    def validate_dimensions(self, dimensions):
        """Check declared dimension sizes satisfy reasonable cursory requirements"""

        #safety checking
        if len(dimensions) != self.dimensionality:
            raise ValueError(f"The number of dimensions provided {len(dimensions)}"
                             f"do not match that of this coordinate system "
                             f"{self.dimensionality}.")

        if not all(isinstance(elem, int) for elem in dimensions):
            raise ValueError(f"Not all dimensions are ints {dimensions}")

        if not all(elem > 0 for elem in dimensions):
            raise ValueError(f"Dimensions must be greater than 1 {dimensions}")

        if not checkallequal(dimensions):
            raise ValueError(f"Not all dimensions are equal {dimensions}.  They "
                             f"must be equal. This will be changed in a future version")

    def gen_coord_set(self, dimensions):
        """Generate a coordinate set based on size dimensions declared. E.G. 5x5x5"""

        #logger.debug("%s(%s): gen_coord_set: dimensions: %s", self.system_tuple,
        #             type(self).__name__, dimensions)
        self.validate_dimensions(dimensions)

        coords = self.coords_in_range(self.coord_cls(0, 0, 0, system=self), dimensions[0]//2)

        #logger.debug("%s(%s):%s", self.system_tuple, type(self).__name__, str(coords))
        #logger.debug("%s(%s): gen_coord_set: dimensions: %s numcells: %s",
        #             self.system_tuple, type(self).__name__, dimensions, str(len(coords)))
        return coords

    def duplicate_coord(self, coord):
        """Duplicates the coordinate of another system into this one

        They must be of the same type
        """
        if coord.system.system_type != self.system_type:
            raise ValueError(f"The coordinate: {coord} is not of the same "
                             f"underlying system type: {self.system_type}")
        return self.coord(x=coord.x, y=coord.y, z=coord.z)

    def duplicate_coords(self, coords):
        """Duplicates the coordinates of another system of the same type into this one
        """
        new_coords = list()
        for coord in coords:
            new_coords.append(self.duplicate_coord(coord))
        return new_coords

@CoordinateSystemMgr.register_coordsystem_type('xy')
@CoordinateSystemMgr.register_coordsystem_type('rect')
@CoordinateSystemMgr.register_coordsystem_type('square')
@CoordinateSystemMgr.register_coordsystem_type('oddr')
@CoordinateSystemMgr.register_coordsystem_type('oddq')
@CoordinateSystemMgr.register_coordsystem_type('evenr')
@CoordinateSystemMgr.register_coordsystem_type('evenq')
class RectCoordinateSystem(CoordinateSystem):
    """
    Represent a square/rectangular coordinate system and handle/generate coordinate
    system algorithms and transforms
    """
    dimension_req_keys = ['x', 'y']
    dimensionality = 2
    to_other_conversions = {}
    from_other_conversions = {}
    sides = 4
    coord_cls = RectCoord

    def __init__(self, **kwargs):
        #logger.debug("%s: __init__ %s", type(self).__name__, kwargs)
        super().__init__(**kwargs)
        self.dirs = [self.coord_cls(-1, 0, self), self.coord_cls(0, -1, self),
                     self.coord_cls(1, 0, self), self.coord_cls(0, 1, self)]

    def coord(self, *args, **kwargs):
        """Generate a coordinate from passed through arguments, and assign this
        system as the coordinate's system"""
        return self.coord_cls(system=self, *args, **kwargs)

    def get_origin(self):
        """Return origin of the coordinate system"""
        return self.coord_cls(x=0, y=0, system=self)

    def validate_dimensions(self, dimensions):
        """Check declared dimension sizes satisfy reasonable cursory requirements"""
        #safety checking
        if len(dimensions) != self.dimensionality:
            raise ValueError(f"The number of dimensions provided {len(dimensions)}"
                             f"do not match that of this coordinate system "
                             f"{self.dimensionality}.")

        if not all(isinstance(elem, int) for elem in dimensions):
            raise ValueError(f"Not all dimensions are ints {dimensions}")

    def gen_coord_set(self, dimensions):
        """Generate a coordinate set based on size dimensions declared. E.G. 5x5x5"""
        coords = set()

        #logger.debug("%s(%s): gen_coord_set: dimensions: %s", self.system_tuple,
        #             type(self).__name__, dimensions)
        self.validate_dimensions(dimensions)

        for x in range(0, dimensions[0]):
            for y in range(0, dimensions[1]):
                coords.add(self.coord_cls(x, y, system=self))

        #logger.debug("%s(%s): gen_coord_set: dimensions: %s numcells: %s",
        #             self.system_tuple, type(self).__name__, dimensions, str(len(coords)))

        return coords

@HexCoordinateSystem.register_from_converter("oddr")
def hex_from_oddr(newsystem, coord):
    """convert from hex coordinate to oddr coordinate"""
    x = coord.x + (coord.y + (coord.y&1)) // 2
    z = -coord.y
    y = -x-z
    newcoord = newsystem.coord(x=x, y=y, z=z)
    #logger.debug("OldCoord:%s NewCoord:%s", coord, newcoord)
    return newcoord

@HexCoordinateSystem.register_to_converter("oddr")
@RectCoordinateSystem.register_from_converter("hex")
def oddr_from_hex(newsystem, coord):
    """convert from oddr coordinate to hex coordinate"""
    x = coord.x + (coord.z - (coord.z&1)) // 2
    y = -coord.z
    return newsystem.coord(x=x, y=y)

@HexCoordinateSystem.register_from_converter("evenr")
def hex_from_evenr(newsystem, coord):
    """convert from hex coordinate to evenr coordinate"""
    x = coord.x - (coord.y + (coord.y&1)) // 2
    z = -coord.y
    y = -x+z
    return newsystem.coord(x=x, y=y, z=z)

@HexCoordinateSystem.register_to_converter("evenr")
def evenr_from_hex(newsystem, coord):
    """convert from evenr coordinate to hex coordinate"""
    y = coord.x + (coord.z + (coord.z&1)) // 2
    x = -coord.z
    return newsystem.coord(x=x, y=y)

@HexCoordinateSystem.register_to_converter("oddq")
def oddq_from_hex(newsystem, coord):
    """convert from oddq coordinate to hex coordinate"""
    x = coord.x
    y = coord.z + (coord.x - (coord.x&1)) // 2
    return newsystem.coord(x=x, y=y)

@HexCoordinateSystem.register_from_converter("oddq")
def hex_from_oddq(newsystem, coord):
    """convert from hex coordinate to oddq coordinate"""
    x = coord.x
    z = coord.y - (coord.x - (coord.x&1)) // 2
    y = -x-z
    return newsystem.coord(x=x, y=y, z=z)

@HexCoordinateSystem.register_to_converter("evenq")
def evenq_from_hex(newsystem, coord):
    """convert from evenq coordinate to hex coordinate"""
    x = coord.x
    y = coord.z + (coord.x + (coord.x&1)) // 2
    return newsystem.coord(x=x, y=y)

@HexCoordinateSystem.register_from_converter("evenq")
def hex_from_evenq(newsystem, coord):
    """convert from hex coordinate to evenq coordinate"""
    x = coord.x
    z = coord.y - (coord.x + (coord.x&1)) // 2
    y = -x-z
    return newsystem.coord(x=x, y=y, z=z)

@RectCoordinateSystem.register_from_converter("square")
@RectCoordinateSystem.register_to_converter("square")
def square_tofrom_square(newsystem, coord):
    """convert from square coordinate to square coordinate
    This identity conversion is used by happenstance in to/from operations
    from config files where apriori knowledge of the systems is not available """
    return newsystem.coord(x=coord.x, y=coord.y)

@HexCoordinateSystem.register_from_converter("hex")
@HexCoordinateSystem.register_to_converter("hex")
def hex_tofrom_hex(newsystem, coord):
    """convert from hex coordinate to hex coordinate
    This identity conversion is used by happenstance in to/from operations
    from config files where apriori knowledge of the systems is not available """
    return newsystem.coord(x=coord.x, y=coord.y, z=coord.z)
