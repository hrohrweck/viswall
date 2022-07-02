#!/usr/bin/perl
#
# vis|wall backend script packet filter
# itsoft Software GmbH 
# 24.03.2003
# Version 1.0 - 27.05.2003
#

my $mysql_db = "viswall";
my $mysql_host ="localhost";
my $mysql_user = "fillme";
my $mysql_passwd = "fillme";
my $datenbank="mysql";
my $db_table_filter="strategies_filter";
my $path_output="/viswall/configscripts/filter.sh"; 
my $path_iptables="/usr/sbin/iptables";
my $first="";

use DBI;


#Description
sub headwrite_filter{
$first=$first."#!/bin/bash\n";
$first=$first."###########################################\n";
$first=$first."# Created by vis|wall                     #\n";
$first=$first."# itsoft Software GmbH                    #\n";
$first=$first."# script developer: Leitner Christian     #\n";
$first=$first."# contact: christian.leitner@itsoft.at    #\n";
$first=$first."# FILTER CONFIGURE SCRIPT  		  #\n";
$first=$first."# TIMESTAMP: ".localtime()."     #\n";
$first=$first."###########################################\n";
return $first;
}


sub write_filter{ # main part of the work
    my ($path_output,$dbh,$db_table_filter,$path_filter,$path_iptables) = @_;
    $head = headwrite_filter();
    my $sth=$dbh->prepare ("Select * from ".$db_table_filter." WHERE status=1 ORDER BY priority"); # Query and solve issue with Priorities
    $sth->execute;
    open (OUTPUT1,">$path_output"); 
    print OUTPUT1 $head;
    # flush old rules
    print OUTPUT1 "$path_iptables -F\n";
    # write policies
    my $policy_input=getpolicies(INPUT, $dbh);
    my $policy_output=getpolicies(OUTPUT, $dbh);
    my $policy_forward=getpolicies(FORWARD, $dbh);

    print OUTPUT1 "\n";
    print OUTPUT1 $path_iptables." -P INPUT ".$policy_input."\n";
    print OUTPUT1 $path_iptables." -P OUTPUT ".$policy_output."\n";
    print OUTPUT1 $path_iptables." -P FORWARD ".$policy_forward."\n";
    print OUTPUT1 "\n";
        
    # print rules
    while (my ($id,$stype,$sid,$satype,$said,$dtype,$did,$datype,$daid,$direction,$baction,$siface,$diface) = $sth->fetchrow_array){
    
        $dir = getdirection($direction);
        $source = getip($stype, $sid,0,$dbh);
        $destination = getip($dtype, $did,1,$dbh);
        if(($siface!="*") || ($diface!="*")){
            $iface=getinterface($direction,$siface,$diface,$dbh);
        }
        else {
            $iface="";
        }
        @protocols=getprotocols($satype,$said,$datype,$daid,$dbh);
        $sservice=getservice($satype,$said,0,$dbh);
        $dservice=getservice($datype,$daid,1,$dbh);
        $states=state_machinery($id,$dbh);
        # print
        my $logging;
        if (($baction==0) || ($baction==2)) { # action not log
            if ($baction==0) {
                $action = "DROP";
            }
            elsif ($baction==2) {
                $action = "ACCEPT";
            }
        }
        elsif (($baction==1) || ($baction==3)) { # action log
            if ($baction==1) {
                $action = "DROP";
                $logging = 1;
            }
            elsif ($baction==3) {
                $action = "ACCEPT";
                $logging = 1;
            }
        }
        
        if (@protocols>1) { # if there is more than one protocol defined
            my $i=0;
            while ($i<@protocols) {
                if ($logging==1) { # if logging is on
                    print OUTPUT1 $path_iptables." -A ".$dir." -p ".@protocols[$i]." ".$iface." ".$source." ".$sservice." ".$destination." ".$dservice." ".$states." -j LOG\n";
                }
                print OUTPUT1 $path_iptables." -A ".$dir." -p ".@protocols[$i]." ".$iface." ".$source." ".$sservice." ".$destination." ".$dservice." ".$states." -j ".$action."\n";
                $i++;
            }
        }
        else { # just one protocol
            if ($logging==1) { # if logging is on
                print OUTPUT1 $path_iptables." -A ".$dir." -p ".@protocols[0]." ".$iface." ".$source." ".$sservice." ".$destination." ".$dservice." ".$states." -j LOG\n";
            }
            print OUTPUT1 $path_iptables." -A ".$dir." -p ".@protocols[0]." ".$iface." ".$source." ".$sservice." ".$destination." ".$dservice." ".$states." -j ".$action."\n";
        }
        $logging=0;
    	$dir="";
	$iface="";
	$source="";
	$sservice="";
	$destination="";
	$dservice="";
	$states="";
    }
    close(OUTPUT1);
	launch_script();
}

