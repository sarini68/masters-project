##############################################################################
############################ code by Marcello Sarini
####################################################
# Marcello Sarini
# 
# Assistant Professor - Computer Science
####################################################
# Department of Psychology - Università degli Studi Milano-Bicocca
# Piazza Ateneo Nuovo 1, 20126 Milano - Italy
# mail: marcello.sarini@unimib.it
# tel: +39-02-6448-3746
####################################################
# For any reference cite:
# Marcello Sarini, "Can Working Style be identified?", 
# Proceedings of the PRE-BIR Forum, 2017
# ceur-ws.org/Vol-1898/paper1.pdf
####################################################
##############################################################################

import matplotlib.pyplot as plt
from neo4j.v1 import GraphDatabase, basic_auth

# connecting to neo4j database through driver
# notice that in the use of basic_auth the first parameter is the user name you defined for accessing the db, the second is the password
# so you have to change these parameters according to the data you provided when creating locally a neo4j db
driver = GraphDatabase.driver("bolt://localhost:7687",
                              auth=basic_auth("neo4j", "nisam0nisam0"))
session = driver.session()

############################################ FIRST PART
################ setting the database and the data structures from the log file
############################################

##########################################
#################### creating the database
##########################################

# query to read the log from csv and putting it into database
# notice that in the csv file, the line[3] is about timestamp (ordering the time of execution of activities
# currently the log file (log.csv) is put into the local directory of the drive
# query = '''
# LOAD CSV FROM 'file:///log.csv' AS line FIELDTERMINATOR ';'
# CREATE (c:case {id:line[0]})
# CREATE (a:activity {name:line[1]})
# SET a.created = line[3]
# CREATE (p:performer {name:line[2]})
# SET p.created = line[3]
# CREATE (c)-[:includes]->(a)
# CREATE (a)-[:performed_by]->(p)
# '''
# # running the query
# session.run(query)

######################################################
############################# building data structures
######################################################

# query to get the unique names of performers involved at least in a case
query = "match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer) return distinct p.name as name order by p.name"

# running the query
result = session.run(query)

# creating the list of all performers read from log, involved in at least one case
performer_dist = []

for record in result:
    performer_dist.append(record["name"])

print('performer_dist')
print(performer_dist)

# query to get the unique names of all cases
query = "match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer) return distinct c.id as id order by c.id"

# running the query
result = session.run(query)

# creating the list of all cases read from log
cases = []

for record in result:
    cases.append(record["id"])

################################################################################################
############ ADDING THE work_with relation in the database through the works_with data structure
############ works_with is a main aspect, as it relates two performers completing two consecutive activities within the same case
################################################################################################

#### list containing information to build the work_with relation in the database
works_with = []

#################################### for any case it is built the works_with relation put in the neo4j database
for i in range(len(cases)):

    ###############################################################################
    # query to get performer names according to activity, ordered for timestamp
    # to have real ordering (avoiding alphanumerical ordering) timestamp was casted to float
    query = "match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer) where c.id = {case} return p.name as name, p.created as time, id(p) as id order by toFloat(time)"

    # running the query, in this case by passing also parameters to the query; {case} in the query will be replaced by real value held in cases[i]
    # as defined in the parameter {'case':cases[i]} when running the query
    result = session.run(query, {'case': cases[i]})

    # building three lists: performers from logs, the related timestamp and the id when executing a certain activity
    performer = []
    time = []
    ident = []

    for record in result:
        performer.append(record["name"])
        time.append(record["time"])
        ident.append(record["id"])

    # works_with data structure is organized as follows: for any case there is : [[performer],[ident],[time]]
    # works_with[0] refers to the first case, works_with[1] to the second case, etc
    # works_with[0][0] is about performers in the first case, works_with[0][1] is about ths ids of performers in the first case,
    # while works_with[0][2] is about timestamps of the activities performed by the related performers in the first case
    works_with.append([performer, ident, time])

# activity list, encompasses all the activities related to a performer, performed to a certain timestamp
# activity[0] contains all activities pertaining to the first case, [1] to the second case and so on
activity = []
for j in range(len(cases)):
    tmpa = []
    for i in range(len(works_with[j][0])):
        query = "match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer) where c.id = {case} and p.name={namename1} and p.created={time} return act.name as name"
        result = session.run(query, {'case': cases[j],
                                     'namename1': works_with[j][0][i],
                                     'time': works_with[j][2][i]})
        for record in result:
            tmpa.append(record["name"])
    activity.append(tmpa)

print(activity)

