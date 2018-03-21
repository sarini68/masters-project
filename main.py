import argparse

from neo4j.v1 import GraphDatabase, basic_auth

import ui
from data_access_layer import DAL

DEFAULT_DRIVER_URI = "bolt://localhost:7687"


def parse_args():
    """Parses commandline arguments using argparse library"""
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("db_username",
                        help="username of the neo4j database")
    parser.add_argument("db_password",
                        help="password of the given user of database")
    parser.add_argument("--driver-uri",
                        nargs="?",
                        default=DEFAULT_DRIVER_URI,
                        help="Uri to create noe4j db driver")
    parser.add_argument("--seed-db",
                        action='store_true',
                        help="pass if database is not seeded")
    return parser.parse_args()


args = parse_args()
print("Connecting to <{}> as an user <{}>".format(args.driver_uri, args.db_username))
driver = GraphDatabase.driver(args.driver_uri, auth=basic_auth(args.db_username, args.db_password))
dal = DAL(driver)

if args.seed_db:
    print("Seeding database")
    dal.seed_database()

ui.ProgramGUI(dal)
