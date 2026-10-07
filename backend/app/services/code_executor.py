import ast
import io
import sys
import time
import math
import concurrent.futures
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

# Safe modules allowed for import
ALLOWED_MODULES = {"pandas", "pd", "numpy", "np", "math"}

# Forbidden function names and attributes
FORBIDDEN_NAMES = {
    "open", "eval", "exec", "compile", "__import__", "globals", "locals",
    "vars", "breakpoint", "exit", "quit", "getattr", "setattr", "delattr",
    "help", "input", "memoryview", "super"
}

FORBIDDEN_ATTRS = {
    "__subclasses__", "__globals__", "__code__", "__dict__",
    "__class__", "__bases__", "__mro__", "__builtins__"
}

class SecurityVisitor(ast.NodeVisitor):
    """Inspects AST nodes to enforce sandboxed execution boundaries."""
    def __init__(self):
        self.violations = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            base_mod = alias.name.split('.')[0]
            if base_mod not in ALLOWED_MODULES:
                self.violations.append(f"Disallowed import '{alias.name}'. Only pandas and numpy are permitted.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base_mod = node.module.split('.')[0]
            if base_mod not in ALLOWED_MODULES:
                self.violations.append(f"Disallowed from-import '{node.module}'. Only pandas and numpy are permitted.")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_NAMES:
                self.violations.append(f"Forbidden function call '{node.func.id}()'.")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if node.attr in FORBIDDEN_ATTRS:
            self.violations.append(f"Forbidden attribute access '{node.attr}'.")
        self.generic_visit(node)

def validate_code_safety(code_str: str) -> Tuple[bool, Optional[str]]:
    """Validates Python code against security constraints before execution."""
    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        return False, f"Syntax error in generated code: {str(e)}"
    
    visitor = SecurityVisitor()
    visitor.visit(tree)
    
    if visitor.violations:
        return False, "; ".join(visitor.violations)
    
    return True, None

def normalize_execution_value(val: Any) -> Any:
    """Normalizes pandas/numpy types into JSON-serializable Python primitives."""
    if val is None:
        return None
    if isinstance(val, (int, bool)):
        return val
    if isinstance(val, (float, np.floating)):
        if math.isnan(val) or np.isnan(val):
            return None
        if math.isinf(val):
            return "Infinity" if val > 0 else "-Infinity"
        # Round to 4 decimal places if it has fractional part
        return round(float(val), 4) if not float(val).is_integer() else int(val)
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    if isinstance(val, pd.Series):
        if len(val) == 1:
            return normalize_execution_value(val.iloc[0])
        return {str(k): normalize_execution_value(v) for k, v in val.items()}
    if isinstance(val, pd.DataFrame):
        return val.to_dict(orient="records")
    if isinstance(val, dict):
        return {str(k): normalize_execution_value(v) for k, v in val.items()}
    if isinstance(val, (list, tuple, set)):
        return [normalize_execution_value(v) for v in val]
    return str(val)

def _execute_in_sandbox(code_str: str, datasets_map: Dict[str, pd.DataFrame], primary_df: Optional[pd.DataFrame]) -> Tuple[bool, Any, Optional[str], str]:
    """Internal runner executed inside worker thread."""
    # Build deep copies of dataframes so user datasets can never be corrupted
    datasets_copies = {k: v.copy(deep=True) for k, v in datasets_map.items()}
    df_copy = primary_df.copy(deep=True) if primary_df is not None else (next(iter(datasets_copies.values())) if datasets_copies else pd.DataFrame())

    safe_builtins = {
        "abs": abs, "min": min, "max": max, "sum": sum, "len": len,
        "range": range, "round": round, "int": int, "float": float,
        "str": str, "bool": bool, "list": list, "dict": dict,
        "set": set, "tuple": tuple, "print": print, "sorted": sorted,
        "enumerate": enumerate, "zip": zip, "any": any, "all": all,
        "True": True, "False": False, "None": None, "isinstance": isinstance
    }

    env_globals = {
        "__builtins__": safe_builtins,
        "pd": pd,
        "np": np,
        "math": math,
        "datasets": datasets_copies,
        "df": df_copy
    }
    env_locals = {}

    stdout_capture = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_capture

    try:
        exec(code_str, env_globals, env_locals)
        captured_output = stdout_capture.getvalue().strip()

        # Check for explicitly assigned 'result'
        if "result" in env_locals:
            raw_result = env_locals["result"]
        elif "result" in env_globals:
            raw_result = env_globals["result"]
        elif captured_output:
            raw_result = captured_output
        else:
            raw_result = None

        normalized = normalize_execution_value(raw_result)
        return True, normalized, None, captured_output
    except Exception as e:
        err_msg = f"{type(e).__name__}: {str(e)}"
        return False, None, err_msg, stdout_capture.getvalue().strip()
    finally:
        sys.stdout = old_stdout

def execute_code(code_str: str, datasets_map: Dict[str, pd.DataFrame], primary_df: Optional[pd.DataFrame] = None, timeout_seconds: float = 4.0) -> Dict[str, Any]:
    """
    Executes Python code in a safe, isolated sandbox with strict timeouts.
    Returns:
        {
            "success": bool,
            "result": Any,
            "error": Optional[str],
            "stdout": str,
            "execution_time_ms": float
        }
    """
    start_time = time.perf_counter()

    # Step 1: AST Safety Validation
    is_safe, violation = validate_code_safety(code_str)
    if not is_safe:
        return {
            "success": False,
            "result": None,
            "error": f"Security boundary violation: {violation}",
            "stdout": "",
            "execution_time_ms": round((time.perf_counter() - start_time) * 1000, 2)
        }

    # Step 2: Thread-bounded execution to protect against infinite loops
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_execute_in_sandbox, code_str, datasets_map, primary_df)
        try:
            success, raw_result, err_msg, stdout_str = future.result(timeout=timeout_seconds)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "success": success,
                "result": raw_result,
                "error": err_msg,
                "stdout": stdout_str,
                "execution_time_ms": elapsed_ms
            }
        except concurrent.futures.TimeoutError:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "success": False,
                "result": None,
                "error": f"Execution timed out after {timeout_seconds} seconds",
                "stdout": "",
                "execution_time_ms": elapsed_ms
            }
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "success": False,
                "result": None,
                "error": f"Execution supervisor error: {str(e)}",
                "stdout": "",
                "execution_time_ms": elapsed_ms
            }
