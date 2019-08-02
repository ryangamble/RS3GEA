import json

import requests
import urllib.request
from bs4 import BeautifulSoup


class APIAException(Exception):
    def __init__(self, *args):
        Exception.__init__(self, *args)


class DataLoader:
    def __init__(self, category_ids):
        self.category_ids = category_ids

    def _get_api_data(self, call_type, category_id=None, first_letter=None, page_number=None):
        category_url = "https://services.runescape.com/m=itemdb_rs/api/catalogue/category.json?category=X"
        item_url = "https://services.runescape.com/m=itemdb_rs/api/catalogue/items.json?category=X&alpha=Y&page=Z"

        if call_type is None:
            raise APIAException("Invalid API Call. Call Type Required")
        if category_id is None:
            raise APIAException("Invalid API URL. Category ID Required.")

        if call_type == "category":
            request = category_url.replace("X", str(category_id))
            response = requests.get(request)
            if response.status_code is not 200:
                raise APIAException("HTTP Error. API Response Was Not 200: " + response.status_code)
            else:
                return str(response.content)
        elif call_type == "item":
            if first_letter is None:
                raise APIAException("Invalid API URL. First Letter Required.")
            if page_number is None:
                raise APIAException("Invalid API URL. Page Number Required.")

            request = item_url.replace("X", str(category_id)).replace("Y", str(first_letter)).replace("Z", str(page_number))
            response = requests.get(request)
            if response.status_code is not 200:
                raise APIAException("HTTP Error. API Response Was Not 200: " + response.status_code)
            else:
                return str(response.content)
        else:
            raise APIAException("Invalid API Call. Unrecognized Call Type: " + str(call_type))

    # TODO add error exceptions
    def _get_web_data(self, item_name):
        wiki_url = "https://runescape.fandom.com/wiki/X"
        wiki_url.replace("X", item_name)
        page = urllib.request.urlopen(wiki_url)
        soup = BeautifulSoup(page)
        return soup.text

    def _scrape_data_text(self, data_text, search_term, ending_character):
        search_result = []

        # Find the index of the first data value
        data_index = data_text.find(search_term)
        # If the data value isn't found, raise an exception
        if data_index is -1:
            raise APIAException("Unexpected Response From API. " + search_term + " not found.")
        else:
            # Add each data value to the result list
            while data_index is not -1:
                # Find the index of the ending character
                data_end_index = data_text.find(ending_character, data_index + len(search_term))
                # Find the data value being searched for
                data = data_text[(data_index + len(search_term)):data_end_index]
                # Add the id to the list of ids
                search_result.append(data)
                # Trim off the processed portion of the data text
                data_text = data_text[data_end_index:]
                # Find the index of the next data value
                data_index = data_text.find(search_term)

        return search_result

    def _get_item_ids(self):
        items_per_item_page = 12
        letters = ['#', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r',
                   's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        all_item_ids = []

        # Load data from each category id provided
        for category_index in range(len(self.category_ids)):
            # Call the API for the category data
            category_data = self._get_api_data("category", self.category_ids[category_index])
            num_items = self._scrape_data_text(category_data, "\"items\":", "}")
            letters = self._scrape_data_text(category_data, "\"letter\":\"", "\"")

            for item_count in range(len(num_items)):
                # Find the number of pages to check for the letter
                if (num_items[item_count].isnumeric()) or (num_items is "#"):
                    if int(num_items[item_count]) < 0:
                        raise APIAException("Unexpected Response From API. Item Count Negative: " + num_items[item_count])
                    elif int(num_items[item_count]) == 0:
                        num_pages = 0
                    elif int(num_items[item_count]) <= items_per_item_page:
                        num_pages = 1
                    else:
                        num_pages = int((int(num_items[item_count]) - (int(num_items[item_count]) % items_per_item_page)) / items_per_item_page) + 1

                    # Check each page of item data for a letter
                    for page in range(num_pages):
                        if letters[item_count] not in letters:
                            raise APIAException("Unexpected Response From API. Letter Not Recognized: " + letters[item_count])
                        else:
                            # Call the API for the item data
                            item_data = self._get_api_data("item", self.category_ids[category_index], letters[item_count], page + 1)
                            item_ids = self._scrape_data_text(item_data, "\"id\":", ",")
                            all_item_ids += item_ids
                else:
                    raise APIAException("Unexpected Response From API. Item Count: " + str(num_items))

        return all_item_ids

    # TODO build item objects containing price and crafting information
    def build_item_objects(self):
        items = []

        item_ids = self._get_item_ids()

        for item_id in item_ids:
            detail_data = self._get_api_data("detail", self.category_ids[category_index])