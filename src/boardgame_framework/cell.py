"""
This module supports the creation and management of cells (regions of the gamespace)
in the boardgame_framework.
"""

import itertools
import pathlib
import logging

from .coord import CoordinateSystemMgr

AUTO_CELLS_REQUIRED_KEYS = ["cell_type", "dimensions"]

logger = logging.getLogger(__name__)



class Cell():
    """
    Be the representation of regions of the gamespace.

    A Cell is a representation of physical space in the game.  This can be squares
    in chess and checkers, regions like playfield etc for magic the gathering,
    hexes in terra mystica, settlers of catan, etc.
    """

    new_uid = itertools.count()
    def __init__(self, uid=None, name=None, attributes=None, coord=None,
                 connections=None, **kwargs):

        self.name = name
        self.uid = next(self.new_uid) if uid is None else uid

        #Structural information
        self.parent = None
        self.children = set()
        self.connections = connections
        self.neighbors = dict()

        #Coordinate System Helper Stuff
        self.coord_system_id = None
        self.coord = None
        self.coords = dict()

        #General storage
        self.data = dict()

        # Anything that relies on raw variables being initialized
        if coord:
            self.assign_coord(coord)
            self.set_default_coord(coord)

        self.attributes = attributes

    def __str__(self):
        return (f"{type(self).__name__}-{self.uid}-'{self.name}'-"
                f"{len(self.children)}-COORD:{self.coord}")

    def __repr__(self):
        return (f"{type(self).__name__}-{self.uid}-'{self.name}'-"
                f"{len(self.children)}-COORD:{self.coord}")

    # @property
    # def coord(self):
    #     if self._coord:
    #         return self._coord
    #     else:
    #         if self.coord_system_id:
    #             CoordinateSystemMgr.get_coord_system(self.coord_system_id)
    #         else:
    #             raise

    def store_data(self, key, data):
        """
        Store arbitrary keyed data.  This allows the Cell to be used as a generic data store
        """
        self.data[key] = data

    def get_data(self, key):
        """Retrieve keyed data stored with the cell"""
        return self.data.get(key, None)

    def assign_coord(self, coord):
        """
        Add the coordinate to the Cells "known cordinates" organized by coordinate system
        Additionally register with CellMgr so that the cell is retrievable using
        coordinate or coordinate_system_id
        """
        CellMgr.register_cell_to_coord(self, coord)
        self.coords[coord.system.system_tuple] = coord
        if coord.system.system_tuple not in self.neighbors:
            self.neighbors[coord.system.system_tuple] = [None] * len(coord.system.dirs)

    def assign_default_coord(self, coord):
        """
        Add the coordinate to the Cells "known cordinates" organized by coordinate system
        Additionally register with CellMgr so that the cell is retrievable using
        coordinate or coordinate_system_id
        Set as default coordinate
        """
        self.assign_coord(coord)
        self.set_default_coord(coord)

    def get_coord(self, coord_sys_id):
        """Retrieve coordinate for this cell in a given coordinate system"""
        return self.coords.get(coord_sys_id, None)

    def set_default_coord(self, coord):
        """Directly set the cells primary coordinate and primary coord system"""
        self.coord = coord
        self.coord_system_id = coord.system.system_tuple

    def set_parent(self, cell, reflexive=False):
        """Set the cells parent directly to the given cell, and optionally add
        this cell to the parent"""
        self.parent = cell
        if reflexive:
            self.parent.add_child(self)

    def add_child(self, cell, reflexive=False):
        """Add a child cell to this cell, and optionally set the child's parent
        to this cell"""
        self.children.add(cell)
        if reflexive:
            cell.set_parent(self)

    def add_children(self, cells, reflexive=False):
        """Add children to this cell, and optionally set the children's parent to
         this cell"""
        for cell in cells:
            self.add_child(cell, reflexive=reflexive)

    def set_neighbor(self, coord_system_id, side, cell):
        """Directly set a neighbor for a given geometrical side """
        self.neighbors[coord_system_id][side] = cell

    def get_neighbors(self, coord_system_id):
        """Retrieve nieghbors given the chosen coordinate system"""
        neighs = []
        coord = self.get_coord(coord_system_id)
        for direction in coord.system.dirs:
            ncell = CellMgr.by_coord(coord+direction)
            if ncell:
                neighs.append(ncell)
        return neighs

    def get_neighbor(self, coord_system_id, side):
        """Retrieve a neighebor given the coordinate system and the given
        geometrical side"""
        coord = self.get_coord(coord_system_id)
        return CellMgr.by_coord(coord+coord.system.dirs[side])

    def add_connection(self, cell):
        """Directly add a cell that is to be considered adjacent"""
        if cell not in self.connections:
            self.connections.append(cell)
        else:
            raise ValueError(F"Attempt to add cell {cell} to connections of {self} multiple times")


