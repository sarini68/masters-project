from neo4j.v1 import GraphDatabase, basic_auth
driver = GraphDatabase.driver("bolt://localhost:7687", auth=basic_auth("neo4j", "nisam0nisam0"))
session = driver.session()

#query per caricare il db da csv
# aggiunta colonna timestamp (line[3]
query = '''
LOAD CSV FROM 'file:///log.csv' AS line FIELDTERMINATOR ';'
CREATE (c:case {id:line[0]})
CREATE (a:activity {name:line[1]})
SET a.created = line[3]
CREATE (p:performer {name:line[2]})
SET p.created = line[3]
CREATE (c)-[:includes]->(a)
CREATE (a)-[:performed_by]->(p)
'''

session.run(query)

#############################
###############################################################################
#query per restituire i nomi univoci dei performer coinvolti in almeno un caso
query = "match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer) return distinct p.name as name order by p.name"

result = session.run(query)

# la lista di tutti i performer estratti dai log, che quindi sono coinvolti in almeno un caso
performer_dist = []

for record in result:
  performer_dist.append(record["name"])

print('performer_dist')
print(performer_dist)
#1-3-17 proviamo a modificare il codice per andare a prendere tutti i casi presenti nei log

#analogamente a sopra va creata query per recuperare tutti i casi

#query per restituire i nomi univoci di tutti i casi presenti
query = "match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer) return distinct c.id as id order by c.id"

result = session.run(query)

# la lista di tutti i casi estratti dai log
cases = []

for record in result:
  cases.append(record["id"])


#################################### per ogni singolo caso vado a costruire

works_with = []

for i in range(len(cases)):

###############################################################################
#query per restituire i nomi dei performer in base alle attività svolte, tenendo conto anche del timestamp su ogni caso
#tieni conto che i dati estratti sono ordinati per timestamp (per evitare ordinamento alfanumerico, dove 10 precederebbe 9 abbiamo convertito
#il timestamp da stringa a float grazie a fx toFloat()
    query = "match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer) where c.id = {case} return p.name as name, p.created as time, id(p) as id order by toFloat(time)"

    result = session.run(query, {'case':cases[i]})

# la lista di tutti i performer estratti dai log , i rispettivi timestamp e gli id in cui eseguono una certa attività

    performer = []
    time = []
    ident = []

    for record in result:
        performer.append(record["name"])
        time.append(record["time"])
        ident.append(record["id"])

    
#works_with contiene per ogni caso una lista [[performer],[ident],[time]] con i nomi dei performer per tutti i casi, in ordine di timestamp, ed i relativi id
# per il primo indice 0 sta per il primo caso e così via
#per il secondo indice 0 sta per performer, 1 per ident, 2 per time


    works_with.append([performer, ident, time])
    
    


# costruisco la lista delle attività collegate ad un performer per tutti i casi
# per evitare la creazione di relazioni works_for non corrette ho considerato come parametro ulteriore il timestamp
# nota che activity raggruppa le attività svolte per caso, prima lista di attività in pos 0 (primo caso) e così via

activity = []
for j in range(len(cases)):
    tmpa=[]
    for i in range(len(works_with[j][0])):
       query = "match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer) where c.id = {case} and p.name={namename1} and p.created={time} return act.name as name"       
       result = session.run(query, {'case':cases[j], 'namename1':works_with[j][0][i], 'time':works_with[j][2][i]})       
       for record in result:
          tmpa.append(record["name"])
    activity.append(tmpa)   

print(activity)
  
# da aggiustare inseirimento relazioni works_with rispetto a tutti i casi!!!

# individuo le coppie di performer per cui costruire le nuove relazioni 
# 28-2-17 nota che ho dovuto aggiungere nel where la condizione p1.created < p2.created
# perchè nei cicli (John che eseguiva A in due momenti, quindi in caso di rework) venivano create delle relazioni in più che non tenevano conto del timestamp
# nota che come sopra per ordinamento rispetto a timestamp ho dovuto aggiungere conversione a float per evitare ordinamento alfanumerico
# anche qui per la condizione sui tempi, ho dovuto modificare in toFloat(p1.created) < toFloat(p2.created)
for j in range(len(cases)):
    for i in range(len(works_with[j][0])-1):
        query = '''
        match (c1)-[]->(a1)-[]->(p1:performer), (c2)-[]->(a2)-[]->(p2:performer) 
        where c1.id = {case} and c2.id = {case} and p1.name={namename1} and p2.name={namename2} and a1.name={actname1} and a2.name={actname2} and toFloat(p1.created) < toFloat(p2.created)
        merge (p1)-[w:works_with]->(p2)
        return w	
        '''  
        result = session.run(query, {'case':cases[j], 'namename1':works_with[j][0][i], 'namename2':works_with[j][0][i+1], 'actname1':activity[j][i], 'actname2':activity[j][i+1]})

