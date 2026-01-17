# MiniC Language Specification

## 1. Overview

MiniC is a small, C-inspired imperative programming language designed specifically for static analysis experiments. It supports block-structured programs with variables, control flow, and functions, while intentionally excluding low-level C features such as pointers, memory management, and user-defined data structures.

MiniC is **not** intended to be a subset of real C. Instead, it provides a clean and well-defined core language whose semantics are simple enough to analyze, yet rich enough to support meaningful control-flow and dataflow analyses.

The primary goal of the MiniC project is to implement a **static analysis framework** that reasons about programs without executing them.

---

## 2. Lexical Structure

### 2.1 Keywords

```
int, bool, if, else, while, return, print
```

### 2.2 Operators

```
+   -   *   /
==  !=  <   >   <=  >=
&&  ||  !
=
```

### 2.3 Delimiters

```
(   )   {   }   ;   ,
```

### 2.4 Identifiers

Identifiers follow the pattern:

```
[a-zA-Z_][a-zA-Z0-9_]*
```

### 2.5 Literals

- Integer literals: `0`, `1`, `42`, ...
- Boolean literals: `true`, `false`

---

## 3. Grammar

The grammar below is informal and intended for documentation purposes. It defines the syntax accepted by the MiniC front-end.

```
program     ::= function*

function    ::= type IDENT "(" params ")" block

params      ::= (param ("," param)*)?
param       ::= type IDENT

type        ::= "int" | "bool"

block       ::= "{" stmt* "}"

stmt        ::= var_decl
              | assignment
              | if_stmt
              | while_stmt
              | return_stmt
              | print_stmt
              | block

var_decl    ::= type IDENT ("=" expr)? ";"
assignment  ::= IDENT "=" expr ";"

if_stmt     ::= "if" "(" expr ")" block ("else" block)?
while_stmt  ::= "while" "(" expr ")" block

return_stmt ::= "return" expr ";"
print_stmt  ::= "print" "(" expr ")" ";"
```

---

### 3.1 Expressions

Expressions follow standard operator precedence:

```
expr        ::= logical_or

logical_or  ::= logical_and ("||" logical_and)*
logical_and ::= equality ("&&" equality)*

equality    ::= relational (("==" | "!=") relational)*
relational  ::= additive (("<" | ">" | "<=" | ">=") additive)*

additive    ::= term (("+" | "-") term)*
term        ::= factor (("*" | "/") factor)*

factor      ::= NUMBER
             | "true"
             | "false"
             | IDENT ("(" args ")")?
             | "(" expr ")"
             | "!" factor
             | "-" factor

args      ::= (expr ("," expr)*)?
```

---

## 4. Semantics

### 4.1 Variables and Scope

- Variables must be declared before they are used.
- Variables are **block-scoped**.
- Inner blocks may shadow variables from outer scopes.
- Redeclaring a variable in the same scope is a semantic error.

### 4.2 Types

- MiniC supports only two primitive types:
  - `int`
  - `bool`
- Integers are represented as 32-bit signed values, ranging from -2,147,483,648 to 2,147,483,647.
- Arithmetic overflow behavior is undefined.
- No implicit type conversions are performed.
- Operators are type-restricted:
  - Unary minus (`-`) operates on `int` and returns `int`.
  - Arithmetic operators (`+ - * /`) operate on `int` and return `int`.
  - Comparison operators (`< > <= >= == !=`) return `bool`.
  - Logical operators (`&& || !`) operate on `bool`.
- Logical operators use short-circuit evaluation:
  - For `&&`, the right operand is evaluated only if the left operand evaluates to true.
  - For `||`, the right operand is evaluated only if the left operand evaluates to false.

### 4.3 Control Flow

#### If / Else
- The condition expression is evaluated first.
- Exactly one branch is executed.
- Control flow merges after both branches.

#### While
- The loop condition is evaluated before each iteration.
- The loop body may execute zero or more times.

#### Return
- A `return` statement immediately exits the current function.
- Statements after a `return` in the same block are unreachable.

### 4.4 Empty Statements

MiniC does not support empty statements.
A standalone semicolon (`;`) is not a valid statement.

An empty block (`{}`) is allowed and represents a block with no statements.

---

## 5. Functions

- Each function has:
  - a name
  - a list of parameters
  - a return type
  - a body block
- Parameters are passed by value.
- Each function introduces a new local scope.
- The initial version of MiniC does **not** support recursion.
- The return type of a function determines the type of the expression required in every `return` statement in that function.

### 5.1 Function Call Semantics

