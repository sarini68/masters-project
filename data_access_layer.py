import collections

import neo4j.v1


class DAL(object):

    def __init__(self, driver: neo4j.v1.Driver):
        self._cases = []
        self._performers = []
        self._works_with = []

        self.driver = driver

    @property
    def session(self) -> neo4j.v1.Session:
        return self.driver.session()

    def run_query(self, query, *args, **kwargs):
        with self.session as session:
            return session.run(query, *args, **kwargs)

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

    PERFORMER_NAMES_QUERY = '''
    match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer)
    return distinct p.name as name order by p.name
    '''

    def fetch_performers(self):
        raw_performer_names = self.run_query(self.PERFORMER_NAMES_QUERY)
        return [record['name'] for record in raw_performer_names]

    @property
    def performers(self):
        if not self._performers:
            self._performers = self.fetch_performers()
        return self._performers

    CASE_NAMES_QUERY = '''
    match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer)
    return distinct c.id as id order by c.id
    '''

    def fetch_cases(self):
        raw_case_names = self.run_query(self.CASE_NAMES_QUERY)
        return [record['id'] for record in raw_case_names]

    @property
    def cases(self):
        if not self._cases:
            self._cases = self.fetch_cases()
        return self._cases

    WORKS_WITH_QUERY = '''
    match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer)
    where c.id = {case}
    return p.name as name, p.created as time, id(p) as id order by toFloat(time)
    '''

    WorksWithEntry = collections.namedtuple('WorksWithEntry',
                                            ['performer', 'time', 'id'])

    def fetch_works_with(self):
        works_with = []
        for case in self.cases:
            performer, _id, time = [], [], []
            query_result = self.run_query(self.WORKS_WITH_QUERY, {'case': case})
            for record in query_result:
                performer.append(record["name"])
                time.append(record["time"])
                _id.append(record["id"])
            works_with.append(self.WorksWithEntry(performer, time, _id))
        return works_with

    @property
    def works_with(self):
        if not self._works_with:
            self._works_with = self.fetch_works_with()
        return self._works_with