class CellMgr():
    """
    Be the representation of regions of the gamespace.

    A Cell is a representation of physical space in the game.  This can be squares
    in chess and checkers, regions like playfield etc for magic the gathering,
    hexes in terra mystica, settlers of catan, etc.
    """

    cell_parsers = dict()
    cell_xforms = dict()
    cells_by_coord = dict()
    cells_by_coord_tuple = dict()
    cells_by_name = dict()
    cells_by_uid = dict()

    def __str__(self):
        return f"{type(self).__name__}"

    def __repr__(self):
        return f"{type(self).__name__} "

    # def __getitem__(self, identifier):
    #     if isinstance(identifier, str):
    #         return

    #The following uses decorator syntax to perform processing
    #on the function but doesn't actually wrap it.
    @classmethod
    def register_cell_parser(cls, extension):
        """Register a new cell parser whose job it is to parse raw input files
        into dicts of cell configuration information"""
        def anon_reg_func(callback):
            logging.debug("registering cell parser for '%s'", extension)
            cls.cell_parsers[extension] = callback
            return callback
        return anon_reg_func

    @classmethod
    def register_cell_xform(cls, xform_name):
        """Register a new cell xform with the CellMgr.  This allows it to be
        used in cell config files to provide transformations and operations on cells.
        """
        def anon_reg_func(callback):
            logging.debug("registering cell xform for '%s'", xform_name)
            cls.cell_xforms[xform_name] = callback
            return callback
        return anon_reg_func

    @classmethod
    def load_cells(cls, cells_path, basedir="."):
        """Dispatch function for loading cells from different filetypes.
        New filetype support can be dynamically provided with the decorator
        @CellMgr.register_cell_parser"""
        return cls.cell_parsers[pathlib.Path(cells_path).suffix](cells_path, basedir=basedir)

    @staticmethod
    def create_auto_cells(parent_cell, cell_dict):
        """Automatically generate cells and map them into a coordinate system,
        attached to a parent, when given dimensions of the coordinate
        system in which to be mapped.  The coordinate system id is the tuple
         (parent_cell.name,"Local") """
        cells = list()
        logger.debug("create_auto_cells for %s", parent_cell.name)
        #safety checking
        if not all(key in cell_dict for key in AUTO_CELLS_REQUIRED_KEYS):
            raise ValueError(f"Missing one of required keys {AUTO_CELLS_REQUIRED_KEYS}")

        #Instantiate coordinate system in which the map is described in the external file.
        dims_coord_system = CoordinateSystemMgr.create_coord_system(cell_dict['dimensions']["system"], (parent_cell.name, "auto_dims", "Local"))
        dims_coords = dims_coord_system.gen_coord_set(dimensions=cell_dict['dimensions']['dims'])

        #Instantiate the coordinate system in which the map is stored.
        #This converts the originating coordinate system into the final coordinate system
        #This allows for easy layout in the config file by using a complex coordinate system
        #under the hood.
        coord_system = CoordinateSystemMgr.create_coord_system(cell_dict["cell_type"], (parent_cell.name, "Local"))
        coords = [coord_system.from_other_system(dcoord) for dcoord in dims_coords]
        CoordinateSystemMgr.delete_coord_system((parent_cell.name, "auto_dims", "Local"))

        #Generate all the cells.
        for idx, coord in enumerate(coords):
            cells.append(Cell(coord=coord, **cell_dict))

        #Register them to their parent.
        if parent_cell:
            parent_cell.add_children(cells, reflexive=True)


        return cells


    @classmethod
    def register_cells(cls, cells):
        """Register multiple cells with the CellMgr to be tracked.  Automatically
        indexes by a number of methods for easy lookup/retrieval"""
        for cell in cells:
            cls.register_cell(cell)

    @classmethod
    def register_cell_to_coord(cls, cell, coord):
        """Registers a cell by coordinate in the CellMgr"""
        cls.cells_by_coord[coord] = cell
        if coord.system.system_tuple not in cls.cells_by_coord_tuple:
            cls.cells_by_coord_tuple[coord.system.system_tuple] = list()
        cls.cells_by_coord_tuple[coord.system.system_tuple].append(cell)



    @classmethod
    def register_cell(cls, cell):
        """Register a single cell with the CellMgr to be tracked.  Automatically
        indexes by a number of methods for easy lookup/retrieval"""
        if cell.name:
            cls.cells_by_name[cell.name] = cell
        if cell.coord:
            cls.register_cell_to_coord(cell, cell.coord)
        cls.cells_by_uid[cell.uid] = cell

    @classmethod
    def unregister_cell(cls, cell):
        """Unregisters the cell by removing it from all the indexes"""
        if hasattr(cell, 'name') and cell.name in cls.cells_by_name:
            del cls.cells_by_name[cell.name]
        if hasattr(cell, 'coord') and cell.coord in cls.cells_by_coord:
            del cls.cells_by_coord[cell.coord]
        del cls.cells_by_uid[cell.uid]

    @classmethod
    def unregister_cells(cls, cells):
        """Unregisters multiple cells by removing them from all the indexes"""
        for cell in cells:
            cls.unregister_cell(cell)

    @classmethod
    def unregister_all(cls):
        """Removes/resets all tracking indexes"""
        cls.cells_by_name = dict()
        cls.cells_by_coord = dict()
        cls.cells_by_uid = dict()

    @classmethod
    def create_cell(cls, cell_dict, parent_cell=None):
        """Create an individual cell with the given properties, attach to parent
        if a parent is given, and recursively generate child cells if any exist"""
        cells = list()
        coord = None
        #Passthrough all the initialization we can for simple construction
        if "cell_type" in cell_dict:
            coord = CoordinateSystemMgr.create_coord_system(cell_dict["cell_type"],
                                                            (cell_dict["name"], "Local")
                                                            ).get_origin()

        cell = Cell(**cell_dict, coord=coord)

        #auxiliary property parsing
        # if 'attributes' in cell_dict:
        #     cell.attributes.update(cell_dict['attributes'])

        if parent_cell:
            parent_cell.add_child(cell)

        cells.append(cell)
        cells.extend(cls.create_subcells(cell, cell_dict))

        return cells

    @classmethod
    def load_seams(cls, seam_type, system_id, raw_system, integrated_system, connections):
        """Generates an integrated coordinate system with multiple distinct
        collections of cells by mapping their disparate coordinate systems into
        one integrated coordinate system.  It is given adjacent edges of cells
        within each collection and it creates transforms between the coordinate
        systems to generate the unified coordinate system.

        This relies on the coordinate systems of the cells being auto-generated
        by auto_cells and therefore, the coordinate system being named after a parent cell.
        """
        if seam_type == "auto":
            mapped_edge_offsets = dict()
            # Actual seamed coordinate system
            seamed_coord_sys = CoordinateSystemMgr.create_coord_system(integrated_system, system_id)
            # Utility cooridinate system from which to read in coordinates
            raw_coord_sys = CoordinateSystemMgr.create_coord_system(raw_system, (system_id, "raw"))
            for conn in connections:
                logger.debug("Seaming with %s", conn)

                #Retrieve super-cells/Containers and coordinate system
                cell1_coord_system = CoordinateSystemMgr.get_coord_system((conn[0][0], "Local"))
                #logger.debug("cell1_cells:{cell1_cells}")
                #cell1_coords = list((cell.coord for cell in cell1_cells))

                cell2_coord_system = CoordinateSystemMgr.get_coord_system((conn[1][0], "Local"))
                cell2_cells = cls.by_coord_id((conn[1][0], "Local"))
                #logger.debug("cell2_cells:{cell2_cells}")
                #cell2_coords = (cell.coord for cell in cell2_cells

                #Retrieve individual adjacent cells from parent containers
                c1 = cls.by_coord(cell1_coord_system.from_other_system(raw_coord_sys.coord(*(conn[0][1]))))
                c2 = cls.by_coord(cell2_coord_system.from_other_system(raw_coord_sys.coord(*(conn[1][1]))))
                #logger.debug("epc1:{c1} epc2:{c2}")

                if not seamed_coord_sys.system_tuple in cls.cells_by_coord_tuple:
                    # Subsume the coordinates into the seamed system
                    # This establishes the first coordinate system as the "root" coordinate system
                    # The others will be seamed onto this one and their properties
                    # will be translated into the context of this one
                    cell1_cells = cls.by_coord_id((conn[0][0], "Local"))
                    for cell in cell1_cells:
                        cell.assign_default_coord(seamed_coord_sys.duplicate_coord(cell.coord))
                    logger.debug("Directly subsumed cells to seed %s Coordinate System:%s",
                                 seamed_coord_sys.system_tuple, cell1_cells)
                    seamededge_idx = conn[0][2]
                else:
                    # map the local edge in the seam data to the equivalent global edge
                    mapping_offset = mapped_edge_offsets[(conn[0][0], "Local")]
                    seamededge_idx = (conn[0][2]+mapping_offset)%len(seamed_coord_sys.dirs)
                    logger.debug("EdgeDetails for %s: localedge:%s glblcnt:%s glbledge: %s",
                                 conn[0][0], conn[0][2], mapping_offset, seamededge_idx)

                # find offset cnt to add or subtract for directions from other
                # system to the "same direction" in the seamed system
                offset = seamed_coord_sys.get_mapping_offset(seamededge_idx, conn[1][2])
                mapped_edge_offsets[(conn[1][0], "Local")] = offset  # Store for later retrieval

                # Create a transform that will create equivalent vectors in the
                # seamed system from vectors in the foreign system
                vec_xform = seamed_coord_sys.make_rotation_transform(offset)
                # logger.debug("DirXForm:{vec_xform}")

                # Directly map anchor c2 cell's coordinate in the seamed coordinate system
                foreign_anchor = c2.coord  # Anchor coord in foreign system
                if not c1.get_coord(seamed_coord_sys.system_tuple):
                    raise RuntimeError((f"Endpoint 1 in {conn} does not have a"
                                        f"{seamed_coord_sys.system_tuple} coordinate"))
                c2.assign_default_coord(c1.get_coord(seamed_coord_sys.system_tuple)
                                        + seamed_coord_sys.dirs[seamededge_idx])
                new_anchor = c2.coord  # Anchor coord in seamed/global system
                #logger.debug("Directly Remapped epc2 coord {c2.coord} old default coord {foreign_anchor}")


                # Calculate new coords from xform and anchor
                for cell in cell2_cells:
                    if cell is not c2:

                        # Create direction vector from anchor
                        #logger.debug("Actual Coord : {cell.coord}")
                        coord_vec = cell.coord - foreign_anchor
                        #logger.debug("Coord Vec: {coord_vec}")
                        # Transform vector to be in terms of the seamed system
                        new_vec = vec_xform(coord_vec)
                        #logger.debug("transformed vec:{new_vec}")
                        # Apply vector to new system coordinate
                        new_coord = new_anchor + new_vec
                        logger.debug("Remapping %s to %s", cell.coord, new_coord)
                        if cls.by_coord(new_coord):
                            raise RuntimeError(F"Mapped coordinate {new_coord} from original coordinate {cell}{cell.coord} already exists")
                        cell.assign_default_coord(new_coord)

        if "explicit" in connections:
            pass

    @classmethod
    def create_subcells(cls, parent_cell, cell_dict):
        """Create a collection of cells, possibly related to a parent."""
        cells = list()

        if "cell" in cell_dict:
            cells.extend(cls.create_cell(cell_dict["cell"], parent_cell))

        if "cells" in cell_dict:
            for cell in cell_dict["cells"]:
                #parse subcells
                cells.extend(cls.create_cell(cell, parent_cell))

        if "auto_cells" in cell_dict:
            auto_cell_dict = cell_dict["auto_cells"]

            #Instantiate the auto_cells
            auto_cells = cls.create_auto_cells(parent_cell, auto_cell_dict)

            logger.debug("Preparing to xform for %s (cell cnt:%s)", cell_dict['name'], len(auto_cells))

            if "xform" in auto_cell_dict and auto_cell_dict["xform"]:
                for xform in auto_cell_dict['xform']:
                    if xform['type'] in cls.cell_xforms:
                        auto_cells = cls.cell_xforms[xform['type']](xform["data"] if "data" in xform else None, auto_cells)
                    else:
                        raise RuntimeError(F"No such xform {xform['type']} exists.  Ensure the xform has been made available to bgframework with decorator @CellMgr.register_cell_xform")

            logger.debug("Cell Summary for %s:\nNumCells:%s", cell_dict['name'], len(auto_cells))
            cells.extend(auto_cells)

        return cells

    @classmethod
    def process_cells(cls, cell_dict, basedir="."):
        """Configure cells based on cell configs fed in through a dict"""
        cells = list()

        if "imports" in cell_dict:
            for imp in cell_dict["imports"]:
                cells.extend(cls.load_cells(imp, basedir=basedir))

        cells.extend(cls.create_subcells(None, cell_dict))

        if "seams" in cell_dict:
            for seam in cell_dict["seams"]:
                cls.load_seams(**seam)

        return cells


    @classmethod
    def by_coord(cls, coord):
        """Retrieve a cell by coordinate"""
        return cls.cells_by_coord.get(coord, None)

    @classmethod
    def by_name(cls, name):
        """Retrieve a cell by name"""
        return cls.cells_by_name.get(name, None)

    @classmethod
    def by_uid(cls, uid):
        """Retrieve a cell by uid"""
        return cls.cells_by_uid.get(uid, None)

    @classmethod
    def by_coord_id(cls, idtuple):
        """Retrieve list of cells by coordinate system id"""
        return cls.cells_by_coord_tuple.get(idtuple, None)


