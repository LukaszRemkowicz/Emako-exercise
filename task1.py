import asyncio
from sqlite3 import connect
import json
import base64

import requests

DOMAIN = "https://recruitment.developers.emako.pl"

HTTP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def user_login() -> requests.Session:
    """ Login user with password/username generated in credentials.json """

    with open('credentials.json') as file:
        credentials = json.load(file)

    user_credentials = credentials['username'] + ":" + credentials['password']
    encoded_credentials = base64.b64encode(user_credentials.encode()).decode()

    HTTP_HEADERS['Authorization'] = 'Basic ' + encoded_credentials
    session = requests.Session()

    try:
        res = session.post(DOMAIN + '/login/aws?grant_type=bearer', headers=HTTP_HEADERS)
        session.headers['Authorization'] = 'Bearer ' + res.json()['access_token']
        print('You have been logged successful')

        return session

    except requests.exceptions.RequestException as e:
        print("Connection Request Error", e)


async def prducts_for_update(session: requests.Session) -> list:
    """ find products to update """

    all_products = session.get(DOMAIN + "/products", json={"detailed": True}).json()['result']
    prducts_for_update = []

    for product in all_products:
        if product["type"] != "bundle":
            stocks = product['details']['supply']
            if stocks:
                for stock in stocks:
                    for stock_data in stock.get('stock_data'):

                        sql_query = """SELECT supply FROM product_stocks 
                                        WHERE product_id=?
                                        AND variant_id=?
                                        AND stock_id=?
                                        ORDER BY time DESC"""
                        try:
                            data = (
                                product.get('id'),
                                int(stock.get('variant_id')),
                                int(stock_data.get('stock_id'))
                            )
                            cursor.execute(sql_query, data)

                        except TypeError as e:
                            print(e)

                        result = cursor.fetchone()
                        if result:
                            prducts_for_update.append(product)
                            stock_data['quantity'] = result[0]

    return prducts_for_update


async def fetch_products(session: requests.Session, products: list) -> None:

    products_pagination = [products[num:num + 20] for num in range(0, len(products), 20)]
    for paginate in products_pagination:
        try:
            res = session.put(DOMAIN + '/products', json={"products": paginate})
            if res:
                print('Update successfull')
        except requests.exceptions.RequestException as e:
            print("Connection Request Error", e)


sql = connect("database.sqlite")
cursor = sql.cursor()

session = user_login()

asyncio.run(fetch_products(session, asyncio.run(prducts_for_update(session))))

cursor.close()
sql.close()
session.close()
