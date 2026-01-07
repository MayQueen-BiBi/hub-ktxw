from enum import Enum, auto


class Intent(str, Enum):
    NEWS = "news"
    TOOL = "tool"
    CHAT = "chat"


class ToolIntent(Enum):
    WEATHER = auto()
    ADDRESS = auto()
    PHONE = auto()
    TRAVEL = auto()
    KNOWLEDGE = auto()
    FINANCE = auto()
    UNKNOWN = auto()


TOOL_INTENT_KEYWORDS = {
    ToolIntent.WEATHER: [
        "天气", "气温", "下雨", "下雪", "温度", "风力",
        "weather", "temperature", "rain", "snow"
    ],

    ToolIntent.ADDRESS: [
        "地址", "省", "市", "区", "街道", "解析地址",
        "address", "location", "parse"
    ],

    ToolIntent.PHONE: [
        "手机号", "电话", "号码", "归属地", "运营商",
        "phone", "mobile", "carrier"
    ],

    ToolIntent.TRAVEL: [
        "景点", "旅游", "景区", "好玩吗", "在哪里",
        "scenic", "travel", "attraction"
    ],

    ToolIntent.KNOWLEDGE: [
        "花语", "花的含义", "象征", "寓意",
        "flower", "meaning"
    ],

    ToolIntent.FINANCE: [
        "汇率", "换算", "兑换", "外币", "人民币",
        "rate", "exchange", "currency"
    ],
}


def detect_intent(text: str, use_tool: bool) -> Intent:
    """
    简单规则版 Intent 分类
    后续可以无缝替换为 LLM / 百炼模型
    """
    if not use_tool:
        return Intent.CHAT

    text = text.lower()

    news_keywords = [
        "新闻", "热点", "热搜", "头条", "douyin", "抖音",
        "体育", "比赛", "资讯", "发生了什么"
    ]

    tool_keywords = [
        "汇率", "转换", "换算", "计算", "工具", "天气", "电话", "地址", "景点"
    ]

    if any(k in text for k in news_keywords):
        return Intent.NEWS

    if any(k in text for k in tool_keywords):
        return Intent.TOOL

    return Intent.CHAT






