from typing import Dict, Set
from enum import Enum
from cfg import ControlFlowGraph, BasicBlock
from ast_nodes import *
from semantic import SemanticError

class CFGReturnAnalyzer:
    def __init__(self, cfg: ControlFlowGraph):
        self.cfg = cfg

    # -------------------------
    # Public API
    # -------------------------

    def function_always_returns(self) -> bool:
        """
        Returns True if every path returns a value.
        """
        entry = self.cfg.entry
        exit = self.cfg.exit

        assert entry is not None and exit is not None

        return_blocks = self._find_return_blocks()

        # DFS from entry, avoiding return blocks
        visited: Set[BasicBlock] = set()
        can_reach_exit = self._dfs_can_reach_exit(
            entry, exit, return_blocks, visited
        )

        # if exit is reachable without hitting return → bad
        return not can_reach_exit

    # -------------------------
    # Helpers
    # -------------------------

    def _find_return_blocks(self) -> Set[BasicBlock]:
        """
        Collect all blocks that contain a return statement.
        """
        result = set()
        for b in self.cfg.blocks:
            if self._is_return_block(b):
                result.add(b)
        return result

    def _is_return_block(self, block: BasicBlock) -> bool:
        if not block.statements:
            return False
        return isinstance(block.statements[-1], ReturnStmt)

    def _dfs_can_reach_exit(
        self,
        current: BasicBlock,
        exit: BasicBlock,
        return_blocks: Set[BasicBlock],
        visited: Set[BasicBlock],
    ) -> bool:

        # reached exit without hitting return
        if current == exit:
            return True

        if current in visited:
            return False

        visited.add(current)

        # stop search at return blocks
        if current in return_blocks:
            return False

        for succ in current.successors:
            if self._dfs_can_reach_exit(succ, exit, return_blocks, visited):
                return True

        return False

class CFGUnreachableAnalyzer:
    def __init__(self, cfg: ControlFlowGraph):
        self.cfg = cfg

    def reachable_blocks(self) -> Set[BasicBlock]:
        entry = self.cfg.entry
        assert entry is not None

        visited: Set[BasicBlock] = set()
        self._dfs(entry, visited)
        return visited

    def unreachable_blocks(self) -> Set[BasicBlock]:
        reachable = self.reachable_blocks()
        return set(self.cfg.blocks) - reachable

    def _dfs(self, block: BasicBlock, visited: Set[BasicBlock]):
        if block in visited:
            return
        visited.add(block)
        for succ in block.successors:
            self._dfs(succ, visited)

class CFGVarAccessHelper:
    def vars_read_in_expr(self, expr) -> set[str]:
        if isinstance(expr, VarExpr):
            return {expr.name}

        if isinstance(expr, Literal):
            return set()

        if isinstance(expr, UnaryExpr):
            return self.vars_read_in_expr(expr.right)

        if isinstance(expr, BinaryExpr):
            return (
                self.vars_read_in_expr(expr.left)
                | self.vars_read_in_expr(expr.right)
            )

        if isinstance(expr, CallExpr):
            result = set()
            for arg in expr.arguments:
                result |= self.vars_read_in_expr(arg)
            return result

        return set()

    def vars_read_in_stmt(self, stmt) -> set[str]:
        if isinstance(stmt, Assign):
            return self.vars_read_in_expr(stmt.value)

        if isinstance(stmt, VarDecl):
            if stmt.value is None:
                return set()
            return self.vars_read_in_expr(stmt.value)

        if isinstance(stmt, PrintStmt):
            return self.vars_read_in_expr(stmt.value)

        if isinstance(stmt, ReturnStmt):
            if stmt.value is None:
                return set()
            return self.vars_read_in_expr(stmt.value)

        if isinstance(stmt, IfStmt):
            return self.vars_read_in_expr(stmt.condition)

        if isinstance(stmt, WhileStmt):
            return self.vars_read_in_expr(stmt.condition)

        return set()

    def vars_written_in_stmt(self, stmt) -> set[str]:
        if isinstance(stmt, Assign):
            return {stmt.name}

        if isinstance(stmt, VarDecl) and stmt.value is not None:
            return {stmt.name}

        return set()

