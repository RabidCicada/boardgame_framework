from boardgame_framework.cell import Cell
import boardgame_framework.utils as utils

def test_explicit_cell_yaml():
    cells = Cell.load_cells("../tests/data_files/level1_explicit_map.yml")

    assert len(cells) == 11

def test_auto_cell_yaml():
    cells = Cell.load_cells("../tests/data_files/level1_auto_map.yml")

    #4 top level cells + 48 + 42 + 19 + 35
    assert len(cells) == 148

def test_explicit_cell_json():
    cells = Cell.load_cells("../tests/data_files/level1_explicit_map.json")

    assert len(cells)  == 11

# def test_auto_cell_json():
#     Cell.load_cells("tests/data_files/level1_auto_map.json")
