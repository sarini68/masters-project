import neo4j.v1


class DAL(object):

    def __init__(self, driver: neo4j.v1.Driver):
        self._cases = []
        self._performers = []

        self.driver = driver

    @property
    def session(self) -> neo4j.v1.Session:
        return self.driver.session()

    def fetch_performers(self):
        PERFORMER_NAMES_QUERY = '''
        match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer)
        return distinct p.name as name order by p.name
        '''

        performer_names = self.run_query(PERFORMER_NAMES_QUERY)
        self._performers = [record['name'] for record in performer_names]

        return self._performers

    @property
    def performers(self):
        return self._performers or self.fetch_performers()

    def fetch_cases(self):
        CASE_NAMES_QUERY = '''
        match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer)
        return distinct c.id as id order by c.id
        '''

        case_names = self.run_query(CASE_NAMES_QUERY)
        self._cases = [record['id'] for record in case_names]

        return self._cases

    @property
    def cases(self):
        return self._cases or self.fetch_cases()

    def run_query(self, query):
        with self.session as session:
            return session.run(query)

    def seed_database(self):
        with self.session as s:
            # Load database graph from csv
            graph_from_csv_query = '''
            LOAD CSV FROM 'file:///log.csv' AS line FIELDTERMINATOR ';'
            CREATE (c:case {id:line[0]})
            CREATE (a:activity {name:line[1]})
            SET a.created = line[3]
            CREATE (p:performer {name:line[2]})
            SET p.created = line[3]
            CREATE (c)-[:includes]->(a)
            CREATE (a)-[:performed_by]->(p)
            '''

            s.run(graph_from_csv_query)
