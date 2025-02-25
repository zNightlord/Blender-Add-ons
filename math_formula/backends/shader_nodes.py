from .builtin_nodes import instances, shader_node_aliases, shader_geo_node_aliases
from .main import BackEnd
from .type_defs import *

shader_nodes: dict[str, list[str | NodeInstance]] = {
    'tex_coords': ['texture_coordinate'],
    'normal': [NodeInstance('ShaderNodeTexCoord', [], [1], [])],
    'geometry': [NodeInstance('ShaderNodeNewGeometry', [], [0, 1, 2, 3, 4, 5, 6, 7], [])],
    'position': [NodeInstance('ShaderNodeNewGeometry', [], [0], [])],
}


class ShaderNodesBackEnd(BackEnd):

    def create_input(self, operations: list[Operation], name: str, value: ValueType, dtype: DataType):
        return super().create_input(operations, name, value, dtype, input_vector=False)

    def coerce_value(self, value: ValueType, type: DataType) -> tuple[ValueType, DataType]:
        if type.value > DataType.VEC3:
            raise TypeError(
                f'Can\'t coerce type {type._name_} to a Shader Nodes value')
        if type == DataType.INT or type == DataType.BOOL:
            value = self.convert(value, type, DataType.FLOAT)
            type = DataType.FLOAT
        return value, type

    def resolve_function(self, name: str, args: list[ty_expr], functions: dict[str, list[TyFunction]]) -> tuple[Union[TyFunction, NodeInstance], list[DataType], list[str]]:
        return self._resolve_function(name, args, [shader_node_aliases, shader_geo_node_aliases], [shader_nodes, instances, functions])
