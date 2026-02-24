import sympy as sp
from sympy.core.function import AppliedUndef
from typing import List


# ===============================
# 可允许函数白名单
# ===============================

ALLOWED_FUNCTIONS = {
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "exp": sp.exp,
    "log": sp.log,
    "sqrt": sp.sqrt,
    "Abs": sp.Abs,
}


# ===============================
# 主校验函数
# ===============================

def validate_expression(expression: str, allowed_params: List[str]) -> None:
    """
    校验表达式是否合法。
    若非法，抛出 ValueError
    """

    if not expression or not isinstance(expression, str):
        raise ValueError("Expression must be non-empty string")

    # 禁止危险字符
    forbidden_tokens = ["__", "import", "exec", "eval", "lambda", "open"]
    for token in forbidden_tokens:
        if token in expression:
            raise ValueError(f"Forbidden token detected: {token}")

    try:
        expr = sp.sympify(expression, locals=ALLOWED_FUNCTIONS)
    except Exception as e:
        raise ValueError(f"Invalid sympy expression: {e}")

    # ===============================
    # 检查变量是否都在参数列表中
    # ===============================

    expr_symbols = {str(s) for s in expr.free_symbols}
    param_set = set(allowed_params)

    illegal_vars = expr_symbols - param_set
    if illegal_vars:
        raise ValueError(f"Expression contains undefined variables: {illegal_vars}")

    # ===============================
    # 检查函数是否在白名单
    # ===============================

    for node in sp.preorder_traversal(expr):
        if isinstance(node, AppliedUndef):
            raise ValueError(f"Undefined function used: {node}")

        if node.func.__name__ not in ALLOWED_FUNCTIONS and isinstance(node, sp.Function):
            if node.func not in ALLOWED_FUNCTIONS.values():
                raise ValueError(f"Illegal function used: {node.func}")

    # ===============================
    # 控制复杂度
    # ===============================

    if expr.count_ops() > 50:
        raise ValueError("Expression too complex")

    # 通过校验
    return
