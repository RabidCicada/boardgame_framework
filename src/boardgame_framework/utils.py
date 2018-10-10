import logging
import pathlib
from . import cell
from enum import Enum
from dataclasses import dataclass
from numpy import ndarray

logger = logging.getLogger(__name__)

def checkallequal(iteratable):
    iterator = iter(iteratable)
    try:
        first = next(iterator)
    except StopIteration:
        return True
    return all(first == rest for rest in iterator)

class CoordinateSystemMgr():
    coord_systems = dict()

    #The following uses decorator syntax to perform processing
    #on the function but doesn't actually wrap it.
    @classmethod
    def register_coord_system(cls,system_name):
        def anon_reg_func(coord_system):
            if not issubclass(coord_system,CoordinateSystem):
                raise ValueError(F"Passed class {coord_system.__name__} not of type CoordinateSystem")

            #register both the short name and the full class name
            instance = coord_system(system_name = system_name)
            cls.coord_systems[system_name] = instance
            return coord_system
        return anon_reg_func

    @classmethod
    def get_coord_system(cls,system_name):
        if system_name not in cls.coord_systems:
            raise ValueError(F"No coordinate system by the name {system_name} registered!")
        return cls.coord_systems[system_name]



class CoordinateSystem():
    to_other_conversions={}
    from_other_conversions={}

    def __str__(self):
        return F"{type(self).__name__}"

    def __repr__(self):
        return F"{type(self).__name__}-{id(self)}"

    def __init__(self, system_name):
        if not system_name:
            raise ValueError(f"System missing name parameter")
        self.system_name=system_name

    def __hash__(self):
        return hash(self.system_name)

    @classmethod
    def register_to_converter(cls,coord_system):
        print(F"Registering to converter for {coord_system} in {cls.__name__}")
        def anon_reg_func(callback):
            cls.to_other_conversions[coord_system] = callback
            return callback
        return anon_reg_func

    @classmethod
    def register_from_converter(cls,coord_system):
        print(F"Registering from converter for {coord_system} in {cls.__name__}")
        def anon_reg_func(callback):
            cls.from_other_conversions[coord_system] = callback
            return callback
        return anon_reg_func

    def to_other_system(self,name,coord):
        #logger.debug(F"to_other_conversions:{self.to_other_conversions}")
        #logger.debug(F"Converting from {self.system_name} to {name}")
        if name in self.to_other_conversions:
            system = self.get_coord_system()
            return self.to_other_conversions[name](system,coord)
        else:
            raise ValueError(F"No Converter from {self.system_name} to {name} Found")


    def from_other_system(self,name,coord):
        #logger.debug(F"from_other_conversions:{self.from_other_conversions}")
        #logger.debug(F"Converting to {self.system_name} from {name}")
        if name == self.system_name:
            return coord
        if name in self.from_other_conversions:
            return self.from_other_conversions[name](self,coord)
        else:
            raise ValueError(F"No Converter from {name} to {self.system_name} Found")

@dataclass(eq=True,frozen=True)
class cubed_coord():
    x: int
    y: int
    z: int
    system: CoordinateSystem

    def __add__(self,coord):
        assert type(self) == type(coord)
        assert self.system == coord.system, "The coordinates must belong to the same system"
        return cubed_coord(x=self.x+coord.x,y=self.y+coord.y,z=self.z+coord.z,system=self.system)

    def __sub__(self,coord):
        assert type(self) == type(coord)
        assert self.system == coord.system, "The coordinates must belong to the same system"
        return cubed_coord(x=self.x-coord.x,y=self.y-coord.y,z=self.z-coord.z,system=self.system)

    def __mul__(self,multiplier):
        assert isinstance(multiplier, int)
        return cubed_coord(x=self.x*multiplier,y=self.y*multipliers,z=self.z*multiplier,system=self.system)

    def __getitem__(self,idx):
        assert idx >=0 or idx < 3, "Index must be between 0 and 3"

        if idx==0:
            return self.x
        if idx==1:
            return self.y
        if idx==2:
            return self.z


@dataclass(eq=True,frozen=True)
class hex_coord(cubed_coord):
    def __post_init__(self):
        assert x+y+z == 0


