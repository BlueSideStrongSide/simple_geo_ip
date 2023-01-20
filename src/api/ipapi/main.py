import asyncio
import aiohttp
import json
from pathlib import Path

#https://ip-api.com/
#
#
#

class IpApi:

    def __init__(self, config_path: str = None, configuration_settings=None, paid:bool =False):

        if paid:
            self.configuration_settings = configuration_settings

            config_path = f"src/api/{__class__.__name__.lower()}/config.json"

            if not Path(config_path).exists():
                config_path = "config.json"

            with open(config_path, "r") as configuration_file:
                self.configuration_settings = json.loads(configuration_file.read())

    # Update ME
    async def send_request(self, ip_list:list =["8.8.8.8","1.1.1.1"]):
        headers = {"Content-Type": "application/json"}
        request_counter = 0

        async with aiohttp.ClientSession() as session:
            for ip in ip_list:
                async with session.get(f'http://ip-api.com/json/{ip}',
                                       headers=headers) as resp:
                    respone_json = await resp.json()

                    yield json.dumps({'API': __class__.__name__,
                            'queried_ip': ip,
                            'http_status': resp.status,
                            'city': respone_json.get("city"),
                            'country': respone_json.get("country"),
                            'latitude': respone_json.get("lat"),
                            'longitude': respone_json.get("lon"),
                           'api_response': respone_json
                                      })

                    if request_counter >= 1:
                        await asyncio.sleep(1)
                    request_counter += 1



    async def summary_fields(self):
        ...


if __name__ == '__main__':
    test = IpApi()
    asyncio.run(test.test_local())