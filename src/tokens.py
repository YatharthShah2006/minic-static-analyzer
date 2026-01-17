from enum import Enum, auto
from dataclasses import dataclass
from typing import Any

class TokenType(Enum):
    # Keywords
    INT = auto()
    BOOL = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    RETURN = auto()
    PRINT = auto()
    TRUE = auto()
    FALSE = auto()

    # Identifiers & literals
    IDENT = auto()
    NUMBER = auto()

    # Operators
    PLUS = auto()      # +
    MINUS = auto()     # -
    STAR = auto()      # *
    SLASH = auto()     # /

    EQ = auto()        # =
    EQEQ = auto()      # ==
    NEQ = auto()       # !=
    LT = auto()        # <
    GT = auto()        # >
    LE = auto()        # <=
    GE = auto()        # >=

    ANDAND = auto()    # &&
    OROR = auto()     # ||
    NOT = auto()      # !

    # Delimiters
    LPAREN = auto()   # (
    RPAREN = auto()   # )
    LBRACE = auto()   # {
    RBRACE = auto()   # }
    SEMI = auto()     # ;
    COMMA = auto()    # ,

    # End of file
    EOF = auto()

@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int

KEYWORDS = {
    "int": TokenType.INT,
    "bool": TokenType.BOOL,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "return": TokenType.RETURN,
    "print": TokenType.PRINT,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
}