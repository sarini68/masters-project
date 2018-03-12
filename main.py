from neo4j.v1 import GraphDatabase, basic_auth

import ui
from data_access_layer import DAL

driver = GraphDatabase.driver("bolt://localhost:7687",
                              auth=basic_auth("neo4j", "123456"))

dal = DAL(driver)
# dal.seed_database()
# print('Cases: {}'.format(dal.cases))
# print('works_with[0]:')
# print('\tids: {}'.format(dal.works_with[0].id))
# print('\ttimes: {}'.format(dal.works_with[0].time))
# print('\tperformers: {}'.format(dal.works_with[0].performer))
# print('Activities: {}'.format(dal.activity))

ui.ProgramGUI(dal)
