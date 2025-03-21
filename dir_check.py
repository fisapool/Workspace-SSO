import os
import streamlit as st

st.title("Directory Structure Check")

# Root directory
root_dir = os.getcwd()
st.write(f"Root directory: {root_dir}")

# Check for specific directories
for dir_name in ["data", "config", ".streamlit", "credentials"]:
    path = os.path.join(root_dir, dir_name)
    exists = os.path.exists(path)
    st.write(f"Directory '{dir_name}' exists: {exists}")

# List all files in the root directory
st.write("### Files in Root Directory:")
for item in os.listdir(root_dir):
    item_path = os.path.join(root_dir, item)
    is_dir = os.path.isdir(item_path)
    st.write(f"- {'📁' if is_dir else '📄'} {item}") 