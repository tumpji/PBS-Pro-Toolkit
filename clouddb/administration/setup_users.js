use admin

/* remove all users */
db.dropAllUsers()


/* creates admin */
db.createUser(
	{ 
		user: "admin", 
		pwd: passwordPrompt(),
		roles: ["userAdminAnyDatabase", "dbAdminAnyDatabase", "readWriteAnyDatabase"]
	}
)


/* creates user */
db.createUser(
	{ 
		user: "user", 
		pwd: passwordPrompt(),
		roles: ["readWriteAnyDatabase"]
	}
)
