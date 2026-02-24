import os
import hashlib
import json
import re
from typing import Dict, Any
from dashscope import Generation


CONVERT_FORMULA_TO_EXPRESSION_PROMPT = """
请将给定的建模文本或公式，转换为一个“可计算的函数定义”。

⚠️ 重要规则：
1. 不要生成 Python 代码
2. 不要写 import
3. 不要写 sympy.symbols
4. 不要写赋值语句
5. 只生成一个“数学表达式字符串”
6. 表达式必须能被 sympy.sympify 解析
7. 变量名必须与参数名完全一致
8. 禁止使用任何非基础数学函数（如 Uniform、scipy 等）

输出格式必须为 JSON，结构如下：

{
    "type": "function",
    "name": "函数英文名（snake_case）",
    "description": "该模型的功能说明",
    "parameters": {
        "type": "object",
        "properties": {
            "参数名": {
                "type": "number",
                "description": "参数说明"
            }
        },
        "required": ["必填参数1", "必填参数2"]
    },
    "expression": "纯数学表达式字符串",
    "return": {
        "type": "number",
        "description": "返回值含义"
    }
}

示例：

输入：
产奶量 = 25 × (feed_quality / 100)

输出：
{
    "type": "function",
    "name": "milk_production",
    "description": "根据饲料质量计算产奶量",
    "parameters": {
        "type": "object",
        "properties": {
            "feed_quality": {
                "type": "number",
                "description": "饲料质量评分（0-100）"
            }
        },
        "required": ["feed_quality"]
    },
    "expression": "25 * (feed_quality / 100)",
    "return": {
        "type": "number",
        "description": "预测产奶量"
    }
}
"""


def extract_json_block(raw_text: str) -> Dict[str, Any]:
    """
    从大模型返回的文本中提取 JSON（支持 function tool spec 格式）
    自动处理:
    - ```json 包裹
    - 前后解释文本
    - 多个 JSON 块
    - 尾随逗号
    """

    if not raw_text or not raw_text.strip():
        return {
            "status": "error",
            "reason": "Empty response from LLM"
        }

    text = raw_text.strip()

    # -------------------------
    # 1️⃣ 去掉 markdown 包裹
    # -------------------------
    text = re.sub(r"^```json", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"^```", "", text).strip()
    text = re.sub(r"```$", "", text).strip()

    # -------------------------
    # 2️⃣ 优先直接尝试整体解析
    # -------------------------
    try:
        data = json.loads(text)
        return data
    except Exception:
        pass

    # -------------------------
    # 3️⃣ 提取第一个完整 JSON 对象
    # -------------------------
    json_candidates = re.findall(r"\{.*?\}", text, flags=re.DOTALL)

    for candidate in json_candidates:
        try:
            # 清理尾随逗号
            candidate = re.sub(r",\s*}", "}", candidate)
            candidate = re.sub(r",\s*]", "]", candidate)

            data = json.loads(candidate)

            # 判断是否是合法 tool spec
            if isinstance(data, dict) and "name" in data and "parameters" in data:
                return data

        except Exception:
            continue

    # -------------------------
    # 4️⃣ 如果还不行，尝试匹配最大 JSON 块
    # -------------------------
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        candidate = match.group(0)
        try:
            candidate = re.sub(r",\s*}", "}", candidate)
            candidate = re.sub(r",\s*]", "]", candidate)
            return json.loads(candidate)
        except Exception:
            pass

    # -------------------------
    # 5️⃣ 最终失败
    # -------------------------
    return {
        "status": "error",
        "reason": "Could not extract valid JSON",
        "raw_preview": raw_text[:300]
    }


def extract_model_function_spec(
    context: str,
    filename: str = None,
    save_dir: str = "data/model_expression"
) -> Dict:
    """
    使用千问大模型将公式文本解析成可计算函数定义（MCP Tool Spec）
    同时自动保存结果到本地 JSON 文件
    """

    if filename is not None:
        file_path = os.path.join(save_dir, f"model_func_{filename}.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": context + "\n" + CONVERT_FORMULA_TO_EXPRESSION_PROMPT
        }
    ]

    response = Generation.call(
        model="qwen-plus",
        messages=messages,
        result_format="message"
    )

    if response.status_code != 200:
        raise RuntimeError(f"Qwen error: {response}")

    content = response.output.choices[0].message.content

    # 解析 JSON
    function_json = extract_json_block(content)

    # =========================
    # 自动保存
    # =========================

    os.makedirs(save_dir, exist_ok=True)

    if not filename:
        # 用公式内容生成 hash 作为文件名
        filename = hashlib.md5(context.encode("utf-8")).hexdigest()[:10]
    file_path = os.path.join(save_dir, f"model_func_{filename}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(function_json, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Model function spec saved to: {file_path}")

    return function_json


