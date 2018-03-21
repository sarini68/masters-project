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

    @property
    def color_case(self):
        # Prototype uses colormap (from matplotlib) to display wsa (and wsa')
        # Note: there are many drawbacks (e.g., at most 10 different performers are displayed)
        # So: another way should be considered (preferably web-based architecture)

        # color_case is the data structure used to generate wsa through the colormap function
        # each color_case is a two indexes list:
        #   the first index is about the number of the case,
        #   the second is about performers involved in that case
        color_case = []

        for entry in self.works_with:  # type: DAL.WorksWithEntry
            color_tmp = []

            for performer in entry.performer:
                color_tmp.append(self.performers.index(performer))
            color_case.append(color_tmp)

        print('original color_case: {}'.format(color_case))

        # One more drawback of using color map is that to generate the correct colormap,
        # all the rows (cases) should have the same length (the same number of activities)
        # so color_case is modified to make all rows the same length (the max_case_length)
        # and a new value is inserted (total number of performers + 1) in color_case  to fill in the blanks
        max_case_length = max(len(case) for case in color_case)
        print('max case length: {}'.format(max_case_length))
        blank_value = len(self.performers) + 1
        color_case = [case + [blank_value] * (max_case_length - len(case)) for case in color_case]
        print('new color_case: {}'.format(color_case))
        color_case.reverse()

        return color_case

    def color_case_from_pattern(self, pattern):
        # stat_pattern contains the count of the matches from the pattern for any of the case
        stat_pattern = []
        for i in range(len(self.cases)):
            stat_pattern.append(len(pattern[i]))

        print('stat_pattern')
        print(stat_pattern)

        # building color_case_pattern from color_case.
        # color_case_pattern is the list containing the number of performers matching the pattern after the query
        # color_case_pattern would be used to build a colormap describing wsa',
        # i.e. the wsa image after the match with the considered pattern
        # we consider to build both wsa and wsa' images, to promote visual comparison to help users to easily recognize
        # the matches found considering a pattern expressed through the query

        # using deepcopy module to copy color_case_pattern from color_case
        from copy import deepcopy

        # color_case_pattern is built from color_case (the original wsa)
        # and then modified according to the results of the query defined through the query pattern interface
        color_case_pattern = deepcopy(self.color_case)

        # reversing color_case_pattern to have the situation as in the original color_case
        # (before reversing for displaying purposes)
        color_case_pattern.reverse()

        # building matches in color_case_pattern; for any of the match found,
        # the corresponding position in the color_case_pattern lisst
        # is filled with the value len(performer_dist)+1 (that is
        # the same color used in color_case to fill in the blanks).
        # To verify whether another color for the match would be more appropriated,
        # may be the color complementary to the color of the corresponding performer:
        # e.g., computed by MAX_COLOR - works_with[j][1].index(pattern[j][i][0][1])
        for j in range(len(self.cases)):
            for i in range(len(pattern[j])):
                x = self.works_with[j].id.index(pattern[j][i][0][1])
                color_case_pattern[j][x] = len(self.performers) + 1
                y = self.works_with[j].id.index(pattern[j][i][1][1])
                color_case_pattern[j][y] = len(self.performers) + 1

        print('color_case_pattern')
        print(color_case_pattern)

        # reversing color_case_pattern as done in color_case for visualization purposes
        # (i.e., to put first case at the top row of the colormap)
        color_case_pattern.reverse()

        return color_case_pattern