@dataclass(eq=True,frozen=True)
class rect_coord():
    x: int
    y: int
    system: CoordinateSystem

    def __add__(self,coord):
        assert type(self) == type(coord)
        assert self.system == coord.system, "The coordinates must belong to the same system"
        return rect_coord(x=self.x+coord.x,y=self.y+coord.y,system=self.system)

    def __sub__(self,coord):
        assert type(self) == type(coord)
        assert self.system == coord.system, "The coordinates must belong to the same system"
        return rect_coord(x=self.x-coord.x,y=self.y-coord.y,system=self.system)

    def __mul__(self,multiplier):
        assert isinstance(multiplier, int)
        return rect_coord(x=self.x*multiplier,y=self.y*multipliers,system=self.system)

    def __getitem__(self,idx):
        assert idx >=0 or idx < 2, "Index must be between 0 and 2"

        if idx==0:
            return self.x
        if idx==1:
            return self.y


@CoordinateSystemMgr.register_coord_system('hex')
class HexCoordinateSystem(CoordinateSystem):
    dimension_req_keys=['x','y','z']
    to_other_conversions={}
    from_other_conversions={}

    def __init__(self,**kwargs):
        #logger.debug("%s: __init__ %s",type(self).__name__,kwargs)
        super().__init__(**kwargs)
        self.dirs=[cubed_coord(1,-1,0,self),cubed_coord(+1,0,-1,self),cubed_coord(0,1,-1,self),
                   cubed_coord(-1,1,0,self),cubed_coord(-1,0,1,self),cubed_coord(0,-1,1,self)]

    def coord(self,**kwargs):
        return cubed_coord(system=self,**kwargs)

    def distance(self,coord1,coord2):
        return (abs(coord1.x - coord2.x) + abs(coord1.y - coord2.y) + abs(coord1.z - coord2.z))//2

    def coords_in_range(self,anchor,steps):
        coords = list()
        xl = -steps
        xh = steps

        #Generate using an axial formula to make it easier
        #calculate z via the other two and throw away ones that aren't in bounds
        for x in range(xl,xh+1):
            for y in range(max(-steps,-x-steps),min(steps,-x+steps)+1):
                z=-x-y
                coords.append(anchor+cubed_coord(x,y,z,system=self))
        return coords

    def coord_reachable(start, distance):
        visited = set() # set of hexes
        visited.add(start)
        fringes = list() # array of arrays of hexes
        fringes.append([start])

        for idx in range(1, movement+1):
            fringes.append([])
            for coord in fringes[k-1]:
                for dir in self.dirs:
                    neighbor = coord+dir
                    if neighbor not in visited: #Add exemptions (impassable) or mandatory neighbors (direct connections)
                        visited.add(neighbor)
                        fringes[k].append(neighbor)

        return visited

    #assuming 60 degree rotations..hence cnt of rotations
    def make_rotate_transform(anchor, cnt):
        neg  = -(cnt&1)
        rotate = cnt % len(dirs) % 3

        def transform(point):
            return cubed_coord(x=neg*point[(0+rotate)%3],y=neg*point[(1+rotate%3)],z=neg*point[(2+rotate%3)])


    def rotate_about(anchor, coords, cnt):
        newcoords = set()
        xform = make_rotate_transform(center,cnt)

        for coord in coords:
            newcoords.add(xform(coord))

        return newcoords

    def coords_in_ring(self,anchor,radius):
        if radius == 0:
            return [anchor]

        results = list()
        # this code doesn't work for radius == 0; can you see why?
        coord = anchor+self.dirs[4]*radius

        for i in range(0,7):
            for j in range(0,radius+1):
                results.append(coord)
                coord = coord+self.dirs[i]
        return results

    def validate_dimensions(self,dimensions):

        #safety checking
        if not all (key in dimensions for key in self.dimension_req_keys):
            raise ValueError(f"Missing` one of required keys {self.dimension_req_keys}")

        if not all(isinstance(elem,int) for elem in dimensions.values()):
            raise ValueError(F"Not all dimensions are ints {dimensions}")

        if not all(elem > 0 for elem in dimensions.values()):
            raise ValueError(F"Dimensions must be greater than 1 {dimensions}")

        if not all(elem > 0 for elem in dimensions.values()):
            raise ValueError(F"Dimensions must be greater than 1 {dimensions}")

        if not checkallequal(dimensions.values()):
            raise ValueError(F"Not all dimensions are equal {dimensions}.  They must be equal.")

    def get_coord_set(self,dimensions):

        #logger.debug("%s(%s): get_coord_set: dimensions: %s",self.system_name,type(self).__name__,dimensions)
        self.validate_dimensions(dimensions)

        coords = self.coords_in_range(cubed_coord(0,0,0,system=self),dimensions['x']//2)

        #logger.debug("%s(%s):%s",self.system_name,type(self).__name__,str(coords))
        #logger.debug("%s(%s): get_coord_set: dimensions: %s numcells: %s",self.system_name,type(self).__name__,dimensions,str(len(coords)))
        return coords

@CoordinateSystemMgr.register_coord_system('rect')
@CoordinateSystemMgr.register_coord_system('square')
@CoordinateSystemMgr.register_coord_system('oddr')
@CoordinateSystemMgr.register_coord_system('oddq')
@CoordinateSystemMgr.register_coord_system('evenr')
@CoordinateSystemMgr.register_coord_system('evenq')
class RectCoordinateSystem(CoordinateSystem):
    dimension_req_keys=['x','y']
    to_other_conversions={}
    from_other_conversions={}

    def __init__(self,**kwargs):
        #logger.debug("%s: __init__ %s",type(self).__name__,kwargs)
        super().__init__(**kwargs)
        self.dirs=[rect_coord(-1,0,self),rect_coord(0,-1,self),rect_coord(1,0,self),
                   rect_coord(0,1,self)]

    def __str__(self):
        return F"{type(self).__name__}"

    def __repr__(self):
        return F"{type(self).__name__}-{id(self)}"

    def coord(self,**kwargs):
        return rect_coord(system=self,**kwargs)

    def validate_dimensions(self,dimensions):
        #safety checking
        if not all (key in dimensions for key in self.dimension_req_keys):
            raise ValueError(F"Missing one of required keys {self.dimension_req_keys}")

        if not all(isinstance(elem,int) for elem in dimensions.values()):
            raise ValueError(F"Not all dimensions are ints {dimensions}")

    def get_coord_set(self,dimensions):
        coords = set()

        #logger.debug("%s(%s): get_coord_set: dimensions: %s",self.system_name,type(self).__name__,dimensions)
        self.validate_dimensions(dimensions)

        for x in range(0,dimensions['x']):
            for y in range(0,dimensions['y']):
                coords.add(rect_coord(x,y,system=self))

        #logger.debug("%s(%s): get_coord_set: dimensions: %s numcells: %s",self.system_name,type(self).__name__,dimensions,str(len(coords)))

        return coords

@HexCoordinateSystem.register_from_converter("oddr")
def cube_from_oddr(newsystem,coord):
    x = coord.x - (coord.y - (coord.y&1)) // 2
    z = coord.y
    y = -x-z
    return newsystem.coord(x=x, y=y, z=z)

@HexCoordinateSystem.register_to_converter("oddr")
@RectCoordinateSystem.register_from_converter("hex")
def oddr_from_cube(newsystem,coord):
    y = coord.x + (coord.z - (coord.z&1)) // 2
    x = coord.z
    return newsystem.coord(x=x,y=y)

@HexCoordinateSystem.register_from_converter("evenr")
def cube_from_evenr(newsystem,coord):
    x = coord.x - (coord.y + (coord.y&1)) // 2
    z = coord.y
    y = -x-z
    return newsystem.coord(x=x, y=y, z=z)

@HexCoordinateSystem.register_to_converter("evenr")
def evenr_from_cube(newsystem,coord):
    y = cube.x + (cube.z + (cube.z&1)) // 2
    x = coord.z
    return newsystem.coord(x=x,y=y)

@HexCoordinateSystem.register_to_converter("oddq")
def oddq_from_cube(newsystem,coord):
    x = coord.x
    y = coord.z + (coord.x - (coord.x&1)) // 2
    return newsystem.coord(x=x,y=y)

@HexCoordinateSystem.register_from_converter("oddq")
def cube_from_oddq(newsystem,coord):
    x = coord.x
    z = coord.y - (coord.x - (coord.x&1)) // 2
    y = -x-z
    return newsystem.coord(x=x,y=y,z=z)

@HexCoordinateSystem.register_to_converter("evenq")
def evenq_from_cube(newsystem,coord):
    col = coord.x
    row = coord.z + (coord.x + (coord.x&1)) // 2
    return newsystem.coord(x=x,y=y)

@HexCoordinateSystem.register_from_converter("evenq")
def cube_from_evenq(newsystem,coord):
    x = coord.x
    z = coord.y - (coord.x + (coord.x&1)) // 2
    y = -x-z
    return newsystem.coord(x=x,y=y,z=z)
