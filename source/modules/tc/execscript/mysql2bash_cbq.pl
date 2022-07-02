#!/usr/bin/perl
#
# vis|wall backend script QoS CBQ
# itsoft Software GmbH
# 02.06.2003
# Version 1.06 - 06.10.2003
#

my $mysql_db = "viswall";
my $mysql_host ="localhost";
my $mysql_user = "fillme";
my $mysql_passwd = "fillme";
my $datenbank="mysql";
my $db_table_cbq="strategies_cbq";
my $db_table_cbq_rules="cbq_rules";
my $db_table_cbq_layer="cbq_layers";
my $db_table_interfaces="io_interfaces";
my $db_table_services="so_services";
my $db_table_protocols="po_protocols";
my $path_tc="/sbin/tc";
my $path_output="/viswall/configscripts/tc_cbq.sh";
my $path_iptables="/usr/sbin/iptables";
my $str_subclass=""; # Global Variable used for recursion

use DBI;
use Net::Netmask;

sub write_qdiscs{ # Write qdiscs for interfaces
	my ($dbh)=@_;
	my $qdiscs;
	$sth_iid=$dbh->prepare("SELECT cid,interface,bandwidth FROM ".$db_table_cbq." WHERE parent=0 AND status=1");
	$sth_iid->execute;
	while(my($cid,$iid,$bandwidth)=$sth_iid->fetchrow_array()) {
		my $interface=get_int_real_name($dbh,$iid); # Get real name of interface
		$qdiscs=$qdiscs.$path_tc." qdisc add dev ".$interface." root handle 1:0 cbq bandwidth ".lc($bandwidth)." avpkt 1000 cell 8\n";
	}
	$sth_iid->finish; # Close sth
	return $qdiscs;
}

sub write_mainclass{ # Write CBQ RootClass (per record)
	my ($dbh,$cid)=@_;
	my $mainclass;
	my $sth_mainclass=$dbh->prepare("SELECT cid,bandwidth,rate,weight,priority,interface,bounded,isolated FROM ".$db_table_cbq." WHERE cid=".$cid);
	$sth_mainclass->execute;
	my ($cid,$bandwidth,$rate,$weight,$prio,$iid,$bounded,$isolated)=$sth_mainclass->fetchrow_array();
	my $interface=get_int_real_name($dbh,$iid); # Get real name of interface
	$mainclass=$path_tc." class add dev ".$interface." parent 1:0 classid 1:".$cid." cbq bandwidth ".lc($bandwidth)." rate ".lc($rate)." weight ".lc($weight)." prio ".$prio." allot 1514 cell 8 ".chk_bounded($bounded)." ".chk_isolated($isolated)."\n";
	$sth_mainclass->finish;
	return $mainclass;
}

sub write_subclass{ # Write CBQ Subclasses (recursive)
	my($dbh,$cid)=@_;
	my $int_subcls=0;
	my $sth_subclass=$dbh->prepare("SELECT cid,bandwidth,rate,weight,priority,interface,bounded,isolated FROM ".$db_table_cbq." WHERE parent=".$cid);
	$sth_subclass->execute;
	$int_subcls=$sth_subclass->rows;
	if ($int_subcls==0) { # Check if there are subclasses
		return;
	} else {
		while (my($subcid,$bandwidth,$rate,$weight,$priority,$interface,$bounded,$isolated)=$sth_subclass->fetchrow_array()){
			# Write subclass
			$str_subclass=$str_subclass.$path_tc." class add dev ".get_int_real_name($dbh,$interface)." parent 1:".$cid." classid 1:".$subcid." cbq bandwidth ".lc($bandwidth)." rate ".lc($rate)." weight ".lc($weight)." prio ".$priority." allot 1514 cell 8 maxburst 20 avpkt 1000 ".chk_bounded($bounded)." ".chk_isolated($isolated)."\n";
			# query recursive for subclasses
			write_subclass($dbh,$subcid);
		}
	}
	$sth_subclass->finish; # Close sth
	return $str_subclass;
}

sub write_filter_rules{ # Write iptable rule to track the traffic. (per id)
	my($dbh,$cid)=@_;
	my $filter_rules;
	my $sth_layer=$dbh->prepare("SELECT rid FROM ".$db_table_cbq_layer." WHERE cid=".$cid);
	$sth_layer->execute;
	if($sth_layer->rows==0){
		return; # Return if there are no records
	}
	# select matching rules
	# query interface and parent
	my $sth_cbq_data=$dbh->prepare("SELECT interface,parent,priority FROM ".$db_table_cbq." WHERE cid=".$cid);
	$sth_cbq_data->execute;
	my($int_id,$parent,$prio)=$sth_cbq_data->fetchrow_array();
	my $interface=get_int_real_name($dbh,$int_id);
	$sth_cbq_data->finish();
	while(my($rid)=$sth_layer->fetchrow_array()) {
		my $sth_rules=$dbh->prepare("SELECT * FROM ".$db_table_cbq_rules." WHERE id=".$rid);
		$sth_rules->execute;
		my($rid,$stype,$sid,$satype,$said,$dtype,$did,$datype,$daid)=$sth_rules->fetchrow_array();
		my $source = getip($stype, $sid,0,$dbh);
        	my $destination = getip($dtype, $did,1,$dbh);
        	my $sservice=getservice($satype,$said,0,$dbh);
        	my $dservice=getservice($datype,$daid,1,$dbh);
        	my @protocols=getprotocols($satype,$said,$datype,$daid,$dbh);
        	my $i=0;
        	# iptables part
        	if(@protocols>1){ # If a service is based upon several protocols
        		while($i<@protocols){
        			$filter_rules=$filter_rules.$path_iptables." -t mangle -A PREROUTING -i ".$interface." -p ".@protocols[$i]." ".$source." ".$sservice." ".$destination." ".$dservice." -j MARK --set-mark ".$cid."\n";
        			$i++
        		}
        	} else {
        		$filter_rules=$filter_rules.$path_iptables." -t mangle -A PREROUTING -i ".$interface." -p ".@protocols[0]." ".$source." ".$sservice." ".$destination." ".$dservice." -j MARK --set-mark ".$cid."\n";
        	}
        }
        # tc part
        $filter_rules=$filter_rules.$path_tc." filter add dev ".$interface." protocol ip parent 1:0 prio ".$prio." handle ".$cid." fw flowid 1:".$cid."\n";
        return $filter_rules;
}

