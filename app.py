#!/usr/bin/env python3
"""
Main application entry point for Photo Club Email Personalization Tool
"""

import streamlit as st
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'streamlit'))

from main_app import main

if __name__ == "__main__":
    main() 