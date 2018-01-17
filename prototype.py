from neo4j.v1 import GraphDatabase, basic_auth
driver = GraphDatabase.driver("bolt://localhost:7687", auth=basic_auth("neo4j", "nisam0nisam0"))
session = driver.session()

#query per caricare il db da csv
# aggiunta colonna timestamp (line[3]
query = '''
LOAD CSV FROM 'file:///log-ws.csv' AS line FIELDTERMINATOR ';'
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
    
print('works_with')
print(works_with)


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


################################################  INSERISCO QUI GUI PATTERN QUERY CREATOR
from tkinter import *
from tkinter import ttk




###########################################################################################
########################################################### start generate_workingstylequery

################################################################################## qui proviamo a scrivere funzione molto simile a generate_query
####################################### richiamata da bottone specifico per generare il working style di un performer
####################################### start generate_workingstylequery

def generate_workingstylequery(*args):
    
##################################### da questa dobbiamo generare la query string
#match (c1)-[]->(a1)-[]->(p1:performer)-[:works_with]->(p2:performer)<-[]-(a2)<-[]-(c2) 
#where c1.id = '1' and c2.id = '1' and p1.name='John' and p2.name='Mike'
#with p1 as pp1, p2 as pp2
#match(pp2:performer)-[:works_with*]->(ppp2:performer) where pp2.name = ppp2.name and pp2.created < ppp2.created 
#match(ppp2)-[:works_with]->(ppp1:performer) where pp1.name = ppp1.name and pp1.created < ppp1.created
#return pp1.name as name1, id(pp1) as id1, ppp1.name as name2, id(ppp1) as id2


#################################### VARIABILI E PARAMETRI PER IL RADAR CHART
####################################
# value_handover, value_rework, value_qa sono i valori usati per posizionare la quantificazione delle dimensioni di handover-orientedness, rework-orientedness e question-answer-orientedness sul radar chart
# trasp_handover, trasp_rework, trasp_qa sono i valori compresi tra 0 ed 1 usati per mostrare la significatività del valore per una certa dimensione (0 la più bassa, 1 la più alta)
# provato a costruire value e trasp con i concetti rispettivamente di media e varianza dei valori relativi al conteggio dell'occorrenza dei pattern nei diversi casi
# proviamo qui a definire value e trasp considerando value il valore massimo con cui compare l'occorrenza di un certo pattern relativo ad una certa dimensione e trasp come supporto (cioè in quanti casi il pattern è rilevato)
####################################
####################################

###########################################################################################################
########################################################################### query per handover-orientedness
###########################################################################################################

    query_string_fisso1="match (c1)-[]->(a1)-[]->(p1:performer)-"

    query_string_works_with="[:works_with*1]"            
        
        
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
    stat_pattern_handover=[]
    for i in range(len(cases)):
        stat_pattern_handover.append(len(pattern[i]))

    print('stat_pattern_handover')
    print(stat_pattern_handover)
    
    #value_handover rappresenta il valore di handover-orientedness mostrata sul radar chart (è la media sui valori)
    #value_handover = 0
    #for i in range(len(stat_pattern_handover)):
    #    value_handover = value_handover + (stat_pattern_handover[i]/len(stat_pattern_handover))

    #value_handover = (value_handover/len(cases))
    
    # definisco qui value_handover come la massima occorrenza del pattern entro i casi
    value_handover = max(stat_pattern_handover)
    print('value_handover')
    print(value_handover)
    
    #var_handover è la varianza dei valori sul pattern, servirà per identificare la dimensione del dot, tanto è maggiore varianza, tanto valore è meno significativo
    #var_handover = 0
    #for i in range(len(stat_pattern_handover)):
    #    var_handover = var_handover + ((stat_pattern_handover[i]/len(stat_pattern_handover)) - value_handover)**2
    
    #var_handover = (var_handover/len(cases))
    
    #print('var_handover')
    #print(var_handover)

    # identifico valore massimo possibile della varianza
    #var_max_handover = (((max(stat_pattern_handover)/len(stat_pattern_handover))-value_handover)**2+((min(stat_pattern_handover)/len(stat_pattern_handover))-value_handover)**2)/2

    #print('var_max_handover')
    #print(var_max_handover)
    
    # a partire dal massimo valore possibile della varianza, normalizzo ad un valore tra 0 ed 1 che descrive il livello di trasparenza (1, cioè pieno, se la varianza è nulla)
    #if (var_handover == 0):
    #    trasp_handover = str(1)
    #else:
    #    trasp_handover = "{0:.2f}".format(1-(var_handover/var_max_handover))

    # definisco trasp_handover come il numero di casi che supporta il pattern fratto il numero complessivo di casi
    # quindi trasp_handover è massima, cioè 1, se il pattern è supportato in tutti i casi
    # aggiungo la condizione per cui se un pattern non occorre in nessuno dei casi, e quindi value_qa = 0, allora la trasparenza è massima (di fatto è come se l'assenza del pattern fosse supportata in tutti i casi)
    trasp_handover = 0
    if (value_handover != 0):
        for i in range(len(stat_pattern_handover)):
            if (stat_pattern_handover[i] != 0):
                trasp_handover = trasp_handover + 1
            
        trasp_handover = "{0:.2f}".format(trasp_handover/len(cases))
    else: trasp_handover = '1'
    
    
    
    print('trasp_handover')
    print(trasp_handover)
        
###########################################################################################################    
########################################################################### end query per handover-orientedness
###########################################################################################################


###########################################################################################################
########################################################################### query per rework-orientedness
###########################################################################################################

    query_string_fisso1="match (c1)-[]->(a1)-[]->(p1:performer)-"

    query_string_works_with="[:works_with*]"
                    
        
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
    # in rework orientedness, il nome del secondo performer deve corrispondere al primo, quindi in query_string_perf2 io uso il nome proposto in performer1
    query_string_perf2 = "p2.name=~'"+performer1.get()+"'"
        
    query_string_performers=" and " + query_string_perf1 + " and " + query_string_perf2 

    query_string_sameperf =""

    # in rework orientedness vogliamo andare a cercare la stessa attività, sullo stesso performer
    query_string_fisso3=" and a1.name=a2.name return p1.name as name1, id(p1) as id1, p2.name as name2, id(p2) as id2"
        
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
    stat_pattern_rework=[]
    for i in range(len(cases)):
        stat_pattern_rework.append(len(pattern[i]))

    print('stat_pattern_rework')
    print(stat_pattern_rework)

    #value_rework rappresenta il valore di rework-orientedness mostrata sul radar chart (è la media sui valori)
    #value_rework = 0
    #for i in range(len(stat_pattern_rework)):
    #    value_rework = value_rework + (stat_pattern_rework[i]/len(stat_pattern_rework))

    #value_rework = (value_rework/len(cases))

    # definisco qui value_rework come la massima occorrenza del pattern entro i casi
    value_rework = max(stat_pattern_rework)
            
    print('value_rework')
    print(value_rework)
    
    #var_rework è la varianza dei valori sul pattern, servirà per identificare la dimensione del dot, tanto è maggiore varianza, tanto valore è meno significativo
    #var_rework = 0
    #for i in range(len(stat_pattern_rework)):
    #    var_rework = var_rework + ((stat_pattern_rework[i]/len(stat_pattern_rework)) - value_rework)**2
    
    #var_rework = (var_rework/len(cases))
    
    #print('var_rework')
    #print(var_rework)                
    
    # identifico valore massimo possibile della varianza
    #var_max_rework = (((max(stat_pattern_rework)/len(stat_pattern_rework))-value_rework)**2+((min(stat_pattern_rework)/len(stat_pattern_rework))-value_rework)**2)/2

    #print('var_max_rework')
    #print(var_max_rework)
    
    # a partire dal massimo valore possibile della varianza, normalizzo ad un valore tra 0 ed 1 che descrive il livello di trasparenza (1, cioè pieno, se la varianza è nulla)
    #if (var_rework == 0):
    #    trasp_rework = str(1)
    #else:
    #    trasp_rework = "{0:.2f}".format(1-(var_rework/var_max_rework))

    # definisco trasp_rework come il numero di casi che supporta il pattern fratto il numero complessivo di casi
    # quindi trasp_rework è massima, cioè 1, se il pattern è supportato in tutti i casi
    # aggiungo la condizione per cui se un pattern non occorre in nessuno dei casi, e quindi value_qa = 0, allora la trasparenza è massima (di fatto è come se l'assenza del pattern fosse supportata in tutti i casi)
    trasp_rework = 0    
    if (value_rework != 0):
        for i in range(len(stat_pattern_rework)):
            if (stat_pattern_rework[i] != 0):
                trasp_rework = trasp_rework + 1
            
        trasp_rework = "{0:.2f}".format(trasp_rework/len(cases))
    else: trasp_rework = '1'
        
    print('trasp_rework')
    print(trasp_rework)

###########################################################################################################    
########################################################################### end query per rework-orientedness
###########################################################################################################

###########################################################################################################
########################################################################### query per question-answer-orientedness
###########################################################################################################

    
    query_string_fisso1="match (c1)-[]->(a1)-[]->(p1:performer)-[:works_with]->(p2:performer)<-[]-(a2)<-[]-(c2) where c1.id = {case} and c2.id = {case}"
        
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
        
    query_string_performers=" and " + query_string_perf1 + " and " + query_string_perf2 + " with p1 as pp1, p2 as pp2 match(pp2:performer)-"
    
    
    # devo cercare su qualunque lunghezza per la identificazione di un qa-pattern
    query_string_works_with="[:works_with*]"
            
        
        
    query_string_fisso2="->(ppp2:performer) where pp2.name = ppp2.name and pp2.created < ppp2.created " 

    # in questo caso la ricerca di differenti performer non ha senso, ai bordi ci deve essere sempre lo stesso performer che ha posto la domanda che riceverà risposta
    query_string_sameperf =""
    #semplifico la condizione e decido di mettere sempre la stringa con i valori diversi, se ho checcato cerca differenti
#    if (sameperformer.get()=='different'):
#        query_string_sameperf =" and p1.name<>p2.name"                 
        #if (performer1.get()!="" and performer1.get()!="*") and (performer2.get()=="" or performer2.get()=="*"):
        #    query_string_sameperf =" and p1.name<>p2.name"     
        #if (performer1.get()=="" or performer1.get()=="*") and (performer2.get()!="" and performer2.get()!="*"):
        #    query_string_sameperf =" and p1.name<>p2.name"                 

    # in questo caso non ha effetto richiedere di cercare se l'attività è la stessa o è diversa, a noi interessa che ci sia attività di richiesta (question), questa attività attiva un rispondente nel creare risposta, che viene fornita a chi ne ha fatto richiesta
    # a seconda che il check box per cercare se i due performer hanno svolto la stessa attività oppure no
    # se è spuntato su stessa attività aggiungo la condizione per cercare la stessa attività and a1.name=a2.name
#    if sameactivity.get()=='same':
#        query_string_fisso3=" and a1.name=a2.name return p1.name as name1, id(p1) as id1, p2.name as name2, id(p2) as id2"
#    else:
#        query_string_fisso3=" return p1.name as name1, id(p1) as id1, p2.name as name2, id(p2) as id2"

    query_string_fisso3="match(ppp2)-[:works_with]->(ppp1:performer) where pp1.name = ppp1.name and pp1.created < ppp1.created return pp1.name as name1, id(pp1) as id1, ppp1.name as name2, id(ppp1) as id2"
        
    query_string=query_string_fisso1+query_string_performers+query_string_works_with+query_string_fisso2+query_string_sameperf+query_string_fisso3



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
    stat_pattern_qa=[]
    for i in range(len(cases)):
        stat_pattern_qa.append(len(pattern[i]))

    print('stat_pattern_qa')
    print(stat_pattern_qa)
    
    #value_qa rappresenta il valore di questionanser-orientedness mostrata sul radar chart (è il valore medio)
    #value_qa = 0
    #for i in range(len(stat_pattern_qa)):
    #    value_qa = value_qa + (stat_pattern_qa[i]/len(stat_pattern_qa))

    #value_qa = (value_qa/len(cases))
    
    # definisco qui value_qa come la massima occorrenza del pattern entro i casi
    value_qa = max(stat_pattern_qa)
        
    print('value_qa')
    print(value_qa)
    
    #var_qa è la varianza dei valori sul pattern, servirà per identificare la dimensione del dot, tanto è maggiore varianza, tanto valore è meno significativo
    #var_qa = 0
    #for i in range(len(stat_pattern_qa)):
    #    var_qa = var_qa + ((stat_pattern_qa[i]/len(stat_pattern_qa)) - value_qa)**2
    
    #var_qa = (var_qa/len(cases))
    
    #print('var_qa')
    #print(var_qa)                
    
    # bisogna ora identificare una formula che, per valori bassi di varianza (per assurdo a varianza 0), associa dei valori di trasparenza prossimi a 1 (1 se var è 0, e viceversa); qual è valore massimo varianza?, per valori massimi di varianza, associa valori di trasparenza prossimi a zero, quando considero però una varianza grande? maggiore del valore medio?
    
    # identifico valore massimo possibile della varianza
    #var_max_qa = (((max(stat_pattern_qa)/len(stat_pattern_qa))-value_qa)**2+((min(stat_pattern_qa)/len(stat_pattern_qa))-value_qa)**2)/2

    #print('var_max_qa')
    #print(var_max_qa)
    
    # a partire dal massimo valore possibile della varianza, normalizzo ad un valore tra 0 ed 1 che descrive il livello di trasparenza (1, cioè pieno, se la varianza è nulla)
    #if (var_qa == 0):
    #    trasp_qa = str(1)
    #else:
    #    trasp_qa = "{0:.2f}".format(1-(var_qa/var_max_qa))

    # definisco trasp_qa come il numero di casi che supporta il pattern fratto il numero complessivo di casi
    # quindi trasp_qa è massima, cioè 1, se il pattern è supportato in tutti i casi
    # aggiungo la condizione per cui se un pattern non occorre in nessuno dei casi, e quindi value_qa = 0, allora la trasparenza è massima (di fatto è come se l'assenza del pattern fosse supportata in tutti i casi)
    trasp_qa = 0    
    if (value_qa != 0):
        for i in range(len(stat_pattern_qa)):
            if (stat_pattern_qa[i] != 0):
                trasp_qa = trasp_qa + 1
            
        trasp_qa = "{0:.2f}".format(trasp_qa/len(cases))
    else: trasp_qa = '1'

    print('trasp_qa')
    print(trasp_qa)
    
    
###########################################################################################################
########################################################################### end query per question-answer-orientedness
###########################################################################################################

########################################################################### query per redundancy-orientedness
# al momento parliamo di redundancy (of functions) within cases
# cioè valutiamo se si presenta ridondanza all'interno del singolo caso, cioè se ci sono le stesse attività che sono eseguite da più
# performers entro lo stesso caso: poi valuteremo il supporto, cioè quanti casi supportano questo pattern
# vediamo se riusciamo anche a fornire un valore massimo e non solo 0 (no redundancy) o 1 (redundancy) andando a
# recuperare la massima cardinalità dell'insieme intersezione
# FATTO: ABBIAMO CARDINALITà. Unica cosa è che sono contate attività solo se differenti, perchè stiamo lavorando con interesezione
###########################################################################################################

############################### questa è la query in Cypher
#match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer) where c.id = '1' and p.name='John' with collect(distinct act.name) as name
#match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer) where c.id = '1' and p.name<>'John' with name as nameperf, collect(distinct act.name) as namenot
#return FILTER(x IN nameperf WHERE x IN namenot) as redundancy
##############################
##################################### VALUTA LA PRESENZA DI DISTINCT RISPETTO ALLE ATTIVITà RESTITUITE, SE NON LO METTIAMO PROBLEMI,
##################################### SE LO METTIAMO PERò COSA PERDIAMO?

    query_string_fisso1="match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p1:performer) where c.id = {case} "
        
    #costruzione condizione su performer1
    if (performer1.get()!=""):
        if (performer1.get()=="*"):
            query_string_perf1 = "p1.name=~'.*'"
        else:
            query_string_perf1 = "p1.name=~'"+performer1.get()+"'"
    else:    
        query_string_perf1 = "p1.name=~'.*'"

        
    query_string_performers=" and " + query_string_perf1

    #semplifico la condizione e decido di mettere sempre la stringa con i valori diversi, se ho checcato cerca differenti
    query_string_fisso2=" with collect(distinct act.name) as name "
    
    query_string_fisso3="match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p1:performer) where c.id = {case} "
    
        #costruzione condizione su performer1
    if (performer1.get()!=""):
        if (performer1.get()=="*"):
            query_string_notperf1 = "and p1.name<>'.*'"
        else:
            query_string_notperf1 = "and p1.name<>'"+performer1.get()+"'"
    else:    
        query_string_notperf1 = "and p1.name<>'.*'"

    query_string_fisso4 = "with name as nameperf, collect(distinct act.name) as namenot "
    
    query_string_fisso5 = "return FILTER(x IN nameperf WHERE x IN namenot) as redundancy"
        
    query_string=query_string_fisso1+query_string_performers+query_string_fisso2+query_string_fisso3+query_string_notperf1+query_string_fisso4+query_string_fisso5
    
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
            patt_case.append(record["redundancy"])
        pattern.append(patt_case)   

    print('pattern')
    print(pattern)

    # primo caso, in posizione [0]
    print('pattern[0]')
    print(pattern[0][0])
    print('len-pattern[0]')
    print(len(pattern[0][0]))
    # questo conta quante volte è stato identificato il pattern nel primo caso (caso in posizione [0])

############################### tabella con le statistiche sui pattern
# diverso rispetto agli altri casi perchè in pattern, se c'è attività ripetuta ho lista di liste, quindi prendo solo il primo elemento che
# identifica appunto quali sono le attività ripetute, se però non c'è ripetizione la lista è vuota quindi non posso prendere il primo elemento
    stat_pattern_redundancy=[]
    for i in range(len(cases)):
        if (len(pattern[i]) != 0):
            stat_pattern_redundancy.append(len(pattern[i][0]))
        else:
            stat_pattern_redundancy.append(len(pattern[i]))
            
    print('stat_pattern_redundancy')
    print(stat_pattern_redundancy)
    
    #value_handover rappresenta il valore di handover-orientedness mostrata sul radar chart (è la media sui valori)
    #value_handover = 0
    #for i in range(len(stat_pattern_handover)):
    #    value_handover = value_handover + (stat_pattern_handover[i]/len(stat_pattern_handover))

    #value_handover = (value_handover/len(cases))
    
    # definisco qui value_handover come la massima occorrenza del pattern entro i casi
    value_redundancy = max(stat_pattern_redundancy)
    print('value_redundancy')
    print(value_redundancy)
    
    #var_handover è la varianza dei valori sul pattern, servirà per identificare la dimensione del dot, tanto è maggiore varianza, tanto valore è meno significativo
    #var_handover = 0
    #for i in range(len(stat_pattern_handover)):
    #    var_handover = var_handover + ((stat_pattern_handover[i]/len(stat_pattern_handover)) - value_handover)**2
    
    #var_handover = (var_handover/len(cases))
    
    #print('var_handover')
    #print(var_handover)

    # identifico valore massimo possibile della varianza
    #var_max_handover = (((max(stat_pattern_handover)/len(stat_pattern_handover))-value_handover)**2+((min(stat_pattern_handover)/len(stat_pattern_handover))-value_handover)**2)/2

    #print('var_max_handover')
    #print(var_max_handover)
    
    # a partire dal massimo valore possibile della varianza, normalizzo ad un valore tra 0 ed 1 che descrive il livello di trasparenza (1, cioè pieno, se la varianza è nulla)
    #if (var_handover == 0):
    #    trasp_handover = str(1)
    #else:
    #    trasp_handover = "{0:.2f}".format(1-(var_handover/var_max_handover))

    # definisco trasp_handover come il numero di casi che supporta il pattern fratto il numero complessivo di casi
    # quindi trasp_handover è massima, cioè 1, se il pattern è supportato in tutti i casi
    # aggiungo la condizione per cui se un pattern non occorre in nessuno dei casi, e quindi value_qa = 0, allora la trasparenza è massima (di fatto è come se l'assenza del pattern fosse supportata in tutti i casi)
    trasp_redundancy = 0
    if (value_redundancy != 0):
        for i in range(len(stat_pattern_redundancy)):
            if (stat_pattern_redundancy[i] != 0):
                trasp_redundancy = trasp_redundancy + 1
            
        trasp_redundancy = "{0:.2f}".format(trasp_redundancy/len(cases))
    else: trasp_redundancy = '1'
    
    
    
    print('trasp_redundancy')
    print(trasp_redundancy)
        
###########################################################################################################    
########################################################################### end query per redundancy-orientedness
###########################################################################################################

########################################################################### query per redundancy-orientedness between
# al momento parliamo di redundancy (of functions) BETWEEN cases
# cioè valutiamo se si presenta ridondanza TRA TUTTE LE ATTIVITà SVOLTE DAL PERFORMER RISPETTO AD UN singolo caso,
# poi valuteremo il supporto, cioè quanti casi supportano questo pattern
###########################################################################################################

############################### questa è la query in Cypher
#match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer) where p.name='John' with collect(distinct act.name) as name
#match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer) where c.id = '1' and p.name<>'John' with name as nameperf, collect(distinct act.name) as namenot
#return FILTER(x IN nameperf WHERE x IN namenot) as redundancy
##############################
##################################### VALUTA LA PRESENZA DI DISTINCT RISPETTO ALLE ATTIVITà RESTITUITE, SE NON LO METTIAMO PROBLEMI,
##################################### SE LO METTIAMO PERò COSA PERDIAMO?


    query_string_fisso1="match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p1:performer) where "
        
    #costruzione condizione su performer1
    if (performer1.get()!=""):
        if (performer1.get()=="*"):
            query_string_perf1 = "p1.name=~'.*'"
        else:
            query_string_perf1 = "p1.name=~'"+performer1.get()+"'"
    else:    
        query_string_perf1 = "p1.name=~'.*'"

        
    query_string_performers=query_string_perf1

    #semplifico la condizione e decido di mettere sempre la stringa con i valori diversi, se ho checcato cerca differenti
    query_string_fisso2=" with collect(distinct act.name) as name "
    
    query_string_fisso3="match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p1:performer) where c.id = {case} "
    
        #costruzione condizione su performer1
    if (performer1.get()!=""):
        if (performer1.get()=="*"):
            query_string_notperf1 = "and p1.name<>'.*'"
        else:
            query_string_notperf1 = "and p1.name<>'"+performer1.get()+"'"
    else:    
        query_string_notperf1 = "and p1.name<>'.*'"

    query_string_fisso4 = "with name as nameperf, collect(distinct act.name) as namenot "
    
    query_string_fisso5 = "return FILTER(x IN nameperf WHERE x IN namenot) as redundancy"
        
    query_string=query_string_fisso1+query_string_performers+query_string_fisso2+query_string_fisso3+query_string_notperf1+query_string_fisso4+query_string_fisso5
    
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
            patt_case.append(record["redundancy"])
        pattern.append(patt_case)   

    print('pattern')
    print(pattern)

    # primo caso, in posizione [0]
    print('pattern[0]')
    print(pattern[0][0])
    print('len-pattern[0]')
    print(len(pattern[0][0]))
    # questo conta quante volte è stato identificato il pattern nel primo caso (caso in posizione [0])

############################### tabella con le statistiche sui pattern
# diverso rispetto agli altri casi perchè in pattern, se c'è attività ripetuta ho lista di liste, quindi prendo solo il primo elemento che
# identifica appunto quali sono le attività ripetute, se però non c'è ripetizione la lista è vuota quindi non posso prendere il primo elemento
    stat_pattern_redundancy_btw=[]
    for i in range(len(cases)):
        if (len(pattern[i]) != 0):
            stat_pattern_redundancy_btw.append(len(pattern[i][0]))
        else:
            stat_pattern_redundancy_btw.append(len(pattern[i]))
            
    print('stat_pattern_redundancy_btw')
    print(stat_pattern_redundancy_btw)
    
    #value_handover rappresenta il valore di handover-orientedness mostrata sul radar chart (è la media sui valori)
    #value_handover = 0
    #for i in range(len(stat_pattern_handover)):
    #    value_handover = value_handover + (stat_pattern_handover[i]/len(stat_pattern_handover))

    #value_handover = (value_handover/len(cases))
    
    # definisco qui value_handover come la massima occorrenza del pattern entro i casi
    value_redundancy_btw = max(stat_pattern_redundancy_btw)
    print('value_redundancy_btw')
    print(value_redundancy_btw)
    
    #var_handover è la varianza dei valori sul pattern, servirà per identificare la dimensione del dot, tanto è maggiore varianza, tanto valore è meno significativo
    #var_handover = 0
    #for i in range(len(stat_pattern_handover)):
    #    var_handover = var_handover + ((stat_pattern_handover[i]/len(stat_pattern_handover)) - value_handover)**2
    
    #var_handover = (var_handover/len(cases))
    
    #print('var_handover')
    #print(var_handover)

    # identifico valore massimo possibile della varianza
    #var_max_handover = (((max(stat_pattern_handover)/len(stat_pattern_handover))-value_handover)**2+((min(stat_pattern_handover)/len(stat_pattern_handover))-value_handover)**2)/2

    #print('var_max_handover')
    #print(var_max_handover)
    
    # a partire dal massimo valore possibile della varianza, normalizzo ad un valore tra 0 ed 1 che descrive il livello di trasparenza (1, cioè pieno, se la varianza è nulla)
    #if (var_handover == 0):
    #    trasp_handover = str(1)
    #else:
    #    trasp_handover = "{0:.2f}".format(1-(var_handover/var_max_handover))

    # definisco trasp_handover come il numero di casi che supporta il pattern fratto il numero complessivo di casi
    # quindi trasp_handover è massima, cioè 1, se il pattern è supportato in tutti i casi
    # aggiungo la condizione per cui se un pattern non occorre in nessuno dei casi, e quindi value_qa = 0, allora la trasparenza è massima (di fatto è come se l'assenza del pattern fosse supportata in tutti i casi)
    trasp_redundancy_btw = 0
    if (value_redundancy_btw != 0):
        for i in range(len(stat_pattern_redundancy_btw)):
            if (stat_pattern_redundancy_btw[i] != 0):
                trasp_redundancy_btw = trasp_redundancy_btw + 1
            
        trasp_redundancy_btw = "{0:.2f}".format(trasp_redundancy_btw/len(cases))
    else: trasp_redundancy_btw = '1'
    
    
    
    print('trasp_redundancy_btw')
    print(trasp_redundancy_btw)
        
###########################################################################################################    
########################################################################### end query per redundancy-btw-orientedness
###########################################################################################################


######################################################################################## WORKINPROGRESS
###########################################################################################################
###########################################################################################################    
########################################################################### end query per autonomy-orientedness
###########################################################################################################

########################################################################### query per autonomy-orientedness 
#Se in un caso ce solo 1 performer a completare tutte le attività
#Vedo se tutte l'attività di un caso sono eseguite da quel performer, simile a trovare redundancy within cases
#In questo caso vale o 0 o 1. O c'è oppure no
###########################################################################################################

############################### questa è la query in Cypher
#match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p:performer) where c.id = '1' and p.name<>'John' with collect(distinct act.name) as namenot
#return namenot

# se namenot = [] allora autonomy = 1, altrimenti autonomy vale 0
##############################
    
    query_string_fisso3="match (c:case)-[:includes]->(act:activity)-[:performed_by]->(p1:performer) where c.id = {case} "
    
        #costruzione condizione su performer1
    if (performer1.get()!=""):
        if (performer1.get()=="*"):
            query_string_notperf1 = "and p1.name<>'.*'"
        else:
            query_string_notperf1 = "and p1.name<>'"+performer1.get()+"'"
    else:    
        query_string_notperf1 = "and p1.name<>'.*'"

    query_string_fisso4 = " with collect(distinct act.name) as namenot "
    
    query_string_fisso5 = "return namenot"
        
    query_string=query_string_fisso3+query_string_notperf1+query_string_fisso4+query_string_fisso5
    
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
            patt_case.append(record["namenot"])
        pattern.append(patt_case)   

    print('pattern')
    print(pattern)

    # primo caso, in posizione [0]
    print('pattern[0]')
    print(pattern[0][0])
    print('len-pattern[0]')
    print(len(pattern[0][0]))
    # questo conta quante volte è stato identificato il pattern nel primo caso (caso in posizione [0])

############################### tabella con le statistiche sui pattern
# diverso rispetto agli altri casi perchè in pattern, se c'è attività ripetuta ho lista di liste, quindi prendo solo il primo elemento che
# identifica appunto quali sono le attività ripetute, se però non c'è ripetizione la lista è vuota quindi non posso prendere il primo elemento
    stat_pattern_autonomy=[]
    for i in range(len(cases)):
        if (len(pattern[i][0]) != 0):
            stat_pattern_autonomy.append(0)
        else:
            stat_pattern_autonomy.append(1)
            
    print('stat_pattern_autonomy')
    print(stat_pattern_autonomy)
    
    #value_handover rappresenta il valore di handover-orientedness mostrata sul radar chart (è la media sui valori)
    #value_handover = 0
    #for i in range(len(stat_pattern_handover)):
    #    value_handover = value_handover + (stat_pattern_handover[i]/len(stat_pattern_handover))

    #value_handover = (value_handover/len(cases))
    
    # definisco qui value_handover come la massima occorrenza del pattern entro i casi
    value_autonomy = max(stat_pattern_autonomy)
    print('value_autonomy')
    print(value_autonomy)
    
    #var_handover è la varianza dei valori sul pattern, servirà per identificare la dimensione del dot, tanto è maggiore varianza, tanto valore è meno significativo
    #var_handover = 0
    #for i in range(len(stat_pattern_handover)):
    #    var_handover = var_handover + ((stat_pattern_handover[i]/len(stat_pattern_handover)) - value_handover)**2
    
    #var_handover = (var_handover/len(cases))
    
    #print('var_handover')
    #print(var_handover)

    # identifico valore massimo possibile della varianza
    #var_max_handover = (((max(stat_pattern_handover)/len(stat_pattern_handover))-value_handover)**2+((min(stat_pattern_handover)/len(stat_pattern_handover))-value_handover)**2)/2

    #print('var_max_handover')
    #print(var_max_handover)
    
    # a partire dal massimo valore possibile della varianza, normalizzo ad un valore tra 0 ed 1 che descrive il livello di trasparenza (1, cioè pieno, se la varianza è nulla)
    #if (var_handover == 0):
    #    trasp_handover = str(1)
    #else:
    #    trasp_handover = "{0:.2f}".format(1-(var_handover/var_max_handover))

    # definisco trasp_handover come il numero di casi che supporta il pattern fratto il numero complessivo di casi
    # quindi trasp_handover è massima, cioè 1, se il pattern è supportato in tutti i casi
    # aggiungo la condizione per cui se un pattern non occorre in nessuno dei casi, e quindi value_qa = 0, allora la trasparenza è massima (di fatto è come se l'assenza del pattern fosse supportata in tutti i casi)
    trasp_autonomy = 0
    if (value_autonomy!= 0):
        for i in range(len(stat_pattern_autonomy)):
            if (stat_pattern_autonomy[i] != 0):
                trasp_autonomy = trasp_autonomy + 1
            
        trasp_autonomy = "{0:.2f}".format(trasp_autonomy/len(cases))
    else: trasp_autonomy = '1'
    
    
    
    print('trasp_autonomy')
    print(trasp_autonomy)
        
###########################################################################################################    
########################################################################### end query per redundancy-btw-orientedness
###########################################################################################################



######################################################################################### ENDWORKINPROGRESS



    import pygal

    # nota consideriamo i valori della dimensione dei dot compresi tra 1 e 16
    radar_chart = pygal.Radar()
    radar_chart.title = 'Working Style assessment'
    radar_chart.x_labels = ['Handover-orientedness', 'Rework-orientedness', 'Question-answer-orientedness', 'Redundancy-orientedness', 'Redundancy_btw-orientedness', 'Autonomy-orientedness']
    #radar_chart.add(performer1.get(), [value_handover, value_rework, value_qa], dots_size=4)
    #radar_chart.add(performer1.get(), [{'value': value_handover, 'node': {'r': 2}}, {'value': value_rework, 'node': {'r': 4}}, {'value': value_qa, 'node': {'r': 6}}])    
    # attraverso l'attributo stile posso definire il livello di trasparenza, che faro variare con varianza, sempre che riesca a mettere valore dentro
    # il valore 0 vuol dire vuoto, il valore 1 pieno

    
    #setto trasparenza per i diversi nodi relativi alle dimensioni che esprimono in base alla varianza
    #trasp_handover='0'
    fill_handover = 'fill : rgba(255, 45, 20, '+trasp_handover+')'
    #trasp_rework='0.4'
    fill_rework = 'fill : rgba(255, 45, 20, '+trasp_rework+')'
    #trasp_qa='1'
    fill_qa = 'fill : rgba(255, 45, 20, '+trasp_qa+')'
    # traspredundancy
    fill_redundancy = 'fill : rgba(255, 45, 20, '+trasp_redundancy+')'
    # traspredundancy_btw
    fill_redundancy_btw = 'fill : rgba(255, 45, 20, '+trasp_redundancy_btw+')'
    # autonomy
    fill_autonomy = 'fill : rgba(255, 45, 20, '+trasp_autonomy+')'

    
    radar_chart.add(performer1.get(), [{'value': value_handover, 'node': {'r': 6}, 'style': fill_handover}, {'value': value_rework, 'node': {'r': 6}, 'style': fill_rework}, {'value': value_qa, 'node': {'r': 6}, 'style': fill_qa}, {'value': value_redundancy, 'node': {'r': 6}, 'style': fill_redundancy}, {'value': value_redundancy_btw, 'node': {'r': 6}, 'style': fill_redundancy_btw}, {'value': value_autonomy, 'node': {'r': 6}, 'style': fill_autonomy}])    

    #radar_chart.add(performer1.get(), [{'value': value_handover, 'node': {'r': 6}, 'style': a}, {'value': value_rework, 'node': {'r': 6}, 'style': 'fill: rgba(255, 45, 20, .4)'}, {'value': value_qa, 'node': {'r': 6}, 'style': 'fill: rgba(255, 45, 20, 1)'}])    
    radar_chart.render_to_file('ws_radar_chart.svg')

########################################################## end generate_workingstylequery

    
root = Tk()
root.title("Working Style assessment")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)


############ aggiungo var per i combobox relativi ai performer
performer1 = StringVar()
performer2 = StringVar()


######################################### da qui costruzione di pattern creator

ttk.Label(mainframe, text="Performer 1").grid(column=1, row=2, sticky=W)

################lista di valori da inserire nelle combo dei performer
perfcombovalues = ['*']
perfcombovalues.extend(performer_dist) 

########### combo performer1
perf1=ttk.Combobox(mainframe, textvariable=performer1)
perf1.grid(column=1, row=3, sticky=W)
#########inserisco i valori possibili (posso usare quindi list performer_dist già preparata)
#perf1['values']=['*', 'Clare', 'Fred', 'Jane', 'John', 'Mike', 'Mona', 'Pete', 'Robert', 'Sue']
perf1['values']=perfcombovalues


ttk.Label(mainframe, text="Performer 2").grid(column=3, row=2, sticky=W)

########### combo performer2
perf2=ttk.Combobox(mainframe, textvariable=performer2)
perf2.grid(column=3, row=3, sticky=W)
#########inserisco i valori possibili (posso usare quindi list performer_dist già preparata)
#perf2['values']=['*', 'Clare', 'Fred', 'Jane', 'John', 'Mike', 'Mona', 'Pete', 'Robert', 'Sue']
perf2['values']=perfcombovalues


ttk.Label(mainframe, text="with respect to").grid(column=2, row=3, sticky=W)

############### bottone per generare working style NUOVO!!!!
ttk.Button(mainframe, text="Get working style of", command=generate_workingstylequery).grid(column=1, row=1, sticky=W)
# nota: dopo ogni search pattern dovresti ripulire le opzioni dall'interfaccia



for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

root.mainloop()
################################################# END GUI


############################### aggiungo parte relativa alle query per identificare patterns


session.close()


