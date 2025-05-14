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
from urllib.parse import urlparse, parse_qs

URL = "https://www.volby.cz/pls/ps2017nss/ps311?xjazyk=CZ&xkraj=13&xobec=592005&xvyber=7202"

def get_html_data(url):

    try:    
        html_data = requests.get(url, timeout = 1)
        html_data.raise_for_status()

# later test the exceptions !!!
    except requests.exceptions.ConnectionError as errc:
        print("Connection failed:")
        raise SystemExit(errc)
    
    except requests.exceptions.HTTPError as errh:
        raise SystemExit(errh)
    
    except requests.exceptions.Timeout as errt:
        print("Connection timed out:", "\n", errt)
        ... # Add "Try again" to the script

    except requests.exceptions.RequestException as errre:
        raise SystemExit(errre)

    else:
        return html_data


def html_parse(html_data):
    
    parsed_html = bs(html_data.text, features="html.parser")

    return parsed_html


def data_scraper(parsed_html):

# alternativly modify to:
# <div class="tab_full_ps311">
# <a href="ps311?xjazyk=CZ&xkraj=13&xobec=592005&xvyber=7202&amp;xf=1">úplné zobrazení</a>
# </div>
# => more universal

    village_url = parsed_html.find("td", class_=True, headers="t1sa3").a["href"]

    parsed_village_url = urlparse(village_url)
    village_number = parse_qs(parsed_village_url.query)["xobec"][0]


    village_selector = parsed_html.select_one("#publikace > h3:nth-child(4)")
    village_name = str(village_selector.string).split(maxsplit=1)[1].strip()


    main_table = parsed_html.find(id="ps311_t1")
    main_table_value = main_table.find_all(class_="cislo", headers=["sa2", "sa3", "sa6"])

    #testing dict - main table data
    data_header = ["registered", "envelopes", "valid"]
    data_value = [tag.string for tag in main_table_value]
    data_dict = dict(zip(data_header, data_value))

    return data_dict

print(data_scraper(html_parse(get_html_data(URL))))