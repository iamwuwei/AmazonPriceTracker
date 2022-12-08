from amazon_config import (
    get_chrome_web_driver,
    get_web_driver_options,
    set_ignore_certificate_error,
    set_browser_as_incognito,
    NAME,
    CURRENCY,
    FILTERS,
    BASE_URL,
    DIRECTORY
)
from selenium.webdriver.common.keys import Keys
import time
from datetime import datetime
import json

class GenerateReport:
    def __init__(self, file_name, filters, base_link, currency, data):
        self.data = data 
        self.file_name = file_name
        self.filters = filters
        self.base_link = base_link
        self.currency = currency
        
        report = {
            'title': self.file_name,
            'date': self.get_now(),
            'best_item': self.get_best_item(),
            'currency': self.currency,
            # 'filters': self.filters,
            'base_link': self.base_link,
            'products': self.data
        }
        print("Creating report...")
        with open(f'{DIRECTORY}/{file_name}.json', 'w', encoding='utf8') as f:
            json.dump(report, f, ensure_ascii=False)
        print("Done...")

    def get_now(self):
        now = datetime.now()
        return now.strftime("%d/%m/%Y %H:%M:%S")
    def get_best_item(self):
        try:
            return sorted(self.data, key=lambda k: k['price'])[0]
        except Exception as e:
            print(e)
            print("problem with sort")
            return None
            

class AmazonAPI:
    def __init__(self, search_term, filters, base_url, currency):
        self.base_url = base_url
        self.search_term = search_term
        options = get_web_driver_options()
        set_ignore_certificate_error(options)
        set_browser_as_incognito(options)
        self.driver = get_chrome_web_driver(options)
        self.currency = currency
        # self.price_filters = 
    def run(self):
        print("Start script...")
        print(f'Looking for {self.search_term} products ...')
        links = self.get_products_links()
        time.sleep(1)
        if not links:
            print("no links")
            return 

        print(f"Got {len(links)} links to product")
        print("Getting detail ...")
        products = self.get_products_detail(links)
        print(f"Got {len(products)} products ...")
        self.driver.quit()
        return products

    def get_products_links(self):
        self.driver.get(self.base_url)
        # element = self.driver.find_element_by_xpath('//*[@id="twotabsearchtextbox"]')
        element = self.driver.find_element_by_id('twotabsearchtextbox')
        element.send_keys(self.search_term)
        element.send_keys(Keys.ENTER)
        time.sleep(2)
        # price filter
        # self.driver.get(f'{self.driver.current_url}{self.price_filter}')
        result_list = self.driver.find_elements_by_css_selector('.s-main-slot.s-result-list.s-search-results.sg-row')
        links = []
        try:
            #get search result items link
            results = result_list[0].find_elements_by_xpath("//div/div/div/div/div/div/div[1]/span/a")
            links = [link.get_attribute('href') for link in results]
            return links
        except Exception as e:
            print("didn't get any products ...")
            print(e)
            return links

    def get_products_detail(self, links):
        asins = self.get_asins(links)
        products = []
        for asin in asins:
            product = self.get_single_product_detail(asin)
            if product:
                products.append(product)
        return products

    def get_asins(self, links):
        return [self.get_asin(link) for link in links]

    def get_asin(self, link):
        # link.find('/dp/') + 4:link.find('/ref') = /dp/B0B9XZ31XD/ref= {get asin between /dp/ and /ref}
        return link[link.find('/dp/') + 4:link.find('/ref')]

    def get_single_product_detail(self, asin):
        print(f"Product ID: {asin} -> getting data ...")
        product_short_url = self.shorten_url(asin)
        self.driver.get(f'{product_short_url}')
        time.sleep(2)
        title = self.get_title()
        seller = self.get_seller()
        price = self.get_price()

        if title and seller and price:
            product_detail = {
                'asin': asin, 
                'url': product_short_url,
                'title': title,
                "seller": seller,
                "price": price
            }
            print(product_detail)
            return product_detail
        return None

    def get_title(self):
        try:
            return self.driver.find_element_by_id('productTitle').text
        except Exception as e:
            print(e)
            print(f"Cant get title of product - {self.driver.current_url}")
            return None

    def get_seller(self):
        try:
            return self.driver.find_element_by_id('bylineInfo').text
        except Exception as e:
            print(e)
            print(f"Cant get seller of product - {self.driver.current_url}")
            return None

    def get_price(self):
        price = None
        try:
            price = self.driver.find_element_by_id('priceblock_ourprice').text
            # price = self.convert_price(price)
            return price
        except Exception as e:
            print(e)
            print(f"Cant get price of product - {self.driver.current_url}")
            return None
    # def convert_price(self, price):
    #     price = price.split(self.currency)[1]
    #     try:
    #         price = price.split("\n")[0] + ""
    def shorten_url(self, asin):
        return self.base_url + 'dp/' + asin
if __name__ == '__main__':
    print("HEY!!!")
    amz = AmazonAPI(NAME, FILTERS, BASE_URL, CURRENCY)
    data = amz.run()
    GenerateReport(NAME, FILTERS, BASE_URL, CURRENCY, data)