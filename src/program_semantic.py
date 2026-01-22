from semantic import SemanticError
from ast_nodes import Program


class ProgramSemanticChecker:
    def check(self, program: Program):
        errors = []

        mains = [fn for fn in program.functions if fn.name == "main"]

        if len(mains) == 0:
            errors.append(
                SemanticError(
                    "Missing entry function 'main'",
                    program
                )
            )
            return errors   # fatal → stop early

        for main_fn in mains:
            # Signature check (adjust if your AST differs)
            if main_fn.return_type != "int":
                errors.append(
                    SemanticError(
                        "Function 'main' must return int",
                        main_fn
                    )
                )

            if len(main_fn.params) != 0:
                errors.append(
                    SemanticError(
                        "Function 'main' must take no parameters",
                        main_fn
                    )
                )

        return errors
