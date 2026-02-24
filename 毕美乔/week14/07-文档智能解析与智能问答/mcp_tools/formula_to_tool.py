import sympy as sp
from typing import Dict, Any
from expression_validator import validate_expression, ALLOWED_FUNCTIONS


class SafeExpressionExecutor:

    def __init__(self, max_ops: int = 100):
        self.max_ops = max_ops

    # ============================================
    # 核心执行函数
    # ============================================
    def execute(
        self,
        expression: str,
        parameters: Dict[str, Any],
    ) -> float:
        """
        安全执行表达式
        expression: LLM 生成的数学表达式字符串
        parameters: 传入参数字典
        """

        if not isinstance(parameters, dict):
            raise ValueError("Parameters must be dict")

        allowed_params = list(parameters.keys())

        # 1️⃣ 表达式合法性校验
        validate_expression(expression, allowed_params)

        # 2️⃣ 构建安全符号表
        local_dict = {k: sp.Symbol(k) for k in allowed_params}
        local_dict.update(ALLOWED_FUNCTIONS)

        # 3️⃣ 解析表达式（不执行 Python）
        expr = sp.sympify(expression, locals=local_dict)

        # 4️⃣ 再次控制复杂度
        if expr.count_ops() > self.max_ops:
            raise ValueError("Expression too complex")

        # 5️⃣ 代入参数
        substituted = expr.subs(parameters)

        # 6️⃣ 数值计算
        result = substituted.evalf()

        return float(result)


class FormulaTool:

    def __init__(self, spec: dict):
        self.name = spec["name"]
        self.description = spec.get("description", "")
        self.parameters = spec["parameters"]["properties"]
        self.required = spec["parameters"].get("required", [])
        self.expression = spec["expression"]

        # 构建时校验表达式
        validate_expression(
            self.expression,
            list(self.parameters.keys())
        )

        self.executor = SafeExpressionExecutor()

    def execute(self, **kwargs):
        return self.executor.execute(
            expression=self.expression,
            parameters=kwargs
        )

