from boardgame_framework.serializers.yaml import yaml
import boardgame_framework.utils as utils
from boardgame_framework.cell import CellMgr
import pathlib
import logging

@CellMgr.register_coord_reg_callback
def coordinate_reg_callback(cell, coord):
    #logging.debug("coordinate %s registered for system %s", coord, coord.system.system_tuple)
    pass

def test_serialize_cell():
    cellmgr = CellMgr()
    cells = cellmgr.load_cells("gloomhaven_scenario1.yml",basedir=pathlib.Path('..','tests','data_files','gloomhaven'))

    assert len(cells) == 94 #The 5 top level rooms + their contained cells

    cells = cellmgr.by_coord_id("Global")

    assert len(cells) == 91 #3 top level rooms don't have coordinate systems (The ones containing auto_cells)

    yamloutput = yaml.dump(cells)

    cellmgr.unregister_all()

    results = yaml.load(yamloutput)

    #Verify we get same number of cells as what went in.
    assert len(results) == len(cells)
