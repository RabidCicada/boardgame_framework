from boardgame_framework.cell import CellMgr
import boardgame_framework.utils as utils
import pathlib

def test_explicit_cell_yaml():
    cellmgr = CellMgr()
    cells = cellmgr.load_cells("level1_explicit_map.yml",basedir=pathlib.Path('..','tests','data_files'))

    assert len(cells) == 11

def test_auto_cell_yaml():
    cellmgr = CellMgr()
    cells = cellmgr.load_cells("level1_auto_map.yml",basedir=pathlib.Path('..','tests','data_files'))

    #4 top level cells + 48 + 42 + 19 + 35 - the 9 xform removed coordinates
    assert len(cells) == 139

def test_explicit_cell_json():
    cellmgr = CellMgr()
    cells = cellmgr.load_cells("level1_explicit_map.json",basedir=pathlib.Path('..','tests','data_files'))

    assert len(cells)  == 2
