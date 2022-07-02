#!/usr/bin/perl
use IPC::SysV;
use IPC::Msg;
$msgtext="/usr/bin/perl";
#use constant 1234=> "/etc/group";
$msg = new IPC::Msg(pack("l","1234"),0);
$msg->snd($msgtype,$msgtext,0);
print "Status of MSGQUEUE:$IPC::Msg::stat\n";
$statusqueue=msgget pack("l","1234"),0;
print "ID MSGQUEUE:$statusqueue\n";
$status = msgsnd pack("l","12345"),$msgtext,0;
#print $status;
#Read MSGQUEUE
#while(1){
$recive = $msg->rcv($buf,"256",0,0);
#$statusrcv=msgrcv pack("l","12345"),$buf,256,0,0;
print "Buffer $statusrcv MSGQUEUE:$buf Recive:$recive";
#}
#$msg->remove;

