class QueryBuilder:

    def __init__(self):
        self.pattern_length = None
        self.pattern_length_to = None
        self.pattern_length_from = None

        self.performer_one = '.*'
        self.performer_two = '.*'

        self.same_activity = True
        self.same_performer = False

    @property
    def length_range(self):
        if self.pattern_length:
            return self.pattern_length

        length_range = f"{self.pattern_length_from or ''}..{self.pattern_length_to or ''}"

        return length_range if length_range != '..' else ''

    @property
    def performer_cmp(self):
        return '=' if self.same_performer else '<>'

    @property
    def activity_cmp(self):
        return '=' if self.same_activity else '<>'

    def build(self):
        return f'''
            match
                (c1)-[]->(a1)-[]->
                (p1:performer)-[:works_with*{self.length_range}]->(p2:performer)
                <-[]-(a2)<-[]-(c2)
            where
                c1.id = {{case}} and
                c2.id = {{case}} and
                p1.name=~'{self.performer_one}' and
                p2.name=~'{self.performer_two}' and
                p1.name{self.performer_cmp}p2.name' and
                a1.name{self.activity_cmp}a2.name'
            return
                p1.name as name1, id(p1) as id1,
                p2.name as name2, id(p2) as id2
        '''
