import itertools
import pathlib
import logging

from .utils import CoordinateSystemMgr

auto_cells_required_keys = ["cell_type","coord_type","dimmensions"]
cell_type_coord_mapping = {"hex":"cubed","square":"rect","linear":"linear"}

class Cell():
    """
    Be the representation of regions of the gamespace.

    A Cell is a representation of physical space in the game.  This can be squares
    in chess and checkers, regions like playfield etc for magic the gathering,
    hexes in terra mystica, settlers of catan, etc.
    """

    new_uid = itertools.count()
    cell_parsers = dict()

    def __init__(self, cell_type, uid=None, name=None, attributes=None, coord=None, **kwargs):

        self.name = name
        self.uid = next(new_uid) if uid is None else uid
        self.connections = set()
        self.attributes = attributes
        self.cell_type = cell_type
        self.coord_system = cell_type_coord_mapping[self.cell_type]

        if coord:
            if isinstance(coord.system, CoordinateSystemMgr.get_coord_system(self.coord_system)):
                self.coord = coord
            else:
                self.coord = self.coord_system.from_other_system(coord.system.shortname,coord)

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
        cls.cell_parsers[pathlib.Path(cells_path).suffix](cells_path)

    @staticmethod
    def create_auto_cells(cell_dict):
        cells = set()
        #safety checking
        if not all (key in cell_dict for key in auto_cells_required_keys):
            raise ValueError(f"Missing one of required keys {auto_cells_required_keys}")

        coord_system = CoordinateSystem.get_coord_system(cell_dict["coord_type"])

        coords = coord_system.get_coord_set(dimensions)

        for idx,coord in enumerate(coords):
            cells.add(Cell(cell_type=cell_dict["cell_type"],coord=coord, attributes=cell_dict["attributes"]))


    @classmethod
    def create_cell(cls,cell_dict):
        #Passthrough all the initialization we can for simple construction
        cell=Cell(**cell_dict)

        #auxiliary property parsing
        cell.attributes.update(cell_dict.attributes)

        if "cell" in cell_dict:
            create_cell(cell_dict["cell"])

        if "cells" in cell_dict:
            for cell in cell_dict["cells"]:
                #parse subcells
                create_cell(cell)

        if "auto_cells" in cell_dict:
            #Instantiate the auto_cells
            create_auto_cells(cell_dict["auto_cells"])



@Cell.register_cell_parser('.json')
def load_cell_json(cell_path):
    import json
    file_path = pathlib.Path(cell_path)
    logging.debug(F"File path: {file_path.absolute()}")
    with open(cell_path, "r") as json_cells:
        data = json.load(json_cells)

@Cell.register_cell_parser('.yml')
def load_cell_yml(cell_path):
    import yaml
    file_path = pathlib.Path(cell_path)
    logging.debug(F"File path: {file_path.absolute()}")
    with open(cell_path, "r") as yaml_cells:
        data = yaml.load(yaml_cells)
