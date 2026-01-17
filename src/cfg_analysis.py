# cfg_analysis.py

from typing import Set
from cfg import ControlFlowGraph, BasicBlock
from ast_nodes import ReturnStmt


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
