#!/usr/bin/perl
#
# vis|wall backend script PPTPD
# Version 1.4 - 22.12.2022
# Standalone Version
#

my $configfile = "/viswall/config";
my $datenbank="mysql";
my $db_table_pptpd="pptp_options";
my $db_table_user = "pptp_layers";
my $path_pptpd_conf="/etc/pptpd.conf";
my $path_options="/viswall/configscripts/options.pptp";
my $path_chap ="/etc/ppp/chap-secrets";
my $path_pptpd ="/usr/local/sbin/pptpd";
my $path_pppd ="/usr/sbin/pppd";
my $path_pptpctrl = "/usr/local/sbin/pptpctrl";
my $first="";

use DBI;
use Config::File;

my $config_hash = Config::File::read_config_file($configfile);

my $mysql_db = $config_hash->{DB_NAME_VISWALL};
my $mysql_host = $config_hash->{DB_HOST};
my $mysql_user = $config_hash->{DB_USER};
my $mysql_passwd = $config_hash->{DB_PASS};

#Beschreibung
sub headwrite_pptpd{
$first="";
$first=$first."###########################################\n";
$first=$first."# Created by vis|wall                     #\n";
$first=$first."# PPTP CONTROL SCRIPT  	        	  #\n";
$first=$first."# TIMESTAMP: ".localtime()."     #\n";
$first=$first."###########################################\n";
return $first;
$first="";
}

sub headwrite_options{
$first="";
$first=$first."###########################################\n";
$first=$first."# Created by vis|wall                     #\n";
$first=$first."# PPTP OPTIONS SCRIPT      		  #\n";
$first=$first."# TIMESTAMP: ".localtime()."     #\n";
$first=$first."###########################################\n";
return $first;
$first="";
}

sub write_pptpd{
my ($path_output,$dbh,$db_table_pptpd,$path_options) = @_;
$head = headwrite_options();

my $sth=$dbh->prepare ("Select * from ".$db_table_pptpd);
$sth->execute;
while (my ($id,$name,$mru,$mtu,$auth,$require_chap,$proxyarp,$chap,$chapms,$chapms2,$mppe40,$mppe128,$mppe_stateless,$ms_dns1,$ms_dns2,$status,$localip,$remoteip,$listenip) = $sth->fetchrow_array){
	
	open (OUTPUT,">$path_options");
	print OUTPUT $head."\n";
	print OUTPUT "name \"".$name."\"\n";
	print OUTPUT "lock \n";
	print OUTPUT "mru ".$mru."\n";
	print OUTPUT "mtu ".$mtu."\n";
	if($auth == 1){
		print OUTPUT "auth \n";
	}
        if($chap!=1){
                print OUTPUT "refuse-chap\n";
        }
        if($chapms!=1){
                print OUTPUT "refuse-mschap\n";
        }
        if($chapms2!=1){
                print OUTPUT "refuse-mschap-v2\n";
        } else {
		print OUTPUT "require-mschap-v2\n";
	}
        if($require_chap == 1){
                print OUTPUT "refuse-pap\nrefuse-eap\n";
        }
	if($proxyarp == 1){
		print OUTPUT "proxyarp\n";
	}
	# Activate mppc:
	#print OUTPUT "mppc\n";
	if(($mppe40==1)||($mppe128==1)){
		print OUTPUT "require-mppe-128\n";
		if($mppe_stateless==1){
			#print OUTPUT "stateless";
			#if(($mpp40==1)&&($mppe128==0)){
		        #        print OUTPUT ",no56,no128\n";
		        #} elsif(($mpp40==0)&&($mppe128==1)){
		        #        print OUTPUT ",no40,no56\n";
		        #} else {
			#	print OUTPUT "\n";
			#}
		} else {
			#print OUTPUT "stateful";
                        #if(($mpp40==1)&&($mppe128==0)){
                        #        print OUTPUT ",no56,no128\n";
                        #} elsif(($mpp40==0)&&($mppe128==1)){
                        #        print OUTPUT ",no40,no56\n";
                        #} else {
                        #        print OUTPUT "\n";
                        #}
		}
	} else {
		#print OUTPUT "nomppe\n";
	}
	if(length($ms_dns1)>=2){
		print OUTPUT "ms-dns ".$ms_dns1."\n";
	}
	if(length($ms_dns2)>=2){
		print OUTPUT "ms-dns ".$ms_dns2."\n";
	}

	# now write the control file: /etc/pptpd.conf
	
	write_pptpd_conf($listenip,$localip,$remoteip);
	#my $serverargs = "1 1 ".$path_options." 1 115200 1 ".$localip." 1 ".$remoteip." 0";
	# control file finished
}
close (OUTPUT);
restart_pptpd();
}

