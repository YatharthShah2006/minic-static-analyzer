# lexer.py

from typing import List
from tokens import Token, TokenType, KEYWORDS


class LexerError(Exception):
    pass


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1

    # -----------------------------
    # Public API
    # -----------------------------

    def tokenize(self) -> List[Token]:
        tokens = []

        while not self._is_at_end():
            self._skip_whitespace_and_comments()

            if self._is_at_end():
                break

            token = self._next_token()
            tokens.append(token)

        tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return tokens

    # -----------------------------
    # Core scanning logic
    # -----------------------------

    def _next_token(self) -> Token:
        ch = self._peek()

        # 1. Identifiers / keywords
        if self._is_alpha(ch) or ch == "_":
            return self._scan_identifier_or_keyword()

        # 2. Numbers
        if self._is_digit(ch):
            return self._scan_number()

        # 3. Operators & delimiters
        start_line = self.line
        start_col = self.column
        
        # Handle multi-char operators first (==, !=, <=, >=, &&, ||)
        
        nt = ch + self._peek_next()

        if nt == '==':
            self._advance()
            self._advance()
            return Token(TokenType.EQEQ, "==", start_line, start_col)
        elif nt == '!=':
            self._advance()
            self._advance()
            return Token(TokenType.NEQ, "!=", start_line, start_col)
        elif nt == '<=':
            self._advance()
            self._advance()
            return Token(TokenType.LE, "<=", start_line, start_col)
        elif nt == '>=':
            self._advance()
            self._advance()
            return Token(TokenType.GE, ">=", start_line, start_col)
        elif nt == '&&':
            self._advance()
            self._advance()
            return Token(TokenType.ANDAND, "&&", start_line, start_col)
        elif nt == '||':
            self._advance()
            self._advance()
            return Token(TokenType.OROR, "||", start_line, start_col)

        # Then single-char tokens (+ - * / = < > ! ( ) { } ; ,)

        if ch == '+':
            self._advance()
            return Token(TokenType.PLUS, "+", start_line, start_col)
        elif ch == '-':
            self._advance()
            return Token(TokenType.MINUS, "-", start_line, start_col)
        elif ch == '*':
            self._advance()
            return Token(TokenType.STAR, "*", start_line, start_col)
        elif ch == '/':
            self._advance()
            return Token(TokenType.SLASH, "/", start_line, start_col)
        elif ch == '=':
            self._advance()
            return Token(TokenType.EQ, "=", start_line, start_col)
        elif ch == '<':
            self._advance()
            return Token(TokenType.LT, "<", start_line, start_col)
        elif ch == '>':
            self._advance()
            return Token(TokenType.GT, ">", start_line, start_col)
        elif ch == '!':
            self._advance()
            return Token(TokenType.NOT, "!", start_line, start_col)
        elif ch == '(':
            self._advance()
            return Token(TokenType.LPAREN, "(", start_line, start_col)
        elif ch == ')':
            self._advance()
            return Token(TokenType.RPAREN, ")", start_line, start_col)
        elif ch == '{':
            self._advance()
            return Token(TokenType.LBRACE, "{", start_line, start_col)
        elif ch == '}':
            self._advance()
            return Token(TokenType.RBRACE, "}", start_line, start_col)
        elif ch == ';':
            self._advance()
            return Token(TokenType.SEMI, ";", start_line, start_col)
        elif ch == ',':
            self._advance()
            return Token(TokenType.COMMA, ",", start_line, start_col)
                
        # 4. If nothing matched → error
        raise LexerError(
            f"Unexpected character '{ch}' at line {self.line}, column {self.column}"
        )

    # -----------------------------
    # Token scanners
    # -----------------------------

    def _scan_identifier_or_keyword(self) -> Token:
        start_line = self.line
        start_col = self.column

        # Consume letters, digits, underscores
        lexeme = self._consume_while(lambda c: self._is_alnum(c) or c == "_")

        # If lexeme in KEYWORDS → keyword token
        # Else → IDENT token
        token_type = KEYWORDS.get(lexeme, TokenType.IDENT)
        return Token(token_type, lexeme, start_line, start_col)

    def _scan_number(self) -> Token:
        start_line = self.line
        start_col = self.column

        # Consume the entire number
        num = self._consume_while(lambda c: self._is_digit(c))

        return Token(TokenType.NUMBER, int(num), start_line, start_col)

    # -----------------------------
    # Helpers for skipping
    # -----------------------------

    def _skip_whitespace_and_comments(self):
        while not self._is_at_end():
            ch = self._peek()

            # whitespace
            if ch in " \t\r\n":
                self._advance()
                continue

            # single-line comments: //
            if ch == "/" and self._peek_next() == "/":
                self._consume_while(lambda c: c != "\n" and self._is_at_end())
                continue

            break

    # -----------------------------
    # Character-level utilities
    # -----------------------------

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.pos]

    def _peek_next(self) -> str:
        if self.pos + 1 >= len(self.source):
            return "\0"
        return self.source[self.pos + 1]

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1

        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return ch

    def _is_at_end(self) -> bool:
        return self.pos >= len(self.source)

    # -----------------------------
    # Character classification
    # -----------------------------

    def _is_alpha(self, c: str) -> bool:
        return c.isalpha()

    def _is_digit(self, c: str) -> bool:
        return c.isdigit()

    def _is_alnum(self, c: str) -> bool:
        return c.isalnum()

    # -----------------------------
    # Generic consume helper
    # -----------------------------

    def _consume_while(self, predicate) -> str:
        result = ""
        while not self._is_at_end() and predicate(self._peek()):
            result += self._advance()
        return result
