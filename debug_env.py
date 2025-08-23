from dotenv import load_dotenv
load_dotenv()

import os
import sys

print("====== DEBUGGING ENVIRONMENT VARIABLES ======")
print(f"GOOGLE_CLIENT_ID: {os.environ.get('GOOGLE_CLIENT_ID')}")
print(f"GOOGLE_CLIENT_SECRET: {os.environ.get('GOOGLE_CLIENT_SECRET')}")
print(f"Python path: {sys.executable}")
print(f"Current directory: {os.getcwd()}")

try:
    from flask import Flask
    from config import Config
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    print(f"app.config['GOOGLE_CLIENT_ID']: {app.config.get('GOOGLE_CLIENT_ID')}")
    print(f"app.config['GOOGLE_CLIENT_SECRET']: {app.config.get('GOOGLE_CLIENT_SECRET')}")
except Exception as e:
    print(f"Error: {str(e)}")

print("=========================================")
