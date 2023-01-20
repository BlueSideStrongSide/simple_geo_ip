import asyncio
import aiohttp
import json
from pathlib import Path

#https://ipgeolocation.io/
#Only one IP at a time
#1000 requests Per Day
#pass protected API Key

#1000 IP's
# /how_many_apis
# 333/333/333 <--

class IpGeoLocation:

    def __init__(self, config_path:str=None, configuration_settings=None, apikey=None):
        self.configuration_settings = configuration_settings

        config_path = f"src/api/{__class__.__name__.lower()}/config.json"

        if not Path(config_path).exists():
            config_path = "config.json"

        try:
            with open(config_path, "r") as configuration_file:
                self.configuration_settings = json.loads(configuration_file.read())
        except FileNotFoundError:
            self.configuration_settings = {}

    @property
    async def valid_apikey(self):
        if self.configuration_settings.get("API_KEY"):
            return True

    # Update ME
    async def send_request(self, ip_list:list =["8.8.8.8","1.1.1.1"]):
        headers = {"Content-Type": "application/json"}
        request_counter = 0

        async with aiohttp.ClientSession() as session:
            for ip in ip_list:
                async with session.get(f'https://api.ipgeolocation.io/ipgeo?'
                                        f'apiKey={self.configuration_settings["API_KEY"]}&ip={ip}',headers=headers) as resp:
                    respone_json = await resp.json()

                    yield json.dumps({'API': __class__.__name__,
                            'queried_ip': ip,
                            'http_status': resp.status,
                            'city': respone_json.get("city"),
                            'country': respone_json.get("country_name"),
                            'latitude': float(respone_json.get("latitude")),
                            'longitude': float(respone_json.get("longitude")),
                            'api_response': respone_json
                                      })

                    if request_counter >= 1:
                        await asyncio.sleep(1)
                    request_counter += 1

if __name__ == '__main__':
    test = IpGeoLocation()
    asyncio.run(test.test_local())

