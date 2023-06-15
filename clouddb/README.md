# Installation 
To install this package run this script.
```   
pip3 install 'git+https://github.com/tumpji/PBS-Pro-Toolkit#subdirectory=clouddb'
```

# Basic usage
The basic usage:
```
connection = DBConnection('name_of_collection_in_the_database')
try:
  while True:
    with connection as arg_dict:
      <use arg_dict = the data saved to database>
except NoMoreWork:
  exit(0)
```

# Template of DB inserting script
The [script](template_job_creation.py) can be modified to fill in the database using the `generator()` function.
The `--collection` is the collection's name in the database. 
It is automatically pre-filled to the script's name without the `.py` suffix.

You must provide action `--action ???` to select the method you want to run.
- The action `insert`, `add` runs insertion process = `generator()`.
- The action  `drop_all`, `clean_all` cleans all data in the collection.
- The action `refresh_blocked`, `refresh_blocks`, `clean_blocked`, `clean_blocks`
  removes all blocked (the computations that threw exceptions) to the beginning.
- The action `refresh_errored`, `refresh_errors`, `clean_errored`, `clean_errors`
  removes all errors (the computations that threw exceptions) to the beginning.
- The action `show`, `list`, `display`
  shows the number of elements in the collection.

If the filling is too slow, you can use the `--multiprocessing` switch with optional `--threads <# of processes>` argument.
