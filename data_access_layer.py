import collections
from typing import List

import neo4j.v1


class DAL(object):

    def __init__(self, driver: neo4j.v1.Driver):
        self._cases = []
        self._performers = []
        self._works_with = []
        self._activity = []

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

        self.build_relations()

    def build_relations(self):
        # Build the works_with relation in the neo4j database.
        # To avoid the insertion of wrong relations (e.g. rework, when John performed A at two different times)
        # a check is added on the time of creation of performers, the first performer must be created before the second.
        # To prevent from alphanumerical ordering, time of creation is casted to float.

        query = '''
        match
            (c1)-[]->(a1)-[]->(p1:performer),
            (c2)-[]->(a2)-[]->(p2:performer)
        where
            c1.id = {case} and
            c2.id = {case} and
            p1.name={namename1} and
            p2.name={namename2} and
            a1.name={actname1} and
            a2.name={actname2} and
            toFloat(p1.created) < toFloat(p2.created)
        merge
            (p1)-[w:works_with]->(p2)
        return w
        '''

        for j, entry in enumerate(self.works_with):
            for i in range(len(entry.performer) - 1):
                self.run_query(
                    query,
                    {
                        'case': entry.case,
                        'namename1': entry.performer[i],
                        'namename2': entry.performer[i + 1],
                        'actname1': self.activity[j][i],
                        'actname2': self.activity[j][i + 1]
                    }
                )

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
                                            ['case', 'performer', 'time', 'id'])

    def fetch_works_with(self):
        works_with = []
        for case in self.cases:
            performer, _id, time = [], [], []
            query_result = self.run_query(self.WORKS_WITH_QUERY, {'case': case})
            for record in query_result:
                performer.append(record["name"])
                time.append(record["time"])
                _id.append(record["id"])
            works_with.append(self.WorksWithEntry(case, performer, time, _id))
        return works_with

    @property
    def works_with(self) -> List[WorksWithEntry]:
        if not self._works_with:
            self._works_with = self.fetch_works_with()
        return self._works_with

    ACTIVITY_QUERY = '''
    match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer)
    where c.id = {case} and p.name={namename1} and p.created={time}
    return act.name as name
    '''

    def fetch_activities(self):
        activity = []
        for entry in self.works_with:
            tmpa = []
            for name, time in zip(entry.performer, entry.time):
                params = {'case': entry.case, 'namename1': name, 'time': time}
                query_result = self.run_query(self.ACTIVITY_QUERY, params)
                tmpa.extend([record['name'] for record in query_result])
            activity.append(tmpa)

        return activity

    @property
    def activity(self):
        if not self._activity:
            self._activity = self.fetch_activities()
        return self._activity
