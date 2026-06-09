"""
L3 baseline: China urban population distribution
Used when L1/L2 constraints don't cover a dimension
"""

BASELINE_TEMPLATE = {
    "gender": {
        "男": 0.51,
        "女": 0.49
    },
    "age_ranges": [
        {"range": [18, 25], "ratio": 0.22, "label": "18-25"},
        {"range": [26, 35], "ratio": 0.28, "label": "26-35"},
        {"range": [36, 45], "ratio": 0.25, "label": "36-45"},
        {"range": [46, 100], "ratio": 0.25, "label": "46+"}
    ],
    "education": {
        "本科": 0.18,
        "大专": 0.15,
        "高中": 0.25,
        "其他": 0.42
    },
    "income_ranges": [
        {"range": [0, 3000], "ratio": 0.15, "label": "<3k"},
        {"range": [3000, 8000], "ratio": 0.35, "label": "3-8k"},
        {"range": [8000, 15000], "ratio": 0.28, "label": "8-15k"},
        {"range": [15000, 25000], "ratio": 0.15, "label": "15-25k"},
        {"range": [25000, 1000000], "ratio": 0.07, "label": ">25k"}
    ],
    "cities": {
        "tier1": ["北京", "上海", "广州", "深圳"],
        "tier2": ["杭州", "南京", "成都", "武汉", "西安", "重庆"],
        "tier3": ["合肥", "济南", "青岛", "郑州", "长沙"]
    },
    "city_distribution": {
        "tier1": 0.15,
        "tier2": 0.35,
        "tier3": 0.50
    }
}

def get_baseline_template():
    """Return a copy of the baseline template."""
    import copy
    return copy.deepcopy(BASELINE_TEMPLATE)