#sembra funzionare, tranne per il fatto che in case2, John che esegue A, creato a tempo 9, non risulta collegato da works_with con Fred con attività B a tempo 10
############################################### costruiamo ora la parte di visualizzazione con la colorbar
import matplotlib.pyplot as plt
import matplotlib as mpl

########### costruisco ora la colormap specifica per i performer che abbiamo in ogni specifico caso, in base alle attività svolte
color_case=[]
# il primo indice fa riferimento al caso, in questo caso il primo caso (id1) che ha posizione 0 in works_with
# il secondo indice fa riferimento ai diversi performer coinvolti in quel caso

for j in range(len(cases)):
    color_tmp=[]
    for i in range(len(works_with[j][0])):
        color_tmp.append(performer_dist.index(works_with[j][0][i]))
    color_case.append(color_tmp)
print('color_case')
print(color_case)

#PROBLEMA, tutte le righe devono avere stessa lunghezza
#quindi modifico color_case per rendere tutte le righe di lunghezza pari a quella di lunghezza massima
#inserisco un valore fittizio per i valori in più che riempiono i buchi usando il colore che non è assegnato ad un performer,
#ottenuto dalla lunghezza di performer_dist, cioè il numero totale di performer su tutti i casi + 1
maxlencase=0
for i in range(len(color_case)):
    if (maxlencase<len(color_case[i])):
        maxlencase=len(color_case[i])

print('max')
print(maxlencase)

for i in range(len(color_case)):
    for j in range(len(color_case[i]), maxlencase):
        color_case[i].append(len(performer_dist)+1)

# qui ho ottenuto la color_case con i buchi riempiti (quindi stesso numero di elementi per ogni caso)
print('new color_case')
print(color_case)

#inverto l'ordine delle righe, questo per fare in modo che il primo caso sia visualizzato più in alto (e non più in basso)
color_case.reverse()
print('reversed color_case')
print(color_case)



# nota mex: ogni riga deve avere lo stesso numero di colonne, cosa che da noi non succede
#infatti ogni caso può avere un numero diverso di attività, quindi non funziona
#o io vado a riempire i vuoti finali con un colore mai usato (tipo quello relativo alla lunghezza di performer_dist + 1 oppure?
#mex=[[3, 4, 3, 8, 6, 2, 8, 3,3, 4, 3, 8, 6, 2, 8, 3,3, 4, 3, 8, 6, 2, 8, 3,3, 4, 3, 8, 6, 2, 8, 3,3, 4, 3, 8, 6, 2, 8, 3,3, 4, 3, 8, 6, 2, 8, 3],[3, 4, 3, 8, 6, 2, 8, 3, 3, 4, 3, 8, 6, 2, 8, 3,3, 4, 3, 8, 6, 2, 8, 3,3, 4, 3, 8, 6, 2, 8, 3,3, 4, 3, 8, 6, 2, 8, 3,3, 4, 3, 8, 6, 2, 8, 3],[3, 4, 3, 8, 6, 2, 8, 2, 3, 4, 3, 8, 6, 2, 8, 3,3, 4, 3, 8, 6, 2, 8, 3,3, 4, 3, 8, 6, 2, 8, 3,3, 4, 3, 8, 6, 2, 8, 3,3, 4, 3, 8, 6, 2, 8, 3]]
#plt.pcolor(mex,cmap='Vega20')

#plt.axis([0, maxlencase, 0, 6])
#plt.set_autoscalex_on(False)








