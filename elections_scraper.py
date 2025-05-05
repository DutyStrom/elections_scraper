"""
elections_scraper.py: Third project for ENGETO online Academy Data Analyst with Python

author: Petr Boček
email: bocek2@seznam.cz
Discord: Seth_Cz#8510

"""
# project_URL: https://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ

import sys
import os
import requests
from bs4 import BeautifulSoup as bs

URL = "https://www.volby.cz/pls/ps2017nss/ps311?xjazyk=CZ&xkraj=13&xobec=592005&xvyber=7202"

def get_html_data(URL):

    try:    
        html_data = requests.get(URL, timeout = 1)
        html_data.raise_for_status()

    except requests.exceptions.ConnectionError as errc:
        print("Connection Error:", errc)
    
    except requests.exceptions.HTTPError as errh:
        raise SystemExit(errh)
    
    except requests.exceptions.Timeout as errt:
        print("Connection timed out:", errt)

    except requests.exceptions.RequestException as errre:
        raise SystemExit(errre)

    return html_data