sub getdirection{ # get packet direction (INPUT / OUTPUT / FORWARD)
    my($direction)=@_;
    my $dir;
    if($direction == 0){
    	$dir = "INPUT";
    }
    if($direction == 1){
    	$dir = "FORWARD";
    }
    if($direction == 2){
    	$dir = "OUTPUT";
    }
    return $dir;
}
sub getip{ # fetch source / dest ip / net
    my($xtype,$xid,$type,$dbh)=@_;
    my $ip;
    if ($type=="0") { #Type Source
        $ip = "-s ";
    }
    elsif ($type=="1") { #Type destination
        $ip = "-d ";    
    }
    if ($xtype=="*") { # Any ip
        $ip = $ip."any/0";
    }
    elsif ($xtype=="1") { # host entry
        my $sth1 =$dbh->prepare ("Select hostip from no_hosts where id=".$xid);
        $sth1->execute;
        $ip =  $ip.$sth1->fetchrow_array."/32";
    }
    elsif ($xtype=="2") { # network entry
        my $sth1 =$dbh->prepare ("Select networkip,networkmask from no_networks where id=".$xid);
        $sth1->execute;
        my ($networkip,$networkmask)=$sth1->fetchrow_array;
        $ip=$ip.$networkip."/".$networkmask;
    }
    return $ip;
}
sub getinterface{ # get interfaces
    my($direction,$siface,$diface,$dbh)=@_;
    my $interface;
    if($direction==0){ # if direction == INPUT than just query -i interface
        $interface="-i ";
        $iface=$siface;
        my $sth1=$dbh->prepare ("SELECT name FROM io_interfaces WHERE id='".$iface."'");
        $sth1->execute;
        $interface=$interface.$sth1->fetchrow_array;
    }
    elsif($direction==1){ # FORWARD
        if($siface=="*") { # No input iface
            $iface=$diface;
            my $sth1=$dbh->prepare ("SELECT name FROM io_interfaces WHERE id='".$iface."'");
            $sth1->execute;
            $interface="-o ".$sth1->fetchrow_array;
        }
        elsif($diface=="*") { # No output iface
            $iface=$siface;
            my $sth1=$dbh->prepare ("SELECT name FROM io_interfaces WHERE id='".$iface."'");
            $sth1->execute;
            $interface="-i ".$sth1->fetchrow_array;
        }
        else { # otherwise -> both are given
            $iface=$siface;
            my $sth1=$dbh->prepare ("SELECT name FROM io_interfaces WHERE id='".$iface."'");
            $sth1->execute;
            $interface="-i ".$sth1->fetchrow_array;
            $iface=$diface;
            my $sth2=$dbh->prepare ("SELECT name FROM io_interfaces WHERE id='".$iface."'");
            $sth2->execute;
            $interface=$interface." -o ".$sth2->fetchrow_array;
        }
        return $interface;
    }
    elsif($direction==2){ # OUTPUT
        $interface="-o ";
        $iface=$diface;
        my $sth1=$dbh->prepare ("SELECT name FROM io_interfaces WHERE id='".$iface."'");
        $sth1->execute;
        $interface=$interface.$sth1->fetchrow_array;
    } 
    return $interface;
}
sub getservice{ # get ports for service
	my($xatype,$xaid,$type,$dbh)=@_;
    	my $service;
    	if ($xatype==1){ # type Service 
	    	if ($type==0) { #Type Source
		        $service = "--sport ";
	    	}
	    	elsif ($type==1) { #Type destination
		        $service = "--dport ";    
	    	}
	    	my $sth1=$dbh->prepare ("SELECT portstart,portend FROM so_services WHERE id='".$xaid."'");
	    	$sth1->execute;
	    	my ($portstart,$portend)=$sth1->fetchrow_array;
	    	if ($portstart==$portend) { # if service is just related to a single port
			$service=$service.$portstart;
	    	}
	        else { # if service needs more ports than define an port range
	            $service=$service.$portstart.":".$portend;
	        }
    	}
	return $service;
}

