# Import dependencies
import streamlit as st
import pandas as pd
from datetime import date 

# Import helper functions
from utilities.download_image_from_github import download_image_from_github

st.set_page_config(layout="wide")


# Import secrets
access_token = st.secrets["GITHUB_TOKEN"]
repo_owner = st.secrets['REPO_OWNER']
repo_name = st.secrets['REPO_NAME']
image_path = st.secrets['IMAGE_PATH']
branch = st.secrets['BRANCH']

# Download and display the logo
logo_image = download_image_from_github(repo_owner, repo_name, image_path, branch, access_token)
if logo_image:
    st.image(logo_image, use_column_width=True)

# Set a title for the page
st.markdown("<h2 style = 'text-align: center; color: black;'>Portfolio Meter Progress</h2>", unsafe_allow_html = True)

# Add uploader to upload portfolio export
st.subheader("Upload Portfolio Export")
portfolio_export = st.file_uploader("Upload the portfolio dashboard export (.xlsx)", type=["xlsx"])


# Date selector for complete through date
comparison_date = st.date_input("Check for completion through:", date(2024, 10, 31))
comparison_date = pd.Timestamp(comparison_date)

if portfolio_export is not None:

    prop_status = []
    util_types = []

    about_df = pd.read_excel(portfolio_export, sheet_name = 'About')
    meter_df = pd.read_excel(portfolio_export, sheet_name = 'Meter Activity')

    for index, row in about_df.iterrows():
        prop_dict = {}
        
        for col in ['ESPM ID', 'Gross Floor Area', 'Property Name', 'Acquisition Date', 'Disposition Date']:
            prop_dict[col] = row[col]
        
        temp_df = meter_df.loc[meter_df['ESPM ID'] == row['ESPM ID']]
        for util in temp_df['Utility Type'].unique():
            if util not in util_types:
                util_types.append(util)
            prop_dict[f'{util} Latest'] = temp_df.loc[(temp_df['Utility Type'] == util) & (temp_df['Meter Active'] == True), 'Latest Entry'].min()
            
        
        prop_status.append(prop_dict)
        
    complete_df = pd.DataFrame(prop_status)
        
    # Create Complete Through columns
    for col in util_types:
        latest_col = f'{col} Latest'
        complete_through_col = f'{col} Complete through {comparison_date.date()}'
        complete_df[complete_through_col] = complete_df[latest_col] >= comparison_date

    # Ensure the properties that do not have any gas meters are marked as complete
    complete_df.loc[complete_df['ESPM ID'].isin([x for x in about_df['ESPM ID'] if x not in list(meter_df.loc[meter_df['Utility Type'] == 'NaturalGas', 'ESPM ID'])]), f'NaturalGas Complete through {comparison_date.date()}'] = True

    # Mark all the builidings as completed if the acquisition date is after the comparison date
    complete_df['Acquisition Date'] = pd.to_datetime(complete_df['Acquisition Date'], errors='coerce') # Clean up Acquisition Date for date comparison with comparison_date
    for util in util_types:
        complete_df.loc[complete_df['Acquisition Date'] >= comparison_date, f'{util} Complete through {comparison_date.date()}'] = True


    # Gather metrics
    total_gfa = complete_df['Gross Floor Area'].sum()
    num_of_builds = about_df.shape[0]

    # Electric completeness
    e_num_complete = complete_df.loc[complete_df[f'Electric Complete through {comparison_date.date()}'] == True].shape[0] # Number of buildings complete
    e_gfa_complete = complete_df.loc[complete_df[f'Electric Complete through {comparison_date.date()}'] == True, 'Gross Floor Area'].sum() # GFA complete
    e_gfa_pct_complete = e_gfa_complete / total_gfa # GFA pct complete

    g_num_complete = complete_df.loc[complete_df[f'NaturalGas Complete through {comparison_date.date()}'] == True].shape[0] # Number of buildings complete
    g_gfa_complete = complete_df.loc[complete_df[f'NaturalGas Complete through {comparison_date.date()}'] == True, 'Gross Floor Area'].sum() # GFA complete
    g_gfa_pct_complete = g_gfa_complete / total_gfa # GFA pct complete

    w_num_complete = complete_df.loc[complete_df[f'Water Complete through {comparison_date.date()}'] == True].shape[0] # Number of buildings complete
    w_gfa_complete = complete_df.loc[complete_df[f'Water Complete through {comparison_date.date()}'] == True, 'Gross Floor Area'].sum() # GFA complete
    w_gfa_pct_complete = w_gfa_complete / total_gfa # GFA pct complete

    # Streamlit app layout
    st.markdown(f"<h2 style = 'text-align: center; color: black;'>Building Completion Metrics through {comparison_date.date()}</h2>", unsafe_allow_html = True)

    # Display high-level metrics side by side
    empty_col1, content_col, empty_col2 = st.columns([1, 2, 1])
    with content_col:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Gross Floor Area", f"{total_gfa:,} sq ft")
        with col2:
            st.metric("Number of Buildings", num_of_builds)

    # Display Electric, Gas, and Water metrics side by side
    empty_col1, content_col, empty_col2 = st.columns([1, 4, 1])
    with content_col:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("Electric")
            st.metric("Buildings Complete", e_num_complete)
            st.metric("GFA Complete", f"{e_gfa_complete:,} sq ft")
            st.metric("Percent GFA Complete", f"{e_gfa_pct_complete:.2%}")

        with col2:
            st.subheader("Gas")
            st.metric("Buildings Complete", g_num_complete)
            st.metric("GFA Complete", f"{g_gfa_complete:,} sq ft")
            st.metric("Percent GFA Complete", f"{g_gfa_pct_complete:.2%}")

        with col3:
            st.subheader("Water")
            st.metric("Buildings Complete", w_num_complete)
            st.metric("GFA Complete", f"{w_gfa_complete:,} sq ft")
            st.metric("Percent GFA Complete", f"{w_gfa_pct_complete:.2%}")


    # Display and export the DataFrame
    st.subheader("Detailed Data")
    st.dataframe(complete_df)

    # Provide export option
    @st.cache_data
    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')

    csv_data = convert_df_to_csv(complete_df)
    st.download_button(
        label="Download Data as CSV",
        data=csv_data,
        file_name='completion_data.csv',
        mime='text/csv',
    )