@CellMgr.register_cell_parser('.json')
def load_cell_json(cell_path, basedir="."):
    """Parse cell file written in json"""
    import json
    file_path = pathlib.Path(basedir, cell_path)
    logging.debug("File path: %s", file_path.absolute())
    with open(file_path, "r") as json_cells:
        data = json.load(json_cells)

    return CellMgr.process_cells(data, basedir=basedir)

@CellMgr.register_cell_parser('.yml')
def load_cell_yml(cell_path, basedir="."):
    """Parse cell file written in yaml"""
    import yaml
    file_path = pathlib.Path(basedir, cell_path)
    logging.debug("File path: %s", file_path.absolute())
    with open(file_path, "r") as yaml_cells:
        data = yaml.load(yaml_cells)

    return CellMgr.process_cells(data, basedir=basedir)

@CellMgr.register_cell_xform("oddr_flat_filter")
def oddr_flat_filter(data, cells):
    """Filter out cells whose positions are marked by a '1' in the input flat
    oddr (x,y -- odd rows shifted right) representation"""
    coords = list()
    oddr = CoordinateSystemMgr.create_coord_system("oddr", "oddr_flat_filter")

    for yidx, row in enumerate(data):
        for xidx, remove in enumerate(row):
            if remove:
                coords.append(oddr.coord(x=xidx, y=yidx))
    logger.debug("filtering out cordinates: '%s'", coords)

    results = list(filter(lambda cell: oddr.from_other_system(cell.coord) not in coords, cells))
    CoordinateSystemMgr.delete_coord_system("oddr_flat_filter")
    return results

