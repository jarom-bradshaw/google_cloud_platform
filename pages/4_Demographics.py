"""
Page 4: Store Demographics Comparison
Uses Census API to compare demographics around store locations.
"""
import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from great_tables import GT
import requests
from utils.data_loader import load_stores

st.set_page_config(page_title="Demographics", layout="wide")

st.title("Store Demographics Comparison")
st.markdown("Compare customer demographics within a specified area around Rigby stores using Census API data.")

# Get Census API key from secrets
try:
    census_api_key = st.secrets.get("CENSUS_API_KEY", None)
    if not census_api_key:
        st.warning("Census API key not found in secrets. Please configure it in Streamlit secrets.")
        census_api_key = st.text_input("Enter Census API Key (or configure in secrets)", type="password")
except:
    census_api_key = st.text_input("Enter Census API Key (or configure in secrets)", type="password")

# Load stores
try:
    stores = load_stores()
    
    if len(stores) == 0:
        st.error("No Rigby stores found.")
        st.stop()
    
    # Store selection
    st.sidebar.header("Store Selection")
    store_options = stores.select(["STORE_ID", "STORE_NAME", "STREET_ADDRESS"]).to_pandas()
    store_options["display"] = store_options["STORE_NAME"] + " - " + store_options["STREET_ADDRESS"]
    
    selected_store_idx = st.sidebar.selectbox(
        "Select Store",
        options=range(len(store_options)),
        format_func=lambda x: store_options.iloc[x]["display"]
    )
    
    selected_store = stores.filter(pl.col("STORE_ID") == store_options.iloc[selected_store_idx]["STORE_ID"])
    
    if len(selected_store) == 0:
        st.error("Selected store not found.")
        st.stop()
    
    store_lat = selected_store["LATITUDE"].item()
    store_lon = selected_store["LONGITUDE"].item()
    store_name = selected_store["STORE_NAME"].item()
    store_address = selected_store["STREET_ADDRESS"].item()
    store_zip = selected_store["ZIP_CODE"].item()
    
    # Radius selection
    radius_miles = st.sidebar.slider(
        "Radius around store (miles)",
        min_value=1,
        max_value=10,
        value=5,
        step=1
    )
    
    st.sidebar.info(f"**Selected Store:**\n{store_name}\n{store_address}\n\n**Coordinates:**\nLat: {store_lat:.6f}\nLon: {store_lon:.6f}")
    
    # Display store location
    st.header("Store Location")
    col_map, col_info = st.columns([2, 1])
    
    with col_map:
        # Create map
        map_data = pl.DataFrame({
            "lat": [store_lat],
            "lon": [store_lon],
            "name": [store_name]
        }).to_pandas()
        
        st.map(map_data, zoom=13)
    
    with col_info:
        st.subheader("Store Information")
        st.write(f"**Name:** {store_name}")
        st.write(f"**Address:** {store_address}")
        st.write(f"**ZIP Code:** {store_zip}")
        st.write(f"**Latitude:** {store_lat:.6f}")
        st.write(f"**Longitude:** {store_lon:.6f}")
        st.write(f"**Analysis Radius:** {radius_miles} miles")
    
    # Census API integration
    if census_api_key:
        st.header("Demographic Data from Census API")
        
        # Get ZIP code for Census API
        zip_code = str(store_zip).split("-")[0]  # Handle ZIP+4
        
        @st.cache_data
        def get_census_data(zip_code: str, api_key: str):
            """Fetch demographic data from Census API."""
            # Using ACS 5-year estimates (most recent)
            # Variables for demographic data
            # B01001: Sex by Age
            # B19013: Median Household Income
            # B15003: Educational Attainment
            # B25064: Median Gross Rent
            # B08301: Means of Transportation to Work
            # B25077: Median Home Value
            # B25003: Tenure (Owner/Renter)
            # B25001: Housing Units
            # B01002: Median Age
            # B17001: Poverty Status
            
            base_url = "https://api.census.gov/data/2022/acs/acs5"
            
            # Define variables to fetch (10+ variables as required)
            variables = {
                "B01001_001E": "Total Population",
                "B01002_001E": "Median Age",
                "B19013_001E": "Median Household Income",
                "B25064_001E": "Median Gross Rent",
                "B25077_001E": "Median Home Value",
                "B25001_001E": "Total Housing Units",
                "B15003_022E": "Bachelor's Degree",
                "B15003_023E": "Master's Degree",
                "B15003_024E": "Professional Degree",
                "B15003_025E": "Doctorate Degree",
                "B08301_010E": "Public Transportation",
                "B08301_019E": "Work from Home",
                "B17001_002E": "Below Poverty Level"
            }
            
            var_list = ",".join(variables.keys())
            
            # Try to get data by ZIP code
            try:
                url = f"{base_url}?get=NAME,{var_list}&for=zip%20code%20tabulation%20area:{zip_code}&key={api_key}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if len(data) > 1:
                        # Parse response
                        headers = data[0]
                        values = data[1]
                        
                        result = {}
                        for i, header in enumerate(headers):
                            if header in variables:
                                try:
                                    result[variables[header]] = float(values[i]) if values[i] != "-" else None
                                except:
                                    result[variables[header]] = None
                        
                        return result
                    else:
                        return None
                else:
                    st.error(f"Census API error: {response.status_code}")
                    return None
            except Exception as e:
                st.error(f"Error fetching Census data: {str(e)}")
                return None
    
        if st.button("Fetch Demographic Data"):
            with st.spinner("Fetching data from Census API..."):
                census_data = get_census_data(zip_code, census_api_key)
                
                if census_data:
                    st.success("Demographic data loaded successfully!")
                    
                    # KPIs
                    st.header("Key Demographic Indicators")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        pop = census_data.get("Total Population", "N/A")
                        st.metric("Total Population", f"{pop:,}" if isinstance(pop, (int, float)) else pop)
                    
                    with col2:
                        income = census_data.get("Median Household Income", "N/A")
                        st.metric("Median Household Income", 
                                f"${income:,.0f}" if isinstance(income, (int, float)) else income)
                    
                    with col3:
                        age = census_data.get("Median Age", "N/A")
                        st.metric("Median Age", f"{age:.1f}" if isinstance(age, (int, float)) else age)
                    
                    with col4:
                        housing = census_data.get("Total Housing Units", "N/A")
                        st.metric("Housing Units", f"{housing:,}" if isinstance(housing, (int, float)) else housing)
                    
                    # Additional metrics
                    col5, col6, col7, col8 = st.columns(4)
                    
                    with col5:
                        rent = census_data.get("Median Gross Rent", "N/A")
                        st.metric("Median Gross Rent", 
                                f"${rent:,.0f}" if isinstance(rent, (int, float)) else rent)
                    
                    with col6:
                        home_value = census_data.get("Median Home Value", "N/A")
                        st.metric("Median Home Value", 
                                f"${home_value:,.0f}" if isinstance(home_value, (int, float)) else home_value)
                    
                    with col7:
                        # Calculate education percentage
                        pop_total = census_data.get("Total Population")
                        bachelors = census_data.get("Bachelor's Degree", 0) or 0
                        masters = census_data.get("Master's Degree", 0) or 0
                        prof = census_data.get("Professional Degree", 0) or 0
                        doctorate = census_data.get("Doctorate Degree", 0) or 0
                        college_educated = bachelors + masters + prof + doctorate
                        if pop_total and pop_total > 0:
                            pct_college = (college_educated / pop_total) * 100
                            st.metric("College Educated", f"{pct_college:.1f}%")
                        else:
                            st.metric("College Educated", "N/A")
                    
                    with col8:
                        poverty = census_data.get("Below Poverty Level", "N/A")
                        pop_total = census_data.get("Total Population")
                        if poverty and pop_total and pop_total > 0:
                            pct_poverty = (poverty / pop_total) * 100
                            st.metric("Below Poverty", f"{pct_poverty:.1f}%")
                        else:
                            st.metric("Below Poverty", "N/A")
                    
                    # Great Tables - Demographic Summary
                    st.header("Demographic Summary Table")
                    
                    # Prepare table data
                    demo_table_data = []
                    for key, value in census_data.items():
                        if value is not None:
                            if "Income" in key or "Rent" in key or "Value" in key:
                                formatted_value = f"${value:,.0f}"
                            elif "Age" in key:
                                formatted_value = f"{value:.1f}"
                            elif "Population" in key or "Units" in key or "Degree" in key or "Transportation" in key or "Home" in key or "Poverty" in key:
                                formatted_value = f"{value:,.0f}"
                            else:
                                formatted_value = str(value)
                            
                            demo_table_data.append({
                                "Demographic Variable": key,
                                "Value": formatted_value
                            })
                    
                    demo_df = pl.DataFrame(demo_table_data).to_pandas()
                    
                    # Use regular dataframe for demographics since values are already formatted
                    st.dataframe(demo_df, width='stretch', hide_index=True)
                    
                    # Charts
                    st.header("Demographic Visualizations")
                    
                    col_chart1, col_chart2 = st.columns(2)
                    
                    with col_chart1:
                        # Education level chart
                        education_data = {
                            "Bachelor's": census_data.get("Bachelor's Degree", 0) or 0,
                            "Master's": census_data.get("Master's Degree", 0) or 0,
                            "Professional": census_data.get("Professional Degree", 0) or 0,
                            "Doctorate": census_data.get("Doctorate Degree", 0) or 0
                        }
                        
                        if sum(education_data.values()) > 0:
                            fig1 = px.bar(
                                x=list(education_data.keys()),
                                y=list(education_data.values()),
                                title="Education Levels (College+)",
                                labels={"x": "Degree Level", "y": "Population"}
                            )
                            fig1.update_layout(height=400)
                            st.plotly_chart(fig1, width='stretch')
                    
                    with col_chart2:
                        # Economic indicators
                        economic_data = {
                            "Median Income": census_data.get("Median Household Income", 0) or 0,
                            "Median Rent": census_data.get("Median Gross Rent", 0) or 0,
                            "Median Home Value": census_data.get("Median Home Value", 0) or 0
                        }
                        
                        # Normalize for visualization (divide by 1000)
                        economic_normalized = {k: (v / 1000) if v else 0 for k, v in economic_data.items()}
                        
                        if sum(economic_normalized.values()) > 0:
                            fig2 = px.bar(
                                x=list(economic_normalized.keys()),
                                y=list(economic_normalized.values()),
                                title="Economic Indicators (in thousands)",
                                labels={"x": "Indicator", "y": "Value ($ thousands)"}
                            )
                            fig2.update_layout(height=400)
                            st.plotly_chart(fig2, width='stretch')
                    
                    # Additional expander with more details
                    with st.expander("Additional Demographic Details", expanded=False):
                        st.subheader("Transportation & Housing")
                        
                        col_trans1, col_trans2 = st.columns(2)
                        
                        with col_trans1:
                            public_trans = census_data.get("Public Transportation", 0) or 0
                            work_home = census_data.get("Work from Home", 0) or 0
                            
                            if public_trans > 0 or work_home > 0:
                                trans_data = {
                                    "Public Transportation": public_trans,
                                    "Work from Home": work_home
                                }
                                fig3 = px.pie(
                                    values=list(trans_data.values()),
                                    names=list(trans_data.keys()),
                                    title="Commuting Patterns"
                                )
                                st.plotly_chart(fig3, width='stretch')
                        
                        with col_trans2:
                            st.metric("Public Transportation Users", f"{public_trans:,}")
                            st.metric("Work from Home", f"{work_home:,}")
                else:
                    st.error("Failed to fetch demographic data. Please check your API key and ZIP code.")
        else:
            st.info("Click 'Fetch Demographic Data' to load demographic information for the selected store.")
    else:
        st.warning("Please enter a Census API key to view demographic data.")
        st.markdown("""
        **How to get a Census API key:**
        1. Visit https://api.census.gov/data/key_signup.html
        2. Sign up for a free API key
        3. Enter the key above or configure it in Streamlit secrets for Cloud Run
        """)

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
