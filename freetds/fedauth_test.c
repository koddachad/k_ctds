/*
 * Spike test for FreeTDS federated (Entra ID) authentication via DB-Library.
 *
 * Build (against the patched install in ~/freetds-fedauth):
 *   gcc -o fedauth_test fedauth_test.c -I$HOME/freetds-fedauth/include \
 *       -L$HOME/freetds-fedauth/lib -lsybdb -Wl,-rpath,$HOME/freetds-fedauth/lib
 *
 * Run:
 *   export FEDAUTH_SERVER=myserver.database.windows.net
 *   export FEDAUTH_DATABASE=mydb
 *   export FEDAUTH_TOKEN="$(az account get-access-token --resource https://database.windows.net/ --query accessToken -o tsv)"
 *   TDSDUMP=/tmp/fedauth.log ./fedauth_test
 *
 * Regression check (SQL authentication, no token):
 *   FEDAUTH_SERVER=host FEDAUTH_USER=sa FEDAUTH_PASSWORD=... ./fedauth_test
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sybfront.h>
#include <sybdb.h>

static int
err_handler(DBPROCESS *dbproc, int severity, int dberr, int oserr, char *dberrstr, char *oserrstr)
{
	(void) dbproc; (void) oserr;
	fprintf(stderr, "DB-Library error %d (severity %d): %s\n", dberr, severity, dberrstr ? dberrstr : "");
	if (oserrstr && *oserrstr)
		fprintf(stderr, "  OS error: %s\n", oserrstr);
	return INT_CANCEL;
}

static int
msg_handler(DBPROCESS *dbproc, DBINT msgno, int msgstate, int severity, char *msgtext, char *srvname, char *procname, int line)
{
	(void) dbproc; (void) msgstate; (void) procname; (void) line;
	fprintf(stderr, "Server message %d (severity %d) from %s: %s\n", (int) msgno, severity, srvname ? srvname : "", msgtext ? msgtext : "");
	return 0;
}

int
main(void)
{
	const char *server = getenv("FEDAUTH_SERVER");
	const char *database = getenv("FEDAUTH_DATABASE");
	const char *token = getenv("FEDAUTH_TOKEN");
	/* regression mode: no token, plain SQL authentication */
	const char *user = getenv("FEDAUTH_USER");
	const char *password = getenv("FEDAUTH_PASSWORD");
	LOGINREC *login;
	DBPROCESS *dbproc;
	char who[256] = "";
	char ver[256] = "";

	if (!server || (!token && !(user && password))) {
		fprintf(stderr, "set FEDAUTH_SERVER and either FEDAUTH_TOKEN or FEDAUTH_USER + FEDAUTH_PASSWORD "
			"(FEDAUTH_DATABASE optional)\n");
		return 2;
	}

	if (dbinit() == FAIL)
		return 1;
	dberrhandle(err_handler);
	dbmsghandle(msg_handler);

	login = dblogin();
	DBSETLAPP(login, "fedauth_test");
	DBSETLVERSION(login, DBVERSION_74);
	DBSETLUTF16(login, 1);
	DBSETLCHARSET(login, "UTF-8");
	DBSETLENCRYPTION(login, "require");
	if (database)
		DBSETLDBNAME(login, database);
	if (token) {
		if (DBSETLFEDAUTHTOKEN(login, token) == FAIL) {
			fprintf(stderr, "DBSETLFEDAUTHTOKEN failed\n");
			return 1;
		}
	} else {
		DBSETLUSER(login, user);
		DBSETLPWD(login, password);
	}

	dbproc = dbopen(login, server);
	dbloginfree(login);
	if (!dbproc) {
		fprintf(stderr, "dbopen failed\n");
		return 1;
	}

	dbcmd(dbproc, "SELECT SUSER_SNAME(), @@VERSION");
	if (dbsqlexec(dbproc) == FAIL || dbresults(dbproc) != SUCCEED) {
		fprintf(stderr, "query failed\n");
		return 1;
	}
	dbbind(dbproc, 1, NTBSTRINGBIND, sizeof(who), (BYTE *) who);
	dbbind(dbproc, 2, NTBSTRINGBIND, sizeof(ver), (BYTE *) ver);
	while (dbnextrow(dbproc) != NO_MORE_ROWS)
		printf("logged in as: %s\nserver: %.80s\n", who, ver);

	dbclose(dbproc);
	dbexit();
	return 0;
}
