"""
This module supports the creation and management of cells (regions of the gamespace)
in the boardgame_framework.
"""

import itertools
import pathlib
import logging
from enum import IntEnum

from .coord import CoordinateSystemMgr

AUTO_CELLS_REQUIRED_KEYS = ["cell_type", "dimensions"]

logger = logging.getLogger(__name__)


class Conn(IntEnum):
    NAME = 0
    COORD = 1
    EDGE = 2


class Cell():
    """
    Representation of regions of the gamespace.

    A Cell is a representation of physical space in the game.  This can be squares
    in chess and checkers, regions like playfield etc for magic the gathering,
    hexes in terra mystica, settlers of catan, etc.
    """

    new_uid = itertools.count()
    assign_coord_cbs = list()
    creation_cbs = list()

    def __init__(self, uid=None, name=None, attributes=None, coord=None,
                 connections=None, **kwargs):

        self.name = name
        self.uid = next(self.new_uid) if uid is None else uid

        #Structural information
        self.parent = None
        self.children = list()
        self.connections = connections
        self.neighbors = dict()

        #Coordinate System Helper Stuff
        self.coord_system_id = None
        self.coord = None
        self.coords = dict()
        self._auto_coord = None

        #General storage
        self.data = dict()

        # Anything that relies on raw variables being initialized
        if coord:
            self.assign_coord(coord)
            self.set_default_coord(coord)

        self.attributes = attributes

        if self.creation_cbs:
            for callback in self.creation_cbs:
                callback(self)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __str__(self):
        return (f"{type(self).__name__}-{self.uid}-'{self.name}'-"
                f"{len(self.children)}-COORD:{self.coord}")

    def __repr__(self):
        return (f"{type(self).__name__}-{self.uid}-'{self.name}'-"
                f"{len(self.children)}-COORD-{self.coord!r}")

    def _str_with_coords(self):
        string = str(self)
        for k,v in self.coords.items():
            string += "\n\t"+repr(v)
        return string


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

    @classmethod
    def register_assign_coord_callback(cls,cb):
        cls.assign_coord_cbs.append(cb)

    @classmethod
    def register_creation_callback(cls,cb):
        cls.creation_cbs.append(cb)

    def assign_coord(self, coord, call_cbs=True):
        """
        Add the coordinate to the Cells "known cordinates" organized by coordinate system
        Additionally register with CellMgr so that the cell is retrievable using
        coordinate or coordinate_system_id
        """
        if self.assign_coord_cbs:
            for callback in self.assign_coord_cbs:
                callback(self, coord) #TODO?!--figure out how to add to correct coordinate manager

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
        #self.children.add(cell)
        self.children.append(cell)
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

    @property
    def auto_coord(self):
        if self._auto_coord:
            return self._auto_coord
        if self.parent:
            self._auto_coord = self.coords[(self.parent.name, "auto_dims", "Local")]
        else:
            self._auto_coord = self.coords[(self.name, "Local")]
        return self._auto_coord