# creating and running the query to build the relation works_with in the neo4j database
# to avoid the insertion of wrong relations (e.g., in case of rework, when John performed A at two different times)
# a check is added on the time of creation of perfomers, the firts performer in the relation (p1) should be created before of the second (p2)
# to prevent from alphanumerical ordering, time of creation is casted to float
for j in range(len(cases)):
    for i in range(len(works_with[j][0]) - 1):
        query = '''
        match (c1)-[]->(a1)-[]->(p1:performer), (c2)-[]->(a2)-[]->(p2:performer) 
        where c1.id = {case} and c2.id = {case} and p1.name={namename1} and p2.name={namename2} and a1.name={actname1} and a2.name={actname2} and toFloat(p1.created) < toFloat(p2.created)
        merge (p1)-[w:works_with]->(p2)
        return w
        '''
        result = session.run(query, {'case': cases[j],
                                     'namename1': works_with[j][0][i],
                                     'namename2': works_with[j][0][i + 1],
                                     'actname1': activity[j][i],
                                     'actname2': activity[j][i + 1]})

############################################### importing module for colormap creations
############################################### currently for the prototype it was chosen to display wsa (and wsa') by using a colormap (from matplotlib)
############################################### notice that there are many drawbacks (e.g., at most 10 different performers are displayed)
############################################### another way (considering also web-based architecture) should be considered

###################################################################################
############## color_case definition
############## color_case is the data structure used to generate wsa through the colormap function
################################################################################### 

########### color_case is a two indexes list: the first index is about the number of the case, the second is about performers involved in that case
color_case=[]

for j in range(len(cases)):
    color_tmp=[]
    for i in range(len(works_with[j][0])):
        color_tmp.append(performer_dist.index(works_with[j][0][i]))
    color_case.append(color_tmp)
print('color_case')
print(color_case)

# for to have a correct colormap generation (this is another drawback), all the rows (cases) should have the same length (the same number of activities)
# so color_case is modified to make all rows the same length (the maxlencase)
# first maxlencase is determined 
maxlencase=0
for i in range(len(color_case)):
    if (maxlencase<len(color_case[i])):
        maxlencase=len(color_case[i])

print('max')
print(maxlencase)

# then in color_case a new value is inserted (total number of performers +1) to fill in the blanks

for i in range(len(color_case)):
    for j in range(len(color_case[i]), maxlencase):
        color_case[i].append(len(performer_dist)+1)

print('new color_case')
print(color_case)

# for displaying purposed (colormap), the list is reversed so that first case will be displayed as the first row
color_case.reverse()
print('reversed color_case')
print(color_case)

######################################## end color_case definition


################################################################# SECOND PART  
##################### building GUI PATTERN QUERY CREATOR using tkinter module
#################################################################

from tkinter import *
from tkinter import ttk


