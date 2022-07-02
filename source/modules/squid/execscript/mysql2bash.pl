#!/usr/bin/perl

my $mysql_db = "viswall";
my $mysql_host ="localhost";
my $mysql_user = "fillme";
my $mysql_passwd = "fillme";
my $datenbank="mysql";
my $db_table_tbf="squid_settings";
#my $path_squid="squid.conf";
my $path_output="/etc/squid/squid.conf"; 
my $first="";

use DBI;


#Beschreibung
sub headwrite{
$first=$first."###########################################\n";
$first=$first."# Created by Viswall                      #\n";
$first=$first."# DOMEDIA Creative Labs                   #\n";
$first=$first."# SQUID CONFIGURE SCRIPT 		 #\n";
$first=$first."# TIMESTAMP: ".localtime()."     #\n";
$first=$first."###########################################\n";
return $first;
}
#Load Kernel Modules

#Verbinden mit der mysql Datenbank
my $dbh = DBI->connect ("dbi:$datenbank:host=$mysql_host;database=$mysql_db",$mysql_user,$mysql_passwd);
my $sth=$dbh->prepare ("Select * from ".$db_table_tbf);
$sth->execute;
$head = headwrite();
open (OUTPUT,">$path_output");
#print OUTPUT "#!/bin/bash\n";
print OUTPUT $heaD; 

while (my ($id,$http_port,$icp_port,$htcp_port,$tcp_outgoing_adress,$udp_outgoing_adress,$udp_incomming_adress,$cache_mem,$cache_swap_low,$cache_swap_high,$maximum_object_size,$minimum_object_size,$icp_query_timeout,$maximum_icp_query_timeout,$mcast_icp_query_timeout,$dead_peer_timeout,$maximum_object_size_in_memory,$ipcache_low,$ipcache_high,$fqdn_cache_size,$cache_replacement_policy,$memory_replacement_policy) = $sth->fetchrow_array){
#write to  output bash 
print OUTPUT "#General Squid Settings\n";
print OUTPUT "#PORTS:\n";
print OUTPUT "http_port ".$http_port."\n";
print OUTPUT "icp_port ".$icp_port."\n";
print OUTPUT "htcp_port ".$htcp_port."\n";
print OUTPUT "#ADRESSES:\n";
print OUTPUT "tcp_outgoing_address ".$tcp_outgoing_adress."\n";
print OUTPUT "udp_outgoing_address ".$udp_outgoing_adress."\n";
print OUTPUT "udp_incoming_address ".$udp_outgoing_adress."\n";
print OUTPUT "#Cache Options:\n";
print OUTPUT "cache_mem ".$cache_mem." bytes\n";
print OUTPUT "cache_swap_low ".$cache_swap_low."\n";
print OUTPUT "cache_swap_high ".$cache_swap_high."\n";
print OUTPUT "maximum_object_size ".$maximum_object_size." bytes\n";
print OUTPUT "minimum_object_size ".$minimum_object_size." bytes\n";
print OUTPUT "maximum_object_size_in_memory ".$maximum_object_size_in_memory." bytes\n";
print OUTPUT "fqdncache_size ".$fqdn_cache_size."\n";
print OUTPUT "cache_replacement_policy lru\n";
print OUTPUT "memory_replacement_policy lru\n";
print OUTPUT "#Timeouts:\n";
print OUTPUT "connect_timeout 120 seconds\n";
print OUTPUT "peer_connect_timeout 30 seconds\n";
print OUTPUT "siteselect_timeout 4 seconds\n";
print OUTPUT "read_timeout 15 minutes\n";
print OUTPUT "request_timeout 30 seconds\n";
print OUTPUT "client_lifetime 1 day\n";
print OUTPUT "half_closed_clients on\n";
print OUTPUT "pconn_timeout 120 seconds\n";
print OUTPUT "ident_timeout 10 seconds\n";
print OUTPUT "shutdown_lifetime 30 seconds\n";
print OUTPUT "#ICP Einstellungen:\n";
print OUTPUT "icp_query_timeout ".$icp_query_timeout."\n";
print OUTPUT "maximum_icp_query_timeout ".$maximum_icp_query_timeout."\n";
print OUTPUT "dead_peer_timeout ".$dead_peer_timeout." seconds\n";
#print OUTPUT "redirect_program /usr/bin/squidGuard -c /viswall/execscripts/squidguard/squidguard.conf\n";
print OUTPUT "acl all src 0.0.0.0/0.0.0.0\n";
print OUTPUT "httpd_accel_host virtual"
print OUTPUT "httpd_accel_port 80"
print OUTPUT "httpd_accel_with_proxy on"
print OUTPUT "httpd_accel_uses_host_header on"
}
close (OUTPUT);
