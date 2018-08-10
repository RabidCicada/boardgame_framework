import pathlib

class CellManager():
    cell_parsers = {}

    @classmethod
    def register_map_parser(callback,extension):
        cell_parsers[extension] = callback

    @classmethod
    def load_cells(cells_path):
        map_parsers[pathlib.Path(cells_path).suffix()](cells_path)


def load_cell_json(cell_path):
    import json
    with open(cell_path, "r") as json_cells:
        data = json.load(json_cells)

def load_cell_yml(cell_path):
    import yaml
    with open(cell_path, "r") as yaml_cells:
        data = yaml.load(yaml_cells)


def create_cell(cell_dict):
    #auxiliary propery parsing
    cell.attributes.__dict__.update(cell_dict.attributes)

    for cells in cell_dict:

        #parse subcells
        create_cell(subcell_dict):
