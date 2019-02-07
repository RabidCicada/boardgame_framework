from boardgame_framework.cell import CellMgr
import boardgame_framework.utils as utils

def test_multiroom():
    cells = CellMgr.load_cells("gloomhaven_scenario1.yml",basedir="../tests/data_files/")

    #5 top level cells + 35 + 24 + 30
    assert len(cells) == 94
