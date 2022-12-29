#!/usr/bin/perl
#
# vis|wall backend script nat and pat
# 24.03.2003
# Version 1.2 - 29.12.2022
#

my $configfile="/viswall/config";
my $datenbank="mysql";
my $db_table_nat="strategies_nat";
my $path_output="/viswall/configscripts/nat.sh"; 
my $path_iptables="/usr/sbin/iptables -t nat";
my $first="";

use DBI;
use Config::File;

my $config_hash = Config::File::read_config_file($configfile);

my $mysql_db = $config_hash->{DB_NAME_VISWALL};
my $mysql_host = $config_hash->{DB_HOST};
my $mysql_user = $config_hash->{DB_USER};
my $mysql_passwd = $config_hash->{DB_PASS};

#Description
sub headwrite_nat{
$first=$first."#!/bin/bash\n";
$first=$first."###########################################\n";
$first=$first."# Created by Viswall                      #\n";
$first=$first."# NAT&PAT CONFIGURE SCRIPT  	          #\n";
$first=$first."# TIMESTAMP: ".localtime()."     #\n";
$first=$first."###########################################\n";
return $first;
}


sub write_nat{ # main part of the work
    my ($path_output,$dbh,$db_table_nat,$path_nat,$path_iptables) = @_;
    $head = headwrite_nat();
    my $sth=$dbh->prepare ("Select * from ".$db_table_nat." WHERE status=1 ORDER BY priority"); # Query and solve issue with Priorities
    $sth->execute;
    open (OUTPUT1,">$path_output"); 
    print OUTPUT1 $head."\n";
    print OUTPUT1 "$path_iptables -F\n\n";
        
    while (my ($id,$stype,$sid,$satype,$said,$ntype,$dtype,$did,$datype,$daid,$totype,$toid,$topid,$iiface,$oiface) = $sth->fetchrow_array){
        $nattype = getntype($ntype);
        $chain = getchain($ntype);
        $source = getip($stype, $sid,0,$dbh);
        $destination = getip($dtype, $did,1,$dbh);
        @protocols = getprotocols($satype,$said,$datype,$daid,$dbh);
        $states = state_machinery($id,$dbh);
        if(($iiface!="*") || ($oiface!="*")){
            $iface=getinterface($ntype,$iiface,$oiface,$dbh);
        }
        else {
            $iface="";
        }
        if(($totype!="*") || ($topid!="*")){
            $tovalue=gettoval($ntype,$totype,$toid,$topid,$dbh);
        }
        else {
            $tovalue="";
        }
        $protocols="-p ALL";
        if ($said!="*") { #if sourceport available
            $sservice=getservice($said,0,$dbh);
        }
        else {
            $sservice="";
        }
        if ($daid!="*") {
            $dservice=getservice($daid,1,$dbh);
        }
        else {
            $dservice="";
        }
        
        if (@protocols>1) { # if there is more than one protocol defined
            my $i=0;
            while ($i<@protocols) {
                print OUTPUT1 $path_iptables." -A ".$chain." -p ".@protocols[$i]." ".$iface." ".$source." ".$sservice." ".$destination." ".$dservice." ".$states." -j ".$nattype." ".$tovalue."\n";
                $i++;
            }
        }
        else { # just one protocol
            print OUTPUT1 $path_iptables." -A ".$chain." -p ".@protocols[0]." ".$iface." ".$source." ".$sservice." ".$destination." ".$dservice." ".$states." -j ".$nattype." ".$tovalue."\n";
        }
    }
    $type="";
    $iface="";
    $tovalue="";
    $sservice="";
    $dservice="";
    close(OUTPUT1);
	launch_script();
}

