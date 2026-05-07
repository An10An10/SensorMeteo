import requests
from datetime import datetime

def get_weather_full(lat, lon, hour_index=0):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,rain,soil_temperature_6cm,wind_speed_10m,visibility,surface_pressure",
            "timezone": "auto",
            "forecast_days": 1  # Берем данные на 1 день
        }
             
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if "hourly" not in data:
            return None

        # Определяем индекс времени. 
        # Если hour_index=0, мы ищем данные на текущий час.
        if hour_index == 0:
            current_hour_str = datetime.now().strftime("%Y-%m-%dT%H:00")
            try:
                i = data["hourly"]["time"].index(current_hour_str)
            except ValueError:
                i = 0 
        else:
            i = hour_index 

        h = data["hourly"]

        return {
            "temp": round(h["temperature_2m"][i], 1),
            "hum": int(h["relative_humidity_2m"][i]),
            "dew": round(h["dew_point_2m"][i], 1),
            "app_temp": round(h["apparent_temperature"][i], 1),
            "rain": float(h["rain"][i]),
            "soil": round(h["soil_temperature_6cm"][i], 1),
            "wind": round(h["wind_speed_10m"][i], 1),
            "vis": int(h["visibility"][i]),
            "pres": int(h["surface_pressure"][i] * 0.750062) # ГПа в мм рт. ст.
        }
    except Exception as e:
        print(f"Ошибка парсинга метео: {e}")
        return None