@CellMgr.register_cell_xform("evenr_flat_filter")
def evenr_flat_filter(data, cells):
    """Filter out cells whose positions are marked by a '1' in the input flat
    evenr (x,y -- even rows shifted right) representation"""
    coords = list()
    evenr = CoordinateSystemMgr.create_coord_system("evenr", "evenr_flat_filter")

    for yidx, row in enumerate(data):
        for xidx, remove in enumerate(row):
            if remove:
                coords.append(evenr.coord(x=xidx, y=yidx))
    logger.debug("filtering out cordinates: '%s'",coords)

    results = list(filter(lambda cell: evenr.from_other_system(cell.coord) not in coords, cells))
    CoordinateSystemMgr.delete_coord_system("evenr_flat_filter")
    return results

@CellMgr.register_cell_xform("square_flat_filter")
def square_flat_filter(data, cells):
    """Filter out cells whose positions are marked by a '1' in the input flat
    square (x,y) representation"""
    coords = list()
    square = CoordinateSystemMgr.create_coord_system("square", "square_flat_filter")

    for yidx, row in enumerate(data):
        for xidx, remove in enumerate(row):
            if remove:
                coords.append(square.coord(x=xidx, y=yidx))

    logger.debug("filtering out cordinates: '%s'", coords)

    results = list(filter(lambda cell: square.from_other_system(cell.coord) not in coords, cells))
    CoordinateSystemMgr.delete_coord_system("square_flat_filter")
    return results


# @Cell.register_cell_xform("hex_flat_filter")
# def cubed_flat_filter(data, cells):
#     coords = list()
#     hexsys = CoordinateSystemMgr.get_coord_system("hex")
#
#     #TODO: implement flat to coord mapping system
#     raise NotImplementedError("Need to implement the generation of hex coords from the array of 0's and 1's")
#
#     return filter(lambda cell: hexsys.from_other_system(cell.coord) not in coords, cells)

@CellMgr.register_cell_xform("auto_connect")
def auto_connect(data, cells, coord_system_id=None):
    """Automatically add explicit connections to cells that are adjacent by
    coordinates"""
    #safety check
    if not cells:
        raise ValueError(F"Cells must not be empty or null cells={cells}")

    if coord_system_id is None:
        coord_system_id = (cells[0].parent.name, "Local")
        coord_system = CoordinateSystemMgr.get_coord_system(coord_system_id)
    else:
        coord_system = CoordinateSystemMgr.get_coord_system(coord_system_id)

    for cell in cells:
        for side, direction in enumerate(coord_system.dirs):
            conn_cell = CellMgr.by_coord(cell.get_coord(coord_system_id) + direction)
            if conn_cell:
                cell.set_neighbor(coord_system_id, side, conn_cell)

    return cells
