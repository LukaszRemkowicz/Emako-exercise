import base64
from datetime import datetime, timedelta
from functools import lru_cache
from os import error
from typing import Dict, List, Optional
import json

from requests import request

DOMAIN = "https://recruitment.developers.emako.pl"


class Connector:

    @lru_cache
    def headers(self) -> Dict[str, str]:
        """ authenticate user """

        with open('credentials.json') as file:
            credentials = json.load(file)

        user_credentials = f"{credentials['username']}:{credentials['password']}"
        encoded_credentials = base64.b64encode(
            user_credentials.encode()
        ).decode()

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Basic " + encoded_credentials
        }

        res = request(
            "POST",
            DOMAIN + "/login/aws?grant_type=bearer",
            headers=headers
        )
        headers['Authorization'] = 'Bearer ' + res.json()['access_token']

        return headers

    def request(self, method: str, path: str, data: dict = {}) -> dict:

        return request(
            method, f"{DOMAIN}/{path}",
            json=data,
            headers=self.headers()
        ).json()

    def paginate_view(self, page: int, page_size: int,
                      products: list, ids: Optional[int] = None,
                      **kwargs) -> list:
        """ Paginate helper function """

        if page > 1:
            for page in range(1, page):
                data = {
                    "ids": ids,
                    "pagination": {"page_size": page_size, "index": page}
                }
                if kwargs:
                    for key, val in kwargs.items():
                        data[key] = val
                new_page = self.request("GET", "products", data)["result"]
                products.extend(new_page)
        return products

    def get_products(self, ids: Optional[List[int]] = None) -> List[dict]:

        result = self.request("GET", "products", {"ids": ids})
        products = result['result']

        return self.paginate_view(result['page_count'], 40, products, ids=ids)

    def get_all_products_summary(self) -> List[dict]:

        result = self.request("GET", "products", {"detailed": False})
        products = result['result']

        return self.paginate_view(
            result['page_count'],
            40,
            products,
            detailed=False
        )

    def get_new_products(self, newer_than: Optional[datetime] = None) -> List[dict]:

        if newer_than is None:
            newer_than = datetime.now() - timedelta(days=5)
        result = self.request("GET", "products")
        products = result['result']

        return self.paginate_view(
            result['page_count'],
            40,
            products,
            created_at={"start": newer_than.isoformat()}
        )

    def add_products(self, products: List[dict]) -> None:

        products_pagination = [
            products[num:num + 20] for num in range(0, len(products), 20)
        ]
        for paginate in products_pagination:
            try:
                res = self.request(
                    'POST',
                    'products',
                    {"products": paginate}
                )["result"]
                if res:
                    print('Update successfull')
            except error:
                print("Connection Request Error", error)

    def update_stocks(self, stocks: Dict[int, list]) -> None:

        current_data = self.get_products(list(stocks))
        for product_entry in current_data:
            product_entry["details"]["supply"] = stocks[
                product_entry["id"]
            ]['details']['supply']

        products_pagination = [
            current_data[num:num + 20] for num in range(0, len(current_data), 20)
        ]
        for paginate in products_pagination:
            try:
                res = self.request('PUT', 'products', {"products": paginate})
                if res:
                    print('Update successfull')
            except error:
                print("Connection Request Error", error)
