"""
elections_scraper.py: Third project for ENGETO online Academy Data Analyst with Python

author: Petr Boček
email: bocek2@seznam.cz
Discord: Seth_Cz#8510

"""
# project_URL: https://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ

import sys
import textwrap
import requests
import re
import csv
import argparse
from bs4 import BeautifulSoup as bs, element
from urllib.parse import urlparse, parse_qs, urljoin
from typing import TYPE_CHECKING


WEB_BASE: str = "https://www.volby.cz/pls/ps2017nss/"


def mandatory_args() -> tuple[str, str]:
    """
    Use the argparse module to check whether the user entered mandatory arguments
    and whether they are in the correct form and order.
    
    Returns:
        args.url, args.file_name (tuple(str, str)): User-entered URL and name of file, which are stored in tuple.
    """

    def url_check(url: str) -> str:

        if re.match(f"^{WEB_BASE}", url):
            return url
        else:
            raise argparse.ArgumentTypeError(f"'{url}' must be valid URL of the specified district")
    
    def file_name_check(file_name: str) -> str:
        
        if file_name.endswith(".csv"):
            return file_name
        else:
            raise argparse.ArgumentTypeError(f"'{file_name}' should have format: 'filename.csv'")
    
    parser = argparse.ArgumentParser(prog="Election Scraper",
                                    description="""
                                                The 'Elections scraper' scrapes data from a webpage 
                                                corresponding to the selected administrative 
                                                unit's URL and saves the extracted data into a 
                                                CSV file with a specified filename.
                                                """
                                    )
    parser.add_argument("url", 
                        help="User-defined 'URL' (wrapped in quotes) of the administrative unit", 
                        action="store", metavar="<URL>", type=url_check)
    parser.add_argument("file_name", 
                        help="'filename.csv' where the results should be saved", 
                        action="store", metavar="<file_name>", type=file_name_check)
    args = parser.parse_args()

    return args.url, args.file_name


def get_raw_html(url: str) -> requests.Response:
    """
    Use the 'Requests' library and send request to the user-specified URL. Return its response.

    Args:
        url (str): User-specified URL of chosen district.

    Returns:
        request_result (request.Response): Response object of the Requests library.
    """

    try:    
        request_result = requests.get(url, timeout = 20)
        request_result.raise_for_status()

    except requests.exceptions.ConnectionError as errc:
        print("Connection failed:")
        raise SystemExit(errc)
    
    except requests.exceptions.HTTPError as errh:
        print("Somthing went wrong...")
        raise SystemExit(errh)
    
    except requests.exceptions.Timeout as errt:
        print("Connection timed out:")
        raise SystemExit(errt)

    except requests.exceptions.RequestException as errre:
        raise SystemExit(errre)

    else:
        return request_result


def html_parse(request_result: requests.Response) -> bs:
    """Parse requests.Response object with BeautifulSoup4 Library."""    
    parsed_result = bs(request_result.text, features="html.parser")

    return parsed_result


def villages_rel_url_scraper(parsed_result: bs) -> element.ResultSet[element.NavigableString]:
    """Scrap relative village URL from the parsed village HTML. Return bs4.ResultSet of NavigableStrings."""    
    villages_url_tags = parsed_result.find_all("td", class_="cislo", headers=re.compile("t.sa1 t.sb1"))

    villages_rel_urls = [tag.a["href"] for tag in villages_url_tags]
    
    return villages_rel_urls


def url_completer(villages_rel_urls: element.ResultSet[element.NavigableString]) -> list[str]:
    """Combine URL base with scraped relative URL into the absolute URL and save it in a list."""
    villages_urls = [urljoin(WEB_BASE, url) for url in villages_rel_urls]
    
    return villages_urls


def elections_results_scraper(parsed_result: bs) -> dict[str, str]:
    """
    Find 'village name', 'village number', 'overall village elections results' 
    and 'names and results of election parties' in parsed HTML.
    
    Args:
        parsed_result (BS4 object): Parsed HTML of village's URL.
    
    Returns:
        scrap_data_dict (dict{str: str}): Results stored in dictionary."""

    scrap_data_dict = dict(code="", location="", registered="", envelopes="", valid="")    
    village_number_url = parsed_result.find("div", class_="tab_full_ps311").a["href"]

    #village number
    parsed_village_number_url = urlparse(village_number_url)
    village_number = parse_qs(parsed_village_number_url.query)["xobec"][0]
    scrap_data_dict["code"] = village_number

    # village name
    village_name_selector = parsed_result.select_one("#publikace > h3:nth-child(4)")
    village_name = str(village_name_selector.string).split(maxsplit=1)[1].strip()
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


def combine_scraped_data(villages_urls: list[str]) -> list[dict[str, str]]:
    """
    Iterate through the given list of URLs and for each URL append result dictionary to the list.

    Args:
        villages_urls (list[str]): List of village URLs for requested district.
    
    Returns:
        overall_data (list[dict{str: str}]): List of dictioneries with the retrieved data.
    """

    overall_data = list()

    for url in villages_urls:
        single_village_data = elections_results_scraper(html_parse(get_raw_html(url)))
        overall_data.append(single_village_data)
    
    return overall_data

def data_writer(overall_data: list[dict[str, str]], file_name: str, _mode: str="x") -> None:
    """
    Write the scraped data to a file with the specified name.

    Args:
        overall_data (list[dict{str: str}]): List of dictioneries with the retrieved data. 
        file_name (str): User-specified output file name.
        _mode (str): Default parameter for open() function.
    Returns: None
    """

    try:
        with open(file_name, mode=_mode, encoding="utf-8", newline="") as result_file:
            writer = csv.DictWriter(result_file, fieldnames=overall_data[0].keys())
            writer.writeheader()
            writer.writerows(overall_data)

    except FileExistsError as feer:

        proceed_check = input(textwrap.dedent(f"""
                            File with specified name '{file_name}' already exists!
                            If you continue, the existing data will be overwritten!!
                            Want to continue?[Y/N]
                            """)
                            )
        
        if proceed_check.lower() == "y":
            data_writer(overall_data, file_name, "w")
           
        elif proceed_check.lower() == "n":
            print("Terminating the program.")
            sys.exit(0)       
        else:
            print(f"{proceed_check} is not valid command! Terminating the program!")
            sys.exit(1)

    except RuntimeError as rter:
        print(f"Somthing went wrong: {rter}")
        sys.exit(1)
    except OSError as oser:
        print(f"This went wrong: {oser}")
        sys.exit(1)
    except Exception as exc:
        print(exc)
        sys.exit(1)
    else:
        print(f"File '{file_name}' succesfuly created with requested elections data\nProgram terminated")
        sys.exit(0)


def main():
    
    args = mandatory_args()

    soup = html_parse(get_raw_html(args[0]))

    links = url_completer(villages_rel_url_scraper(soup))

    scraped_data = combine_scraped_data(links)

    data_writer(scraped_data, args[1])


if __name__ == "__main__":
    main()

# https://github.com/DutyStrom/elections_scraper.git