# header
sub headwrite_cbq{
	my $first="";
	$first=$first."###########################################\n";
	$first=$first."# Created by Viswall                      #\n";
	$first=$first."# itsoft Software GmbH                    #\n";
	$first=$first."# Traffic Control Script (CBQ)            #\n";
	$first=$first."# TIMESTAMP: ".localtime()."     #\n";
	$first=$first."###########################################\n";
	return $first;
}

# check if class is bounded or not
sub chk_bounded{
	my($input)=@_;
	if ($input==1) {
		return "bounded";
	} else {
		return "borrow";
	}
}

# check if class is isolated or not
sub chk_isolated{
	my($input)=@_;
	if ($input==1) {
		return "isolated";
	} else {
		return "sharing";
	}
}

sub flush_cbq{
	$flush=$flush.$path_tc." qdisc del dev eth0 root\n";
	$flush=$flush.$path_tc." qdisc del dev eth1 root\n";
	$flush=$flush.$path_tc." qdisc del dev eth2 root\n";
	$flush=$flush.$path_iptables." -t mangle -F\n";
	return $flush
}

# convert gbit to mbit
sub gbit2mbit{
	my($value)=@_;
	if(substr(lc($value),-4) ne "gbit"){
		return $value;
	}
	$gbitval=substr(lc($value), 0, index($value, "g"))."\n";
	$mbitval=$gbitval * 1000;
	return $mbitval."mbit";
}

sub get_int_real_name{ # Takes interface_id and returns interface's real name
	my($dbh,$interface_id)=@_;
	my $sth_interface=$dbh->prepare("SELECT name FROM ".$db_table_interfaces." WHERE id=".$interface_id); # Fetch interface's real name
	$sth_interface->execute;
	my($interface_real)=$sth_interface->fetchrow_array();
	$sth_interface->finish; # Close sth and free resources
	return $interface_real;
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
	$sth1=$dbh->prepare("SELECT pr_decimal FROM ".$db_table_protocols." WHERE id=".$xaid);
	$sth1->execute;
	my($pr_decimal)=$sth1->fetchrow_array;
	$sth1->finish;
	return $pr_decimal;
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

# Control Funtion
sub write_cbq{
	my $dbh = DBI->connect ("dbi:$datenbank:host=$mysql_host;database=$mysql_db",$mysql_user,$mysql_passwd);
	my $sth=$dbh->prepare ("SELECT cid FROM ".$db_table_cbq." WHERE parent=0 AND status=1"); # query all mainclass id's
	$sth->execute;
	# get data
	my $first=headwrite_cbq(); # get description
	my $flush=flush_cbq(); # get flush rules
	my $qdiscs=write_qdiscs($dbh); # get qdiscs
	# init variables
	my $mainclasses;
	my $subclasses;
	my $filter_rules;
	while(my($cid)=$sth->fetchrow_array()){
		$mainclasses=$mainclasses.write_mainclass($dbh,$cid); # get main classes
		$subclasses=$subclasses.write_subclass($dbh,$cid); # get sub classes
		$str_subclass=""; # Clear String subclass to prevent overflow
	}
	# get filter rules
	my $sth_all=$dbh->prepare("SELECT cid FROM ".$db_table_cbq." WHERE status=1");
	$sth_all->execute;
	while(my($cid_all)=$sth_all->fetchrow_array()){
		$filter_rules=$filter_rules.write_filter_rules($dbh,$cid_all); # get filter rules
	}
	$sth_all->finish();
	# open output file
	open (OUTPUT,">$path_output");
	print OUTPUT "#!/bin/bash\n"; # Print file header
	print OUTPUT $first."\n"; # Print description
	print OUTPUT "\n"; # blank line
	print OUTPUT $flush."\n"; # Print flush rules
	print OUTPUT "\n"; # blank line
	print OUTPUT $qdiscs; # Print qdiscs
	print OUTPUT "\n"; # blank line
	print OUTPUT $mainclasses; # Print Mainclasses
	print OUTPUT "\n"; # blank line
	print OUTPUT $subclasses; # Print Subclasses
	print OUTPUT "\n"; # blank line
	print OUTPUT $filter_rules; # Print Filter Rules
	close (OUTPUT); # Close Output file
	$sth->finish();
	$dbh->disconnect();
}

# do the job
write_cbq();
