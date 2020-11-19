from selenium import webdriver
import time
from selenium.common.exceptions import StaleElementReferenceException
from sys import platform
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if platform == "darwin":
    chrome_driver_path = os.path.join(BASE_DIR, 'bin/chromedriver_macos')
elif os.name == "nt":
    chrome_driver_path = os.path.join(BASE_DIR, 'bin/chromedriver_win32.exe')
else:
    chrome_driver_path = os.path.join(BASE_DIR, 'bin/chromedriver')

chrome_driver_path = os.path.normpath(chrome_driver_path)
print(chrome_driver_path)


class MercadonaScrapper(object):


    search_url = 'https://tienda.mercadona.es/categories/%d'

    def __init__(self):
        self.driver = webdriver.Chrome(chrome_driver_path)
        self.driver.implicitly_wait(2)

    # login when a cp needs to be introduced
    def login(self):
        cp = 46010
        input_cp = self.driver.find_element_by_name("postalCode")
        input_cp.send_keys(cp)
        form = self.driver.find_element_by_class_name("postal-code-checker")
        continue_button = form.find_element_by_tag_name('button')
        continue_button.click()
        self.remove_popup()

    def remove_popup(self):
        banner = self.driver.find_element_by_class_name('cookie-banner')
        banner.find_element_by_class_name('ui-button--primary').click()

    def get_products(self):
        products = []
        categories = self._get_categories()
        for super_category_element, name in categories:
            super_category_element.click()
            for category in self._get_super_category_elements(super_category_element):
                category.click()
                self.super_category_name = name
                self._get_category_name()
                products = products + self._scrap_elements()

        return products

    def _get_categories(self):
        # 112 is an arbitrary number to check all other categories
        self.search_in_category(112)
        super_categories_elements = self.driver.find_elements_by_class_name('category-menu__item')
        categories = []
        for super_category_element in super_categories_elements:
            super_category_name = super_category_element.find_element_by_tag_name('label').text
            categories.append((super_category_element, super_category_name))
        return categories

    def _get_super_category_elements(self, super_category_element):
        category_buttons = super_category_element.find_element_by_tag_name('ul').find_elements_by_tag_name('button')
        return category_buttons

    def search_in_category(self, category):
        self.driver.get(self.search_url % (category))
        self.login()

    def _get_category_name(self):
        category_element = self.driver.find_element_by_class_name("category-detail__name")
        self.category_name = category_element.text

    def _scrap_elements(self):
        product_elements = self.driver.find_elements_by_class_name("product-cell")
        products = []
        for product_element in product_elements:
            try:
                product = self._scrap_product(product_element)
                assert isinstance(product, Product)
            except StaleElementReferenceException:
                print("product not available")
        products.append(product)
        return products

    def _scrap_product(self, product_element):
        product_button = product_element.find_element_by_tag_name('button')
        product_button.click()
        product_details_element = self.driver.find_element_by_class_name('modal-content')

        name = product_details_element.find_element_by_class_name('title2-r').text

        weight_label = product_details_element.find_element_by_class_name('product-format').text
        weight = None
        volume = None
        expect_weight_unit = False
        quantity = 0
        for label in weight_label.split():
            if expect_weight_unit:
                if label.lower() in ('l', 'ml'):
                    volume = quantity
                    if label.lower() == 'l':
                        volume *= 1000
                    break
                elif label.lower() in ('kg', 'g'):
                    weight = quantity
                    if label.lower() == 'kg':
                        weight *= 1000
                    break
                else:
                    expect_weight_unit = False
            if label.isdigit(): 
                quantity = float(label)
                expect_weight_unit = True

        unit_price = product_details_element.find_element_by_class_name('product-price__unit-price').text
        unit_price = float(unit_price.split()[0].replace(',', '.'))

        thumbmail_elements = product_details_element.find_element_by_class_name("product-gallery-thumbnails")
        img_elements = thumbmail_elements.find_elements_by_tag_name('img')
        images = list(map(lambda e: e.get_attribute('src'), img_elements))

        current_url = self.driver.current_url
        id_str = current_url.split("/")[4]
        product_id = int(id_str)
        zeros_needed = 14 - len(id_str)
        barcode = product_id * (10 ** zeros_needed)

        product = Product(self.super_category_name, self.category_name, product_id, barcode, name, weight, volume, unit_price, images)
        self._leave_product_details()
        print(product)
        return product

    def _leave_product_details(self):
        unit_price = self.driver.find_element_by_class_name('modal-content__close').click()

    
    def __del__(self):
        try:
            self.driver.close()
        except:
            pass


class Product(object):

    def __init__(self, super_category, category, product_id, barcode, name, weight, volume, price, images):
        self.super_category = super_category
        self.category = category
        self.product_id = product_id
        self.barcode = barcode
        self.name = name
        self.weight = weight
        self.volume = volume
        self.price = price
        self.images = images

    def __repr__(self):
        return "Product: %s | %s | %s | %s | %s | %s | %s | %s | %d" % (
            self.product_id, 
            self.super_category, 
            self.category, 
            self.barcode, 
            self.name, 
            self.price, 
            self.weight, 
            self.volume, 
            len(self.images)
        )