- Function arguments are evaluated from left to right.
- Parameters are passed by value.
- A function call creates a new local environment in which:
  - parameters are bound to argument values,
  - local variables are allocated.
- Execution of the callee begins at the start of its body.
- A `return` statement immediately terminates the function and yields a value to the caller.
- Control then resumes at the statement following the call.

Calling a function with an incorrect number of arguments is a semantic error.

### 5.2 Program Entry Point

- Every MiniC program must define a function named `main`.
- Execution of the program begins by calling `main`.
- The `main` function must:
  - take no parameters,
  - return a value of type `int`.
- If `main` is missing or incorrectly defined, the program is considered invalid.

### 5.3 Return Values

- Every function in MiniC has a return type (`int` or `bool`).
- A function must return a value of its declared return type on all possible control-flow paths.
- If control reaches the end of a function without executing a `return` statement, the program is considered invalid.

---

## 6. Explicit Non-Features

MiniC intentionally excludes the following features:

- Pointers
- Arrays
- Structs or classes
- Dynamic memory allocation
- Recursion
- Floating-point types
- Strings
- Preprocessor directives
- `break` / `continue` statements
- Function overloading

These exclusions are deliberate design choices to keep the language small, deterministic, and easy to analyze.

---

## 7. Static Analysis and Semantic Checks

The MiniC analyzer performs static checks without executing programs. These checks are divided into two categories: semantic validation and control/dataflow analysis.

---

### 7.1 Semantic Checks

The analyzer enforces the following semantic rules:

#### 7.1.1 Function Calls
- A function call must refer to a declared function.
- The number of arguments in a call must match the number of parameters in the function definition.
- Each argument expression must be type-compatible with the corresponding parameter.
- (Initial version) Recursive calls are disallowed.

#### 7.1.2 Program Entry Point
- Every MiniC program must define a function named `main`.
- The `main` function must:
  - take no parameters,
  - return a value of type `int`.
- If `main` is missing or incorrectly defined, the analyzer reports an error.

#### 7.1.3 Integer Range Safety

- Integer literals are required to be within the 32-bit signed integer range [−2,147,483,648, 2,147,483,647].
- The analyzer evaluates constant expressions at analysis time and reports an error if their values exceed the valid range.
- For non-constant arithmetic expressions, the analyzer performs conservative checking and may emit warnings indicating that an expression could potentially overflow.
- The analyzer does not attempt to prove overflow-freedom for all execution paths.

#### 7.1.4 Division by Zero

- If the divisor in a division expression is statically known to be zero, the analyzer reports an error.
- If the divisor is statically known to be non-zero, no warning is issued.
- If the analyzer cannot determine whether the divisor may evaluate to zero, it emits a warning indicating a potential division-by-zero error.
- The analyzer does not attempt full path-sensitive reasoning to prove the absence of division-by-zero errors.
  
#### 7.1.5 Return Path Completeness

- The analyzer verifies that every function returns a value on all possible execution paths.
- If a function may terminate without executing a `return` statement, the analyzer reports an error.

#### 7.1.6 Return Type Checking

- The type of the expression in a `return` statement must match the
  declared return type of the enclosing function.
- A mismatch is reported as a semantic error.

---

### 7.2 Control-Flow and Dataflow Analyses

The analyzer performs the following program analyses:

#### 7.2.1 Use-before-definition
Detects variables that may be read before they are assigned a value.

#### 7.2.2 Possibly uninitialized variables
Reports variables that may remain uninitialized along some control-flow path.

#### 7.2.3 Unreachable code
Detects statements that can never be executed due to control-flow structure
(e.g., code after a `return`).

#### 7.2.4 Constant-condition detection
Finds conditionals whose conditions always evaluate to the same value.

#### 7.2.5 Dead assignments
Detects assignments whose values are never subsequently used.

---

## 8. Example Program

```c
int max(int a, int b) {
    int m;
    if (a > b) {
        m = a;
    } else {
        m = b;
    }
    return m;
}

int main() {
    int x = 3;
    int y = 5;
    print(max(x, y));
    return 0;
}
```

---

## 9. Design Philosophy

MiniC is designed to be:

- **Small but expressive** – only essential constructs are included.
- **Semantically clear** – behavior is well-defined and predictable.
- **Easy to analyze** – features are chosen to support control-flow and dataflow analysis.
- **Explicit in limitations** – what MiniC does *not* support is as important as what it does.

The focus of this project is not language completeness, but the construction of a clean,
well-structured **static analysis pipeline** over a realistic imperative core language.

