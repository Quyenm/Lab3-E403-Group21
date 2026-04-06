"""
weather_tools.py
Gồm 3 tools chính theo spec:
  1. get_current_weather(city)
  2. get_forecast(city, date)
  3. assess_outdoor_suitability(activity, weather_data)
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Optional

API_KEY = "166968d9b8037e6300b6fd89a1107f94"


# ============================================================
# Helper: city → lat/lon
# ============================================================
def _get_lat_lon(city: str):
    url = "http://api.openweathermap.org/geo/1.0/direct"
    res = requests.get(url, params={"q": city, "limit": 1, "appid": API_KEY}, timeout=10)
    data = res.json()
    if not data:
        return None, None, None, None
    return data[0]["lat"], data[0]["lon"], data[0]["name"], data[0]["country"]


# ============================================================
# Tool 1: get_current_weather
# ============================================================
def get_current_weather(city: str) -> str:
    """Lấy thời tiết hiện tại. Output: JSON string theo schema chuẩn."""
    try:
        lat, lon, name, country = _get_lat_lon(city)
        if lat is None:
            return json.dumps({
                "city": city, "status": "error",
                "error_code": "CITY_NOT_FOUND",
                "message": f"Could not retrieve current weather for the specified city."
            }, ensure_ascii=False)

        url = "https://api.openweathermap.org/data/2.5/weather"
        res = requests.get(url, params={
            "lat": lat, "lon": lon,
            "appid": API_KEY, "units": "metric", "lang": "vi"
        }, timeout=10)
        res.raise_for_status()
        d = res.json()

        return json.dumps({
            "city": name,
            "country": country,
            "temperature_c": d["main"]["temp"],
            "feels_like_c": d["main"]["feels_like"],
            "humidity": d["main"]["humidity"],
            "wind_speed": d["wind"]["speed"],
            "weather_main": d["weather"][0]["main"],
            "weather_description": d["weather"][0]["description"],
            "status": "success"
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "city": city, "status": "error",
            "error_code": "API_ERROR", "message": str(e)
        }, ensure_ascii=False)


# ============================================================
# Tool 2: get_forecast
# ============================================================
def get_forecast(city: str, date: str) -> str:
    """
    Dự báo thời tiết cho ngày cụ thể (YYYY-MM-DD, tối đa 5 ngày tới).
    Output: JSON string theo schema chuẩn.
    """
    try:
        # Validate date
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        today = datetime.now().date()

        if target_date < today:
            return json.dumps({
                "city": city, "date": date, "status": "error",
                "error_code": "FORECAST_NOT_AVAILABLE",
                "message": "API miễn phí không hỗ trợ dữ liệu quá khứ."
            }, ensure_ascii=False)

        if target_date > today + timedelta(days=5):
            return json.dumps({
                "city": city, "date": date, "status": "error",
                "error_code": "FORECAST_NOT_AVAILABLE",
                "message": "Chỉ hỗ trợ dự báo tối đa 5 ngày tới."
            }, ensure_ascii=False)

        lat, lon, name, country = _get_lat_lon(city)
        if lat is None:
            return json.dumps({
                "city": city, "date": date, "status": "error",
                "error_code": "CITY_NOT_FOUND",
                "message": "Forecast data is not available for the requested date."
            }, ensure_ascii=False)

        url = "https://api.openweathermap.org/data/2.5/forecast"
        res = requests.get(url, params={
            "lat": lat, "lon": lon,
            "appid": API_KEY, "units": "metric", "lang": "vi"
        }, timeout=10)
        res.raise_for_status()
        items = res.json()["list"]

        # Lọc các slot trong ngày target
        day_items = [
            i for i in items
            if datetime.fromtimestamp(i["dt"]).date() == target_date
        ]

        if not day_items:
            return json.dumps({
                "city": name, "date": date, "status": "error",
                "error_code": "FORECAST_NOT_AVAILABLE",
                "message": "Không có dữ liệu cho ngày này."
            }, ensure_ascii=False)

        temps = [i["main"]["temp"] for i in day_items]
        pops  = [i.get("pop", 0) * 100 for i in day_items]  # pop: 0–1 → %

        # Snapshot gần 12:00 nhất để lấy description
        best = min(day_items, key=lambda x: abs(datetime.fromtimestamp(x["dt"]).hour - 12))

        return json.dumps({
            "city": name,
            "country": country,
            "date": date,
            "min_temp_c": round(min(temps), 1),
            "max_temp_c": round(max(temps), 1),
            "rain_probability": round(max(pops), 1),
            "weather_summary": best["weather"][0]["description"],
            "status": "success"
        }, ensure_ascii=False)

    except ValueError:
        return json.dumps({
            "city": city, "date": date, "status": "error",
            "error_code": "INVALID_DATE",
            "message": "Định dạng ngày không hợp lệ. Dùng YYYY-MM-DD."
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "city": city, "date": date, "status": "error",
            "error_code": "API_ERROR", "message": str(e)
        }, ensure_ascii=False)


# ============================================================
# Tool 3: assess_outdoor_suitability
# ============================================================

# Rule table theo spec
_ACTIVITY_RULES = {
    "football": {
        "good":  {"rain_probability": ("<", 40), "max_temp_c": ("<=", 34)},
        "bad":   {"rain_probability": (">", 60), "max_temp_c": (">", 35)},
        "suggestion": "Chuyển sang sân trong nhà hoặc dời giờ sáng sớm."
    },
    "picnic": {
        "good":  {"rain_probability": ("<", 30), "max_temp_c": ("<=", 32)},
        "bad":   {"rain_probability": (">", 40), "max_temp_c": (">", 33)},
        "suggestion": "Dời lịch hoặc chuyển sang indoor cafe."
    },
    "beach": {
        "good":  {"rain_probability": ("<", 30), "max_temp_c": ("<=", 34)},
        "bad":   {"rain_probability": (">", 40), "wind_speed": (">", 7)},
        "suggestion": "Chuyển sang hoạt động indoor hoặc dời ngày khác."
    },
    "running": {
        "good":  {"rain_probability": ("<", 40), "max_temp_c": ("<=", 30)},
        "bad":   {"rain_probability": (">", 60), "max_temp_c": (">", 32)},
        "suggestion": "Chạy sáng sớm hoặc chọn indoor gym."
    },
}

SUPPORTED_ACTIVITIES = list(_ACTIVITY_RULES.keys())


def _evaluate(weather: dict, conditions: dict) -> int:
    """Đếm số điều kiện thỏa mãn."""
    count = 0
    ops = {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
           ">": lambda a, b: a > b, ">=": lambda a, b: a >= b}
    for key, (op, threshold) in conditions.items():
        val = weather.get(key)
        if val is not None and ops[op](val, threshold):
            count += 1
    return count


def assess_outdoor_suitability(activity: str, weather_data: str) -> str:
    """
    Đánh giá mức độ phù hợp của hoạt động ngoài trời.
    Args:
        activity    : tên hoạt động (football / picnic / beach / running)
        weather_data: JSON string từ get_current_weather hoặc get_forecast
    Returns:
        JSON string với suitable, score, reason, suggestion.
    """
    try:
        activity_key = activity.lower().strip()

        if activity_key not in _ACTIVITY_RULES:
            return json.dumps({
                "activity": activity, "status": "error",
                "error_code": "INVALID_ACTIVITY",
                "message": f"Unsupported activity type. Supported: {SUPPORTED_ACTIVITIES}"
            }, ensure_ascii=False)

        # Parse weather_data (có thể là string JSON hoặc dict)
        if isinstance(weather_data, str):
            weather = json.loads(weather_data)
        else:
            weather = weather_data

        if weather.get("status") == "error":
            return json.dumps({
                "activity": activity, "status": "error",
                "error_code": "INVALID_WEATHER_DATA",
                "message": "Dữ liệu thời tiết không hợp lệ hoặc bị lỗi."
            }, ensure_ascii=False)

        rules = _ACTIVITY_RULES[activity_key]
        good_hits = _evaluate(weather, rules["good"])
        bad_hits  = _evaluate(weather, rules["bad"])

        total_good = len(rules["good"])
        total_bad  = len(rules["bad"])

        # Score 1–10
        score = round(10 * good_hits / total_good) if total_good else 5
        score = max(1, score - bad_hits * 2)  # trừ điểm nếu có điều kiện xấu

        suitable = score >= 6

        # Reason
        rain = weather.get("rain_probability", weather.get("pop", 0))
        temp = weather.get("max_temp_c", weather.get("temperature_c", "N/A"))

        if suitable:
            reason = f"Điều kiện thời tiết phù hợp. Nhiệt độ {temp}°C, xác suất mưa {rain}%."
        else:
            reason = f"Điều kiện không thuận lợi. Nhiệt độ {temp}°C, xác suất mưa {rain}%."

        return json.dumps({
            "activity": activity_key,
            "city": weather.get("city", ""),
            "suitable": suitable,
            "score": score,
            "reason": reason,
            "suggestion": rules["suggestion"] if not suitable else "Thời tiết tốt, hãy tận hưởng!",
            "status": "success"
        }, ensure_ascii=False)

    except json.JSONDecodeError:
        return json.dumps({
            "activity": activity, "status": "error",
            "error_code": "INVALID_WEATHER_DATA",
            "message": "weather_data không phải JSON hợp lệ."
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "activity": activity, "status": "error",
            "error_code": "UNKNOWN_ERROR", "message": str(e)
        }, ensure_ascii=False)


# ============================================================
# Tool definitions cho ReActAgent
# ============================================================
WEATHER_TOOLS = [
    {
        "name": "get_current_weather",
        "description": (
            "Lấy thời tiết hiện tại của một thành phố. "
            "Dùng khi user hỏi hiện tại, hôm nay, bây giờ. "
            "Cú pháp: get_current_weather(Hanoi)"
        ),
        "func": lambda args: get_current_weather(args.strip().strip("'\"")),
    },
    {
        "name": "get_forecast",
        "description": (
            "Dự báo thời tiết cho một ngày cụ thể (tối đa 5 ngày tới)."
            "Dùng khi user hỏi ngày mai, cuối tuần, hoặc ngày cụ thể. "
            "Cú pháp: get_forecast(Hanoi, 2026-04-08)"
        ),
        "func": lambda args: _call_forecast(args),
    },
    {
        "name": "assess_outdoor_suitability",
        "description": (
            "Đánh giá thời tiết có phù hợp cho hoạt động ngoài trời không. "
            "Hỗ trợ: football, picnic, beach, running. "
            "Phải có weather data từ get_current_weather hoặc get_forecast trước. "
            "Cú pháp: assess_outdoor_suitability(football, <json_weather_data>)"
        ),
        "func": lambda args: _call_assess(args),
    },
]


def _call_forecast(args: str) -> str:
    """Parse 'City, YYYY-MM-DD' và gọi get_forecast."""
    parts = [p.strip().strip("'\"") for p in args.split(",", 1)]
    if len(parts) != 2:
        return json.dumps({
            "status": "error", "error_code": "INVALID_ARGS",
            "message": "Cú pháp: get_forecast(city, YYYY-MM-DD)"
        }, ensure_ascii=False)
    return get_forecast(parts[0], parts[1])


def _call_assess(args: str) -> str:
    """Parse 'activity, {json}' và gọi assess_outdoor_suitability."""
    idx = args.find(",")
    if idx == -1:
        return json.dumps({
            "status": "error", "error_code": "INVALID_ARGS",
            "message": "Cú pháp: assess_outdoor_suitability(activity, weather_json)"
        }, ensure_ascii=False)
    activity = args[:idx].strip().strip("'\"")
    weather_json = args[idx+1:].strip()
    return assess_outdoor_suitability(activity, weather_json)