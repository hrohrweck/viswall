#!/usr/bin/perl
use IPC::SysV;
use IPC::Msg;
$msgtext="/usr/bin/perl";
$msg = new IPC::Msg(pack("l","1234"),0);
$msg->snd($msgtype,$msgtext,0);
#while(1){
$recive = $msg->rcv($buf,"256",0,0);
print "Buffer QUEUE:$buf Recive:$recive\n";
$status = $msg->stat;
print "Status of QUEUE:$status\n";

