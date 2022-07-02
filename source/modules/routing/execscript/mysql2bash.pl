#!/usr/bin/perl
#
# vis|wall backend script ip routing
# itsoft Software GmbH 
# 29.03.2003
# Version 1.1 - 27.05.2003
#

my $mysql_db = "viswall";
my $mysql_host ="localhost";
my $mysql_user = "fillme";
my $mysql_passwd = "fillme";
my $datenbank="mysql";
my $path_output="/viswall/configscripts/route.sh"; 
my $path_route="/sbin/route";
my $path_net_route="/proc/net/route";
my $db_table_routing="strategies_routing";
my $db_table_interfaces="io_interfaces";
my $db_table_hosts="no_hosts";
my $db_table_networks="no_networks";
my $pack_template="V"; # used by the pack() function. "N" for Network style (big endian), "V" for VAX style (little endian)
my $first="";

use DBI;
use Socket;
use Net::Netmask;
#Description
sub headwrite_routing{
	$first=$first."#!/bin/bash\n";
	$first=$first."###########################################\n";
	$first=$first."# Created by vis|wall                     #\n";
	$first=$first."# itsoft Software GmbH                    #\n";
	$first=$first."# ROUTING CONTROL SCRIPT  		  #\n";
	$first=$first."# TIMESTAMP: ".localtime()."     #\n";
	$first=$first."###########################################\n";
	return $first;
}


sub write_routes{ # main part of the work
    my ($dbh) = @_;
    $head = headwrite_routing();
    my $sth=$dbh->prepare ("Select * from ".$db_table_routing." WHERE status=1"); 
    $sth->execute;
    open (OUTPUT1,">$path_output"); 
    print OUTPUT1 $head;
    # flush old rules
    print OUTPUT1 "\n";
    print OUTPUT1 cleanup(); # Print cleanup rules.
    print OUTPUT1 "\n";
    # print rules
    while (my ($id,$type,$did,$gateway,$metric,$iid) = $sth->fetchrow_array){
   	# get values
        $destination=getip($type,$did,$dbh);
        $gateway=getip(1,$gateway,$dbh);
        $iface=getinterface($iid,$dbh);
        
        # print
    	print OUTPUT1 $path_route." --inet add ".$destination." gw ".$gateway." metric ".$metric.$iface."\n";
        $destination="";
        $gateway="";
        $metric="";
        $iface="";
    }
    close(OUTPUT1);
	launch_script();
    return;
}

sub cleanup{
        my $line;
        my $del_line;
        open (OUTPUT, "<$path_net_route");
        # read dummy line
        readline(OUTPUT);
        while (!(eof(OUTPUT))) {
                $line = readline(OUTPUT);
                my ($iface,$dest,$gateway,$flags,$refCnt,$use,$metric,$mask) = split(chr(9),$line);
                if (chk_rule($iface,$dest,$gateway,$flags,$refCnt,$use,$metric,$mask)==0){
                	$del_line=$del_line.print_del_rule($iface,$dest,$gateway,$flags,$refCnt,$use,$metric,$mask);
                }
        }
        close (OUTPUT);
	return $del_line."\n";
}

sub chk_rule{
        my($iface,$dest,$gateway,$flags,$refCnt,$use,$metric,$mask)=@_;
        my $selected=0;
        # $selected = fate of rule: 0 delete, 1 keep
        if(hex($dest)==0x00000000) { # case default route
                $selected=1;
        }
        if(hex($gateway)==0x00000000) { # case route to local attached network
                $selected=1;
        }
        return $selected;
}

sub print_del_rule{ # returns one cleanup record
        my($iface,$dest,$gateway,$flags,$refCnt,$use,$metric,$mask)=@_;
	my $del_rule;
	my $addon;
	# get human readable values
	my $dest_dec=convert_ip($dest);
	my $mask_dec=convert_ip($mask);
	my $gateway_dec=convert_ip($gateway);
       	my $mask_bits=netmask_bits($dest_dec, $mask_dec);
       	
        if ($mask eq "255.255.255.255") {
                $addon="-host";
        } else {
                $addon="-net";
        }


       	$del_rule=$path_route." del ".$addon." ".$dest_dec."/".$mask_bits." gw ".$gateway_dec." dev ".$iface." metric ".$metric."\n";
 
	# Comment by: Christian Leitner 27.05.2003: Wer zum Henker hat das editiert? 
      	#$del_rule=$path_route." del ".	($mask_bits).$dest_dec."/".$mask_bits." gw ".$gateway_dec." dev ".$iface." metric ".$metric."\n";
       	#$del_rule=$path_route." del ".$dest." netmask ".$mask." gw ".$gateway." dev ".$iface." metric ".$metric."\n";
        return $del_rule;
}

sub getip{ # fetch source / dest ip / net
    my($type,$did,$dbh)=@_;
    my $ip;
    if ($type=="1") { #Type Hostroute
        my $sth1 =$dbh->prepare ("Select hostip from ".$db_table_hosts." where id=".$did);
        $sth1->execute;
        $ip = $sth1->fetchrow_array;
        $sth1->finish;
    }
    elsif ($type=="2") { #Type Networkroute
        my $sth1 =$dbh->prepare ("Select networkip,networkmask from ".$db_table_networks." where id=".$did);
        $sth1->execute;
        my ($networkip,$networkmask)=$sth1->fetchrow_array;
        $ip="-net ".$networkip." netmask ".$networkmask;
        $sth1->finish;
    }
    return $ip;
}

sub getinterface{ # get interfaces
    my($iid,$dbh)=@_;
    my $interface;
    if ($iid=="*"){
    	$interface="";
    } else {
    	my $sth1=$dbh->prepare ("SELECT name FROM ".$db_table_interfaces." WHERE id='".$iid."'");
        $sth1->execute;
        $interface=" dev ".$sth1->fetchrow_array;
        $sth1->finish;
    }
    return $interface;
}

sub convert_ip{
        my($ip_hex)=@_;
        my $ip_packed = pack($pack_template, hex($ip_hex));
        return inet_ntoa($ip_packed);
}

sub netmask_bits{
	my ($ip, $netmask)=@_;
	$block = new Net::Netmask ($ip,$netmask);
	return $block->bits();
}

sub chk_netroute{
	my ($bits)=@_;
	my $ret;
	if ($bits!=32){
		$ret="-net ";
	}
	return $ret;
}

sub launch_script{
	system("/bin/bash ".$path_output);
}

# connect to database
my $dbh = DBI->connect ("dbi:$datenbank:host=$mysql_host;database=$mysql_db",$mysql_user,$mysql_passwd);
my $sth=$dbh->prepare ("Select * from ".$db_table_routing);
$sth->execute;

# call write function
write_routes($dbh);
