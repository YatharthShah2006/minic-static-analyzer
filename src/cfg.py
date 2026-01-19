from typing import List, Optional
from ast_nodes import *


class BasicBlock:
    def __init__(self, name: str):
        self.name = name
        self.statements: List[Stmt] = []
        self.out_edges: List["CFGEdge"] = []
        self.in_edges: List["CFGEdge"] = []

    def add_out_edge(self, edge: "CFGEdge") -> None:
        self.out_edges.append(edge)

    def add_in_edge(self, edge: "CFGEdge") -> None:
        self.in_edges.append(edge)

    # -------------------------
    # Convenience views
    # -------------------------

    @property
    def predecessors(self) -> list["BasicBlock"]:
        return [e.src for e in self.in_edges]

    @property
    def successors(self) -> list["BasicBlock"]:
        return [e.dst for e in self.out_edges]

    def __repr__(self):
        return f"<BB {self.name}>"


class ControlFlowGraph:
    def __init__(self):
        self.entry: Optional[BasicBlock] = None
        self.exit: Optional[BasicBlock] = None
        self.blocks: List[BasicBlock] = []

    def new_block(self, name: str) -> BasicBlock:
        bb = BasicBlock(name)
        self.blocks.append(bb)
        return bb

class CFGEdge:
    def __init__(
        self,
        src: BasicBlock,
        dst: BasicBlock,
        cond: Optional[Expr] = None,
        assume_true: Optional[bool] = None
    ):
        self.src = src
        self.dst = dst
        self.cond = cond
        self.assume_true = assume_true

class CFGBuilder:
    def __init__(self):
        self.cfg: Optional[ControlFlowGraph] = None
        self.block_id = 0

    # -------------------------
    # Public entry
    # -------------------------

    def build(self, body: Block) -> ControlFlowGraph:
        """
        Build CFG for a function body (Block).
        """
        self.cfg = ControlFlowGraph()
        self.block_id = 0

        entry = self._new_block("entry")
        self.cfg.entry = entry

        # function exit block
        exit_block = self._new_block("exit")
        self.cfg.exit = exit_block

        # build body starting from entry
        end = self._build_block(body, entry)

        if end is not None:
            self._connect(end, exit_block)

        return self.cfg

    # -------------------------
    # Block / Statement builders
    # -------------------------

    def _build_block(self, block: Block, current: BasicBlock) -> Optional[BasicBlock]:
        """
        Build CFG for a Block node.
        Returns the block where control ends, or None if terminated.
        """
        for stmt in block.statements:
            next_block = self._build_stmt(stmt, current)
            if next_block is None:
                return None
            current = next_block
        return current

    def _build_stmt(self, stmt: Stmt, current: BasicBlock) -> Optional[BasicBlock]:
        """
        Dispatch based on statement kind.
        """
        if isinstance(stmt, VarDecl):
            return self._build_simple(stmt, current)

        elif isinstance(stmt, Assign):
            return self._build_simple(stmt, current)

        elif isinstance(stmt, PrintStmt):
            return self._build_simple(stmt, current)

        elif isinstance(stmt, ReturnStmt):
            return self._build_return(stmt, current)

        elif isinstance(stmt, IfStmt):
            return self._build_if(stmt, current)

        elif isinstance(stmt, WhileStmt):
            return self._build_while(stmt, current)

        elif isinstance(stmt, Block):
            return self._build_block(stmt, current)

        else:
            raise RuntimeError(f"Unhandled stmt type in CFGBuilder: {type(stmt)}")

    # -------------------------
    # Concrete builders
    # -------------------------

    def _build_simple(self, stmt: Stmt, current: BasicBlock) -> BasicBlock:
        """
        For VarDecl / Assign / Print.
        Just add stmt to current block.
        """
        current.statements.append(stmt)
        return current

    def _build_return(self, stmt: ReturnStmt, current: BasicBlock) -> Optional[BasicBlock]:
        """
        Return terminates the current block.
        """
        current.statements.append(stmt)

        # connect this return directly to the function exit
        assert self.cfg is not None and self.cfg.exit is not None
        self._connect(current, self.cfg.exit)

        # no fall-through after return
        return None


    def _build_if(self, stmt: IfStmt, current: BasicBlock) -> Optional[BasicBlock]:
        # record the if statement in current block
        current.statements.append(stmt)

        assert self.cfg is not None

        # create blocks
        then_block = self._new_block("if_then")
        join_block = self._new_block("if_join")

        # connect current → then
        
        self._connect(current, then_block, cond = stmt.condition, assume_true = True)

        # build then branch
        end_then = self._build_block(stmt.then_body, then_block)

        # handle else branch
        if stmt.else_body is not None:
            else_block = self._new_block("if_else")
            self._connect(current, else_block, cond = stmt.condition, assume_true = False)

            end_else = self._build_block(stmt.else_body, else_block)

            # connect both ends to join if they fall through
            if end_then is not None:
                self._connect(end_then, join_block)
            if end_else is not None:
                self._connect(end_else, join_block)

        else:
            # no else: false path goes directly to join
            self._connect(current, join_block, cond = stmt.condition, assume_true = False)

            if end_then is not None:
                self._connect(end_then, join_block)

        return join_block


    def _build_while(self, stmt: WhileStmt, current: BasicBlock) -> Optional[BasicBlock]:
        assert self.cfg is not None

        # create blocks
        cond_block = self._new_block("while_cond")
        body_block = self._new_block("while_body")
        after_block = self._new_block("while_after")

        # jump from current to condition
        self._connect(current, cond_block)

        # record the while statement in the condition block
        cond_block.statements.append(stmt)

        # true branch → body
        self._connect(cond_block, body_block, cond = stmt.condition, assume_true = True)
        # false branch → after loop
        self._connect(cond_block, after_block, cond = stmt.condition, assume_true = False)

        # build loop body
        end_body = self._build_block(stmt.body, body_block)

        # body falls back to condition
        if end_body is not None:
            self._connect(end_body, cond_block)

        # control continues after the loop
        return after_block


    # -------------------------
    # Helpers
    # -------------------------

    def _new_block(self, prefix: str) -> BasicBlock:
        assert self.cfg is not None, "CFGBuilder used before build()"
        name = f"{prefix}_{self.block_id}"
        self.block_id += 1
        return self.cfg.new_block(name)
    
    def _connect(
        self,
        src: BasicBlock,
        dst: BasicBlock,
        cond: Expr | None = None,
        assume_true: bool | None = None,
    ) -> None:
        edge = CFGEdge(src, dst, cond, assume_true)
        src.add_out_edge(edge)
        dst.add_in_edge(edge)
