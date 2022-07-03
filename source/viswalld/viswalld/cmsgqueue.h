/***************************************************************************
                          cmsgqueue.h  -  description
                             -------------------
    begin                : Wed Feb 20 2002
    copyright            : (C) 2002 by Rohrweck Horst
    email                : horst.rohrweck@domedia.at
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

#include <sys/msg.h>
#include <sys/ipc.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>

#ifndef CMSGQUEUE_H
#define CMSGQUEUE_H


/**
  *@author Rohrweck Horst
  */

struct Message {
	long mtype;
	char mtext[1025];
};

class CMsgQueue {
private:
	int Qhandle;

public:
	CMsgQueue(key_t QUEUE_KEY);
	~CMsgQueue();

	int Send (long type, char *msgtext);
	int Receive (long *type, char *msgtext, int max_length);
};

#endif