################################################  INSERISCO QUI GUI PATTERN QUERY CREATOR
from tkinter import *
from tkinter import ttk

    
def generate_query(*args):
    
    query_string_fisso1="match (c1)-[]->(a1)-[]->(p1:performer)-"

    if patternlen.get()=='any':
        query_string_works_with="[:works_with*]"
    elif patternlen.get()=='exactly':
        query_string_works_with="[:works_with*"+exactlenval.get()+"]"
    elif patternlen.get()=='at least':
        query_string_works_with="[:works_with*"+atleastlenval.get()+"..]"
    elif patternlen.get()=='at most': 
        query_string_works_with="[:works_with*.."+atmostlenval.get()+"]"
    elif patternlen.get()=='between': 
        query_string_works_with="[:works_with*"+btwminlenval.get()+".."+btwmaxlenval.get()+"]"            
    else:
        query_string_works_with="[:works_with]"        
            
        
        
    query_string_fisso2="->(p2:performer)<-[]-(a2)<-[]-(c2) where c1.id = {case} and c2.id = {case}" 
        
    #costruzione condizione su performer1
    if (performer1.get()!=""):
        if (performer1.get()=="*"):
            query_string_perf1 = "p1.name=~'.*'"
        else:
            query_string_perf1 = "p1.name=~'"+performer1.get()+"'"
    else:    
        query_string_perf1 = "p1.name=~'.*'"

    #costruzione condizione su performer2        
    if (performer2.get()!=""):
        if (performer2.get()=="*"):
            query_string_perf2 = "p2.name=~'.*'"
        else:
            query_string_perf2 = "p2.name=~'"+performer2.get()+"'"
    else:    
        query_string_perf2 = "p2.name=~'.*'"
        
    query_string_performers=" and " + query_string_perf1 + " and " + query_string_perf2 

    query_string_sameperf =""
    #semplifico la condizione e decido di mettere sempre la stringa con i valori diversi, se ho checcato cerca differenti
    if (sameperformer.get()=='different'):
        query_string_sameperf =" and p1.name<>p2.name"                 
        #if (performer1.get()!="" and performer1.get()!="*") and (performer2.get()=="" or performer2.get()=="*"):
        #    query_string_sameperf =" and p1.name<>p2.name"     
        #if (performer1.get()=="" or performer1.get()=="*") and (performer2.get()!="" and performer2.get()!="*"):
        #    query_string_sameperf =" and p1.name<>p2.name"                 

    # a seconda che il check box per cercare se i due performer hanno svolto la stessa attività oppure no
    # se è spuntato su stessa attività aggiungo la condizione per cercare la stessa attività and a1.name=a2.name
    if sameactivity.get()=='same':
        query_string_fisso3=" and a1.name=a2.name return p1.name as name1, id(p1) as id1, p2.name as name2, id(p2) as id2"
    else:
        query_string_fisso3=" return p1.name as name1, id(p1) as id1, p2.name as name2, id(p2) as id2"
        
    query_string=query_string_fisso1+query_string_works_with+query_string_fisso2+query_string_performers+query_string_sameperf+query_string_fisso3
    
    
    print(query_string)
    # fino a qui ho prodotto la stringa per la generazione della query
    
    ################################ devo mettere qui tutto quello che segue per la generazione dei pattern?
    ################################# in realtà è stato preso codice da testpattern identando tutto in modo da inserire entro fx generate_query
    
    ######################
    pattern =  []
    for j in range(len(cases)):
        patt_case=[]
    #questa è la query per il pattern da cercare
    #in questo caso si va a cercare su ogni singolo caso:
    ####---pattern3bis, trovo tutti i pattern di lunghezza due, in cui uno specifico performer compare per primo, es. John
    #### nota che in questa versione di pattern non vado a considerare però i pattern di lunghezza due costituiti dallo stesso performer
    #### cioè evito di considerare ad es. i casi John-John, ma considero solo i casi John-p dove p non è John
        query = query_string
        result = session.run(query, {'case':cases[j]})
        #NOTA: USANDO IL PATTERN GENERATOR NON AVRò PIù BISOGNO DEI PARAMETRI RELATIVI AI NOMI DEI PERFORMER, PERCHè QUELLI SARANNO GIà CABLATI NELLA STRINGA COSTRUITA DAL PATTERNGENERATOR, L'UNICO PARAMETRO CHE RESTA DA PASSARE è IL CASO
    
        for record in result:
            patt_case.append([[record["name1"],record["id1"]],[record["name2"],record["id2"]]])
        pattern.append(patt_case)   

    print('pattern')
    print(pattern)

    # primo caso, in posizione [0]
    print('pattern[0]')
    print(pattern[0])
    print('len-pattern[0]')
    print(len(pattern[0]))
    # questo conta quante volte è stato identificato il pattern nel primo caso (caso in posizione [0])

