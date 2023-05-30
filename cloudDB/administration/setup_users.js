
/* remove all users */
db.dropAllUsers()


/* creates admin */
db.createUser(
	{ 
		user: "admin", 
		pwd: "adminpassword", 
		roles: ["userAdminAnyDatabase", "dbAdminAnyDatabase", "readWriteAnyDatabase"]
	}
)


/* creates user */
db.createUser(
	{ 
		user: "user", 
		pwd: "userpassword", 
		roles: ["readWriteAnyDatabase"]
	}
)