class CellMgr():
    """
    Be the representation of regions of the gamespace.

    A Cell is a representation of physical space in the game.  This can be squares
    in chess and checkers, regions like playfield etc for magic the gathering,
    hexes in terra mystica, settlers of catan, etc.
    """

    _cell_parsers = dict()
    _cell_xforms = dict()
    _register_coord_callbacks = list()

    def __str__(self):
        return f"{type(self).__name__}"

    def __repr__(self):
        return f"{type(self).__name__} "

    def __init__(self):
        self._cells_by_coord = dict()
        self._cells_by_coord_tuple = dict()
        self._cells_by_name = dict()
        self._cells_by_uid = dict()
        Cell.register_assign_coord_callback(self.register_coord_to_cell)
        Cell.register_creation_callback(self.register_cell)

    def print_cells_coords(self):
        print(f"Cells With Coords {len(self._cells_by_uid)}:")
        for v in self._cells_by_uid.values():
            print("**"+v._str_with_coords())

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
            logger.debug("registering cell parser for '%s'", extension)
            cls._cell_parsers[extension] = callback
            return callback
        return anon_reg_func

    @classmethod
    def register_cell_xform(cls, xform_name):
        """Register a new cell xform with the CellMgr.  This allows it to be
        used in cell config files to provide transformations and operations on cells.
        """
        def anon_reg_func(callback):
            logger.debug("registering cell xform for '%s'", xform_name)
            cls._cell_xforms[xform_name] = callback
            return callback
        return anon_reg_func

    def process_cells(self, cell_dict, basedir="."):
        """Configure cells based on cell configs fed in through a dict"""
        cells = list()

        if "imports" in cell_dict:
            for imp in cell_dict["imports"]:
                cells.extend(self.load_cells(imp, basedir=basedir))

        cells.extend(self.create_subcells(None, cell_dict))

        if "seams" in cell_dict:
            for seam in cell_dict["seams"]:
                self.load_seams(**seam)

        return cells

    def load_cells(self, cells_path, basedir="."):
        """Dispatch function for loading cells from different filetypes.
        New filetype support can be dynamically provided with the decorator
        @CellMgr.register_cell_parser"""
        return self._cell_parsers[pathlib.Path(cells_path).suffix](self, cells_path, basedir=basedir)

    def create_cell(self, cell_dict, parent_cell=None):
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
        cells.extend(self.create_subcells(cell, cell_dict))

        return cells

    def create_subcells(self, parent_cell, cell_dict):
        """Create a collection of cells, possibly related to a parent."""
        cells = list()

        if "cell" in cell_dict:
            cells.extend(self.create_cell(cell_dict["cell"], parent_cell))

        if "cells" in cell_dict:
            for cell in cell_dict["cells"]:
                #parse subcells
                cells.extend(self.create_cell(cell, parent_cell))

        if "auto_cells" in cell_dict:
            auto_cell_dict = cell_dict["auto_cells"]

            #Instantiate the auto_cells
            cells.extend(self.create_auto_cells(parent_cell, auto_cell_dict))

        return cells

    def create_auto_cells(self, parent_cell, auto_cell_dict):
        """Automatically generate cells and map them into a coordinate system,
        attached to a parent, when given dimensions of the coordinate
        system in which to be mapped.  The coordinate system id is the tuple
         (parent_cell.name,"Local") """
        auto_cells = list()
        logger.debug("create_auto_cells for %s", parent_cell.name)
        #safety checking
        if not all(key in auto_cell_dict for key in AUTO_CELLS_REQUIRED_KEYS):
            raise ValueError(f"Missing one of required keys {AUTO_CELLS_REQUIRED_KEYS}")

        #Instantiate coordinate system in which the map is described in the external file.
        dims_coord_system = CoordinateSystemMgr.create_coord_system(
            auto_cell_dict['dimensions']["system"],
            (parent_cell.name, "auto_dims", "Local"),
            )
        dims_coords = dims_coord_system.gen_coord_set(
            dimensions=auto_cell_dict['dimensions']['dims']
            )

        #Instantiate the coordinate system in which the map is stored in game memory.
        #This converts the originating coordinate system into the final coordinate system
        #This allows for easy layout in the config file but using a complex coordinate system
        #under the hood.
        coord_system = CoordinateSystemMgr.create_coord_system(
            auto_cell_dict["cell_type"],
            (parent_cell.name, "Local"),
            )
        coords = [(dcoord,coord_system.from_other_system(dcoord)) for dcoord in dims_coords]

        #CoordinateSystemMgr.delete_coord_system((parent_cell.name, "auto_dims", "Local"))

        #Generate all the cells.
        for idx, coords in enumerate(coords):
            cell = Cell(coord=coords[1], **auto_cell_dict) # Create with
            cell.assign_coord(coords[0]) # Add auto-dim coord
            auto_cells.append(cell)

        logger.debug("Preparing to xform for %s (cell cnt:%s)",
                     parent_cell.name, len(auto_cells))

        #Register them to their parent.
        if parent_cell:
            parent_cell.add_children(auto_cells, reflexive=True)

        if "xform" in auto_cell_dict and auto_cell_dict["xform"]:
            for xform in auto_cell_dict['xform']:
                if xform['type'] in self._cell_xforms:
                    auto_cells = (
                        self._cell_xforms[xform['type']](
                            self,
                            xform["data"] if "data" in xform else None,
                            auto_cells
                        )
                    )
                else:
                    raise RuntimeError(f"No such xform {xform['type']} exists."
                                       f" Ensure the xform has been made available"
                                       f" to bgframework with decorator "
                                       f"@CellMgr.register_cell_xform")

        logger.debug("Cell Summary for %s: NumCells:%s", parent_cell.name, len(auto_cells))

        return auto_cells

    def load_seams(self, seam_type, system_id, raw_system, integrated_system, connections, root_sys_id):
        """Generates an integrated cell/coordinate system from multiple distinct
        collections of cells by mapping their disparate coordinate systems into
        one integrated coordinate system.  It is given adjacent edges of cells
        within each collection and it creates transforms between the coordinate
        systems to generate the unified coordinate system.

        This relies on the coordinate systems of the cells being named after a
        parent cell (e.g ('parent_cell', 'Local')).

        The algorithm handles arbitrary clusters of cells being annealed without
        consideration for order or grouping.  It other words, it is fine if
        separate groups form islands first then get annealed into the solid whole.
        It pretty much has to due to the un-ordered nature of dicts even though they
        are provided in order in the file.

        """
        if seam_type == "auto":
            self.annealed = set() #persistent between executions on purpose.  In case of multipel seam entries in config file
            mapped_edge_offsets = dict()

            def get_next_conn(annealed, connections, root_sys_id):
                index = 0
                stopmarker = -1
                num_conns = len(connections)
                initialized = False

                #Find connection using root system
                for idx,val in  enumerate(connections):
                    if (connections[index][0][Conn.NAME], "Local") == root_sys_id:
                        logger.debug("Found root_sys_id: %s",(connections[index][0][Conn.NAME], "Local"))
                        index = idx
                        stopmarker = index
                        logger.debug("Returning %s", (0, connections[index]))
                        yield (0,connections[index])
                        index = (index + 1) % num_conns
                        initialized = True

                if initialized is not True:
                    raise RuntimeError("Couldn't find root coordinate system id.  Perhaps there is a spelling error")

                logger.debug("Beginning iteration")

                while True:
                    logger.debug("Iterating")
                    if index == stopmarker:
                        return
                    # logger.debug("tuple type:%s val:%s", type((connections[index][0][Conn.NAME], "Local")),(connections[index][0][Conn.NAME], "Local"))
                    # logger.debug("annealed type:%s  val:%s", type(annealed), annealed)
                    c1sysin = (connections[index][0][Conn.NAME], "Local") in annealed
                    c2sysin = (connections[index][1][Conn.NAME], "Local") in annealed
                    logger.debug("system: %s in-annealed: %s",(connections[index][0][Conn.NAME], "Local"),c1sysin)
                    logger.debug("system: %s in-annealed: %s",(connections[index][1][Conn.NAME], "Local"),c2sysin)

                    # valid for next connection if only one is integrated
                    if bool(c1sysin) ^ bool(c2sysin):
                        stopmarker = index # set the stopmarker so we can see if we cycle back
                        logger.debug("Returning %s", (int(c2sysin), connections[index]))
                        yield (int(c2sysin), connections[index])

                    index = (index + 1) % num_conns


            # Actual seamed coordinate system
            seamed_coord_sys = CoordinateSystemMgr.create_coord_system(integrated_system, system_id)
            logger.debug("Created seamed coordinate system %s, %s",seamed_coord_sys, seamed_coord_sys.system_tuple)
            cells = self.by_coord_id(seamed_coord_sys.system_tuple)
            # If cells exist already then
            if cells:
                raise RuntimeError(f"Seamed coord system {system_id} already exists."
                    "  Possible misconfiguration of map files")


            # Utility coordinate system from which to read in coordinates
            # Used to convert from the system format in the config file to the
            # seamed coordinate system
            raw_coord_sys = CoordinateSystemMgr.create_coord_system(raw_system, (system_id, "raw"))


            real_root_sys_id = (root_sys_id, "Local")
            logger.debug("Connecting pairs with root_sys_id: %s", real_root_sys_id)

            try:
                for idx, conn_pair in get_next_conn(self.annealed,connections,real_root_sys_id):
                    logger.debug("Seaming with %s {%s already integrated}", conn_pair, idx)
                    c1_sysid = (conn_pair[0][Conn.NAME], "Local")
                    c2_sysid = (conn_pair[1][Conn.NAME], "Local")

                    #Retrieve super-cell's coordinate system
                    cell1_coord_system = CoordinateSystemMgr.get_coord_system(c1_sysid)

                    cell2_coord_system = CoordinateSystemMgr.get_coord_system(c2_sysid)
                    cell2_cells = self.by_coord_id(c2_sysid)
                    logger.debug("cell2_cells:%s",''.join(["\n"+cell._str_with_coords() for cell in cell2_cells]))

                    #Retrieve individual adjacent cells from parent cells
                    c1 = self.by_coord(cell1_coord_system.from_other_system(
                        raw_coord_sys.coord(*(conn_pair[0][Conn.COORD]))))
                    c2 = self.by_coord(cell2_coord_system.from_other_system(
                        raw_coord_sys.coord(*(conn_pair[1][Conn.COORD]))))
                    if not c1:
                        raise RuntimeError(f"Cannot retrieve cell 1 in {cell1_coord_system} with coord {conn_pair[0][Conn.COORD]}")
                    if not c2:
                        raise RuntimeError(f"Cannot retrieve cell 2 in {cell2_coord_system} with coord {conn_pair[1][Conn.COORD]}")
                    #logger.debug("epc1:{c1} epc2:{c2}")
                    #logger.debug(CoordinateSystemMgr)

                    #logger.debug("cells for %s: %s", seamed_coord_sys.system_tuple, cells)

                    # If there's no cells in the seamed system yet...
                    if not len(self.annealed):
                        logger.debug("No Base System Yet.  Subsuming Initial System")
                        # Subsume the coordinates into the seamed system
                        # This establishes the first coordinate system as the "root" coordinate system
                        # The others will be seamed onto this one and their properties (edges, vectors etc)
                        # will be translated into the context of this one
                        cell1_cells = self.by_coord_id(c1_sysid)
                        for cell in cell1_cells:
                            cell.assign_default_coord(seamed_coord_sys.duplicate_coord(cell.coord))
                        logger.debug("Directly subsumed cells to seed %s Coordinate System: Cells -->%s",
                                     seamed_coord_sys.system_tuple, cell1_cells)
                        seamededge_idx = conn_pair[0][Conn.EDGE]
                        mapped_edge_offsets[c1_sysid] = 0  # Assign identity mapping
                        self.annealed.add(c1_sysid)
                    else: # Look up previously calculated information for c1
                        logger.debug("Known systems: %s", list(CoordinateSystemMgr.get_known_systems()))
                        logger.debug("mapped_edge_offsets: %s", mapped_edge_offsets)
                        logger.debug("Trying to map for %s",conn_pair[0][Conn.NAME])
                        # map the local edge in the seam data to the equivalent global edge
                        mapping_offset = mapped_edge_offsets[c1_sysid]
                        seamededge_idx = (conn_pair[0][Conn.EDGE]+mapping_offset)%len(seamed_coord_sys.dirs)
                        logger.debug("EdgeDetails for %s: localedge:%s offset:%s glbledge: %s",
                                     conn_pair[0][0], conn_pair[0][Conn.EDGE], mapping_offset, seamededge_idx)

                    # find offset cnt to add or subtract for directions from other
                    # system to the "same actual direction" in the seamed system
                    offset = seamed_coord_sys.get_mapping_offset(seamededge_idx, conn_pair[1][Conn.EDGE])
                    mapped_edge_offsets[c2_sysid] = offset  # Store for later retrieval
                    logger.debug("Post Set --> mapped_edge_offsets: %s", mapped_edge_offsets)

                    # Create a transform that will create equivalent vectors in the
                    # seamed system from vectors in the foreign system
                    vec_xform = seamed_coord_sys.make_rotation_transform(offset)
                    # logger.debug("DirXForm:{vec_xform}")

                    # Directly map anchor c2 cell's coordinate in the seamed coordinate system
                    anchor = c2.coord  # Anchor coord in foreign system
                    if not c1.get_coord(seamed_coord_sys.system_tuple):
                        raise RuntimeError(f"Endpoint 1 in {conn_pair} does not have a"
                                           f"{seamed_coord_sys.system_tuple} coordinate")
                    c2.assign_default_coord(c1.get_coord(seamed_coord_sys.system_tuple)
                                            + seamed_coord_sys.dirs[seamededge_idx])
                    remapped_anchor = c2.coord  # Anchor coord in seamed/global system
                    #logger.debug("Directly Remapped epc2 coord {c2.coord} "
                    #             "old default coord {anchor}")


                    # Calculate new coords from xform and anchor
                    for cell in cell2_cells:
                        if cell is not c2:

                            # Create direction vector from anchor
                            logger.debug("Anchor Coord: %s Original Coord : %s", anchor, cell.coord)
                            coord_vec = cell.coord - anchor
                            logger.debug("Coord Vec: %s", coord_vec)
                            # Transform vector to be in terms of the seamed system
                            new_vec = vec_xform(coord_vec)
                            logger.debug("rotated vec: %s", new_vec)
                            # Apply vector to new system coordinate
                            new_coord = remapped_anchor + new_vec
                            logger.debug("remapped anchor + rotated vec = %s + %s ==> %s", remapped_anchor, new_vec, new_coord)
                            # logger.debug("Remapping %s to %s", repr(cell.coord), repr(new_coord))
                            if self.by_coord(new_coord):
                                raise RuntimeError(
                                    f"Mapped coordinate {new_coord} from original "
                                    f"coordinate {cell} already exists")
                            cell.assign_default_coord(new_coord)

                    self.annealed.add(c2_sysid)
                    logger.debug("annealed-->:%s",self.annealed)
            except StopIteration:
                logger.debug("Done Iterating")

        if "explicit" in connections:
            pass

    def register_cells(self, cells):
        """Register multiple cells with the CellMgr to be tracked.  Automatically
        indexes by a number of methods for easy lookup/retrieval"""
        for cell in cells:
            self.register_cell(cell)

        #logger.error("Recorded Stats for coord from %s %s",coord.system.system_tuple,
        #             cls._stats_by_coord_tuple[coord.system.system_tuple])

    @classmethod
    def register_coord_reg_callback(cls, callback):
        """Registers a callback that is called each time a coordinate is registered with a cell"""
        cls._register_coord_callbacks.append(callback)

    def register_coord_to_cell(self, cell, coord):
        """Registers a cell by coordinate in the CellMgr"""
        #logger.debug("rc2c: %s --> %s", coord, repr(cell))

        for callback in self._register_coord_callbacks:
            callback(cell, coord)

        if coord in self._cells_by_coord.items():
            for key,val in self._cells_by_coord:
                logger.debug("coord:%s cell:%s", key, val)
            logger.error("coordalreadypresent: %s cell:%s", coord, cell)
            raise RuntimeError("Coordinate Already Registered.")
        self._cells_by_coord[coord] = cell
        if coord.system.system_tuple not in self._cells_by_coord_tuple:
            self._cells_by_coord_tuple[coord.system.system_tuple] = set()
        self._cells_by_coord_tuple[coord.system.system_tuple].add(cell)

    def register_cell(self, cell):
        """Register a single cell with the CellMgr to be tracked.  Automatically
        indexes by a number of methods for easy lookup/retrieval"""
        #logger.debug("RegCell: %s ", repr(cell))
        if cell.name:
            self._cells_by_name[cell.name] = cell
        if cell.coord:
            self.register_coord_to_cell(cell, cell.coord)
        self._cells_by_uid[cell.uid] = cell

    def unregister_cell(self, cell):
        """Unregisters the cell by removing it from all the indexes"""
        if cell is None:
            raise ValueError("Illegal cell object (None)")
        #logger.debug("deleting by uid %s", repr(cell))

        if hasattr(cell, 'name') and cell.name in self._cells_by_name:
            #logger.debug(f"deleting {cell} by name {cell.name}")
            del self._cells_by_name[cell.name]
        if hasattr(cell, 'coord') and cell.coord in self._cells_by_coord:
            #logger.debug(f"deleting {cell} by coord {cell.coord!r} ")
            del self._cells_by_coord[cell.coord]

        if cell in self._cells_by_uid:
            del self._cells_by_uid[cell.uid]

        for sysid in cell.coords.keys():
            #logger.debug(f"deleting {cell} by coordtuple {sysid}")
            self._cells_by_coord_tuple[sysid].remove(cell)

    def unregister_cells(self, cells):
        """Unregisters multiple cells by removing them from all the indexes"""
        for cell in cells:
            self.unregister_cell(cell)

    def unregister_all(self):
        """Removes/resets all tracking indexes"""
        self._cells_by_name = dict()
        self._cells_by_coord = dict()
        self._cells_by_uid = dict()
        self._cells_by_coord_tuple = dict()

    def by_coord(self, coord):
        """Retrieve a cell by coordinate"""
        return self._cells_by_coord.get(coord, None)

    def by_name(self, name):
        """Retrieve a cell by name"""
        return self._cells_by_name.get(name, None)

    def by_uid(self, uid):
        """Retrieve a cell by uid"""
        return self._cells_by_uid.get(uid, None)

    def by_coord_id(self, idtuple):
        """Retrieve list of cells by coordinate system id"""
        return self._cells_by_coord_tuple.get(idtuple, None)


