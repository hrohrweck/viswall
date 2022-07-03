/***************************************************************************
                          cmsgqueue.cpp  -  description
                             -------------------
    begin                : Wed Feb 20 2002
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

#include "cmsgqueue.h"
#include "errno.h"
#include <iostream>
#include <stdlib.h>
#include <fcntl.h>

CMsgQueue::CMsgQueue(key_t QUEUE_KEY){
struct msqid_ds my_msginfo;
	Qhandle=msgget (QUEUE_KEY, IPC_CREAT);
	my_msginfo.msg_perm.mode=666;
	msgctl(Qhandle, IPC_SET, &my_msginfo);
}

CMsgQueue::~CMsgQueue(){
struct msqid_ds my_msginfo;

	msgctl (Qhandle, IPC_RMID, &my_msginfo);
}

int CMsgQueue::Send (long type, char *msgtext)
{
struct Message my_msg;

	my_msg.mtype=type;
	
	if (strlen (msgtext)>=256) {
		strncpy (my_msg.mtext, msgtext, 255);
		my_msg.mtext[255]=0;
	} else strcpy (my_msg.mtext, msgtext);

	if (msgsnd (Qhandle, &my_msg, strlen(my_msg.mtext), IPC_NOWAIT)!=0) {
		return -1;
	}
	else return 0;

	return 0;
}

int CMsgQueue::Receive (long *type, char *msgtext, int max_length)
{
struct Message my_msg;
int errorcode;
	memset (&my_msg,0,sizeof(my_msg));

	errorcode=msgrcv (Qhandle, &my_msg, max_length, 0, IPC_NOWAIT);
	
	if (errorcode==-1) {
		return errno;
	} else {
		strcpy (msgtext, my_msg.mtext);
		*type=my_msg.mtype;
	}

	return 0;
}
