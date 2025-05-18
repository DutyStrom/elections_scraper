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
from urllib.parse import urlparse, parse_qs, urljoin
import re
import csv
import argparse

URL = "https://www.volby.cz/pls/ps2017nss/ps311?xjazyk=CZ&xkraj=13&xobec=592005&xvyber=7202"
URL_DISTRICT = "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7103"
web_base = "https://www.volby.cz/pls/ps2017nss/"


def mandatory_args():

    def url_check(url): # upravit na odpovidajici url
        parsed_url = urlparse(url)
        return bool(parsed_url.scheme) and bool(parsed_url.netloc)
    
    
    def file_name_check(file_name):
        return file_name.endswith(".csv")
    
    parser = argparse.ArgumentParser(prog="Election Scraper",
                                        description="""
                                                    The script scrapes data from a webpage 
                                                    corresponding to the selected administrative 
                                                    unit's URL and saves the extracted data into a 
                                                    CSV file with a specified filename.
                                                    """
                                    )
    parser.add_argument("url", help="User-defined URL of the administrative unit", action="store", metavar="<URL>")
    parser.add_argument("file_name", help="'Filename.csv' where the results should be saved", action="store", metavar="<file_name>")
    args = parser.parse_args()


    if not url_check(args.url) and not file_name_check(args.file_name): # lepe zformatovat a popsat
        print(f"First argument: '{args.url}' must be valid URL, and second argument: '{args.file_name}' should have format: 'filename.csv'")
        sys.exit()

    return args.url, args.file_name


def get_html_data(url):

    try:    
        request_result = requests.get(url, timeout = 1)
        request_result.raise_for_status()

# test the exceptions later !!!
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
        return request_result


def html_parse(request_result):
    
    parsed_result = bs(request_result.text, features="html.parser")

    return parsed_result


def villages_rel_url_scraper(parsed_result):
    
    villages_url_tags = parsed_result.find_all("td", class_="cislo", headers=re.compile("t.sa1 t.sb1"))

    villages_rel_urls = [tag.a["href"] for tag in villages_url_tags]
    
    return villages_rel_urls


def url_completer(villages_rel_urls):
    
    villages_urls = [urljoin(web_base, url) for url in villages_rel_urls]
    
    return villages_urls


def elections_results_scraper(parsed_result):

    scrap_data_dict = dict(code="", location="", registered="", envelopes="", valid="")    
    village_url = parsed_result.find("div", class_="tab_full_ps311").a["href"]

    #village number
    parsed_village_url = urlparse(village_url)
    village_number = parse_qs(parsed_village_url.query)["xobec"][0]
    scrap_data_dict["code"] = village_number

    # village name
    village_selector = parsed_result.select_one("#publikace > h3:nth-child(4)")
    village_name = str(village_selector.string).split(maxsplit=1)[1].strip()
    scrap_data_dict["location"] = village_name

    # overall village results
    main_table = parsed_result.find(id="ps311_t1")
    main_table_value = main_table.find_all(class_="cislo", headers=["sa2", "sa3", "sa6"])

    overall_results_header = ["registered", "envelopes", "valid"]
    overall_results_value = [tag.string for tag in main_table_value]
    overall_results_dict = dict(zip(overall_results_header, overall_results_value))

    scrap_data_dict |= overall_results_dict # update dictionary "scrap_data_dict" with dict "overall_results_dict"


    # parties names and results
    parties_names_tags = parsed_result.find_all("td", class_="overflow_name")
    parties_results_tags = parsed_result.find_all("td", headers=re.compile("t.sa2 t.sb3"))
    parties_dict = {
                    party_name_tag.string: party_result_tag.string
                for (party_name_tag, party_result_tag)
                in zip(parties_names_tags, parties_results_tags)
                }
    
    scrap_data_dict |= parties_dict # update dictionary "scrap_data_dict" with dict "parties_dict"

    return scrap_data_dict


def combine_scraped_data(villages_urls):

    overall_raw_data = list()

    for url in villages_urls:
        single_raw_data = elections_results_scraper(html_parse(get_html_data(url)))
        overall_raw_data.append(single_raw_data)
    
    return overall_raw_data



#print(elections_results_scraper(html_parse(get_html_data(URL))))
#print(villages_rel_url_scraper(html_parse(get_html_data(URL_DISTRICT))))
mandatory_args()
print(combine_scraped_data(url_completer(villages_rel_url_scraper(html_parse(get_html_data(URL_DISTRICT))))))


# https://github.com/DutyStrom/elections_scraper.git