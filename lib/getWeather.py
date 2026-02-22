from playwright.sync_api import sync_playwright
import asyncio
import json
import requests

class MSWeather:
    def __init__(self,city):
        self.city = city
        self.ls=[]
        self.get_url = ''
        self.url = f"https://www.msn.cn/zh-cn/weather/forecast/in-{self.city}"

    def get_weather_data(self):
        with sync_playwright() as p:
            browser =  p.chromium.launch(headless=True)
            page =  browser.new_page()
            page.goto(self.url)
            page.on("request", self.on_request)
            page.wait_for_timeout(3000)
            page.close()

        response = requests.get(self.get_url)
        self.ls = response.json()

    def on_request(self,request):
        # print(request.url)
        if "https://assets.msn.cn/service/weather/overview?apikey=" in request.url:
            self.get_url = request.url
            print(self.get_url)


    def analyze_data(self):
        '''
        analyze_data 的 Docstring
        
        分析数据,并返回结果
        '''
        data = self.ls["responses"][0]["weather"][0]["current"]
        return data

    def format_weather_report(self, weather_data):
        '''
        format_weather_report 的 Docstring
        
        格式化天气数据为易读的报告
        '''
        # 基础天气信息
        temperature = weather_data.get('temp', 'N/A')
        feels_like = weather_data.get('feels', 'N/A')
        condition = weather_data.get('cap', 'N/A')
        humidity = weather_data.get('rh', 'N/A')
        
        # 风力信息
        wind_speed = weather_data.get('windSpd', 'N/A')
        wind_direction = self._get_wind_direction(weather_data.get('windDir', 0))
        wind_level = weather_data.get('pvdrWindSpd', 'N/A')
        
        # 紫外线和空气质量
        uv_index = weather_data.get('uv', 'N/A')
        uv_desc = weather_data.get('uvDesc', 'N/A')
        aqi = weather_data.get('aqi', 'N/A')
        aqi_severity = weather_data.get('aqiSeverity', 'N/A')
        
        # 其他信息
        pressure = weather_data.get('baro', 'N/A')
        visibility = weather_data.get('vis', 'N/A')
        cloud_cover = weather_data.get('cloudCover', 'N/A')
        
        # 创建格式化的报告
        report = f"""
{'='*50}
           {self.city} 天气报告
{'='*50}

🌤️  天气状况: {condition}
🌡️  当前温度: {temperature}°C (体感温度: {feels_like}°C)
💧  湿度: {humidity}%
💨  风力: {wind_direction} {wind_speed} km/h ({wind_level})
☀️  紫外线: {uv_index}级 ({uv_desc})
🌍  空气质量: AQI {aqi} ({aqi_severity})
📊  气压: {pressure} hPa
👁️  能见度: {visibility} km
☁️  云量: {cloud_cover}%

更新时间: {weather_data.get('created', 'N/A')}
{'='*50}
        """
        
        return report.strip()

    def _get_wind_direction(self, degree):
        '''
        _get_wind_direction 的 Docstring
        
        根据风向角度返回方向描述
        '''
        directions = ['北风', '东北风', '东风', '东南风', '南风', '西南风', '西风', '西北风']
        index = round(degree / 45) % 8
        return directions[index]

    def save_data(self):
        '''
        save_data 的 Docstring
        
        保存数据
        '''
        with open("weather_data.json","w") as f:
            json.dump(self.analyze_data(),f,indent=4)

    def return_to_ai(self):
        '''
        return_to_ai 的 Docstring
        
        将数据返回给AI
        '''
        self.get_weather_data()
        format_weather_report = self.analyze_data()
        return self.format_weather_report(format_weather_report)
    
    def run(self):
        self.get_weather_data()
        self.save_data()


def ai_get_local_weather():
    '''
    ai获取本地天气的函数
    '''
    from lib.user_ip import UserIP
    user_address = UserIP().sendAddress()
    ms = MSWeather(user_address)
    return ms.return_to_ai()

def main():
    input_city = input("请输入城市名称:")
    ms = MSWeather(input_city)
    ms.run()
    
    # 读取并显示格式化的天气报告
    with open("weather_data.json","r", encoding='utf-8') as f:
        data = json.load(f)
        formatted_report = ms.format_weather_report(data)
        print(formatted_report)
    

if __name__ == "__main__":
    main()