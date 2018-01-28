from neo4j.v1 import GraphDatabase

from data_access_layer import DAL

driver = GraphDatabase.driver("bolt://localhost:7687")

dal = DAL(driver)
dal.seed_database()
print('Performers: {}'.format(dal.performers))
print("Cases: {}".format(dal.cases))
