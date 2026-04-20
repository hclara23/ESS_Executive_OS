import os
import requests
from Features.Face.Mouth import speak

def get_danfoss_drive_options(hp=None, voltage=None):
    """
    In a real app, this would call the Danfoss Developer Portal API
    to find matching drive part numbers.
    """
    # Mock data based on common Danfoss VLT series
    drives = [
        {"series": "FC-302", "hp": 5, "voltage": 460, "part": "131B0001"},
        {"series": "FC-302", "hp": 10, "voltage": 460, "part": "131B0002"},
        {"series": "FC-102", "hp": 5, "voltage": 230, "part": "131H0001"},
    ]
    
    matches = []
    for d in drives:
        if hp and d["hp"] != hp: continue
        if voltage and d["voltage"] != voltage: continue
        matches.append(d)
    
    return matches

def validate_drive_spec(part_number):
    """
    Validates a part number against Danfoss technical specs.
    """
    # Mock validation
    if part_number.startswith("131"):
        return True, "Valid VLT Series Drive."
    return False, "Unknown part number format."

def get_drive_manual_link(series):
    """
    Returns a link to the Danfoss documentation for a series.
    """
    base_url = "https://www.danfoss.com/en/search/?filter=type%3Adocumentation"
    return f"{base_url}&q={series}"