sub getntype{ # Get NAT Type
    my($type)=@_;
    my $ntype;
    if($type==0){
        $ntype="SNAT";
    }
    elsif($type==1){
        $ntype="DNAT";
    }
    elsif($type==2){
        $ntype="MASQUERADE";
    }
    elsif($type==3){
        $ntype="REDIRECT";
    }
    elsif($type==4){
	$ntype="ACCEPT";
    }
    elsif($type==5){
	$ntype="ACCEPT";
    }
    return $ntype;
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
    if (($xtype=="*") || ($xid=="*")) { # Any ip
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
    my($ntype,$iiface,$oiface,$dbh)=@_;
    my $interface;
    if($ntype==0){ # if ntype == SNAT than just query -o interface
        $iface=$oiface;
        my $sth1=$dbh->prepare ("SELECT name FROM io_interfaces WHERE id='".$iface."'");
        $sth1->execute;
        $interface="-o ".$sth1->fetchrow_array;
    }
    elsif($ntype==1){ # DNAT
        $iface=$iiface;
	my $sth1=$dbh->prepare ("SELECT name FROM io_interfaces WHERE id='".$iface."'");
        $sth1->execute;
        $interface="-i ".$sth1->fetchrow_array;
    }
    elsif($ntype==2){ # MASQ
        $iface=$oiface;
	my $sth1=$dbh->prepare ("SELECT name FROM io_interfaces WHERE id='".$iface."'");
        $sth1->execute;
        $interface="-o ".$sth1->fetchrow_array;
    }
    elsif($ntype==3){ # REDIRECT
        $iface=$iiface;
	my $sth1=$dbh->prepare ("SELECT name FROM io_interfaces WHERE id='".$iface."'");
        $sth1->execute;
        $interface="-i ".$sth1->fetchrow_array;
    }
    elsif($ntype==4){ # ACCEPT PRETROUTING
        $iface=$iiface;
	my $sth1=$dbh->prepare ("SELECT name FROM io_interfaces WHERE id='".$iface."'");
        $sth1->execute;
        $interface="-i ".$sth1->fetchrow_array;
    }
    elsif($ntype==5){ # ACCEPT POSTROUTING
        $iface=$iiface;
	my $sth1=$dbh->prepare ("SELECT name FROM io_interfaces WHERE id='".$iface."'");
        $sth1->execute;
        $interface="-i ".$sth1->fetchrow_array;
    }
    return $interface;
}
sub getservice{ # get ports for service
    my($xaid,$type,$dbh)=@_;
    my $service;
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
    return $service;
}

sub gettoval{ # get target value (host/port)
    my($ntype,$totype,$toid,$topid,$dbh)=@_;
    my $tovalue;
    if ($ntype==0) {
        $tovalue="--to-source ";
    }
    elsif ($ntype==1) {
        $tovalue="--to-destination ";
    }
    elsif ($ntype==2) { 
        if ($topid!="*") {
            $tovalue="--to-ports ";
        }
    }
    elsif ($ntype==3) { 
        if ($topid!="*") {
            $tovalue="--to-ports ";
        }
    }
    if (($ntype==0) ||($ntype==1)) { #only when types are DNAT or SNAT
        if ($totype==1){ #target is host
            $sth1=$dbh->prepare("SELECT hostip FROM no_hosts WHERE id='".$toid."'");
            $sth1->execute;
            my($hostip)=$sth1->fetchrow_array;
            $tovalue=$tovalue.$hostip;
        }
    }
    if ($topid!="*"){ #just if we have Ports
        $tovalue=$tovalue.getports($ntype,$dbh,$topid);
    }
    return $tovalue;
}
sub getports{ #get ports for gettoval
    my($type,$dbh,$topid)=@_;
    my $retval;    
    # now lets get the ports
    $sth=$dbh->prepare("SELECT portstart,portend FROM so_services where id='".$topid."'");
    $sth->execute;
    my ($portstart,$portend)= $sth->fetchrow_array;    
    my $rport=$portstart;
    if ($portend!=$portstart) { # if we have a portrange
        $rport."-".$portend;
    }
    if($type<2) { #How to handle the stuff if type is one of= SNAT, DNAT
        $retval=":".$rport;
    }
    else
    {
        $retval=$rport;
    }
    return $retval;
}

sub getchain{ # get chainname
    my($ntype)=@_;
    my $chain;
    if ($ntype==0){ #case SNAT
        $chain="POSTROUTING";
    }
    elsif ($ntype==1) { #case DNAT
        $chain="PREROUTING";
    }
    elsif ($ntype==2) { #case MASQ
        $chain="POSTROUTING";
    }
    elsif ($ntype==3) { #case REDIRECT
        $chain="PREROUTING";
    }
    elsif ($ntype==4) { #case ACCEPT PRETROUTING
	$chain="PREROUTING";
    }
    elsif ($ntype==5) { #case ACCEPT POSTROUTING
	$chain="POSTROUTING";
    }
    return $chain;
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

sub state_machinery{
	my ($id,$dbh)=@_;
	my $states;
	my $sth1=$dbh->prepare("SELECT state_new, state_established, state_related, state_invalid FROM ".$db_table_nat." WHERE id=".$id);
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
	system("/usr/sbin/iptables -t nat -I OUTPUT -d 10.1.1.1 -m tcp -p tcp --dport 25 -j DNAT --to 10.1.1.1:2525");
}

#Load Kernel Modules

# connect to database
my $dbh = DBI->connect ("dbi:$datenbank:host=$mysql_host;database=$mysql_db",$mysql_user,$mysql_passwd);
my $sth=$dbh->prepare ("Select * from ".$db_table_nat);
$sth->execute;

# call write function
write_nat($path_output,$dbh,$db_table_nat,$path_nat,$path_iptables);
