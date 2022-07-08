import copy
from math_formula.backends.geometry_nodes import GeometryNodesBackEnd
from math_formula.backends.type_defs import *
from math_formula.backends.main import BackEnd
from math_formula.backends import builtin_nodes
from math_formula.parser import Error
from math_formula.type_checking import TypeChecker
from math_formula import ast_defs


class Compiler():
    def __init__(self, back_end: BackEnd) -> None:
        self.operations: list[Operation] = []
        self.errors: list[Error] = []
        self.back_end: BackEnd = back_end

    def compile(self, source: str) -> bool:
        type_checker = TypeChecker(self.back_end)
        succeeded = type_checker.type_check(source)
        typed_ast = type_checker.typed_repr
        self.errors = type_checker.errors
        if not succeeded:
            return False
        statements = typed_ast.body
        for statement in statements:
            if isinstance(statement, ty_expr):
                self.compile_expr(statement)
            elif isinstance(statement, TyAssign):
                self.compile_assign(statement)
            else:
                # These are the only possibilities for now
                assert False, "Unreachable code"
            self.operations.append(Operation(OpType.END_OF_STATEMENT, None))
        return True

    def compile_assign(self, assign: TyAssign):
        raise NotImplementedError
        targets = assign.targets
        if isinstance(assign.value, ast_defs.Constant):
            # Assignment to a value, so we need to create an input
            # node.
            assert len(targets) == 1, 'No structured assignment yet'
            if (target := targets[0]) is None:
                return
            value = assign.value.value
            dtype = assign.value.type
            dtype = self.back_end.create_input(
                self.operations, target.id, value, dtype)
            self.curr_type = dtype
            return
        # Output will be some node socket, so just simple assignment
        self.compile_expr(assign.value)
        dtype = self.curr_type
        # TODO: handle functions with multiple outputs, assignment to multiple
        # inputs here
        if len(targets) != 1 or isinstance(dtype, list):
            raise NotImplementedError('Structured assignments')
        target = targets[0]
        if target is None:
            return
        self.operations.append(Operation(OpType.CREATE_VAR, target.id))
        self.curr_type = dtype

    def compile_expr(self, expr: ty_expr):
        if isinstance(expr, Const):
            self.const(expr)
        elif isinstance(expr, Var):
            self.var(expr)
        elif isinstance(expr, NodeCall):
            self.node_call(expr)
        else:
            print(expr, type(expr))
            assert False, "Unreachable code"

    def node_call(self, expr: NodeCall):
        for arg in expr.args:
            self.compile_expr(arg)
        # To add the node we need the bl_name instead.
        expr.node = copy.copy(expr.node)
        expr.node.key = builtin_nodes.nodes[expr.node.key].bl_name
        self.operations.append(Operation(OpType.CALL_BUILTIN, expr.node))

    def const(self, const: Const):
        self.operations.append(Operation(OpType.PUSH_VALUE, const.value))

    def var(self, var: Var):
        # We should only end up here when we want to 'load' a variable.
        # If the name doesn't exist yet, create a default value
        if var.needs_instantion:
            self.back_end.create_input(
                self.operations, var.id, None, var.dtype[0])
        self.operations.append(Operation(OpType.GET_VAR, var.id))


if __name__ == '__main__':
    import os
    add_on_dir = os.path.dirname(
        os.path.realpath(__file__))
    test_directory = os.path.join(add_on_dir, 'tests')
    filenames = os.listdir(test_directory)
    verbose = 3
    num_passed = 0
    tot_tests = 0
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[96m'
    ENDC = '\033[0m'
    for filename in filenames:
        tot_tests += 1
        print(f'Testing: {BOLD}{filename}{ENDC}:  ', end='')
        with open(os.path.join(test_directory, filename), 'r') as f:
            compiler = Compiler(GeometryNodesBackEnd())
            try:
                success = compiler.compile(f.read())
                print(GREEN + 'No internal errors' + ENDC)
                if verbose > 0:
                    print(
                        f'{YELLOW}Syntax errors{ENDC}' if not success else f'{BLUE}No syntax errors{ENDC}')
                if verbose > 1 and success:
                    print(compiler.errors)
                if verbose > 2:
                    print(*compiler.operations, sep='\n')
                num_passed += 1
            except NotImplementedError:
                print(RED + 'Internal errors' + ENDC)
                # if verbose > 0:
                #     print(
                #         f'{YELLOW}Syntax errors{ENDC}:' if compiler.parser.had_error else f'{BLUE}No syntax errors{ENDC}')
                # if verbose > 1 and compiler.parser.had_error:
                #     print(compiler.operations)
    print(f'Tests done: Passed: ({num_passed}/{tot_tests})')
