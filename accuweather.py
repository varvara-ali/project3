import json
import requests
from config import Config
from pprint import pprint
import logging
logging.basicConfig(level=logging.DEBUG)
urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.CRITICAL)

class WeatherManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, use_file_cache = True):
        self.location_key_dict = dict()
        self.weather_dict = dict()
        self.use_file_cache = use_file_cache
        if use_file_cache:
            try:
                with open('key_cache.json', 'r') as f:
                    self.location_key_dict = json.load(f)
                with open('weather_cache.json', 'r') as f:
                    self.weather_dict = json.load(f)
            except FileNotFoundError:
                pass



    def add_key(self, dict_key, location_key):
        self.location_key_dict[dict_key] = location_key
        if self.use_file_cache:
            with open('key_cache.json', 'w') as f:
                json.dump(self.location_key_dict, f)

    def add_weather_cache(self, location_key, weather):
        self.weather_dict[location_key] = weather
        if self.use_file_cache:
            with open('weather_cache.json', 'w') as f:
                json.dump(self.weather_dict, f)

    def get_location_key(self, latitude, longitude):
        dict_key = f"{float(latitude)};{float(longitude)}"
        if dict_key in self.location_key_dict:
            location_key = self.location_key_dict.get(dict_key)
            return location_key
        else:
            logging.debug("Получаем новый ключ")

        url = "http://dataservice.accuweather.com/locations/v1/cities/geoposition/search"
        params = {
            "apikey": Config.accuweather_key,
            "q": f"{latitude},{longitude}"
        }
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    raise RuntimeError(f"Нет локации по координатам: {longitude=}, {latitude=}")
                location_key = data.get("Key")

                self.add_key(dict_key, location_key)

                return location_key
            elif response.status_code == 503:
                raise RuntimeError("Превышено максимальное количество запросов в день. Попробуйте снова завтра или обновите токен")
            else:
                logging.error(response.text)
                raise RuntimeError(f"Запрос провален с таким кодом статуса: {response.status_code}")

        except Exception as e:
            raise RuntimeError(f"Ошибка при получении ключа: \n{e}")

    def get_weather(self, location_key, name):
        if location_key in self.weather_dict:
            # logging.debug("Погода из кэша")
            weather = self.weather_dict.get(location_key)
            return weather
        else:
            logging.debug("Получаем новую погоду")


        params = {
            "apikey": Config.accuweather_key,
            "details": True,
            'metric': True
        }
        url = f'http://dataservice.accuweather.com/forecasts/v1/daily/5day/{location_key}'
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()

                weather = {
                    "point_name": name,
                    "date": [],
                    "min_temperature": [],
                    "max_temperature": [],
                    "mean_temperature": [],
                    "relative_humidity": [],
                    "precipitation_probability": [],
                    "wind_speed": [],
                }
                for day in data['DailyForecasts']:
                    weather['date'].append(day['Date'])
                    weather['min_temperature'].append(day['Temperature']['Minimum']['Value'])
                    weather['max_temperature'].append(day['Temperature']['Maximum']['Value'])
                    weather['relative_humidity'].append(day['Day']['RelativeHumidity']['Average'])
                    weather['precipitation_probability'].append(day['Day']['PrecipitationProbability'])
                    weather['wind_speed'].append(day['Day']['Wind']['Speed']['Value'])

                weather['mean_temperature'] = list(map(
                    lambda x, y: (x + y) / 2,
                    weather['min_temperature'], weather['max_temperature']
                ))

                self.add_weather_cache(location_key, weather)

                # Доп проверка на успешность
                return weather
            elif response.status_code == 503:
                raise RuntimeError("Превышено максимальное количество запросов в день. Попробуйте снова завтра или обновите токен")
        except Exception as e:
            logging.error(response)
            logging.error(response.text)

            raise RuntimeError(f"Проблемы с доступом к api: \n{str(e)}")

if __name__ == '__main__':
    manager = WeatherManager()
    location_key =  None
    try:
        location_key = manager.get_location_key(37.37, 54.12)
    except RuntimeError as e:
        logging.error(e)

    for _ in range(10):
        if location_key:
            data = manager.get_weather(location_key, '123')
    pprint(data)