@CellMgr.register_cell_parser('.json')
def load_cell_json(cellmgr, cell_path, basedir="."):
    """Parse cell file written in json"""
    import json
    file_path = pathlib.Path(basedir, cell_path)
    logger.debug("File path: %s", file_path.absolute())
    with open(file_path, "r") as json_cells:
        data = json.load(json_cells)

    return cellmgr.process_cells(data, basedir=basedir)

@CellMgr.register_cell_parser('.yml')
def load_cell_yml(cellmgr, cell_path, basedir="."):
    """Parse cell file written in yaml"""
    import ruamel.yaml as yaml
    file_path = pathlib.Path(basedir, cell_path)
    logger.debug("File path: %s", file_path.absolute())
    with open(file_path, "r") as yaml_cells:
        data = yaml.safe_load(yaml_cells)

    return cellmgr.process_cells(data, basedir=basedir)

def _flat_filter(cellmgr, data, cells, system):
    coords = list()
    ysize = len(data)#Use Size to calculate y-up axis coordinate
    for yidx, row in enumerate(data):
        for xidx, remove in enumerate(row):
            if remove:
                coords.append(system.coord(x=xidx, y=ysize-yidx-1))
    logger.debug("filtering out cordinates: '%s'", coords)

    #Split cells into keep and remove
    keep, remove = list(), list()
    for cell in cells:
        keep.append(cell) if system.from_other_system(cell.coord) not in coords else remove.append(cell)

    for cell in remove:
        cellmgr.unregister_cell(cell)

    return keep

