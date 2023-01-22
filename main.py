import time
import streamlit as st
import pandas as pd
import asyncio
import ipaddress
from src.request_dispatch.dispatch import Api_Dispatch

SUPPORTED_APIS = {"IpAPI":
                      {"selected": False,
                       "API_HomePage": "google.com",
                       "API_Label": "IpAPI",
                       "_method": "get_ipapi"
                       },
                  "IPGeo":
                      {"selected": False,
                       "API_HomePage": "google.com",
                       "API_Label": "IPGeo",
                       "_method": "get_ipgeolocation"
                       },
                  "IPWhois":
                      {"selected": False,
                       "API_HomePage": "google.com",
                       "API_Label": "IPWhois",
                       "_method": "get_ipwhois"
                       }
                  }

async def communicate_with_backend(internal_dispatch,selected_apis: dict = None, input_data: list = None, page=None):

    if SUPPORTED_APIS["IpAPI"]["selected"]:
        asyncio.create_task(internal_dispatch.get_ipapi())

    if SUPPORTED_APIS["IPWhois"]["selected"]:
        asyncio.create_task(internal_dispatch.get_ipwhois())

    if SUPPORTED_APIS["IPGeo"]["selected"]:
        asyncio.create_task(internal_dispatch.get_ipgeolocation())

    print("DONE WITH EVERYTHING")

async def validate_input(ip_data=None):
    for provided_ip in ip_data:
        try:
            ipaddress.ip_address(provided_ip)
        except ValueError:
            return False

    return True

async def build_streamlit_app(button_disbled:bool = True,input_valid:bool =False):

    st.set_page_config(page_title="IP_Geo_Checker",page_icon=":bar_chart:",layout="wide")
    st.sidebar.title("IP Geo Locator")
    st.header("IP Geo Locator Service")
    st.write("This web page completes async queries to the supported API's shown below.")
    st.write("As this is a hosted page,it may run into useage issues, if that occurs. ")
    st.write("Feel free to clone the repo and run the application local.")

    st.subheader("IP Geo Locator Service")
    st.write("Repo Link:","https://github.com/BlueSideStrongSide/simple_geo_ip")
    st.write("IPapi", "https://ip-api.com/")
    st.write("IPGeo:", "https://ipgeolocation.io/", "Currently disabled in the streamlit deployed version")
    st.write("IPWhois", "https://ipwhois.io/")

    #Checking Inputs
    uploaded_file = st.sidebar.file_uploader("SOURCE FILE", accept_multiple_files=False, key=None, help=None, on_change=None, args=None,
                     kwargs=None, disabled=False, label_visibility="visible")

    col1, col2, col3 = st.sidebar.columns(3)
    with col2:
        st.write("OR")

    manual_entry = st.sidebar.text_input("Enter IP or Multiple ex: (8.8.8.8,1.1.1.1)", key="manual_text_input")

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
    with col2:
        SUPPORTED_APIS["IPWhois"]["selected"] = st.checkbox(SUPPORTED_APIS["IPWhois"]["API_Label"])
    with col3:
        geo_paid = True
        if await internal_dispatch.ipgeolocation_api():
            geo_paid = False
            SUPPORTED_APIS["IPGeo"]["selected"] = st.checkbox(SUPPORTED_APIS["IPGeo"]["API_Label"], disabled=geo_paid)

    placeholder = st.empty()
    tab1, tab2 = st.tabs(["Detailed Results","Summary"])

    # Go_Button Formatting
    col1, col2, col3 = st.columns(3)
    with col2:
        if input_data \
                and not input_data[0] == "" \
                and await validate_input(ip_data=input_data)\
                and any([SUPPORTED_APIS["IpAPI"]["selected"],SUPPORTED_APIS["IPGeo"]["selected"],SUPPORTED_APIS["IPWhois"]["selected"]]):

            button_disbled = False
        else:
            with warning_location:
                st.warning('Only one IP in the manual field, input file should be new line seperated', icon="⚠️")

        if st.button("Submit Request",disabled=button_disbled):
            asyncio.create_task(communicate_with_backend(internal_dispatch))

            #Result View Near-Realtime return
            for i in range(120):
                with placeholder.container():
                    print("WORKING...", i)
                    with tab1:
                        if internal_dispatch.get_ipapi_results:
                            st.json(await internal_dispatch.get_latest_result("ipapi"), expanded=True)

                        if internal_dispatch.get_ipgeolocation_results:
                            st.json(await internal_dispatch.get_latest_result("ipgeolocation"), expanded=True)

                        if internal_dispatch.get_ipwhois_results:
                            st.json(await internal_dispatch.get_latest_result("ipwhois"), expanded=True)

                    if internal_dispatch.all_done or i==120:
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

