from json import dump
from os.path import exists
from sys import exit, path

from requests import request
from requests.auth import HTTPBasicAuth

if not exists("credentials.json"):
    password = input("please enter credentials file password: ")
    print("extracting credentials...")
    response = request(
        "POST",
        "https://recruitment.developers.emako.pl/credentials",
        auth=HTTPBasicAuth("grasshopper", password),
    )
    if response.status_code != 200:
        print(
            f" - [ERROR] extraction failed, invalid password? (server responded {response.status_code})"
        )
        exit(2)
    with open("credentials.json", "w") as file:
        dump(response.json(), file)
        print(" - [OK] credentials dumped to ./credentials.json")

if not exists("database.sqlite"):
    print("seeding database...")
    path.insert(0, "util")
    import seed

    if not exists("database.sqlite"):
        print(" - [ERROR] failed to create database")
        exit(4)
    else:
        print(" - [OK] ./database.sqlite created")