class CFGDefiniteAssignmentAnalyzer(CFGVarAccessHelper):
    def __init__(self, cfg: ControlFlowGraph, params):
        self.cfg = cfg
        self.params = {p.name for p in params}

        self.IN: Dict[BasicBlock, Set[str]] = {}
        self.OUT: Dict[BasicBlock, Set[str]] = {}
        self.errors: List[SemanticError] = []
    # -------------------------
    # Public API
    # -------------------------

    def analyze(self):
        """
        Compute IN/OUT sets for all blocks.
        """
        self._initialize()
        self._fixed_point()

    def is_definitely_assigned(self, block: BasicBlock, name: str) -> bool:
        return name in self.IN[block]

    # -------------------------
    # Core algorithm
    # -------------------------

    def _initialize(self):
        all_vars = self._collect_all_variables()

        for b in self.cfg.blocks:
            if b == self.cfg.entry:
                self.IN[b] = set(self.params)
            else:
                self.IN[b] = set(all_vars)
            self.OUT[b] = set()

    def _fixed_point(self):
        changed = True
        while changed:
            changed = False
            for b in self.cfg.blocks:
                new_in = self._compute_in(b)
                new_out = self._compute_out(b, new_in)

                if new_in != self.IN[b] or new_out != self.OUT[b]:
                    self.IN[b] = new_in
                    self.OUT[b] = new_out
                    changed = True

    # -------------------------
    # Helpers
    # -------------------------

    def _compute_in(self, block: BasicBlock) -> Set[str]:
        if not block.predecessors:
            return self.IN[block]

        result = self.OUT[block.predecessors[0]].copy()
        for p in block.predecessors[1:]:
            result &= self.OUT[p]
        return result

    def _compute_out(self, block: BasicBlock, in_set: Set[str]) -> Set[str]:
        assigned = self._assigned_in_block(block)
        return in_set | assigned

    def _assigned_in_block(self, block: BasicBlock) -> Set[str]:
        result = set()
        for stmt in block.statements:
            if isinstance(stmt, Assign):
                result.add(stmt.name)
            elif isinstance(stmt, VarDecl) and stmt.value is not None:
                result.add(stmt.name)
        return result

    def _collect_all_variables(self) -> Set[str]:
        result = set()
        for b in self.cfg.blocks:
            for stmt in b.statements:
                if isinstance(stmt, VarDecl):
                    result.add(stmt.name)
        return result
    # -------------------------
    # Definite assignment: use-before-assign checking
    # -------------------------

    def check_uses(self):
        """
        Must be called AFTER analyze() so IN sets are available.
        error_callback(msg: str, node: ASTNode)
        """
        for block in self.cfg.blocks:
            assigned = self.IN[block].copy()

            for stmt in block.statements:
                # check reads
                for var in self.vars_read_in_stmt(stmt):
                    if var not in assigned:
                        self.errors.append(
                            SemanticError(
                                f"Variable '{var}' may be unassigned",
                                stmt
                            )
                        )

                # apply writes
                assigned |= self.vars_written_in_stmt(stmt)

class CFGDeadStoreAnalyzer(CFGVarAccessHelper):
    def __init__(self, cfg):
        self.cfg: ControlFlowGraph = cfg
        self.IN: Dict[BasicBlock, Set[str]] = {}
        self.OUT: Dict[BasicBlock, Set[str]] = {}
        self.dead_stores: List[ASTNode] = []

    def analyze(self):
        self._initialize()
        self._fixed_point()
        self._collect_dead_stores()

    def _initialize(self):
        for b in self.cfg.blocks:
            self.IN[b] = set()
            self.OUT[b] = set()

    def _fixed_point(self):
        changed = True
        while changed:
            changed = False
            for b in reversed(self.cfg.blocks):
                new_out = set()
                for succ in b.successors:
                    new_out |= self.IN[succ]

                new_in = self._compute_in(b, new_out)

                if new_in != self.IN[b] or new_out != self.OUT[b]:
                    self.IN[b] = new_in
                    self.OUT[b] = new_out
                    changed = True

    def _compute_in(self, block, out_set):
        live = out_set.copy()

        for stmt in reversed(block.statements):
            # kill
            for var in self.vars_written_in_stmt(stmt):
                live.discard(var)

            # gen
            for var in self.vars_read_in_stmt(stmt):
                live.add(var)

        return live

    def _collect_dead_stores(self):
        for block in self.cfg.blocks:
            live = self.OUT[block].copy()

            for stmt in reversed(block.statements):
                written = self.vars_written_in_stmt(stmt)
                read = self.vars_read_in_stmt(stmt)

                for var in written:
                    if var not in live:
                        self.dead_stores.append(stmt)

                # update liveness
                live -= written
                live |= read

class ZeroState(Enum):
    ZERO = 0
    NONZERO = 1
    UNKNOWN = 2

# Abstract state: variable -> zero information
State = Dict[str, ZeroState]


