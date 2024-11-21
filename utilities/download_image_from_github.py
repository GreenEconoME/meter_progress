# Import dependencies
import requests
import base64
from io import BytesIO
from PIL import Image
import streamlit as st

# Define function to pull the GE logo from github
def download_image_from_github(repo_owner, repo_name, image_path, branch, access_token):
    # Construct GitHub API URL
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{image_path}?ref={branch}"
    
    # Set up headers with the access token
    headers = {
        'Authorization': f'token {access_token}'
    }
    
    # Request the file from GitHub
    response = requests.get(url, headers = headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        content = response.json().get('content')
        file_bytes = base64.b64decode(content)
        image = Image.open(BytesIO(file_bytes))
        
        return image
    else:
        st.error("Failed to retrieve the logo from GitHub.")
        return None