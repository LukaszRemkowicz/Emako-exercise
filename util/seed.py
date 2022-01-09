from datetime import datetime
from json import load
from os import getpid, remove
from os.path import abspath, dirname, join
from random import Random
from sqlite3 import connect
from time import sleep

random = Random(getpid())

DB_FILE = join(dirname(dirname(abspath(__file__))), "database.sqlite")
try:
    remove(DB_FILE)
except FileNotFoundError:
    pass
database = connect(DB_FILE)
cursor = database.execute(
    """CREATE TABLE product_stocks (
    id          INTEGER  NOT NULL  PRIMARY KEY,
    time        TEXT     NOT NULL,
    product_id  INT      NOT NULL,
    variant_id  INT      NULL,
    stock_id    INT      NOT NULL,
    supply      INT      NOT NULL
);"""
)
database.commit()
cursor.close()

DATA_FILE = join(dirname(abspath(__file__)), "products.json")
with open(DATA_FILE, "r") as file:
    data = load(file)

ID_FILE = join(dirname(dirname(abspath(__file__))), "ids.csv")
with open(ID_FILE, "w") as file:
    for product in random.choices(data, k=30):
        file.write(f"{product['id']}\n")


for _ in range(5):
    for product in data:
        cursor = database.cursor()
        if product["type"] == "product":
            modify = random.randint(0, 3)
            for variant_supply in product["details"]["supply"]:
                for stock_data in variant_supply["stock_data"]:
                    supply = stock_data["quantity"]
                    if modify:
                        supply = max(
                            0, round(random.random() * supply) + random.randint(-5, 5)
                        )
                    cursor.execute(
                        "INSERT INTO product_stocks "
                        "(time, product_id, variant_id, stock_id, supply) "
                        "VALUES ('{}', {}, {}, {}, {})".format(
                            str(datetime.now())[:19],
                            product["id"],
                            variant_supply["variant_id"],
                            stock_data["stock_id"],
                            supply,
                        )
                    )
        database.commit()
        cursor.close()
    sleep(3)
