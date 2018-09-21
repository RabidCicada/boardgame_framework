import itertools
import pathlib
import logging

from .utils import CoordinateSystemMgr

auto_cells_required_keys = ["cell_type","system","dimensions"]
cell_type_coord_mapping = {"hex":"hex","square":"square","linear":"linear"}

logger = logging.getLogger(__name__)

class Cell():
    """
    Be the representation of regions of the gamespace.

    A Cell is a representation of physical space in the game.  This can be squares
    in chess and checkers, regions like playfield etc for magic the gathering,
    hexes in terra mystica, settlers of catan, etc.
    """

    new_uid = itertools.count()
    cell_parsers = dict()

    def __init__(self, cell_type=None, uid=None, name=None, attributes=None, coord=None, connections=None, **kwargs):

        self.name = name
        self.uid = next(self.new_uid) if uid is None else uid
        self.connections = connections
        self.attributes = attributes
        self.cell_type = cell_type
        self.coord_system = CoordinateSystemMgr.get_coord_system(cell_type_coord_mapping[self.cell_type]) if cell_type else None

        if coord:
            if isinstance(coord.system, type(self.coord_system)):
                self.coord = coord
            else:
                self.coord = self.coord_system.from_other_system(coord.system.system_name,coord)

    def __str__(self):
        return f"{type(self).__name__}-{self.uid}"

    def __repr__(self):
        return f"{type(self).__name__}-{self.uid}"

    #The following uses decorator syntax to perform processing
    #on the function but doesn't actually wrap it.
    @classmethod
    def register_cell_parser(cls,extension):
        def anon_reg_func(callback):
            logging.debug(F"registering cell parser for '{extension}'")
            cls.cell_parsers[extension] = callback
            return callback
        return anon_reg_func

    @classmethod
    def load_cells(cls,cells_path):
        return cls.cell_parsers[pathlib.Path(cells_path).suffix](cells_path)

    @staticmethod
    def create_auto_cells(cell_dict):
        cells = set()
        #safety checking
        if not all (key in cell_dict for key in auto_cells_required_keys):
            raise ValueError(f"Missing one of required keys {auto_cells_required_keys}")

        coord_system = CoordinateSystemMgr.get_coord_system(cell_dict["system"])

        coords = coord_system.get_coord_set(cell_dict['dimensions'])

        for idx,coord in enumerate(coords):
            cells.add(Cell(coord=coord,**cell_dict))

        return cells


    @classmethod
    def create_cell(cls,cell_dict):
        cells = list()
        #Passthrough all the initialization we can for simple construction
        cell = Cell(**cell_dict)

        #auxiliary property parsing
        if 'attributes' in cell_dict:
            cell.attributes.update(cell_dict['attributes'])

        cells.append(cell)
        cells.extend(cls.create_subcells(cell_dict))

        return cells

    @classmethod
    def create_subcells(cls,cell_dict):
        cells = list()

        if "cell" in cell_dict:
            cells.extend(cls.create_cell(cell_dict["cell"]))

        if "cells" in cell_dict:
            for cell in cell_dict["cells"]:
                #parse subcells
                cells.extend(cls.create_cell(cell))

        if "auto_cells" in cell_dict:
            #Instantiate the auto_cells
            cells.extend(cls.create_auto_cells(cell_dict["auto_cells"]))

        return cells

@Cell.register_cell_parser('.json')
def load_cell_json(cell_path):
    import json
    file_path = pathlib.Path(cell_path)
    #logging.debug(F"File path: {file_path.absolute()}")
    with open(cell_path, "r") as json_cells:
        data = json.load(json_cells)

    return Cell.create_subcells(data)

@Cell.register_cell_parser('.yml')
def load_cell_yml(cell_path):
    import yaml
    file_path = pathlib.Path(cell_path)
    #logging.debug(F"File path: {file_path.absolute()}")
    with open(cell_path, "r") as yaml_cells:
        data = yaml.load(yaml_cells)

    return Cell.create_subcells(data)
