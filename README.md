
### Preliminaries

python version: 3.6.3

You can use python pip to install required dependencies. Run following command from project root directory

```bash
pip install -r requirements.txt
```

### How to run?

Program receives 2 mandatory and 2 optional arguments to see the usage of the program run

```bash
python tournament_simulator.py -h
```

Assuming neo4j database is already populated with the data from event log file you can run the program using following command

```bash
python main.py db-username-here corresponding-password-here
```

If the neo4j database is empty you can force program to populate it using --seed-db flag

```bash
python main.py db-username-here corresponding-password-here --seed-db
```
