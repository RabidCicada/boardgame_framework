import pathlib
from . import cell
from enum import Enum
from dataclasses import dataclass


class CoordinateSystemMgr():
    coord_systems = dict()

    #The following uses decorator syntax to perform processing
    #on the function but doesn't actually wrap it.
    @classmethod
    def register_coord_system(cls,system_name):
        def anon_reg_func(coord_system):
            if not issubclass(coord_system,CoordinateSystem):
                raise ValueError(F"Passed class {coord_system.__name__} not of type CoordinateSystem")
            coord_system.shortname = system_name

            #register both the short name and the full class name
            cls.coord_systems[system_name] = coord_system
            cls.coord_systems[coord_system.__name__] = coord_system
            return coord_system
        return anon_reg_func

    @classmethod
    def get_coord_system(cls,system_name):
        if system_name in cls.coord_systems:
            return cls.coord_systems[system_name]()

    @classmethod
    def get_coord_type(cls,system_name):
        if system_name in cls.coord_systems:
            return cls.coord_systems[system_name]


class CoordinateSystem():
    to_other_conversions={}
    from_other_conversions={}

    def __str__(self):
        return F"{type(self).__name__}"

    def __repr__(self):
        return F"{type(self).__name__}-{id(self)}"

    @classmethod
    def register_to_converter(cls,coord_system):
        def anon_reg_func(callback):
            cls.to_other_conversions[coord_system] = callback
            return callback
        return anon_reg_func

    @classmethod
    def register_from_converter(cls,coord_system):
        def anon_reg_func(callback):
            cls.from_other_conversions[coord_system] = callback
            return callback
        return anon_reg_func

    @classmethod
    def to_other_system(cls,name,coord):
        if name in to_other_conversions:
            to_other_conversions[name](coord)
        else:
            raise ValueError(F"No Converter to {name} Found")


    @classmethod
    def from_other_system(cls,name,coord):
        if name in to_other_conversions:
            to_other_conversions[name](coord)
        else:
            raise ValueError(F"No Converter from {name} Found")


@CoordinateSystemMgr.register_coord_system('cubed')
class CubedCoordinateSystem(CoordinateSystem):
    dimension_req_keys=['x','y','z']



    #coord_type = cubed_coord

    class FromRectOffsetType(Enum):
        ODDR = 1
        EVENR = 2
        ODDC = 3
        EVENC = 4

    def __init__(self):
        pass



    def coord():
        return cubed_coord(**kwargs)

    def get_coord_set(self,dimensions):
        #safety checking
        if not all (key in dimensions for key in self.dimension_req_keys):
            raise ValueError(f"Missing one of required keys {self.dimension_req_keys}")

    def validate_dimensions(self,dimensions):
        #safety checking
        if not all (key in dimensions for key in self.dimension_req_keys):
            raise ValueError(f"Missing one of required keys {self.dimension_req_keys}")

        if not all(isinstance(elem) for elem in dimensions):
            raise ValueError(f"Not all dimensions are ints {dimensions}")

    def get_coord_set(self,dimensions):
        assert False, "Not Implemented Yet"

        return coords

    def from_rect_coord(self,rect_coord,offset_type=FromRectOffsetType.ODDR):
        assert(rect_coord.coord_type==RectCoordinateSystem)

    @CoordinateSystem.register_from_converter("rect")
    @staticmethod
    def from_oddr(coord):
        x = coord.x - (coord.y - (coord.y&1)) / 2
        z = coord.y
        y = -x-z
        return cubed_coord(x, y, z)

    @CoordinateSystem.register_to_converter("rect")
    @staticmethod
    def to_oddr(coord):
        col = coord.x + (coord.z - (coord.z&1)) / 2
        row = coord.z
        return RectCoordinateSystem.rect_coord(col, row)


@dataclass
class cubed_coord():
    x: int
    y: int
    z: int
    system: CoordinateSystem = CubedCoordinateSystem

@CoordinateSystemMgr.register_coord_system('rect')
class RectCoordinateSystem(CoordinateSystem):
    dimension_req_keys=['x','y']



    def __init__(self):
        pass

    def __str__(self):
        return F"{type(self).__name__}"

    def __repr__(self):
        return F"{type(self).__name__}-{id(self)}"

    def validate_dimensions(self,dimensions):
        #safety checking
        if not all (key in dimensions for key in self.dimension_req_keys):
            raise ValueError(F"Missing one of required keys {self.dimension_req_keys}")

        if not all(isinstance(elem) for elem in dimensions):
            raise ValueError(F"Not all dimensions are ints {dimensions}")

    def get_coord_set(self,dimensions):
        coords = set()

        validate_dimensions(dimensions)

        for x in range(0,dimensions['x']):
            for y in range(0,dimensions['y']):
                coords.add(rect_coord(x,y))

        return coords

@dataclass
class rect_coord():
    x: int
    y: int
    coord_type: CoordinateSystem = RectCoordinateSystem
