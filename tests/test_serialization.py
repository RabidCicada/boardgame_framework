from boardgame_framework.serializers.yaml import yaml
import boardgame_framework.utils as utils
from boardgame_framework.cell import CellMgr
import pathlib

def test_serialize_cell():
    CellMgr.load_cells("gloomhaven_scenario1.yml",basedir=pathlib.Path('..','tests','data_files','gloomhaven'))
    cells = cellmgr.by_coord_id("Global")

    assert len(cells) == 94

    yamloutput = yaml.dump(cells)

    results = yaml.safe_load(yamloutput)

    assert len(results) == len(cells)