@CellMgr.register_cell_xform("oddr_flat_filter")
def oddr_flat_filter(cellmgr, data, cells):
    """Filter out cells whose positions are marked by a '1' in the input flat
    oddr (x,y -- odd rows shifted right) representation"""
    oddr = CoordinateSystemMgr.create_coord_system("oddr", "oddr_flat_filter")

    keep = _flat_filter(cellmgr, data, cells, oddr)

    CoordinateSystemMgr.delete_coord_system("oddr_flat_filter")
    return keep

@CellMgr.register_cell_xform("evenr_flat_filter")
def evenr_flat_filter(cellmgr, data, cells):
    """Filter out cells whose positions are marked by a '1' in the input flat
    evenr (x,y -- even rows shifted right) representation"""
    evenr = CoordinateSystemMgr.create_coord_system("evenr", "evenr_flat_filter")

    keep = _flat_filter(cellmgr, data, cells, evenr)

    CoordinateSystemMgr.delete_coord_system("evenr_flat_filter")
    return keep

@CellMgr.register_cell_xform("square_flat_filter")
def square_flat_filter(cellmgr, data, cells):
    """Filter out cells whose positions are marked by a '1' in the input flat
    square (x,y) representation"""
    square = CoordinateSystemMgr.create_coord_system("square", "square_flat_filter")

    keep = _flat_filter(cellmgr, data, cells, square)

    CoordinateSystemMgr.delete_coord_system("square_flat_filter")
    return keep


