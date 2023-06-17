# Installation 
The following command installs the clouddb package
```
pip3 install 'git+https://github.com/tumpji/PBS-Pro-Toolkit#subdirectory=clouddb'
```

# The package clouddb
The basic usage:
```
from clouddb import DBConnection, NoMoreWork

connection = DBConnection('name_of_collection_in_the_database')
try:
  while True:
    with connection as arg_dict:
      <use arg_dict = the data saved to database>
except NoMoreWork:
  exit(0)
```

# Template of DB inserting script
Using the [script](template_job_creation.py) template is advised.
Firstly, fill in the script's implementation of the `generator()` function.
It should be a generator that yields dictionaries that make the database content - the keys are database fields.
There is no need to specify the field beforehand.

The collection can be changed using `--collection <name>`. 
The default value is the name of the script `aaa.py -> aaa`, so 
it can be beneficial to name the script to match the collection's name or change the default value generation.

The script has a required argument `--action <?>`. 
- The action `insert`, `add` runs the insertion process (`generator()`). It does not delete anything.
- The action `drop_all`, `clean_all` cleans all data in the collection.
- The action `refresh_blocked`, `refresh_blocks`, `clean_blocked`, `clean_blocks`
  removes all blocked (the computations that threw exceptions) to the beginning.
- The action `refresh_errored`, `refresh_errors`, `clean_errored`, `clean_errors`
  removes all errors (the computations that threw exceptions) to the beginning.
- The action `show`, `list`, `display`
  shows the number of elements in the collection - in all 4 documents in the selected collection.

If the filling is too slow, you can use the `--multiprocessing` switch with optional `--threads <# of processes>` argument.
