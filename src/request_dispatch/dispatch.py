from ..api.ipapi.main import IpApi
from ..api.ipgeolocation.main import IpGeoLocation
from ..api.ipwhois.main import IpWhois
import pandas as pd
import json
import asyncio

#build logic to send data to our APIs
class Api_Dispatch:

    def __init__(self,selected_apis:dict=None,
                 input_data:list=["1.1.1.1", "8.8.8.8"],
                 ):
        self.selected_apis = selected_apis
        self.input_data = input_data
        self.get_ipapi_results  = []
        self.get_ipgeolocation_results = []
        self.get_ipwhois_results = []
        self.get_ipapi_status  = "Finished"
        self.get_ipgeolocation_status = "Finished"
        self.get_ipwhois_status = "Finished"
        self.all_results = []

    @property
    def all_done(self):

        if ((len(self.all_results) >= len(self.input_data)) and
                (self.get_ipapi_status == self.get_ipgeolocation_status == self.get_ipwhois_status == "Finished")):
            return True

    @property
    async def all_results_json(self):
        return f'[{",".join(self.all_results)}]'

    @property
    async def summary_results_csv(self):
        summary_df = await self.summarize_results()
        return summary_df.to_csv(index=False)

    @property
    async def summary_map(self):
        summary_df = await self.summarize_results()
        summary_df =summary_df[["lat", "lon"]]

        return summary_df

    async def summarize_results(self):
        data = {
            "API": [json.loads(x).get("API") for x in self.all_results],
            "queried_ip": [json.loads(x).get("queried_ip") for x in self.all_results],
            "http_status": [json.loads(x).get("http_status") for x in self.all_results],
            "city": [json.loads(x).get("city") for x in self.all_results],
            "country": [json.loads(x).get("country") for x in self.all_results],
            "lat": [json.loads(x).get("latitude") for x in self.all_results],
            "lon": [json.loads(x).get("longitude") for x in self.all_results]
        }
        return pd.DataFrame(data)

    async def get_latest_result(self, api:str):
        if api == "ipapi":
            latest_result = self.get_ipapi_results[0]
            self.get_ipapi_results.pop(0)

        if api == "ipgeolocation":
            latest_result = self.get_ipgeolocation_results[0]
            self.get_ipgeolocation_results.pop(0)

        if api == "ipwhois":
            latest_result = self.get_ipwhois_results[0]
            self.get_ipwhois_results.pop(0)

        self.all_results.append(latest_result)
        return latest_result

    async def get_ipapi(self):
        print("get_ipapi Worker Starting")
        self.get_ipapi_status = "Running"

        async for result in IpApi().send_request(self.input_data):
            print(result)
            self.get_ipapi_results.append(result)

        self.get_ipapi_status = "Finished"

    async def ipgeolocation_api(self):
        if await IpGeoLocation().valid_apikey:
            return True

    async def get_ipgeolocation(self):
        print("get_ipgeolocation_ Worker Starting")
        self.get_ipgeolocation_status = "Running"

        async for result in IpGeoLocation().send_request(self.input_data):
            print(result)
            self.get_ipgeolocation_results.append(result)

        self.get_ipgeolocation_status = "Finished"

    async def get_ipwhois(self):
        print("get_ipwhois Worker Starting")
        self.get_ipwhois_status = "Running"

        async for result in IpWhois().send_request(self.input_data):
            print(result)
            self.get_ipwhois_results.append(result)

        self.get_ipwhois_status = "Finished"

if __name__ == '__main__':
    ...