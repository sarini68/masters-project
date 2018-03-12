from tkinter import ttk, Tk, StringVar, N, W, E, S, BooleanVar

from data_access_layer import DAL
from query_builder import QueryBuilder


class ProgramGUI:

    def __init__(self, dal: DAL):
        self.dal = dal
        # building the query pattern generator user interface

        self.master = Tk()
        self.master.title("Pattern creator")

        self.mainframe = ttk.Frame(self.master, padding="3 3 12 12")
        self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(0, weight=1)

        self.performers = ['.*']
        self.performers.extend(self.dal.performers)

        self.performer_one_var = StringVar()
        self.performer_two_var = StringVar()
        self.search_same_activity_var = BooleanVar()
        self.search_different_performer_var = BooleanVar()

        self.length_option_var = StringVar()
        self.length_option_var.set('any')

        self.exact_length_var = StringVar()
        self.at_least_length_var = StringVar()
        self.at_most_length_var = StringVar()
        self.from_length_var = StringVar()
        self.to_length_var = StringVar()

        self.setup_gui()

        # Note: after each search options are cleared from the interface

        # running the interface
        for child in self.mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        self.master.mainloop()

    def setup_gui(self):
        ttk.Label(self.mainframe, text="-[:works_with]->").grid(column=2, row=1, sticky=W)

        # Combobox to choose performer one for the query
        ttk.Label(self.mainframe, text="Performer 1").grid(column=1, row=1, sticky=W)
        combobox = ttk.Combobox(self.mainframe, textvariable=self.performer_one_var)
        combobox.grid(column=1, row=2, sticky=W)
        combobox['values'] = self.performers
        combobox.current(0)

        # Combobox to choose performer two for the query
        ttk.Label(self.mainframe, text="Performer 2").grid(column=7, row=1, sticky=W)
        combobox = ttk.Combobox(self.mainframe, textvariable=self.performer_two_var)
        combobox.grid(column=7, row=2, sticky=W)
        combobox['values'] = self.performers
        combobox.current(0)

        ttk.Label(self.mainframe, text="Pattern length:").grid(column=2, row=2, sticky=W)

        # Length option: any
        rb = ttk.Radiobutton(self.mainframe, text='Any', variable=self.length_option_var, value='any')
        rb.grid(column=2, row=3, sticky=W)

        # Length option: exactly
        rb = ttk.Radiobutton(self.mainframe, text='Exactly', variable=self.length_option_var, value='exactly')
        rb.grid(column=2, row=4, sticky=W)
        ttk.Entry(self.mainframe, width=3, textvariable=self.exact_length_var).grid(column=3, row=4, sticky=(W, E))

        # Length option: at least
        rb = ttk.Radiobutton(self.mainframe, text='At least', variable=self.length_option_var, value='at least')
        rb.grid(column=2, row=5, sticky=W)
        ttk.Entry(self.mainframe, width=3, textvariable=self.at_least_length_var).grid(column=3, row=5, sticky=(W, E))

        # Length option: at most
        rb = ttk.Radiobutton(self.mainframe, text='At most', variable=self.length_option_var, value='at most')
        rb.grid(column=2, row=6, sticky=W)
        ttk.Entry(self.mainframe, width=3, textvariable=self.at_most_length_var).grid(column=3, row=6, sticky=(W, E))

        # Length option: from ... to ...
        rb = ttk.Radiobutton(self.mainframe, text='Between', variable=self.length_option_var, value='between')
        rb.grid(column=2, row=7, sticky=W)
        ttk.Entry(self.mainframe, width=3, textvariable=self.from_length_var).grid(column=3, row=7, sticky=(W, E))
        ttk.Label(self.mainframe, text="and").grid(column=4, row=7, sticky=W)
        ttk.Entry(self.mainframe, width=3, textvariable=self.to_length_var).grid(column=5, row=7, sticky=(W, E))

        # Checkbox to choose if the query should look for the same activity or not
        ttk.Checkbutton(
            self.mainframe,
            text='Same activity',
            variable=self.search_same_activity_var,
            onvalue=True,
            offvalue=False
        ).grid(column=1, row=8, sticky=W)

        # Checkbox to choose if the query should look for same performer or not
        ttk.Checkbutton(
            self.mainframe,
            text='Search different performers',
            variable=self.search_different_performer_var,
            onvalue=True,
            offvalue=False
        ).grid(column=7, row=8, sticky=W)

        # Action button (generate and runs the query to look for the pattern)
        ttk.Button(self.mainframe, text="Search pattern", command=self.search_pattern).grid(column=7, row=9, sticky=W)

    def query_pattern(self, query):
        # pattern is a list containing, all of the performers which belong to the pattern
        # found through the query specified from the pattern generator query interface (for each case)
        return [
            [
                [
                    [record["name1"], record["id1"]],
                    [record["name2"], record["id2"]]
                ]
                for record in self.dal.run_query(query, {'case': case})
            ]
            for case in self.dal.cases[:1]
        ]

    def search_pattern(self):
        query_builder = QueryBuilder()
        query_builder.performer_one = self.performer_one_var.get()
        query_builder.performer_two = self.performer_two_var.get()
        query_builder.same_activity = self.search_same_activity_var.get()
        query_builder.different_performer = self.search_different_performer_var.get()

        length_option = self.length_option_var.get()
        if length_option == 'exactly':
            query_builder.pattern_length = self.exact_length_var.get()

        if length_option == 'at least':
            query_builder.pattern_length_from = self.at_least_length_var.get()

        if length_option == 'at most':
            query_builder.pattern_length_to = self.at_most_length_var.get()

        if length_option == 'between':
            query_builder.pattern_length_from = self.from_length_var.get()
            query_builder.pattern_length_to = self.to_length_var.get()

        query = query_builder.build()

        print('-' * 80)
        print(query.replace('    ', ' '))

        pattern = self.query_pattern(query)

        print('pattern')
        print(pattern)

        # match found in the first case, pattern[0]
        print('pattern[0]')
        print(pattern[0])
        print('len-pattern[0]')
        print(len(pattern[0]))
        # len(pattern[0]), count how many times a match with the considered pattern is found within the first case
