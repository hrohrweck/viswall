/***************************************************************************
                          main.cpp  -  description
                             -------------------
    begin                : Tue Feb 19 13:14:41 CET 2002
    copyright            : (C) 2002 by Rohrweck Horst
    email                : horst.rohrweck@webmasters.co.at
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <iostream>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <stdio.h>
#include <fcntl.h>
#include <errno.h>
#include <unistd.h>
#include <syslog.h>
#include "cmsgqueue.h"
#include "convert.h"

using namespace std;

//#define QUEUE_KEY_READ	650001L
//#define QUEUE_KEY_WRITE 650002L
#define QUEUE_KEY_READ	10001L
#define QUEUE_KEY_WRITE 10002L
#define APP_NAME	"viswalld"

#define SIG_KILLINGME	9999
#define SIG_OK		0
#define SIG_NOK		1

int demonize ()
{
	pid_t pid;

	if ((pid=fork()) <0)
		return(-1);
	else if (pid != 0)
		exit (0);

	setsid ();

	chdir ("/");

	umask(0);

	return (0);
}

int main(int argc, char *argv[])
{
	CMsgQueue *readQueue;
	CMsgQueue *writeQueue;
	long type;
	char Message[1024];
	int errorcode;

	demonize ();
	
	openlog (APP_NAME, LOG_PID | LOG_CONS | LOG_NDELAY, LOG_LOCAL0 );
	
	readQueue=new CMsgQueue(QUEUE_KEY_READ);
	writeQueue=new CMsgQueue(QUEUE_KEY_WRITE);

	syslog (LOG_NOTICE, "gone to daemon mode\n");

	for (;;)
	{
		memset (Message,0,1024);
		errorcode=readQueue->Receive (&type, Message, 1024);
		
		if (errorcode==EIDRM) {
			syslog (LOG_NOTICE, "received EIDRM, killing myself");
			writeQueue->Send(1, (char *)::string(::string("[") + stringify(SIG_NOK) + ::string("]: ") + ::string("received EIDRM, killing myself")).c_str());		
			break;
		}
		
		if (errorcode!=ENOMSG) {
			if (strcmp (Message, "KILLYOU")==0) {
				writeQueue->Send(1, (char *)::string(::string("[") + stringify(SIG_KILLINGME) + ::string("]: ") + ::string("killing me")).c_str());
				break;
			} else {
				errorcode=system (Message);

				syslog (LOG_NOTICE, ::string(::string(Message) + ::string (" executed, result: ") + stringify (errorcode) + ::string("\n")).c_str());
				writeQueue->Send(1, (char *)::string(::string("[") + stringify(SIG_OK) + ::string("]: ") + ::string("executed \"") + ::string (Message) + ::string("\" with errorcode [") + stringify (errorcode) + ::string("]")).c_str());
			}
		}

		sleep (1);
	}

	delete readQueue;
	delete writeQueue;

	syslog(LOG_NOTICE, "shutting down.\n");

	closelog();
  
  	return EXIT_SUCCESS;
}