class CFGZeroAnalysis(CFGVarAccessHelper):
    def __init__(self, cfg: ControlFlowGraph):
        self.cfg: ControlFlowGraph = cfg

        # block -> abstract state
        self.IN: Dict[BasicBlock, State] = {}
        self.OUT: Dict[BasicBlock, State] = {}

        self.errors: list[SemanticError] = []

    # -------------------------
    # Initialization
    # -------------------------

    def _initial_state(self) -> State:
        # empty dict means: all variables UNKNOWN
        return {}

    def _initialize(self) -> None:
        for b in self.cfg.blocks:
            self.IN[b] = self._initial_state()
            self.OUT[b] = self._initial_state()

    # -------------------------
    # Main analysis
    # -------------------------

    def analyze(self) -> None:
        self._initialize()

        changed: bool = True
        while changed:
            changed = False

            for b in self.cfg.blocks:
                in_state: State = self._compute_in(b)
                out_state: State = self._transfer_block(b, in_state)

                if in_state != self.IN[b] or out_state != self.OUT[b]:
                    self.IN[b] = in_state
                    self.OUT[b] = out_state
                    changed = True

        for b in self.cfg.blocks:
            state = dict(self.IN[b])
            for stmt in b.statements:
                self._check_stmt(stmt, state)
                self._apply_stmt(stmt, state)

    # -------------------------
    # Data-flow equations
    # -------------------------

    def _compute_in(self, block: BasicBlock) -> State:
        state: State | None = None

        for edge in block.in_edges:
            pred_state: State = dict(self.OUT[edge.src])

            if edge.cond is not None:
                assert edge.assume_true is not None
                pred_state = self.refine_on_condition(
                    edge.cond,
                    edge.assume_true,
                    pred_state
                )

            if state is None:
                state = pred_state
            else:
                state = self._join_states(state, pred_state)

        return state if state is not None else {}


    def _transfer_block(self, block: BasicBlock, state: State) -> State:
        # copy because we mutate locally
        cur: State = dict(state)

        for stmt in block.statements:
            self._apply_stmt(stmt, cur)

        return cur

    # -------------------------
    # Statement effects
    # -------------------------

    def _apply_stmt(self, stmt: Stmt, state: State) -> None:
        if isinstance(stmt, Assign):
            state[stmt.name] = self._eval_expr(stmt.value, state)

        elif isinstance(stmt, VarDecl):
            if stmt.value is not None:
                state[stmt.name] = self._eval_expr(stmt.value, state)
            else:
                state[stmt.name] = ZeroState.UNKNOWN

    def _eval_expr(self, expr: Expr, state: State) -> ZeroState:
        if isinstance(expr, Literal):
            return (
                ZeroState.ZERO
                if isinstance(expr.value, int) and expr.value == 0
                else ZeroState.NONZERO
            )

        if isinstance(expr, VarExpr):
            return state.get(expr.name, ZeroState.UNKNOWN)

        # conservative default
        return ZeroState.UNKNOWN

    # -------------------------
    # Condition refinement
    # -------------------------

    def refine_on_condition(
        self,
        cond: Expr,
        assume_true: bool,
        state: State
    ) -> State:
        new_state: State = state

        if isinstance(cond, VarExpr):
            new_state[cond.name] = (
                ZeroState.NONZERO if assume_true else ZeroState.ZERO
            )
            return new_state

        if isinstance(cond, UnaryExpr) and cond.op == "!":
            inner = cond.right
            if isinstance(inner, VarExpr):
                new_state[inner.name] = (
                    ZeroState.ZERO if assume_true else ZeroState.NONZERO
                )
                return new_state

        return state


    # -------------------------
    # State join
    # -------------------------

    def _join_states(self, a: State, b: State) -> State:
        result: State = {}

        keys = set(a.keys()) | set(b.keys())
        for k in keys:
            va: ZeroState = a.get(k, ZeroState.UNKNOWN)
            vb: ZeroState = b.get(k, ZeroState.UNKNOWN)

            if va == vb:
                result[k] = va
            else:
                result[k] = ZeroState.UNKNOWN

        return result

    # -------------------------
    # Diagnostics
    # -------------------------

    def _check_stmt(self, stmt: Stmt, state: State) -> None:
        if isinstance(stmt, Assign):
            self._check_expr(stmt.value, state)

        elif isinstance(stmt, VarDecl):
            if stmt.value is not None:
                self._check_expr(stmt.value, state)

        elif isinstance(stmt, PrintStmt):
            self._check_expr(stmt.value, state)

        elif isinstance(stmt, ReturnStmt):
            if stmt.value is not None:
                self._check_expr(stmt.value, state)

    def _check_expr(self, expr: Expr, state: State) -> None:
        if isinstance(expr, BinaryExpr):
            if expr.op == "/":
                rhs: Expr = expr.right
                if isinstance(rhs, VarExpr):
                    v: str = rhs.name
                    if state.get(v, ZeroState.UNKNOWN) != ZeroState.NONZERO:
                        self.errors.append(
                            SemanticError(
                                "Possible division by zero",
                                expr
                            )
                        )

            # recurse
            self._check_expr(expr.left, state)
            self._check_expr(expr.right, state)

        elif isinstance(expr, UnaryExpr):
            self._check_expr(expr.right, state)

        elif isinstance(expr, CallExpr):
            for arg in expr.arguments:
                self._check_expr(arg, state)