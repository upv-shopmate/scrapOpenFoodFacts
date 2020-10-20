import requests
from bs4 import BeautifulSoup
import re
import random
import unicodedata
import sys
import numpy as np

from countries import countries_ES

MAIN_URL = "https://world.openfoodfacts.org"
URL = "https://es.openfoodfacts.org/tienda/mercadona"

products = {}

# page count
LIMIT = 162 

if len(sys.argv) > 1:
    LIMIT = int(sys.argv[1])
print("LIMIT =", LIMIT)

def get_html(url, n=None):
    page = None
    if n:
        page = requests.get(url + "/" + str(n))
    else:
        page = requests.get(url)
    assert page is not None
    return page.text

# get products of that page
def get_products():
    ul = soup.find("ul", "products")
    if ul is not None:
        for a in ul.findChildren("a", recursive=True):
            title = a.get("title", None).partition("-")[0].strip()
            normalized_title = ''.join(filter(lambda c : ord(c) < 127, unicodedata.normalize("NFKC", title)))
            link = re.sub(r"producto", "product", MAIN_URL + a.get("href", None))
            gtin = re.match(r".*\/product\/(\d+)", link).group(1)
            products[gtin] = {
                "name": normalized_title,
                "link": link 
            }
            get_product(gtin, link)

        
def get_product(gtin, link):
    product_page_html = get_html(link)
    product_soup = BeautifulSoup(product_page_html, 'html.parser')
    get_weight(gtin, product_soup)
    get_origin(gtin, product_soup)
    get_brand(gtin, product_soup)
    get_categories(gtin, product_soup)
    get_images(gtin, product_soup)
    get_price(gtin)
    get_stock(gtin)
    get_edible(gtin)
    get_times_sold(gtin)
    get_units(gtin)


def get_units(gtin):
    units = np.random.choice([None, 1, 2, 3], p=[0.5, 0.2, 0.2, 0.1])
    products[gtin]["units"] = True

def get_edible(gtin):
    products[gtin]["edible"] = True

def get_images(gtin, product_soup):
    image_link = product_soup.find("img", id="og_image")
    if image_link is not None:
        products[gtin]["images"] = [image_link["src"]]
    else:
        products[gtin]["images"] = []

def get_stock(gtin):
    stock = random.randint(0, 1000)
    products[gtin]["available_stock"] = stock

def get_times_sold(gtin):
    times_sold = random.randint(0, 1000)
    products[gtin]["times_sold"] = times_sold

def get_price(gtin):
    price = round(random.uniform(0, 4), 2)
    products[gtin]["price"] = price

def get_brand(gtin, product_soup):
    brand_span = product_soup.find("span", text="Brands:")
    if brand_span is not None:
        brands = re.sub(r"Brands:", "", brand_span.parent.text).strip().split(", ")
        products[gtin]["brands"] = brands

def get_categories(gtin, product_soup):
    categories_span = product_soup.find("span", text="Categories:")
    if categories_span is not None:
        categories = re.sub(r"Categories:", "", categories_span.parent.text).strip().split(", ")
        products[gtin]["categories"] = categories

def get_origin(gtin, product_soup):
    origin_span = product_soup.find("span", text="Origin of ingredients:")
    if origin_span is not None:
        tokens = filter(None, re.split(r",|\s", re.sub(r"Origin of ingredients:", "", origin_span.parent.text).strip()))
        origin = next((value for key, value in countries_ES.items() if any(token.lower() in key.lower() for token in tokens)), None)
        products[gtin]["origin_country"] = origin

def get_weight(gtin, product_soup):
    quantity_span = product_soup.find("span", text="Quantity:")
    if quantity_span is not None:
        with_unit = re.sub(r"Quantity:", "", quantity_span.parent.text).strip()
        try:
            quantity = int(''.join(filter(str.isdigit, with_unit)))
        except ValueError:
            quantity = None
        products[gtin]["weight"] = quantity
    

def save():
    import json
    with open("products.json", "w") as f:
        json.dump(products, f)

n = 0
while n < LIMIT:
    html = get_html(URL, n)
    soup = BeautifulSoup(html, 'html.parser')
    get_products()
    save()
    n += 1