# @Cell.register_cell_xform("hex_flat_filter")
# def cubed_flat_filter(data, cells):
#     coords = list()
#     hexsys = CoordinateSystemMgr.get_coord_system("hex")
#
#     #TODO: implement flat to coord mapping system
#     raise NotImplementedError(f"Need to implement the generation of hex coords"
#                               f" from the array of 0's and 1's")
#
#     return filter(lambda cell: hexsys.from_other_system(cell.coord) not in coords, cells)

@CellMgr.register_cell_xform("auto_connect")
def auto_connect(cellmgr, data, cells, coord_system_id=None):
    """Automatically add explicit connections to cells that are adjacent by
    coordinates"""
    #safety check
    if not cells:
        raise ValueError(f"Cells must not be empty or null cells={cells}")

    if coord_system_id is None:
        coord_system_id = (cells[0].parent.name, "Local")
        coord_system = CoordinateSystemMgr.get_coord_system(coord_system_id)
    else:
        coord_system = CoordinateSystemMgr.get_coord_system(coord_system_id)

    for cell in cells:
        for side, direction in enumerate(coord_system.dirs):
            conn_cell = cellmgr.by_coord(cell.get_coord(coord_system_id) + direction)
            if conn_cell:
                cell.set_neighbor(coord_system_id, side, conn_cell)

    return cells