####################################################################################################
## generate_query 
#
##main function to build the query to the db as a consequence of the user's choice on the interface    
####################################################################################################
def generate_query(*args):
    # each query is built as a string combining fixed parts with parts changing according to the choices made by the user through the pattern query generator interface

    # fixed part starting the text of the query
    query_string_fisso1 = "match (c1)-[]->(a1)-[]->(p1:performer)-"

    # part of the query related to the length of the pattern to be identified changing according to the UI
    if patternlen.get() == 'any':
        query_string_works_with = "[:works_with*]"
    elif patternlen.get() == 'exactly':
        query_string_works_with = "[:works_with*" + exactlenval.get() + "]"
    elif patternlen.get() == 'at least':
        query_string_works_with = "[:works_with*" + atleastlenval.get() + "..]"
    elif patternlen.get() == 'at most':
        query_string_works_with = "[:works_with*.." + atmostlenval.get() + "]"
    elif patternlen.get() == 'between':
        query_string_works_with = "[:works_with*" + btwminlenval.get() + ".." + btwmaxlenval.get() + "]"
    else:
        query_string_works_with = "[:works_with]"

    # other fixed part of the query
    query_string_fisso2 = "->(p2:performer)<-[]-(a2)<-[]-(c2) where c1.id = {case} and c2.id = {case}"

    # building changing part about the condition expressed on performer1, i.e., if a specific performers' name was chosen or any performer (*)
    if (performer1.get() != ""):
        if (performer1.get() == "*"):
            query_string_perf1 = "p1.name=~'.*'"
        else:
            query_string_perf1 = "p1.name=~'" + performer1.get() + "'"
    else:
        query_string_perf1 = "p1.name=~'.*'"

    # building changing part about the condition expressed on performer2, i.e., if a specific performers' name was chosen or any performer (*)
    if (performer2.get() != ""):
        if (performer2.get() == "*"):
            query_string_perf2 = "p2.name=~'.*'"
        else:
            query_string_perf2 = "p2.name=~'" + performer2.get() + "'"
    else:
        query_string_perf2 = "p2.name=~'.*'"

    # adding in the query text the conditions on the two performers
    query_string_performers = " and " + query_string_perf1 + " and " + query_string_perf2

    # adding in the query text if same performers were chosen or not from the interface
    query_string_sameperf = ""
    if (sameperformer.get() == 'different'):
        query_string_sameperf = " and p1.name<>p2.name"

    # adding in the query text if same activity  was chosen or not from the interface
    if sameactivity.get() == 'same':
        query_string_fisso3 = " and a1.name=a2.name return p1.name as name1, id(p1) as id1, p2.name as name2, id(p2) as id2"
    else:
        query_string_fisso3 = " return p1.name as name1, id(p1) as id1, p2.name as name2, id(p2) as id2"

    # combining fixed and changing parts to have the final text of the query to be performed
    query_string = query_string_fisso1 + query_string_works_with + query_string_fisso2 + query_string_performers + query_string_sameperf + query_string_fisso3

    print(query_string)

    # pattern is a list containing, for any case (first index), all of the performers which belong to the pattern found through the query
    # specified from the pattern generator query interface
    ######################
    pattern = []
    for j in range(len(cases)):
        patt_case = []

        query = query_string

        # running the query
        result = session.run(query, {'case': cases[j]})

        for record in result:
            patt_case.append([[record["name1"], record["id1"]],
                              [record["name2"], record["id2"]]])
        pattern.append(patt_case)

    print('pattern')
    print(pattern)

    # match found in the first case, pattern[0]
    print('pattern[0]')
    print(pattern[0])
    print('len-pattern[0]')
    print(len(pattern[0]))
    # len(pattern[0]), count how many times a match with the considered pattern is found within the first case

    ########################### stat_pattern contains the count of the matches from the pattern for any of the case
    stat_pattern = []
    for i in range(len(cases)):
        stat_pattern.append(len(pattern[i]))

    print('stat_pattern')
    print(stat_pattern)

    # building color_case_pattern from color_case.
    # color_case_pattern is the list containing the number of performers matching the pattern after the query
    # color_case_pattern would be used to build a colormap describing wsa', i.e. the wsa image after the match with the considered pattern
    # we consider to build both wsa and wsa' images, to promote visual comparison to help users to easily recognize the matches found considering a pattern expressed through the query

    # using deepcopy module to copy color_case_pattern from color_case
    from copy import deepcopy

    ##### color_case_pattern is built from color_case (the original wsa)
    ##### and then modified according to the results of the query defined through the query pattern interface
    color_case_pattern = deepcopy(color_case)

    ################ reversing color_case_pattern to have the situation as in the original color_case (before reversing for displaying purposes)
    color_case_pattern.reverse()

    # building matches in color_case_pattern; for any of the match found, the corresponding position in the color_case_pattern lisst
    # is filled with the value len(performer_dist)+1 (that is the same color used in color_case to fill in the blanks).
    # To verify whether another color for the match would be more appropriated, may be the color complementary to the color of the corresponding performer:
    # e.g., computed by MAX_COLOR - works_with[j][1].index(pattern[j][i][0][1])
    for j in range(len(cases)):
        for i in range(len(pattern[j])):
            x = works_with[j][1].index(pattern[j][i][0][1])
            color_case_pattern[j][x] = len(performer_dist) + 1
            y = works_with[j][1].index(pattern[j][i][1][1])
            color_case_pattern[j][y] = len(performer_dist) + 1

    print('color_case_pattern')
    print(color_case_pattern)

    # reversing color_case_pattern as done in color_case for visualization purposes (i.e., to put first case at the top row of the colormap)
    color_case_pattern.reverse()

    ############################################################################
    ########### displaying the figures: wsa and wsa'
    ########### the first figure is about color_case, i.e., the original wsa as determined by the log file
    ########### the second figure is about color_case_patterns, i.e., the wsa' which is changed according to the matches from the pattern found
    ########### through the query built from the user's choice in the query pattern interface
    ############################################################################

    # displaying color_case (the related wsa image) with the Vega20 color map (20 max colors allowed)
    plt.subplot(2, 1, 1)
    plt.pcolor(color_case, cmap='Vega20', edgecolors='k', linewidths=1)

    # displaying color_case_pattern (the related wsa' image about the matches found) with the Vega20 color map (20 max colors allowed)
    plt.subplot(2, 1, 2)
    plt.pcolor(color_case_pattern, cmap='Vega20', edgecolors='k', linewidths=1)

    # showing colormaps
    plt.show()

    # notice that alternative ways of visualization should be considered (e.g., to facilitate visual comparison of wsa and wsa')


############ end visualization
    
##################################################################################	
#####################end function generate_query
##################################################################################

####################################################################################
####################### building the query pattern generator user interface
####################################################################################    
root = Tk()
root.title("Pattern creator")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

