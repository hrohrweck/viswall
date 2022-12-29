#!/usr/bin/perl
#
# vis|wall backend script QoS TBF
# 05.06.2003
# Version 1.1 - 29.12.2022
#

my $configfile = "/viswall/config";
my $datenbank="mysql";
my $db_table_tbf="strategies_tbf";
my $path_tc="/sbin/tc";
my $path_output="/viswall/configscripts/tc_tbf.sh";
my $first="";

use DBI;
use Config::File;

my $config_hash = Config::File::read_config_file($configfile);

my $mysql_db = $config_hash->{DB_NAME_VISWALL};
my $mysql_host = $config_hash->{DB_HOST};
my $mysql_user = $config_hash->{DB_USER};
my $mysql_passwd = $config_hash->{DB_PASS};

sub get_intname{
my ($iid,$dbh)=@_; 
$sth=$dbh->prepare("Select * from io_interfaces where id=".$iid);
$sth->execute;
my($id,$name,$ip,$note,$sticky,$netmask)=$sth->fetchrow_array;
return $name;
}

#Beschreibung
$first=$first."###########################################\n";
$first=$first."# Created by Viswall                      #\n";
$first=$first."# Traffic Control Script (TBF)            #\n";
$first=$first."# TIMESTAMP: ".localtime()."     #\n";
$first=$first."###########################################\n";
#Load Kernel Modules
my $kernel_mod="/sbin/modprobe sch_tbf \n";
#Verbinden mit der mysql Datenbank
my $dbh = DBI->connect ("dbi:$datenbank:host=$mysql_host;database=$mysql_db",$mysql_user,$mysql_passwd);
my $sth=$dbh->prepare ("Select * from ".$db_table_tbf." order by iid");
$sth->execute;
open (OUTPUT,">$path_output");
print OUTPUT "#!/bin/bash\n";
print OUTPUT $first; 
#flush start
print OUTPUT "/sbin/tc qdisc del dev eth0 root\n";
print OUTPUT "/sbin/tc qdisc del dev eth1 root\n";
print OUTPUT "/sbin/tc qdisc del dev eth2 root\n";
# flush end
#print OUTPUT $kernel_mod;
while (my ($id,$rate,$burst,$latency_limit,$mpu,$peakrate,$mtu,$iid,$name,$status) = $sth->fetchrow_array){
#write to  output bash 
$intname = get_intname($iid,$dbh);
print OUTPUT "#TBF Roule fuer Int:".$intname." Name:".$name."\n";
if ($status==0){
print OUTPUT "#";
}
print OUTPUT $path_tc." qdisc add dev ".$intname." root tbf rate ".$rate." latency ".$latency_limit." burst ".$burst."\n"; 
}
close (OUTPUT);
