from boardgame_framework.cell import CellMgr
import boardgame_framework.utils as utils
import pathlib

def test_multiroom():
    cellmgr = CellMgr()
    cells = cellmgr.load_cells("gloomhaven_scenario1.yml",basedir=pathlib.Path('..','tests','data_files','gloomhaven'))

    #5 top level cells + 35 + 24 + 30
    assert len(cells) == 94
