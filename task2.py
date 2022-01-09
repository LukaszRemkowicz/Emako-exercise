import datetime
import json
from sqlite3 import connect

from requests import request

sql = connect(database="database.sqlite")
cursor = sql.cursor()

for target in [-2, -3]:
    try:
        flag = True
        response = request(
            "GET", f"https://recruitment.developers.emako.pl/"
                   f"products/example?id={target}"
        )
        response_content = response.content

        with open("tmp.txt", "wb") as file:
            file.write(response_content)
            file.flush()
        print(f"data downloaded from server {len(response_content)}")
        with open("tmp.txt", "r") as file:
            product = json.load(file)

        product_id = product["id"]

        if product["type"] != "bundle":
            print("product loaded")

            for supply in product["details"]["supply"]:
                for stock_data in supply["stock_data"]:
                    if stock_data["stock_id"] == 1:
                        productSupply = stock_data["quantity"]

                        cursor = sql.cursor()
                        sql_query = """INSERT INTO product_stocks(time, product_id, variant_id, stock_id, supply)
                                        VALUES (?, ?, ?, ?, ?)"""

                        data = (
                            datetime.datetime.now(),
                            int(product_id),
                            int(supply["variant_id"]),
                            1,
                            int(productSupply)
                        )

                        cursor.execute(sql_query, data)

        if product["type"] == "bundle":
            print("bundle loaded")
            products = [p['id'] for p in product['bundle_items']]
            print(f"products {len(products)}")
            all_supply = []

            for prodd in products:
                res = request(
                    "GET", f"https://recruitment.developers.emako.pl/"
                           f"products/example?id={prodd}"
                )
                respContent = res.content
                with open("tmp.txt", "wb") as file:
                    file.write(respContent)
                    file.flush()
                with open("tmp.txt", "r") as file:
                    product = json.load(file)

                supply = sum([
                    stock['quantity'] for supply in product["details"]["supply"]
                    for stock in supply["stock_data"] if stock["stock_id"] == 1
                ])

                all_supply.append(supply)

            productSupply = min(all_supply)

            sql_query = """INSERT INTO product_stocks (time, product_id, variant_id, stock_id, supply)
                           VALUES (?, ?, NULL, ?, ?)"""

            data = (
                datetime.datetime.now(),
                int(product_id),
                1,
                int(productSupply)
            )
            cursor.execute(sql_query, data)

    except Exception as e:
        print('Exception', e)
        flag = False

    if flag:
        print("ok")
    else:
        print("error")

sql.commit()
sql.close()
