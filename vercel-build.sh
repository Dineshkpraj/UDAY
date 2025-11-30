#!/bin/bash

# Vercel needs a "build" output. Since Streamlit is a server,
# we simply execute the Streamlit run command.
# This script will install dependencies and then run the app.

echo "Starting Streamlit build on Vercel..."

# The main command to run the Streamlit app:
# Streamlit will run on port 8501 by default
streamlit run app.py --server.port $PORT --server.enableCORS true