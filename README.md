
### Intro

Neovis has problems communicating with neo4j database on Amazon. Namely, neovis does not trust the self-signed certificates that reaside on Amazon server thus refuses to fetch the data from there. Until we fix the issue the only way to test whole application is to use local instance of neo4j database.

### Preliminaries

Clone source code from Github. Install required dependencies (```pip install -r requirements.txt```).

There is the `config.py` file in the project root directory. It contains DevelopmentConfig object. You have to change DB_USER and DB_PASSWORD with the correct values (i.e. your user and your password)

Note: Program is written and tested in `python: 3.6`.

### Populate database

You can use data base management script, `dbms.py`, to populate database from csv data. Run `python dbms.py` from project root directory.

Note: This will drop and recreate whole database.

### Running the web application

Run command `python app.py` from project root directory. This will start the debug web server on `127.0.0.1:5000`, after this you can use your browser to access the application via url `http://localhost:5000`.
