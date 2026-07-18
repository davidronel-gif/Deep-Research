"""Simple script to check required API keys using python-dotenv.
Run from repository root or adjust working directory as needed.
"""
from dotenv import load_dotenv
import os

# Load .env from current working directory
load_dotenv()

print('OPENROUTER: ', 'OK' if os.getenv('OPENROUTER_API_KEY') else 'MISSING')
print('TAVILY:     ', 'OK' if os.getenv('TAVILY_API_KEY') else 'MISSING')