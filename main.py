import argparse
import os

from neo4j.v1 import GraphDatabase, basic_auth

import ui
from data_access_layer import DAL

DEFAULT_USER = "app92124873-nY8mkb"
DEFAULT_PASSWORD = "b.hrxpJRs9BVRq.ZqM9sSBJTMkU2OfR"
DEFAULT_DRIVER_URI = "bolt://hobby-ooiobamoecilgbkepmmbabal.dbs.graphenedb.com:24786"


def parse_args():
    """Parses commandline arguments using argparse library"""
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--db-username",
                        nargs="?",
                        default=os.environ.get("GRAPHENEDB_BOLT_USER", default=DEFAULT_USER),
                        help="username of the neo4j database")
    parser.add_argument("--db-password",
                        nargs="?",
                        default=os.environ.get("GRAPHENEDB_BOLT_PASSWORD", default=DEFAULT_PASSWORD),
                        help="password of the given user of database")
    parser.add_argument("--driver-uri",
                        nargs="?",
                        default=os.environ.get("GRAPHENEDB_BOLT_URL", default=DEFAULT_DRIVER_URI),
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
