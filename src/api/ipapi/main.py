import aiohttp
import asyncio
import json
from aiohttp.client_exceptions import ContentTypeError


class IpApi:
    async def generate_batch_string(self, input_ip_list: list, start_limit: int = 0, groups_of_limit: int = 30) -> list[str]:
        """
        This method will take in a list of ips and break them into smaller list based of the groups_of_limit parameter
        
        :param input_ip_list: list of IPs
        :param start_limit: the starting index for splitting
        :param groups_of_limit: number of IP addresses within each subgroup
        :return: list  of strings
        """
        sub_list_tracker = []
        current_loop = 0
        for group_increment in range(start_limit, len(input_ip_list), groups_of_limit):
            print(f'start_index={group_increment} end_index={group_increment + groups_of_limit} current_loop={current_loop}')
            sub_list_tracker.append(input_ip_list[group_increment:group_increment + groups_of_limit])
            current_loop += 1
        
        return sub_list_tracker
    
    async def send_request(self, ip_list=["8.8.8.8", "1.1.1.1"]):
        headers = {"Content-Type": "application/json"}
        request_counter = 0
        
        async with aiohttp.ClientSession() as session:
            if len(ip_list) < 30:
                for ip in ip_list:
                    async with session.get(f'http://ip-api.com/json/{ip}', headers=headers) as resp:
                        try:
                            x_rl = int(resp.headers.get('X-Rl', '1'))
                            x_ttl = int(resp.headers.get('X-Ttl', '0'))
                            print(f'The seconds until the limit is reset {x_ttl}')
                            print(f'number of requests remaining in the current rate limit window {x_rl}')
                            if x_rl == 0:
                                # Wait for the TTL duration if rate limit is reached
                                await asyncio.sleep(x_ttl)
                                request_counter = 0
                            
                            response_json = await resp.json()
                            yield json.dumps({
                                'API': self.__class__.__name__,
                                'queried_ip': ip,
                                'http_status': resp.status,
                                'city': response_json.get("city"),
                                'country': response_json.get("country"),
                                'latitude': response_json.get("lat", 0),
                                'longitude': response_json.get("lon", 0),
                                'api_response': response_json,
                                'content': await resp.text()
                            })
                        except ContentTypeError:
                            # Handle the case where response is empty or not JSON
                            yield json.dumps({
                                'ip': ip,
                                'error': 'Failed to decode JSON response',
                                'payload': await resp.text()
                            })
                        except Exception as e:
                            # Handle other potential exceptions
                            yield json.dumps({
                                'ip': ip,
                                'error': str(e)
                            })
                        
                        request_counter += 1
                        
                        if request_counter >= 45:
                            # Sleep for the TTL duration if we've made 45 requests
                            print("Waiting for connection window to reset")
                            await asyncio.sleep(x_ttl)
                            request_counter = 0
            else:
                
                groups_of_limit = 30
                batch_list = await self.generate_batch_string(ip_list, groups_of_limit=groups_of_limit)
                
                for batch_item in batch_list:
                    async with session.post(f'http://ip-api.com/batch', headers=headers, data=json.dumps(batch_item)) as resp:
                        try:
                            x_rl = int(resp.headers.get('X-Rl', '1'))
                            x_ttl = int(resp.headers.get('X-Ttl', '0'))
                            if x_rl == 0:
                                # Wait for the TTL duration if rate limit is reached
                                await asyncio.sleep(x_ttl)
                                request_counter = 0
                            
                            response_json = await resp.json()
                            for result in response_json:
                                yield json.dumps({
                                    'API': self.__class__.__name__,
                                    'queried_ip': 'batch',
                                    'http_status': resp.status,
                                    'city': result.get("city"),
                                    'country': result.get("country"),
                                    'latitude': result.get("lat", 0),
                                    'longitude': result.get("lon", 0),
                                    'api_response': result,
                                })
                        except ContentTypeError:
                            # Handle the case where response is empty or not JSON
                            yield json.dumps({
                                'ip': 'batch job',
                                'error': 'Failed to decode JSON response',
                            })
                        except Exception as e:
                            # Handle other potential exceptions
                            yield json.dumps({
                                'ip': 'batch job',
                                'error': str(e)
                            })
                        
                        request_counter += 1
                        
                        if request_counter >= 45:
                            # Sleep for the TTL duration if we've made 45 requests
                            print("Waiting for connection window to reset")
                            await asyncio.sleep(x_ttl)
                            request_counter = 0


async def get_ipapi(ip_addresses):
    async for result in IpApi().send_request(ip_addresses):
        print(result)

#
# # Example usage
# ip_addresses = ['157.230.244.49', '8.8.8.8', '45.77.83.185', '1.1.1.1', '8.8.4.4']
# asyncio.run(get_ipapi(ip_addresses))
