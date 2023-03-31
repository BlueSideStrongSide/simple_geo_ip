import asyncio
import aiohttp
import json

#https://ipwhois.io/


class IpWhois:

    async def send_request(self, ip_list:list =["8.8.8.8","1.1.1.1"]):
        headers = {"Content-Type": "application/json"}
        request_counter = 0

        async with aiohttp.ClientSession() as session:
            for ip in ip_list:
                async with session.post(f'http://ipwho.is/{ip}',headers=headers) as resp:
                    respone_json = await resp.json()

                    yield json.dumps({'API': __class__.__name__,
                            'queried_ip': ip,
                            'http_status': resp.status,
                            'city': respone_json.get("city"),
                            'country': respone_json.get("country"),
                            'latitude': respone_json.get("latitude"),
                            'longitude': respone_json.get("longitude"),
                            'api_response': respone_json
                                      })

                    if request_counter >= 1:
                        await asyncio.sleep(1)
                    request_counter += 1

if __name__ == '__main__':
    test = IpWhois()
    asyncio.run(test.test_local())