############################### tabella con le statistiche sui pattern
    stat_pattern=[]
    for i in range(len(cases)):
        stat_pattern.append(len(pattern[i]))

    print('stat_pattern')
    print(stat_pattern)
################################# in base ai risultati della query che identifica il pattern di interesse, vado a costruire una lista di colori specifica
################################# per costruire la lista dei colori specifica per il pattern color_case_pattern, parto dalla lista dei colori esistente color_case
# uso funzione deepcopy 
    from copy import deepcopy

    color_case_pattern=deepcopy(color_case)
    
    ################DEVO REINVERTIRE DI NUOVO PERCHè HO RICEVUTO UNA LISTA ROVERSCIATA
    color_case_pattern.reverse()

################# NEL COSTRUIRE LA LISTA DEL PATTERN RICONOSCIUTO DALLA QUERY
################ VA VALUTATO SE INVECE DI ASSEGNARE IL VALORE len(performer_dist)+1 che è lo stesso colore usato per riempire i buchi
############### usare un'altra colorazione, o luce, o colore complementare tipo MAX_COLOR - works_with[j][1].index(pattern[j][i][0][1])
    for j in range(len(cases)):
        for i in range(len(pattern[j])):
            x=works_with[j][1].index(pattern[j][i][0][1])
            #provo a modificare aggiungendo un altro colore diverso da spazio vuoto, sommando 2 rispetto al numero complessivo di performer
            color_case_pattern[j][x]=len(performer_dist)+1
            #color_case_pattern[j][x]=len(performer_dist)+2
            y=works_with[j][1].index(pattern[j][i][1][1])
            #provo a modificare aggiungendo un altro colore diverso da spazio vuoto, sommando 2 rispetto al numero complessivo di performer
            color_case_pattern[j][y]=len(performer_dist)+1
            #color_case_pattern[j][y]=len(performer_dist)+2
            ############## NOTA CHE METTENDO + 2 PROBABILMENTE SI SFORA IL NUMERO DI COLORI DA USARE, OLTRE10 E QUINDI CAMBIA TUTTA LA COLORAZIONE
            ####### QUINDI NON VA BENE

#l=[4,4,3]
#i=l.index(3)
#l[i]=4
#l
#[4,4,4]
    print('color_case_pattern')
    print(color_case_pattern)

#################### per visualizzare...
##########################################color_case è stata costruita
##########################################ho messo anche i colori per riempire i buchi
########################################### ora per visualizzare tenendo conto della posizione (se dovessi cambiare modalità di visualizzazione potrei non dover più fare così)
######################################### vado ad invertire la color_case


################## questa è la lista dei pattern
    color_case_pattern.reverse()
    
######################################################    

# ora dovrei migliorare figura, ad es. togliendo valori sugli assi e facendo in modo che ogni riga sia visualizzata di altezza costante (ad es. di 1)
    plt.subplot(2, 1, 1)
    plt.pcolor(color_case,cmap='Vega20',edgecolors='k', linewidths=1)

############ questa riguarda la visualizzazione della lista dei colori relativi al pattern identificato
    plt.subplot(2, 1, 2)
    plt.pcolor(color_case_pattern,cmap='Vega20',edgecolors='k', linewidths=1)

##############DA STUDIARE IL MODO PER VISUALIZZARE ENTRAMBE LE LISTE, MAGARI CON GLI EVENTI ENTER END LEAVE FIGURE


    plt.show()    
    
    ###################### end codice importato da testpattern
        
#####################end string generator
    
root = Tk()
root.title("Pattern creator")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)


############ aggiungo var per i combobox relativi ai performer
performer1 = StringVar()
performer2 = StringVar()

#########var relativa alla scelta di cercare performer che svolgevano o meno stessa attività
sameactivity = StringVar()

#########var relativa alla scelta di permettere di avere nel pattern gli stessi o performer diversi
sameperformer = StringVar()

################## variabile relativa alle scelte (radiobutton) relative alla lunghezza del pattern
patternlen= StringVar()

################## variabili relativi ai valori inseriti per specificare la lunghezza del pattern
exactlenval= StringVar()
atleastlenval= StringVar()
atmostlenval= StringVar()
btwminlenval= StringVar()
btwmaxlenval= StringVar()

######################################### da qui costruzione di pattern creator

