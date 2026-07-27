#!/bin/bash

# Azure App Service Startup Script
# Runs the Streamlit app on port 8501 (mapped via WEBSITES_PORT)

streamlit run app.py --server.port 8501 --server.headless true --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false