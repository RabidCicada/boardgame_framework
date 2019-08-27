import ruamel.yaml
import io
from boardgame_framework.cell import CellMgr, Cell
from boardgame_framework.coord import CoordinateSystem, CoordinateSystemMgr, RectCoord, CubedCoord, HexCoord, HexCoordinateSystem, RectCoordinateSystem


class MyYAML(ruamel.yaml.YAML):
    def dump(self, data, stream=None, **kw):
        inefficient = False
        if stream is None:
            inefficient = True
            stream = io.StringIO()
        ruamel.yaml.YAML.dump(self, data, stream, **kw)
        if inefficient:
            return stream.getvalue()

yaml = MyYAML(typ='safe')

def represent_cell(representer, cell):
    return representer.represent_mapping('!cell', cell.__dict__)

def construct_cell(constructor, node):
    #print("node.value:{}".node.value)
    mapping = constructor.construct_mapping(node)
    return Cell(**mapping)

def represent_cubed_coord(representer, coord):
    return representer.represent_mapping('!CubedCoord', coord.__dict__)

def construct_cubed_coord(constructor, node):
    #print("node.value:{}".node.value)
    mapping = constructor.construct_mapping(node)
    return CubedCoord(**mapping)

def represent_hex_coord(representer, coord):
    return representer.represent_mapping('!HexCoord', coord.__dict__)

def construct_hex_coord(constructor, node):
    #print("node.value:{}".node.value)
    mapping = constructor.construct_mapping(node)
    return HexCoord(**mapping)

def represent_rect_coord(representer, coord):
    return representer.represent_mapping('!RectCoord', coord.__dict__)

def construct_rect_coord(constructor, node):
    #print("node.value:{}".node.value)
    mapping = constructor.construct_mapping(node)
    return RectCoord(**mapping)

def represent_c_sys_mgr(representer, csysmgr):
    return representer.represent_mapping('!csysmgr', csysmgr.__dict__)

def construct_c_sys_mgr(constructor, node):
    #print("node.value:{}".node.value)
    mapping = constructor.construct_mapping(node)
    return CoordinateSystemMgr(**mapping)

def represent_cell_mgr(representer, cmgr):
    return representer.represent_mapping('!cellmgr', cmgr.__dict__)

def construct_cell_mgr(constructor, node):
    #print("node.value:{}".node.value)
    mapping = constructor.construct_mapping(node)
    return CellMgr(**mapping)

def represent_hex_cs(representer, csys):
    return representer.represent_mapping('!hexcs', csys.__dict__)

def construct_hex_cs(constructor, node):
    #print("node.value:{}".format(node.value))
    mapping = constructor.construct_mapping(node)
    #print("mapping:{}".format(mapping))
    return HexCoordinateSystem(**mapping)

def represent_rect_cs(representer, csys):
    return representer.represent_mapping('!rectcs', csys.__dict__)

def construct_rect_cs(constructor, node):
    #print("node.value:{}".node.value)
    mapping = constructor.construct_mapping(node)
    return RectCoordinateSystem(**mapping)

def represent_cs(representer, csys):
    return representer.represent_mapping('!cs', csys.__dict__)

def construct_cs(constructor, node):
    #print("node.value:{}".node.value)
    mapping = constructor.construct_mapping(node)
    return CoordinateSystem(**mapping)


yaml.representer.add_representer(Cell,represent_cell)
yaml.constructor.add_constructor('!cell',construct_cell)
yaml.representer.add_representer(CubedCoord,represent_cubed_coord)
yaml.constructor.add_constructor('!CubedCoord',construct_cubed_coord)
yaml.representer.add_representer(HexCoord,represent_cell)
yaml.constructor.add_constructor('!HexCoord',represent_hex_coord)
yaml.representer.add_representer(RectCoord,represent_rect_coord)
yaml.constructor.add_constructor('!RectCoord',construct_rect_coord)
yaml.representer.add_representer(CoordinateSystemMgr,represent_c_sys_mgr)
yaml.constructor.add_constructor('!csysmgr',construct_c_sys_mgr)
yaml.representer.add_representer(CellMgr,represent_cell_mgr)
yaml.constructor.add_constructor('!cellmgr',construct_cell_mgr)
yaml.representer.add_representer(HexCoordinateSystem,represent_hex_cs)
yaml.constructor.add_constructor('!hexcs',construct_hex_cs)
yaml.representer.add_representer(RectCoordinateSystem,represent_rect_cs)
yaml.constructor.add_constructor('!rectcs',construct_rect_cs)
yaml.representer.add_representer(CoordinateSystem,represent_cs)
yaml.constructor.add_constructor('!cs',construct_cs)
