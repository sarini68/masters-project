import json

from neo4j.v1 import GraphDatabase, basic_auth

from data_access_layer import DAL

driver = GraphDatabase.driver("bolt://localhost:7687",
                              auth=basic_auth("neo4j", "123456"))

dal = DAL(driver)
dal.seed_database()
print('Performers: {}'.format(dal.performers))
print('Cases: {}'.format(dal.cases))
print(json.dumps(dal.works_with[0].id))
print(json.dumps(dal.works_with[0].time))
print(json.dumps(dal.works_with[0].performer))