ttk.Label(mainframe, text="Performer 1").grid(column=1, row=1, sticky=W)

################lista di valori da inserire nelle combo dei performer
perfcombovalues = ['*']
perfcombovalues.extend(performer_dist) 

########### combo performer1
perf1=ttk.Combobox(mainframe, textvariable=performer1)
perf1.grid(column=1, row=2, sticky=W)
#########inserisco i valori possibili (posso usare quindi list performer_dist già preparata)
#perf1['values']=['*', 'Clare', 'Fred', 'Jane', 'John', 'Mike', 'Mona', 'Pete', 'Robert', 'Sue']
perf1['values']=perfcombovalues


ttk.Label(mainframe, text="Performer 2").grid(column=7, row=1, sticky=W)

########### combo performer2
perf2=ttk.Combobox(mainframe, textvariable=performer2)
perf2.grid(column=7, row=2, sticky=W)
#########inserisco i valori possibili (posso usare quindi list performer_dist già preparata)
#perf2['values']=['*', 'Clare', 'Fred', 'Jane', 'John', 'Mike', 'Mona', 'Pete', 'Robert', 'Sue']
perf2['values']=perfcombovalues

########### checkbox stessa attività
sameact=ttk.Checkbutton(mainframe, text='Same activity',variable=sameactivity,onvalue='same')
sameact.grid(column=1, row=8, sticky=W)

########### checkbox per decidere se permettere di cercare stesso performer nel pattern
sameperf=ttk.Checkbutton(mainframe, text='Search different performers',variable=sameperformer,onvalue='different')
sameperf.grid(column=7, row=8, sticky=W)

ttk.Label(mainframe, text="-[:works_with]->").grid(column=2, row=1, sticky=W)

ttk.Label(mainframe, text="Pattern length:").grid(column=2, row=2, sticky=W)

########### radiobutton qualunque lunghezza
anylenchk=ttk.Radiobutton(mainframe, text='Any',variable=patternlen, value='any')
anylenchk.grid(column=2, row=3, sticky=W)

########### radiobutton lunghezza esatta
exactlenchk=ttk.Radiobutton(mainframe, text='Exactly',variable=patternlen, value='exactly')
exactlenchk.grid(column=2, row=4, sticky=W)

################quale valore per la lunghezza
lenentry = ttk.Entry(mainframe, width=3, textvariable=exactlenval)
lenentry.grid(column=3, row=4, sticky=(W, E))

########### radiobutton almeno lunghezza 
atleastlenchk=ttk.Radiobutton(mainframe, text='At least',variable=patternlen, value='at least')
atleastlenchk.grid(column=2, row=5, sticky=W)

################valore almeno per la lunghezza
atleastlenentry = ttk.Entry(mainframe, width=3, textvariable=atleastlenval)
atleastlenentry.grid(column=3, row=5, sticky=(W, E))

########### radiobutton al massimo lunghezza 
atmostlenchk=ttk.Radiobutton(mainframe, text='At most',variable=patternlen, value='at most')
atmostlenchk.grid(column=2, row=6, sticky=W)

################valore al massimo per la lunghezza
atmostlenentry = ttk.Entry(mainframe, width=3, textvariable=atmostlenval)
atmostlenentry.grid(column=3, row=6, sticky=(W, E))

########### radiobutton lunghezza compresa tra
btwlenchk=ttk.Radiobutton(mainframe, text='Between',variable=patternlen, value='between')
btwlenchk.grid(column=2, row=7, sticky=W)

################valore da lunghezza minima
btwminlenentry = ttk.Entry(mainframe, width=3, textvariable=btwminlenval)
btwminlenentry.grid(column=3, row=7, sticky=(W, E))

ttk.Label(mainframe, text="and").grid(column=4, row=7, sticky=W)

################valore da lunghezza massima
btwmaxlenentry = ttk.Entry(mainframe, width=3, textvariable=btwmaxlenval)
btwmaxlenentry.grid(column=5, row=7, sticky=(W, E))

############### bottone per generare il pattern
ttk.Button(mainframe, text="Search pattern", command=generate_query).grid(column=7, row=9, sticky=W)
# nota: dopo ogni search pattern dovresti ripulire le opzioni dall'interfaccia


for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

root.mainloop()
################################################# END GUI


############################### aggiungo parte relativa alle query per identificare patterns


session.close()