# defining variables to be associated to query pattern UI widgets, used to build the query text

############ vars for the combobox related to performers
performer1 = StringVar()
performer2 = StringVar()

######### var to look for same activity performed or not
sameactivity = StringVar()

######### var to look for same performer or not
sameperformer = StringVar()

################## var for radiobuttons to choose the length of the pattern
patternlen= StringVar()

################## vars related to one of the choice of the user in specifying the length of the pattern to be looked for
exactlenval= StringVar()
atleastlenval= StringVar()
atmostlenval= StringVar()
btwminlenval= StringVar()
btwmaxlenval= StringVar()

######################################### building the widgets of the interface

# label for performer1
ttk.Label(mainframe, text="Performer 1").grid(column=1, row=1, sticky=W)

################ list expressing the values for the performers to be chosen in the related comboboxes
perfcombovalues = ['*']
perfcombovalues.extend(performer_dist) 

########### combo performer1
perf1=ttk.Combobox(mainframe, textvariable=performer1)
perf1.grid(column=1, row=2, sticky=W)
perf1['values']=perfcombovalues

# label for performer2
ttk.Label(mainframe, text="Performer 2").grid(column=7, row=1, sticky=W)

########### combo performer2
perf2=ttk.Combobox(mainframe, textvariable=performer2)
perf2.grid(column=7, row=2, sticky=W)
perf2['values']=perfcombovalues

########### checkbox to have a pattern looking for same activity or not
sameact=ttk.Checkbutton(mainframe, text='Same activity',variable=sameactivity,onvalue='same')
sameact.grid(column=1, row=8, sticky=W)

########### checkbox to have a pattern looking for same performer or not
sameperf=ttk.Checkbutton(mainframe, text='Search different performers',variable=sameperformer,onvalue='different')
sameperf.grid(column=7, row=8, sticky=W)

# labels for pattern length
ttk.Label(mainframe, text="-[:works_with]->").grid(column=2, row=1, sticky=W)

ttk.Label(mainframe, text="Pattern length:").grid(column=2, row=2, sticky=W)

########### radiobutton pattern of any length 
anylenchk=ttk.Radiobutton(mainframe, text='Any',variable=patternlen, value='any')
anylenchk.grid(column=2, row=3, sticky=W)

########### radiobutton pattern of exact length
exactlenchk=ttk.Radiobutton(mainframe, text='Exactly',variable=patternlen, value='exactly')
exactlenchk.grid(column=2, row=4, sticky=W)

################ inserting the expected length of the pattern
lenentry = ttk.Entry(mainframe, width=3, textvariable=exactlenval)
lenentry.grid(column=3, row=4, sticky=(W, E))

########### radiobutton pattern of at least lenght 
atleastlenchk=ttk.Radiobutton(mainframe, text='At least',variable=patternlen, value='at least')
atleastlenchk.grid(column=2, row=5, sticky=W)

################ inserting the expected value for at least
atleastlenentry = ttk.Entry(mainframe, width=3, textvariable=atleastlenval)
atleastlenentry.grid(column=3, row=5, sticky=(W, E))

########### radiobutton pattern of at most length
atmostlenchk=ttk.Radiobutton(mainframe, text='At most',variable=patternlen, value='at most')
atmostlenchk.grid(column=2, row=6, sticky=W)

################ inserting the expected value for at most length
atmostlenentry = ttk.Entry(mainframe, width=3, textvariable=atmostlenval)
atmostlenentry.grid(column=3, row=6, sticky=(W, E))

########### radiobutton pattern of length ranging from ... to ...
btwlenchk=ttk.Radiobutton(mainframe, text='Between',variable=patternlen, value='between')
btwlenchk.grid(column=2, row=7, sticky=W)

################ inserting value for from
btwminlenentry = ttk.Entry(mainframe, width=3, textvariable=btwminlenval)
btwminlenentry.grid(column=3, row=7, sticky=(W, E))

# label for ranging length
ttk.Label(mainframe, text="and").grid(column=4, row=7, sticky=W)

################ inserting value for to
btwmaxlenentry = ttk.Entry(mainframe, width=3, textvariable=btwmaxlenval)
btwmaxlenentry.grid(column=5, row=7, sticky=(W, E))

############### button to generate the query text and running the query to look for the pattern
ttk.Button(mainframe, text="Search pattern", command=generate_query).grid(column=7, row=9, sticky=W)
# nota: dopo ogni search pattern dovresti ripulire le opzioni dall'interfaccia

####################################################################
######################################## end definition interface
####################################################################

######################################################################
############################ running the interface
######################################################################
for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)

root.mainloop()

#######################################################################
################################################# end second part
################################################# END GUI
#######################################################################


# closing access to the db
session.close()
