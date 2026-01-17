from typing import List
from tokens import Token, TokenType
from ast_nodes import *


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # -----------------------------
    # Entry point
    # -----------------------------

    def parse(self) -> Program:
        """
        program ::= function*
        """
        functions = []
        pos = SourcePos(self._peek().line, self._peek().column)

        while not self._is_at_end():
            functions.append(self._parse_function())
        
        return Program(pos, functions)


    # -----------------------------
    # Helpers for token handling
    # -----------------------------

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _previous(self) -> Token:
        return self.tokens[self.pos - 1]

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.pos += 1
        return self._previous()

    def _check(self, ttype: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == ttype

    def _match(self, *types: TokenType) -> bool:
        """
        If current token matches any in types, consume it and return True.
        """
        if self._peek().type in types:
            self._advance()
            return True
        return False
        

    def _expect(self, ttype: TokenType, msg: str):
        """
        Consume token of type ttype, else error.
        """
        if self._peek().type == ttype:
            self._advance()
        else:
            tok = self._peek()
            raise ParseError(
                f"{msg} (expected {ttype}, got {tok.type} at {tok.line}:{tok.column})"
            )

    # -----------------------------
    # Top-level constructs
    # -----------------------------

    def _parse_function(self) -> FunctionDef:
        """
        function ::= type IDENT "(" params ")" block
        """
        
        if not self._match(TokenType.INT, TokenType.BOOL):
            tok = self._peek()
            raise ParseError(
                f"Expected function return type at {tok.line}:{tok.column}"
            )
        rtype = self._previous().value
        pos = SourcePos(self._previous().line, self._previous().column)

        self._expect(TokenType.IDENT, "Missing function name")
        fname = self._previous().value

        self._expect(TokenType.LPAREN, f"Missing '(' after function name {fname}")

        params = self._parse_params()

        self._expect(TokenType.RPAREN, f"Missing ')' for function {fname}")

        body = self._parse_block()

        return FunctionDef(pos, fname, params, rtype, body)

    def _parse_params(self) -> List[Param]:
        """
        params ::= (type IDENT ("," type IDENT)*)?
        """
        params = []

        # empty parameter list
        if self._check(TokenType.RPAREN):
            return params

        while not self._check(TokenType.RPAREN) and not self._is_at_end():
            if not (self._check(TokenType.INT) or self._check(TokenType.BOOL)):
                tok = self._peek()
                raise ParseError(
                    f"Expected parameter type at {tok.line}:{tok.column}"
                )

            ptype = self._advance().value
            pos = SourcePos(self._previous().line, self._previous().column)

            self._expect(TokenType.IDENT, "Missing parameter name")
            pname = self._previous().value

            params.append(Param(pos, ptype, pname))

            if not self._match(TokenType.COMMA):
                break

        return params

    def _parse_block(self) -> Block:
        """
        block ::= "{" statement* "}"
        """
        self._expect(TokenType.LBRACE, "Missing '{'")
        pos = SourcePos(self._previous().line, self._previous().column)
        
        statements = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            statements.append(self._parse_statement())

        self._expect(TokenType.RBRACE, "Missing '}'")

        return Block(pos, statements)


    # -----------------------------
    # Statements
    # -----------------------------

    def _parse_statement(self) -> Stmt:
        """
        statement ::= var_decl
                    | assign_stmt
                    | if_stmt
                    | while_stmt
                    | return_stmt
                    | print_stmt
                    | block
        """
        if self._check(TokenType.IF):
            return self._parse_if()
        elif self._check(TokenType.WHILE):
            return self._parse_while()
        elif self._check(TokenType.RETURN):
            return self._parse_return()
        elif self._check(TokenType.LBRACE):
            return self._parse_block()
        elif self._check(TokenType.PRINT):
            return self._parse_print()
        elif self._check(TokenType.IDENT):
            return self._parse_assign()
        elif self._check(TokenType.INT) or self._check(TokenType.BOOL):
            return self._parse_var_decl()
        else:
            tok = self._peek()
            raise ParseError(
                f"Unexpected token {tok.type} at {tok.line}:{tok.column}"
            )

    def _parse_var_decl(self) -> VarDecl:
        var_type = self._advance().value
        pos = SourcePos(self._previous().line, self._previous().column)
        
        self._expect(TokenType.IDENT, "Variable name missing")
        var_name = self._previous().value

        if self._match(TokenType.EQ):
            expr = self._parse_expr()
        else:
            expr = None
        
        self._expect(TokenType.SEMI, "Missing ';' after variable declaration")
        return VarDecl(pos, var_type, var_name, expr)

    def _parse_assign(self) -> Assign:
        var_name = self._advance().value
        pos = SourcePos(self._previous().line, self._previous().column)

        self._expect(TokenType.EQ, "Missing '=' in variable assignment")
        val = self._parse_expr()

        self._expect(TokenType.SEMI, "Missing ';' after variable assignment")
        return Assign(pos, var_name, val)

    def _parse_if(self) -> IfStmt:
        self._expect(TokenType.IF, "Expected 'if'")
        pos = SourcePos(self._previous().line, self._previous().column)

        self._expect(TokenType.LPAREN, "Missing '(' in if statement")

        expr = self._parse_expr()

        self._expect(TokenType.RPAREN, "Missing ')' in if statement")

        body = self._parse_block()

        if self._match(TokenType.ELSE):
            else_body = self._parse_block()
        else:
            else_body = None

        return IfStmt(pos, expr, body, else_body)

    def _parse_while(self) -> WhileStmt:
        self._expect(TokenType.WHILE, "Expected 'while'")
        pos = SourcePos(self._previous().line, self._previous().column)
        
        self._expect(TokenType.LPAREN, "Missing '(' in while statement")

        expr = self._parse_expr()

        self._expect(TokenType.RPAREN, "Missing ')' in while statement")

        body = self._parse_block()

        return WhileStmt(pos, expr, body)


    def _parse_return(self) -> ReturnStmt:
        self._expect(TokenType.RETURN, "Expected 'return'")
        pos = SourcePos(self._previous().line, self._previous().column)

        val = self._parse_expr()

        self._expect(TokenType.SEMI, "Missing ';' after return statement")
        return ReturnStmt(pos, val)

    def _parse_print(self) -> PrintStmt:
        self._expect(TokenType.PRINT, "Expected 'print'")
        pos = SourcePos(self._previous().line, self._previous().column)

        self._expect(TokenType.LPAREN, "Missing '(' in print statement")
        
        val = self._parse_expr()
        
        self._expect(TokenType.RPAREN, "Missing ')' in print statement")
        
        self._expect(TokenType.SEMI, "Missing ';' after print statement")
        
        return PrintStmt(pos, val)

    # -----------------------------
    # Expressions
    # -----------------------------

    def _parse_expr(self) -> Expr:
        """
        expr ::= logical_or
        """
        return self._parse_logical_or()

    def _parse_logical_or(self) -> Expr:
        left = self._parse_logical_and()
        
        while self._match(TokenType.OROR):
            op = self._previous().value
            right = self._parse_logical_and()
            left = BinaryExpr(left.pos, left, op, right)
        
        return left

    def _parse_logical_and(self) -> Expr:
        left = self._parse_equality()
        
        while self._match(TokenType.ANDAND):
            op = self._previous().value
            right = self._parse_equality()
            left = BinaryExpr(left.pos, left, op, right)
        
        return left

    def _parse_equality(self) -> Expr:
        left = self._parse_relational()
        
        while self._match(TokenType.EQEQ, TokenType.NEQ):
            op = self._previous().value
            right = self._parse_relational()
            left = BinaryExpr(left.pos, left, op, right)
        
        return left

    def _parse_relational(self) -> Expr:
        left = self._parse_additive()
        
        while self._match(TokenType.GT, TokenType.LT, TokenType.LE, TokenType.GE):
            op = self._previous().value
            right = self._parse_additive()
            left = BinaryExpr(left.pos, left, op, right)
        
        return left

    def _parse_additive(self) -> Expr:
        left = self._parse_term()
        
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._previous().value
            right = self._parse_term()
            left = BinaryExpr(left.pos, left, op, right)
        
        return left

    def _parse_term(self) -> Expr:
        left = self._parse_factor()
        
        while self._match(TokenType.STAR, TokenType.SLASH):
            op = self._previous().value
            right = self._parse_factor()
            left = BinaryExpr(left.pos, left, op, right)
        
        return left

    def _parse_factor(self) -> Expr:
        """
        factor ::= NUMBER
                 | true | false
                 | IDENT ("(" args ")")?
                 | "(" expr ")"
                 | "!" factor
                 | "-" factor
        """

        curr = self._advance()
        pos = SourcePos(self._previous().line, self._previous().column)

        if curr.type == TokenType.NUMBER:
            return Literal(pos, curr.value)
        
        elif curr.type in [TokenType.TRUE, TokenType.FALSE]:
            if curr.value == "true":
                return Literal(pos, True)
            else:
                return Literal(pos, False)
            
        elif curr.type == TokenType.IDENT:
            if self._match(TokenType.LPAREN):
                args = self._parse_args()
                self._expect(TokenType.RPAREN, "Missing ')' after function arguments")
                return CallExpr(pos, curr.value, args)
            else:
                return VarExpr(pos, curr.value)
        
        elif curr.type == TokenType.LPAREN:
            expr = self._parse_expr()
            self._expect(TokenType.RPAREN, "Matching ')' not found")

            return expr
        
        elif curr.type == TokenType.NOT:
            expr = self._parse_factor()
            return UnaryExpr(pos, "!", expr)
        
        elif curr.type == TokenType.MINUS:
            expr = self._parse_factor()
            return UnaryExpr(pos, "-", expr)
        
        else:
            raise ParseError(f"Unknown token {curr.value} of type {curr.type} in expression at position {curr.line} {curr.column}")

    def _parse_args(self) -> List[Expr]:
        args = []
        
        if self._check(TokenType.RPAREN):
            return args
        
        while True:
            args.append(self._parse_expr())
            if not self._match(TokenType.COMMA):
                break

        return args