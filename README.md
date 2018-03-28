
### Intro

Our neo4j database is already deploied on remote server and holds the data from log.csv file. By default program uses that (remote) database. It is possible to alter this behavioure using 4 optional arguments that program supports. They can be used to inject custom database configuration (maybe you want to use local database)

### Preliminaries

Program is written and tested in `python: 3.6.3`


```bash
# Run following command from project root directory to install required dependencies
pip install -r requirements.txt
```

### How to run?

```bash
# See usage information of the program
python main.py -h
```


```bash
# Run program without any arguments to use remote database
python main.py
```


```bash
# Let's say you have local neo4j database (with username neorj, password 123456) up and running.
# If you want to use that instance instead of the remote one use following command 
python main.py --db-username=neo4j --db-password=123456 --driver-uri=bolt://localhost
```


```bash
# You can also use additional --seed-db flag to force program to populate neo4j database from log.csv
python main.py --db-username=neo4j --db-password=123456 --driver-uri=bolt://localhost --seed-db
```
