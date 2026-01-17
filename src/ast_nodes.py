from dataclasses import dataclass, field
from typing import List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from symbols import Type

# -----------------------------
# Position classes
# -----------------------------

@dataclass
class SourcePos:
    line: int
    column: int

@dataclass
class ASTNode:
    pos: SourcePos


@dataclass
class Expr(ASTNode):
    inferred_type: Optional["Type"] = field(default=None, init=False)


class Stmt(ASTNode):
    pass


# -----------------------------
# Program structure
# -----------------------------

@dataclass
class Program(ASTNode):
    functions: List["FunctionDef"]


@dataclass
class FunctionDef(ASTNode):
    name: str
    params: List["Param"]
    return_type: str
    body: "Block"    


@dataclass
class Param(ASTNode):
    type: str
    name: str


@dataclass
class Block(Stmt):
    statements: List["Stmt"]


# -----------------------------
# Statements
# -----------------------------

@dataclass
class VarDecl(Stmt):
    type: str
    name: str
    value: Optional["Expr"]


@dataclass
class Assign(Stmt):
    name: str
    value: "Expr"


@dataclass
class IfStmt(Stmt):
    condition: "Expr"
    then_body: "Block"
    else_body: Optional["Block"]


@dataclass
class WhileStmt(Stmt):
    condition: "Expr"
    body: "Block"


@dataclass
class ReturnStmt(Stmt):
    value: "Expr"


@dataclass
class PrintStmt(Stmt):
    value: "Expr"


# -----------------------------
# Expressions
# -----------------------------

@dataclass
class BinaryExpr(Expr):
    left: "Expr"
    op: str
    right: "Expr"


@dataclass
class UnaryExpr(Expr):
    op: str
    right: "Expr"


@dataclass
class CallExpr(Expr):
    fname: str
    arguments: List["Expr"]


@dataclass
class VarExpr(Expr):
    name: str


@dataclass
class Literal(Expr):
    value: Union[int, bool]
