#!/usr/bin/perl
#
# vis|wall backend script packet filter
# itsoft Software GmbH 
# 24.03.2003
# Version 1.0 - 12.5.2003
#


my $mysql_db = "viswall";
my $mysql_host ="localhost";
my $mysql_user = "fillme";
my $mysql_passwd = "fillme";
my $datenbank="mysql";
my $db_table_interfaces="io_interfaces";
my $db_table_gateway="io_gateway";
my $path_output="/viswall/configscripts/interfaces.sh"; 
my $path_ifconfig="/sbin/ifconfig";
my $path_route="/sbin/route";
my $echo_program="/bin/echo";
my $first="";

use DBI;


#Description
sub headwrite_interface{
$first=$first."#!/bin/bash\n";
$first=$first."###########################################\n";
$first=$first."# Created by Viswall                      #\n";
$first=$first."# itsoft Software GmbH                    #\n";
$first=$first."# script developer: Leitner Christian     #\n";
$first=$first."# contact: christian.leitner@itsoft.at    #\n";
$first=$first."# INTERFACE CONFIGURE SCRIPT 		  #\n";
$first=$first."# TIMESTAMP: ".localtime()."     #\n";
$first=$first."###########################################\n";
return $first;
}


sub write_interfaces{ # main part of the work
    my ($path_output,$path_ifconfig,$dbh,$db_table_interfaces,$db_table_gateway,$path_route) = @_;
    $head = headwrite_interface();
    my $sth=$dbh->prepare ("Select * from ".$db_table_interfaces."");
    $sth->execute;
    # get default Route
    my $sth1=$dbh->prepare("SELECT adress FROM ".$db_table_gateway."");
    $sth1->execute;
    my $adress=$sth1->fetchrow_array;
    open (OUTPUT1,">$path_output"); 
    print OUTPUT1 $head."\n";       
    while (my ($id,$name,$ip,$note,$sticky,$netmask) = $sth->fetchrow_array){
	print OUTPUT1 $echo_program." \"bringing up interface ".$name." [".$note."]\"\n";
        print OUTPUT1 $path_ifconfig." ".$name." ".$ip." netmask ".$netmask." # ".$note."\n";
    }
    print OUTPUT1 $path_route." del default\n";
    print OUTPUT1 $path_route." add default gw ".$adress."\n\n";
    close(OUTPUT1);
	launch_script();
}

sub launch_script{
        system("/bin/bash ".$path_output);
}
    

#Load Kernel Modules

# connect to database
my $dbh = DBI->connect ("dbi:$datenbank:host=$mysql_host;database=$mysql_db",$mysql_user,$mysql_passwd);


# call write function
write_interfaces($path_output,$path_ifconfig,$dbh,$db_table_interfaces,$db_table_gateway,$path_route);