sub write_chap{
my ($path_output,$dbh) = @_;
$head = headwrite_pptpd();
my $sth=$dbh->prepare ("Select * from ".$db_table_user." WHERE status=1");
$sth->execute;
open (OUTPUT1,">$path_output");
#print OUTPUT1 $head;

while (my ($id,$pid,$servername,$ipadress,$status) = $sth->fetchrow_array){
	$username=getusername($pid,$dbh);
	# for further use: Servername
	#if ($servername!="*") {
	#	my $sth2=$dbh->prepare("SELECT name FROM ".$db_table_pptpd." WHERE id=".$servername);
	#	$sth2->execute;
	#	$servername=$sth2->fetchrow_array;
	#}
	$servername="*";
	$passwd=getpasswd($pid,$dbh);
	$ip_adress=getipadress($ipadress,$dbh);
	if ($status == 1){
		print OUTPUT1 $username." ".$servername." \"".$passwd."\" ".$ip_adress."\n";
	}
}

close(OUTPUT1);
}

sub write_pptpd_conf{
	my($listenip,$localip,$remoteip)=@_;
	my $output;
	$output=$output."#debug\n";
	$output=$output."lock\n";
	$output=$output."option ".$path_options."\n";
	$output=$output."listen ".$listenip."\n";
	$output=$output."localip ".$localip."\n";
	$output=$output."remoteip ".$remoteip."\n";
	open (OUTPUT2, ">$path_pptpd_conf");
	$header=headwrite_pptpd();
	print OUTPUT2 $header."\n";
	print OUTPUT2 $output;
	close (OUTPUT2);
	return;
}
sub restart_pptpd{
	# Kill all active connections
#	system("killall $path_pppd 2> /dev/null");
	# Kill pptpd Server
	system("killall $path_pptpd 2> /dev/null");
	# Start pptpd Server
	system($path_pptpd);
	return;
}

sub getusername{
	my($pid,$dbh)=@_;
	my $sth1=$dbh->prepare ("Select username from users where id=".$pid);
	$sth1->execute;
	my ($username)=$sth1->fetchrow_array;
	return $username;
}

sub getpasswd{
	my($pid,$dbh)=@_;
	my $sth1=$dbh->prepare ("Select password from users where id=".$pid);
	$sth1->execute;
	my $passwd=$sth1->fetchrow_array;
	return $passwd;
}

sub getipadress{
	my($ip,$dbh)=@_;
	my $sth1=$dbh->prepare ("Select hostip from no_hosts where id='".$ip."'");
	$sth1->execute;
	my $ipadress=$sth1->fetchrow_array;
	if(length($ipadress==0)){
		$ipadress="*";
	}
	return $ipadress;
}
#Load Kernel Modules

#Verbinden mit der mysql Datenbank
my $dbh = DBI->connect ("dbi:$datenbank:host=$mysql_host;database=$mysql_db",$mysql_user,$mysql_passwd);
my $sth=$dbh->prepare ("Select * from ".$db_table_pptpd);
$sth->execute;
write_pptpd($path_output,$dbh,$db_table_pptpd,$path_options);
write_chap($path_chap,$dbh);