sub getprotocols{ # get protocols ()
	my($satype,$said,$datype,$daid,$dbh)=@_;
	my @protocols;
	if ($satype=="*") {
    		if ($datype=="*") {
    			@protocols=("ALL");
    		} elsif ($datype==1) {
    			@protocols=get_protocols_from_service($daid,$dbh);
    		}
	} elsif ($satype==1) {
		if ($datype=="*") {
			@protocols=get_protocols_from_service($said,$dbh);
		} elsif ($datype==1) {
			my ($tcp_source,$udp_source)=get_protocols_from_service($said,$dbh);
			my ($tcp_dest,$udp_dest)=get_protocols_from_service($daid,$dbh);
			if ((length($tcp_source)>0) or (length($tcp_dest)>0)){ # gather required protocols
				@protocols=(@protocols,"tcp");
			}
			if ((length($udp_source)>0) or (length($udp_dest)>0)){
				@protocols=(@protocols,"udp");
			}
		}
	} elsif ($satype==2) {
		@protocols=get_protocols_from_protocol($said,$dbh);
		if ($daid!="*") { # looks like we've got protocol options (icmp)
			$protocols[0]=$protocols[0]." --icmp-type ".get_icmp_type($daid,$dbh);
		}
	}
	return @protocols;
}

sub get_protocols_from_service{ # fetch protocol information from so_services table
	my($xaid,$dbh)=@_;
	my @protocols;
	$sth1=$dbh->prepare("SELECT tcp,udp FROM so_services WHERE id=".$xaid);
	$sth1->execute;
	my ($tcp,$udp)=$sth1->fetchrow_array;
	$sth1->finish;
	if (($tcp==1) and ($udp==1)){ # Convert db Value
		@protocols=("tcp","udp");
	} elsif (($tcp==1) and ($udp==0)){
		@protocols=("tcp");
	} elsif (($tcp==0) and ($udp==1)){
		@protocols=("udp");
	}
	return @protocols;
}

sub get_protocols_from_protocol{ # fetch protocol information from po_protocols table
	my($xaid,$dbh)=@_;
	$sth1=$dbh->prepare("SELECT pr_decimal FROM po_protocols WHERE id=".$xaid);
	$sth1->execute;
	my($pr_decimal)=$sth1->fetchrow_array;
	$sth1->finish;
	return $pr_decimal;
}

sub get_icmp_type{
	my ($daid,$dbh)=@_;
	$sth1=$dbh->prepare("SELECT icmp_type FROM icmp_types WHERE id=".$daid);
	$sth1->execute;
	my ($icmp_type)=$sth1->fetchrow_array;
	$sth1->finish;
	return $icmp_type;
}

sub getpolicies{ # get default policy of chain
    my($chain,$dbh)=@_;
    my $policy;
    $sth1=$dbh->prepare("SELECT chainvalue FROM strategies_filter_default WHERE chainname='".$chain."'");
    $sth1->execute;
    my ($policy_raw)=$sth1->fetchrow_array;
    if ($policy_raw==0) {
        $policy="DROP";
    }
    elsif ($policy_raw==1) {
        $policy="ACCEPT";    
    }
    return $policy;
}

sub state_machinery{
	my ($id,$dbh)=@_;
	my $states;
	my $sth1=$dbh->prepare("SELECT state_new, state_established, state_related, state_invalid FROM ".$db_table_filter." WHERE id=".$id);
	$sth1->execute;
	my ($state_new, $state_established, $state_related, $state_invalid)=$sth1->fetchrow_array;
	my $sum=($state_new + $state_established + $state_related + $state_invalid);
	if ($sum==0){ # if no state is set
		return;
	}
	# else
	$states="-m state --state ";
	if ($state_new==1){
		$states=$states."NEW";
		if ($sum!=1){
			$states=$states.","; 
		}
		$sum--;
	}
	if ($state_established==1){
		$states=$states."ESTABLISHED";
		if ($sum!=1){
			$states=$states.","; 
		}
		$sum--;
	}
	if ($state_related==1){
		$states=$states."RELATED";
		if ($sum!=1){
			$states=$states.","; 
		}
		$sum--;
	}
	if ($state_invalid==1){
		$states=$states."INVALID";
	}
	return $states;
}

sub launch_script{
        system("/bin/bash ".$path_output);
}

#Load Kernel Modules

# connect to database
my $dbh = DBI->connect ("dbi:$datenbank:host=$mysql_host;database=$mysql_db",$mysql_user,$mysql_passwd);
my $sth=$dbh->prepare ("Select * from ".$db_table_filter);
$sth->execute;

# call write function
write_filter($path_output,$dbh,$db_table_filter,$path_filter,$path_iptables);
