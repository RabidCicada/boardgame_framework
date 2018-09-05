import boardgame_framework.cell as cell
import boardgame_framework.utils as utils

def test_cell():
    CMgr = utils.CellManager()
    CMgr.load_cells("./data_files/level1map.json")
