# symbols.py

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ast_nodes import ASTNode
# ---------------------------
# Kinds of symbols
# ---------------------------

class SymbolKind(Enum):
    VAR = auto()
    FUNC = auto()
    PARAM = auto()


# ---------------------------
# Types in the language
# ---------------------------

class Type(Enum):
    INT = auto()
    BOOL = auto()


# ---------------------------
# Symbol
# ---------------------------

@dataclass
class Symbol:
    """
    Represents a named entity in the program:
    variable, function, or parameter.
    """
    name: str
    kind: SymbolKind
    type: Type
    decl_node: "ASTNode"   # reference to declaration AST node


# ---------------------------
# Scope
# ---------------------------

class Scope:
    """
    A single lexical scope.
    Holds a mapping from names to symbols
    and a link to the parent scope.
    """

    def __init__(self, parent: Optional["Scope"] = None):
        self.parent: Optional["Scope"] = parent
        self.symbols: Dict[str, Symbol] = {}

    # ----- definition -----

    def define(self, sym: Symbol) -> None:
        """
        Define a symbol in the current scope.
        Assumes redeclaration checks are done by caller.
        """
        self.symbols[sym.name] = sym

    # ----- lookup -----

    def lookup_current(self, name: str) -> Optional[Symbol]:
        """
        Look up a name only in this scope.
        """
        return self.symbols.get(name)

    def lookup(self, name: str) -> Optional[Symbol]:
        """
        Look up a name in this scope and all parent scopes.
        """
        scope = self
        while scope is not None:
            sym = scope.symbols.get(name)
            if sym is not None:
                return sym
            scope = scope.parent
        return None


# ---------------------------
# Scope stack helper
# ---------------------------

class ScopeStack:
    """
    Manages a stack of scopes for semantic analysis.
    """

    def __init__(self):
        self.current: Optional[Scope] = None

    # ----- scope control -----

    def push_scope(self) -> None:
        """
        Create a new scope on top of the stack.
        """
        self.current = Scope(parent=self.current)

    def pop_scope(self) -> None:
        """
        Pop the current scope.
        """
        if self.current is None:
            raise RuntimeError("No scope to pop")
        self.current = self.current.parent

    # ----- symbol ops -----

    def define(self, sym: Symbol) -> None:
        if self.current is None:
            raise RuntimeError("No active scope")
        self.current.define(sym)

    def lookup(self, name: str) -> Optional[Symbol]:
        if self.current is None:
            return None
        return self.current.lookup(name)

    def lookup_current(self, name: str) -> Optional[Symbol]:
        if self.current is None:
            return None
        return self.current.lookup_current(name)
