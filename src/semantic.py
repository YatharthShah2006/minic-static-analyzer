from typing import List

from symbols import Symbol, SymbolKind, ScopeStack, Type
from ast_nodes import *


# -------------------------
# Diagnostics
# -------------------------

class SemanticError:
    def __init__(self, message: str, node: ASTNode):
        self.message = message
        self.node = node   # ASTNode

    def __str__(self):
        return f"{self.message} at {self.node.pos.line}:{self.node.pos.column}"



# -------------------------
# Analyzer
# -------------------------

class SemanticAnalyzer:
    def __init__(self):
        self.scopes = ScopeStack()
        self.errors: List[SemanticError] = []
        self.current_function_return_type = None

    # -------------------------
    # Entry point
    # -------------------------

    def analyze(self, program: Program):

        self.scopes.push_scope()     # global scope
        self._visit_program(program)
        self.scopes.pop_scope()
        return self.errors

    # -------------------------
    # Program / Functions
    # -------------------------

    def _visit_program(self, program: Program):
        """
        Two-pass:
        1) Declare all functions in global scope
        2) Analyze function bodies
        """
        # pass 1: collect function symbols
        for fn in program.functions:
            self._declare_function(fn)

        # pass 2: analyze bodies
        for fn in program.functions:
            self._visit_function(fn)

    def _declare_function(self, node: FunctionDef):

        # redeclaration check (global scope)
        if self.scopes.lookup_current(node.name):
            self._error(f"Redeclaration of function '{node.name}'", node)
            return

        sym = Symbol(
            name = node.name,
            kind = SymbolKind.FUNC,
            type = self._map_type(node.return_type),
            decl_node = node
        )
        self.scopes.define(sym)

    def _visit_function(self, node: FunctionDef):
        self.scopes.push_scope()

        old_ret_type = self.current_function_return_type

        self.current_function_return_type = self._map_type(node.return_type)


        # define parameters
        for param in node.params:
            if self.scopes.lookup_current(param.name):
                self._error(f"Redeclaration of parameter '{param.name}'", param)
            else:
                psym = Symbol(
                    name = param.name,
                    kind = SymbolKind.PARAM,
                    type = self._map_type(param.type),
                    decl_node = param
                )
                self.scopes.define(psym)

        # visit body
        self._visit_block(node.body)

        self.current_function_return_type = old_ret_type
        self.scopes.pop_scope()

    # -------------------------
    # Blocks / Statements
    # -------------------------

    def _visit_block(self, node: Block):
        self.scopes.push_scope()
        reachable = True

        for stmt in node.statements:
            if not reachable:
                self._error("Unreachable code", stmt)
                continue

            self._visit_stmt(stmt)

            if isinstance(stmt, ReturnStmt):
                reachable = False
        
        self.scopes.pop_scope()

    def _visit_stmt(self, node: Stmt):
        """
        Dispatch based on statement kind.
        """
        # Replace these isinstance checks with your real AST classes
        if isinstance(node, VarDecl):
            self._visit_var_decl(node)
        elif isinstance(node, Assign):
            self._visit_assign(node)
        elif isinstance(node, IfStmt):
            self._visit_if(node)
        elif isinstance(node, WhileStmt):
            self._visit_while(node)
        elif isinstance(node, ReturnStmt):
            self._visit_return(node)
        elif isinstance(node, PrintStmt):
            self._visit_print(node)
        elif isinstance(node, Block):
            self._visit_block(node)
        else:
            raise RuntimeError(f"Unhandled statement type: {type(node)}")

    def _visit_var_decl(self, node: VarDecl):

        # redeclaration in same scope?
        if self.scopes.lookup_current(node.name):
            self._error(f"Redeclaration of variable '{node.name}'", node)
            sym = None
        else:
            sym = Symbol(
                name = node.name,
                kind = SymbolKind.VAR,
                type = self._map_type(node.type),
                decl_node = node
            )

            self.scopes.define(sym)

        # visit initializer if present
        if node.value is not None:
            self._visit_expr(node.value)

            if sym is not None and node.value.inferred_type != sym.type:
                self._error(
                    f"Type mismatch in initialization of '{node.name}' "
                    f"(expected {sym.type}, got {node.value.inferred_type})",
                    node
                )

    def _visit_assign(self, node: Assign):
        sym = self.scopes.lookup(node.name)
        if sym is None:
            self._error(f"Use of undeclared variable '{node.name}'", node)

        self._visit_expr(node.value)

        if sym is not None:
            if sym.type != node.value.inferred_type:
                self._error(
                    f"Type mismatch in assignment to '{node.name}' "
                    f"(expected {sym.type}, got {node.value.inferred_type})",
                    node
                )

    
    # -------------------------
    # Control-flow statements
    # -------------------------

    def _visit_if(self, node: IfStmt):

        # visit condition expression
        self._visit_expr(node.condition)

        if node.condition.inferred_type != Type.BOOL:
            self._error("Condition of if-statement must be bool", node.condition)

        # then-branch
        self._visit_block(node.then_body)

        # else-branch (if present)
        if node.else_body is not None:
            self._visit_block(node.else_body)


    def _visit_while(self, node: WhileStmt):

        # visit condition expression
        self._visit_expr(node.condition)

        if node.condition.inferred_type != Type.BOOL:
            self._error("Condition of while-statement must be bool", node.condition)
            
        # loop body
        self._visit_block(node.body)


    # -------------------------
    # Return / Print
    # -------------------------

    def _visit_return(self, node: ReturnStmt):
        if self.current_function_return_type is None:
            self._error("Return statement outside of function", node)
            return


        if node.value is not None:
            self._visit_expr(node.value)
            rt = node.value.inferred_type
        else:
            # this indicates a frontend bug, not user error
            raise RuntimeError("Parser produced ReturnStmt without value")
        
        if rt != self.current_function_return_type:
            self._error(
                f"Return type mismatch "
                f"(expected {self.current_function_return_type}, got {rt})",
                node
            )



    def _visit_print(self, node: PrintStmt):

        # print(expr) — just analyze the expression
        self._visit_expr(node.value)


    # -------------------------
    # Expressions
    # -------------------------

    def _visit_expr(self, node: Expr):
        if isinstance(node, VarExpr):
            self._visit_var_expr(node)
        elif isinstance(node, CallExpr):
            self._visit_call_expr(node)
        elif isinstance(node, BinaryExpr):
            self._visit_binary(node)
        elif isinstance(node, UnaryExpr):
            self._visit_unary(node)
        elif isinstance(node, Literal):
            self._visit_literal(node)
        else:
            pass

    
    def _visit_var_expr(self, node: VarExpr):
        sym = self.scopes.lookup(node.name)
        if sym is None:
            self._error(f"Use of undeclared variable '{node.name}'", node)
            node.inferred_type = Type.INT
            return

        node.inferred_type = sym.type

    def _visit_call_expr(self, node: CallExpr):
        sym = self.scopes.lookup(node.fname)
        if sym is None:
            self._error(f"Call to undefined function '{node.fname}'", node)
            node.inferred_type = Type.INT
        elif sym.kind != SymbolKind.FUNC:
            self._error(f"'{node.fname}' is not a function", node)
            node.inferred_type = Type.INT
        else:
            node.inferred_type = sym.type   # return type

        # visit arguments
        for arg in node.arguments:
            self._visit_expr(arg)

            
    def _visit_binary(self, node: BinaryExpr):
        self._visit_expr(node.left)
        self._visit_expr(node.right)

        lt = node.left.inferred_type
        rt = node.right.inferred_type
        op = node.op

        # arithmetic
        if op in {"+", "-", "*", "/"}:
            if lt == Type.INT and rt == Type.INT:
                node.inferred_type = Type.INT
            else:
                self._error(f"Arithmetic operator '{op}' requires int operands", node)
                node.inferred_type = Type.INT

        # relational
        elif op in {"<", ">", "<=", ">="}:
            if lt == Type.INT and rt == Type.INT:
                node.inferred_type = Type.BOOL
            else:
                self._error(f"Relational operator '{op}' requires int operands", node)
                node.inferred_type = Type.BOOL

        # equality
        elif op in {"==", "!="}:
            if lt == rt:
                node.inferred_type = Type.BOOL
            else:
                self._error(f"Equality operator '{op}' requires operands of same type", node)
                node.inferred_type = Type.BOOL

        # logical
        elif op in {"&&", "||"}:
            if lt == Type.BOOL and rt == Type.BOOL:
                node.inferred_type = Type.BOOL
            else:
                self._error(f"Logical operator '{op}' requires bool operands", node)
                node.inferred_type = Type.BOOL

        else:
            self._error(f"Unknown binary operator '{op}'", node)
            node.inferred_type = Type.INT


    def _visit_unary(self, node: UnaryExpr):
        self._visit_expr(node.right)
        t = node.right.inferred_type

        if node.op == "-" and t == Type.INT:
            node.inferred_type = Type.INT
        elif node.op == "!" and t == Type.BOOL:
            node.inferred_type = Type.BOOL
        else:
            self._error(f"Invalid operand type for '{node.op}'", node)
            node.inferred_type = Type.INT   # dummy
    
    def _visit_literal(self, node: Literal):
        if isinstance(node.value, bool):
            node.inferred_type = Type.BOOL
        else:
            node.inferred_type = Type.INT

    # -------------------------
    # Helpers
    # -------------------------

    def _error(self, message: str, node: ASTNode):
        self.errors.append(SemanticError(message, node))

    def _map_type(self, t: str) -> Type:
        if t == "int":
            return Type.INT
        elif t == "bool":
            return Type.BOOL
        else:
            raise RuntimeError(f"Unknown type {t}")