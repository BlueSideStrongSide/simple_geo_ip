import time
import streamlit as st
import pandas as pd
import asyncio
import ipaddress
import re
from typing import Type
from src.request_dispatch.dispatch import Api_Dispatch

SUPPORTED_APIS = {"IpAPI":
                      {"selected": False,
                       "API_HomePage": "https://ip-api.com/",
                       "API_Label": "IpAPI",
                       "_method": "get_ipapi"
                       },
                  "IPGeo":
                      {"selected": False,
                       "API_HomePage": "https://ipgeolocation.io/",
                       "API_Label": "IPGeo",
                       "_method": "get_ipgeolocation"
                       },
                  "IPWhois":
                      {"selected": False,
                       "API_HomePage": "https://ipwhois.io/",
                       "API_Label": "IPWhois",
                       "_method": "get_ipwhois"
                       }
                  }
async def communicate_with_backend(backend_handler: Type[Api_Dispatch]=None):

    if SUPPORTED_APIS["IpAPI"]["selected"]:
        asyncio.create_task(backend_handler.get_ipapi())

    if SUPPORTED_APIS["IPWhois"]["selected"]:
        asyncio.create_task(backend_handler.get_ipwhois())

    if SUPPORTED_APIS["IPGeo"]["selected"]:
        asyncio.create_task(backend_handler.get_ipgeolocation())

async def update_input(validated_data:list=None, backend_handler: Type[Api_Dispatch]=None):
    #updating class property with update ip address data
    try:
        backend_handler.input_data = validated_data
    except Exception as e:
        print(e)
        return False
    return True

async def validate_input(ip_data:list=None, backend_handler: Type[Api_Dispatch]=None) -> bool:
    ipv4_draft_regex = "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"

    possible_ipv4 = re.findall(ipv4_draft_regex, ','.join(ip_data))

    validated_inputs = []
    for provided_ip in possible_ipv4:
        # provided_ip = provided_ip.strip()
        try:
            ipaddress.ip_address(provided_ip)
            validated_inputs.append(provided_ip)
        except ValueError:
            return False

    if not backend_handler.input_data == validated_inputs:
        await update_input(validated_data=validated_inputs, backend_handler=backend_handler)

    return True

async def build_streamlit_app(button_disbled:bool = True,input_valid:bool =False):

    repo_data = {'API':["IPapi","IPGeo","IPWhois"],
                 'API_Wbsite':["https://ip-api.com/","https://ipgeolocation.io/","https://ipwhois.io/"]}

    st.set_page_config(page_title="IP_Geo_Checker",page_icon=":bar_chart:",layout="wide")
    st.sidebar.title("IP Geo Locator")
    st.header("IP Geo Locator Service")
    st.write("IP Geo Locator Service. This web page completes async queries to the supported API's shown below. As this is a hosted page, it may run into useage issues, if that occurs.Feel free to clone the repo and run the application local.")

    st.write("Repo Link:","https://github.com/BlueSideStrongSide/simple_geo_ip")

    st.subheader("IP Geo Locator Service")
    st.write("This website currently uses the API services shown below excluding IPGeo, for the streamlit version.")
    st.dataframe(pd.DataFrame.from_dict(repo_data))

    #Checking Inputs
    uploaded_file = st.sidebar.file_uploader("SOURCE FILE", accept_multiple_files=False, key=None, help=None, on_change=None, args=None,
                     kwargs=None, disabled=False, label_visibility="visible")

    col1, col2, col3 = st.sidebar.columns(3)
    with col2:
        st.write("OR")

    manual_entry = st.sidebar.text_input("Enter IP addresses", key="manual_text_input")
    st.sidebar.write("A regex parser will attempt extract IPv4 addresses from the provided input. ")


    if manual_entry is not None:
        input_data = manual_entry.split(",")

    if uploaded_file is not None:
        input_data = uploaded_file.read().decode().split()
        raw_enabled = st.sidebar.checkbox('View Input Data')
        if raw_enabled:
            st.sidebar.caption(f'There are {len(input_data)} addresses in this data')
            st.sidebar.write(input_data)

    internal_dispatch = Api_Dispatch(input_data=input_data)

    warning_location = st.empty()

    #API Formatting
    st.header("Select API:")
    col1, col2, col3 = st.columns(3)
    with col1:
        SUPPORTED_APIS["IpAPI"]["selected"] = st.checkbox(SUPPORTED_APIS["IpAPI"]["API_Label"])
        ip_api_status = st.empty()

    with col2:
        SUPPORTED_APIS["IPWhois"]["selected"] = st.checkbox(SUPPORTED_APIS["IPWhois"]["API_Label"])
        ip_whois_status = st.empty()

    with col3:
        #checking if we have an API key for ipgeo
        geo_paid = True
        if await internal_dispatch.ipgeolocation_api():
            geo_paid = False
            SUPPORTED_APIS["IPGeo"]["selected"] = st.checkbox(SUPPORTED_APIS["IPGeo"]["API_Label"], disabled=geo_paid, label_visibility="visible")
            ip_geo_status = st.empty()

    placeholder = st.empty()
    tab1, tab2 = st.tabs(["Detailed Results","Summary"])

    # Go_Button Formatting
    col1, col2, col3 = st.columns(3)
    with col2:
        if input_data \
                and not input_data[0] == "" \
                and await validate_input(ip_data=input_data, backend_handler=internal_dispatch)\
                and any([SUPPORTED_APIS["IpAPI"]["selected"],SUPPORTED_APIS["IPGeo"]["selected"],SUPPORTED_APIS["IPWhois"]["selected"]]):

            button_disbled = False

        else:
            with warning_location:
                st.warning('IPv4 verification failed', icon="⚠️")

        if st.button("Submit Request",disabled=button_disbled):

            asyncio.create_task(communicate_with_backend(backend_handler=internal_dispatch))

            batch_timeout_seconds = 120

            #Result View Near-Realtime return
            for i in range(batch_timeout_seconds):
                with placeholder.container():

                    with tab1:
                        if internal_dispatch.get_ipapi_results:
                            st.json(await internal_dispatch.get_latest_result("ipapi"), expanded=True)
                            ip_api_status.write(f'{await internal_dispatch.get_api_status(api="ipapi")}')

                        if internal_dispatch.get_ipgeolocation_results:
                            st.json(await internal_dispatch.get_latest_result("ipgeo"), expanded=True)
                            ip_geo_status.write(f'{await internal_dispatch.get_api_status(api="ipgeo")}')


                        if internal_dispatch.get_ipwhois_results:
                            st.json(await internal_dispatch.get_latest_result("ipwhois"), expanded=True)
                            ip_whois_status.write(f'{await internal_dispatch.get_api_status(api="ipwhois")}')

                    if internal_dispatch.all_done or i==batch_timeout_seconds:
                        break

                    i+=1
                    await asyncio.sleep(.5)
            with tab2:
                st.text("Summarize Result")
                summary_table = st.dataframe(await internal_dispatch.summarize_results(),use_container_width=True)
                st.map(await internal_dispatch.summary_map,zoom=2, use_container_width=True)

            st.sidebar.download_button(
                label="Download All JSON Results",
                file_name="data.json",
                data=f'{await internal_dispatch.all_results_json}',
            )

            st.sidebar.download_button(
                label="Download Summary Table",
                file_name="summary.csv",
                data=f'{await internal_dispatch.summary_results_csv}',
            )

if __name__ == '__main__':
    # Drives the logic used to build our simple DB web app
    asyncio.run(build_streamlit_app())

