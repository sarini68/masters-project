from neo4j.v1 import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687")


class Query(object):
    graph_from_csv = '''
    LOAD CSV FROM 'file:///log.csv' AS line FIELDTERMINATOR ';'
    CREATE (c:case {id:line[0]})
    CREATE (a:activity {name:line[1]})
    SET a.created = line[3]
    CREATE (p:performer {name:line[2]})
    SET p.created = line[3]
    CREATE (c)-[:includes]->(a)
    CREATE (a)-[:performed_by]->(p)
    '''

    # Query of the unique names of the performers involved in at least one case
    performer_names = '''
    match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer)
    return distinct p.name as name order by p.name
    '''

    # Query of the unique names of the cases
    case_names = '''
    match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer)
    return distinct c.id as id order by c.id
    '''


with driver.session() as s:
    # Load database graph from csv
    s.run(Query.graph_from_csv)

    # Extract the list of performers involved in at least one case
    performers = [record['name'] for record in s.run(Query.performer_names)]
    print('Performers: {}'.format(performers))

    # Extract the list of unique case names
    cases = [record['id'] for record in s.run(Query.case_names)]
    print("Cases: {}".format(cases))
