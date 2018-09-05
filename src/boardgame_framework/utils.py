import pathlib
from boardgame_framework.cell import Cell

class CellManager():
    cell_parsers = {}

    #The following uses decorator syntax to perform processing
    #on the function but doesn't actually wrap it.
    @classmethod
    def register_cell_parser(cls,extension):
        def anon_reg_func(callback):
            cls.cell_parsers[extension] = callback
            return callback
        return anon_reg_func

    @classmethod
    def load_cells(cls,cells_path):
        cls.cell_parsers[pathlib.Path(cells_path).suffix](cells_path)

    @classmethod
    def create_cell(cell_dict):

        #Passthrough all the initialization we can for simple construction
        Cell(**cell_dict)

        #auxiliary property parsing
        cell.attributes.update(cell_dict.attributes)

        for cell in cell_dict.cells:

            #parse subcells
            cls.create_cell(subcell_dict)


@CellManager.register_cell_parser('.json')
def load_cell_json(cell_path):
    import json
    with open(cell_path, "r") as json_cells:
        data = json.load(json_cells)

@CellManager.register_cell_parser('.yml')
def load_cell_yml(cell_path):
    import yaml
    with open(cell_path, "r") as yaml_cells:
        data = yaml.load(yaml_cells)
