#!/usr/bin/perl
#
# Exim extension
# itsoft Software GmbH 
# 25.08.2004
# Version 1.1 - 12.09.2004
# H. Rohrweck
#

my $mysql_db = "exim";
my $mysql_host ="localhost";
my $mysql_user = "fillme";
my $mysql_passwd = "fillme";
my $datenbank="mysql";
my $SPAMCOUNTMIN=30;
my $observation_path="/var/spool/mail/observation";
my $message_path="/var/spool/mail/scan";
my $message_input_path="/var/spool/mail/input";
my $db_table_watchlist_maillog="maillog_watchlist";
my $db_table_blacklist="Blocklists";
my $db_table_whitelist="Whitelists";
my $db_table_watchlist="Watchlist";
my $db_table_statistics="statistics";
my $db_table_aliases="Aliases";
my $db_table_AdditionalMailDomains="AdditionalMailDomains";
my $db_table_LocalMailDomains="LocalMailDomains";
my $db_table_mailsettings="Mail_Settings";
my $db_table_spamsettings="Spam_Settings";
my $pack_template="V"; # used by the pack() function. "N" for Network style (big endian), "V" for VAX style (little endian)
my $first="";

use DBI;
use Socket;
use Time::localtime;
use File::Copy;
#use Net::Netmask;

# CheckBlock blacklists IP addresses if the spamcount of a message exceeds 10 spam points (-> $spamscore>100) and the IP isn't in the Whitelist
sub CheckBlock {
    my ($spamscore, $type, $value, $description) = @_;

    # connect to database
    if ($spamscore>100) {
        my $dbh = DBI->connect ("dbi:$datenbank:host=$mysql_host;database=$mysql_db",$mysql_user,$mysql_passwd);

        my $white=$dbh->prepare ("select * from ".$db_table_whitelist." where Value='".$value."' and active=1");
        $white->execute;

	if ($white->rows<=0) {
	    $tm=localtime;
	    $date=($tm->year+1900)."-".($tm->mon+1)."-".$tm->mday." ".$tm->hour.":".$tm->min.":".$tm->sec;
	    
            my $sth=$dbh->prepare ("select * from ".$db_table_blacklist." where BlockValue='".$value."'");
	    $sth->execute;

            if ($sth->rows>0) {
                while (my ($BLID,$BlockType,$BlockValue,$Timestamp,$Timestamp_added,$Timestamp_last_activation,$spamcount,$active,$description,$delivery_tries,$AMDID,$AID) = $sth->fetchrow_array){
                    my $sth=$dbh->prepare ("update ".$db_table_blacklist." set spamcount=spamcount+1 where BlockValue='".$value."'");
                    $sth->execute;
	            Exim::log_write ($value." Spamcount increased.");

	            if (!$active) {
    		        my $sth=$dbh->prepare ("update ".$db_table_blacklist." set active=1, autolisted=1, Timestamp_last_activation='".$date."' where BlockValue='".$value."'");
    		        $sth->execute;
         	        Exim::log_write ($value." was re-activated because of spam activity.");
	            }
                }
            } else {
                my $sth=$dbh->prepare ("insert into ".$db_table_blacklist." (BlockType, BlockValue, description, Timestamp_added, Timestamp_last_activation, autolisted) values (".$type.",'".$value."','".$description."','".$date."','".$date."',1)");
                $sth->execute;
	        Exim::log_write ($value." was added to the blacklist.");
            }

#            $dbh->disconnect;
        } 
    }

    return 1;
}

# DeliveryCount provides the statistics for the Blocklist (delivery_tries, etc.)
sub DeliveryCount {
    my ($host_address) = @_;

    # connect to database
    my $dbh = DBI->connect ("dbi:$datenbank:host=$mysql_host;database=$mysql_db",$mysql_user,$mysql_passwd);

    my $sth=$dbh->prepare ("select BLID,BlockType,BlockValue,Timestamp,spamcount,active,description,delivery_tries,AMDID,AID from ".$db_table_blacklist." where BlockValue='".$host_address."'");
    $sth->execute;

    if ($sth->rows>0) {
        while (my ($BLID,$BlockType,$BlockValue,$Timestamp,$spamcount,$active,$description,$delivery_tries,$AMDID,$AID) = $sth->fetchrow_array){
            my $sth=$dbh->prepare ("update ".$db_table_blacklist." set delivery_tries=delivery_tries+1 where BlockValue='".$host_address."'");
            $sth->execute;
	    Exim::log_write ($value." delivery count increased.");
        }
    }

    return 1;
}

# UpdateStatistics provides overall mail statistics (except for blacklisted IP's)
sub UpdateStatistics {
    my ($host_address,$spamscore,$message_size) = @_;
    my $count=0;
    # connect to database
    my $dbh = DBI->connect ("dbi:$datenbank:host=$mysql_host;database=$mysql_db",$mysql_user,$mysql_passwd);

    my $sth=$dbh->prepare ("select STATID,IP,spamscore,deliveries_spam,deliveries_ham,traffic,Timestamp,Timestamp_added,active,description from ".$db_table_statistics." where IP='".$host_address."'");
    $sth->execute;

    if ($sth->rows>0) {
        while (my ($STATID,$IP,$spamscore_now,$deliveries_spam,$deliveries_ham,$traffic,$Timestamp,$Timestamp_added,$active,$description) = $sth->fetchrow_array){
            my $query="update ".$db_table_statistics." set ";
	    if ($spamscore>0) {
		$query=$query."spamscore=spamscore+".$spamscore;
		$count++;
	    }
	    
	    if ($message_size>0) {
		if ($count) {$query=$query.","};
		$query=$query."traffic=traffic+".$message_size;
		$count++;
	    }
	    
	    if ($spamscore>$SPAMCOUNTMIN) {
		if ($count) {$query=$query.","};
		$query=$query."deliveries_spam=deliveries_spam+1";
		$count++;
	    } else {
		if ($count) {$query=$query.","};
		$query=$query."deliveries_ham=deliveries_ham+1";
		$count++;
	    }
	    $query=$query." where IP='".$host_address."'";
	    print ($query);
	    my $sth=$dbh->prepare ($query);
            $sth->execute;
        }
    } else {
	my $spam=0;
	my $ham=0;

	if ($spamscore>$SPAMCOUNTMIN) {
	    $spam=1;
	} else {
	    $ham=1;
	}
	
	$tm=localtime;
	$date=($tm->year+1900)."-".($tm->mon+1)."-".$tm->mday." ".$tm->hour.":".$tm->min.":".$tm->sec;
	my $query="insert into ".$db_table_statistics." (IP, spamscore, deliveries_spam, deliveries_ham, traffic, Timestamp_added) values ('".$host_address."',spamscore+".$spamscore.",".$spam.",".$ham.",".$message_size.",'".$date."')";
	
	my $sth=$dbh->prepare ($query);
	$sth->execute;
    }

    return 1;    
}

# checks wether the mail to the recipient should be scanned for virus or not (returns 1 for yes and 0 for no)
sub isvirusprotected {
    my ($recipient_list,$description) = @_;
    my $count=0;
    
    @recipients=split(/,/,$recipient_list);
    # connect to database
    my $dbh = DBI->connect ("dbi:$datenbank:host=$mysql_host;database=$mysql_db",$mysql_user,$mysql_passwd);

    my $query="select antivirus from ".$db_table_aliases." where active=1";
    
    foreach $address (@recipients) {
	if (!$count) {
	    $query=$query." and (";
	} else {
	    $query=$query." or ";
	}
	
	$query=$query." Email='".qq($address)."'";
	
	$count++;
    }

    if ($count) {
	$query=$query.")";
    }
    
    #Exim::log_write ($query);
    
    my $sth=$dbh->prepare ($query);
    $sth->execute;

    if ($sth->rows>0) {
	# Alias Code goes here
        while (my ($antivirus) = $sth->fetchrow_array){
	    if ($antivirus) {
		Exim::log_write ("Virus scan activated for ".$local_part."@".$domain." (".$description.") based on entry in ".$db_table_aliases);
		return 1;
	    }
	}
    } else {
	$query="select antivirus from ".$db_table_AdditionalMailDomains." where active=1";
	$count=0;

	foreach $address (@recipients) {
	    if (!$count) {
		$query=$query." and (";
	    } else {
		$query=$query." or ";
	    }
	    
	    ($local_part,$domain)=split("@",$address);
	    $query=$query." Domain='".$domain."'";
	    
	    $count++;
	}
    
	if ($count) {
	    $query=$query.")";
	}
        
	#Exim::log_write ($query);

	my $sth=$dbh->prepare ($query);
	$sth->execute;

	if ($sth->rows>0) {
	    # AdditionalMailDomain Code goes here
	    while (my ($antivirus) = $sth->fetchrow_array){
		if ($antivirus) {
		    Exim::log_write ("Virus scan activated for ".$local_part."@".$domain." (".$description.") based on entry in ".$db_table_AdditionalMailDomains);
		    return 1;
		}
	    }
	} else {
	    $query="select antivirus from ".$db_table_LocalMailDomains." where active=1";
	    $count=0;

	    foreach $address (@recipients) {
		if (!$count) {
		    $query=$query." and (";
		} else {
		    $query=$query." or ";
		}
		
		($local_part,$domain)=split("@",$address);
		$query=$query." Domain='".$domain."'";
		
		$count++;
	    }
	
	    if ($count) {
		$query=$query.")";
	    }
	    
	    #Exim::log_write ($query);

	    my $sth=$dbh->prepare ($query);
	    $sth->execute;

	    if ($sth->rows>0) {
		# LocalMailDomain Code goes here
		while (my ($antivirus) = $sth->fetchrow_array){
		    if ($antivirus) {
			Exim::log_write ("Virus scan activated for ".$local_part."@".$domain." (".$description.") based on entry in ".$db_table_LocalMailDomains);
			return 1;
		    }
		}
	    } else {
		my $query="select ParamValue from ".$db_table_mailsettings." where active=1 and ParamName='default_antivirus_policy'";
		
	       #Exim::log_write ($query);
		
		my $sth=$dbh->prepare ($query);
		$sth->execute;
	    
		if ($sth->rows>0) {
		    while (my ($ParamValue) = $sth->fetchrow_array){
			if ($ParamValue==1) {
			    Exim::log_write ("Virus scan activated for ".$local_part."@".$domain." (".$description.") based on default policy");
			    return 1;
			}
		    }
		}
	    }
	}
    }

    Exim::log_write ("no virus scan for ".$local_part."@".$domain)." (".$description.")";
    return 0;
}

# checks wether the mail to the recipient should be scanned for spam or not (returns 1 for yes and 0 for no)
sub isspamprotected {
    my ($recipient_list,$description) = @_;
    my $count=0;

    #Exim::log_write ($recipient_list);
    @recipients=split(/,/,$recipient_list);

    # connect to database
    my $dbh = DBI->connect ("dbi:$datenbank:host=$mysql_host;database=$mysql_db",$mysql_user,$mysql_passwd);

    my $query="select antispam from ".$db_table_aliases." where active=1";
    
    foreach $address (@recipients) {
	if (!$count) {
	    $query=$query." and (";
	} else {
	    $query=$query." or ";
	}
	
	$query=$query." Email='".$address."'";
	
	$count++;
    }

    if ($count) {
	$query=$query.")";
    }
    
    #Exim::log_write ($query);
    
    my $sth=$dbh->prepare ($query);
    $sth->execute;

    if ($sth->rows>0) {
	# Alias Code goes here
        while (my ($antispam) = $sth->fetchrow_array){
	    if ($antispam) {
		Exim::log_write ("Spam scan activated for ".$local_part."@".$domain." (".$description.") based on entry in ".$db_table_aliases);
		return 1;
	    }
	}
    } else {
	$query="select antispam from ".$db_table_AdditionalMailDomains." where active=1";
	$count=0;
	
	foreach $address (@recipients) {
	    if (!$count) {
		$query=$query." and (";
	    } else {
		$query=$query." or ";
	    }
	    
	    ($local_part,$domain)=split("@",$address);
	    $query=$query." Domain='".$domain."'";
	    
	    $count++;
	}
    
	if ($count) {
	    $query=$query.")";
	}
        
	#Exim::log_write ($query);

	my $sth=$dbh->prepare ($query);
	$sth->execute;

	if ($sth->rows>0) {
	    # AdditionalMailDomain Code goes here
	    while (my ($antispam) = $sth->fetchrow_array){
		if ($antispam) {
		    Exim::log_write ("Spam scan activated for ".$local_part."@".$domain." (".$description.") based on entry in ".$db_table_AdditionalMailDomains);
		    return 1;
		}
	    }
	} else {
	    $query="select antispam from ".$db_table_LocalMailDomains." where active=1";
	    $count=0;

	    foreach $address (@recipients) {
		if (!$count) {
		    $query=$query." and (";
		} else {
		    $query=$query." or ";
		}
		
		($local_part,$domain)=split("@",$address);
		$query=$query." Domain='".$domain."'";
		
		$count++;
	    }
	
	    if ($count) {
		$query=$query.")";
	    }
	    
	    #Exim::log_write ($query);

	    my $sth=$dbh->prepare ($query);
	    $sth->execute;

	    if ($sth->rows>0) {
		# LocalMailDomain Code goes here
		while (my ($antispam) = $sth->fetchrow_array){
		    if ($antispam) {
			Exim::log_write ("Spam scan activated for ".$local_part."@".$domain." (".$description.") based on entry in ".$db_table_LocalMailDomains);
			return 1;
		    }
		}
	    } else {
		my $query="select ParamValue from ".$db_table_mailsettings." where active=1 and ParamName='default_antispam_policy'";
		
		#Exim::log_write ($query);
		
		my $sth=$dbh->prepare ($query);
		$sth->execute;
	    
		if ($sth->rows>0) {
		    while (my ($ParamValue) = $sth->fetchrow_array){
			if ($ParamValue==1) {
			    Exim::log_write ("Spam scan activated for ".$local_part."@".$domain." (".$description.") based on default policy");
			    return 1;
			}
		    }
		}
	    }
	}
    }

    Exim::log_write ("no spam scan for ".$local_part."@".$domain)."(".$description.")";
    return 0;
}

sub getscansetting {
    my ($recipient_list,$parameter,$description) = @_;
    my $count=0;
    
    @recipients=split(/,/,$recipient_list);
    # connect to database
    my $dbh = DBI->connect ("dbi:$datenbank:host=$mysql_host;database=$mysql_db",$mysql_user,$mysql_passwd);

    my $query="select AID,antivirus,antispam from ".$db_table_aliases." where active=1";
    
    foreach $address (@recipients) {
	if (!$count) {
	    $query=$query." and (";
	} else {
	    $query=$query." or ";
	}
	
	$query=$query." Email='".$address."'";
	
	$count++;
    }

    if ($count) {
	$query=$query.")";
    }
    
    #Exim::log_write ($query);
    
    my $sth=$dbh->prepare ($query);
    $sth->execute;

    if ($sth->rows>0) {
	# Alias Code goes here
        while (my ($AID, $antivirus, $antispam) = $sth->fetchrow_array){
	    my $query="select value, additional from ".$db_table_spamsettings." where parameter='".$parameter."' and AID=".$AID;
	    my $settings=$dbh->prepare ($query);
	    $settings->execute;

	    if ($settings->rows>0) {
		while (my ($value, $additional) = $settings->fetchrow_array){
		    Exim::log_write ("parameter ".$parameter." found for ".$local_part."@".$domain." (".$description.") based on entry in ".$db_table_aliases.", returned value is ".$value.", additional is ".$additional);
		    
		    if (($value==1) && ($additional ne "")) {
			return $additional;
		    } else {
			return $value;
		    }
		}
	    } 
	}
    }
	
    $query="select AMDID, antivirus, antispam from ".$db_table_AdditionalMailDomains." where active=1";
    $count=0;

    foreach $address (@recipients) {
	if (!$count) {
	    $query=$query." and (";
	} else {
	    $query=$query." or ";
	}
	
	($local_part,$domain)=split("@",$address);
	$query=$query." Domain='".$domain."'";
	
	$count++;
    }

    if ($count) {
	$query=$query.")";
    }
    
    #Exim::log_write ($query);

    my $sth=$dbh->prepare ($query);
    $sth->execute;

    if ($sth->rows>0) {
	while (my ($AMDID, $antivirus, $antispam) = $sth->fetchrow_array){
	    my $query="select value, additional from ".$db_table_spamsettings." where parameter='".$parameter."' and AMDID=".$AMDID;
	    my $settings=$dbh->prepare ($query);
	    $settings->execute;

	    if ($settings->rows>0) {
		while (my ($value, $additional) = $settings->fetchrow_array){
		    Exim::log_write ("parameter ".$parameter." found for ".$local_part."@".$domain." (".$description.") based on entry in ".$db_table_AdditionalMailDomains.", returned value is ".$value.", additional is ".$additional);
		    
		    if (($value==1) && ($additional ne "")) {
			return $additional;
		    } else {
			return $value;
		    }
		}
	    } 
	}
    }
    
    my $query="select value, additional from ".$db_table_spamsettings." where parameter='".$parameter."' and AMDID=0 and AID=0";
    my $settings=$dbh->prepare ($query);
    $settings->execute;

    if ($settings->rows>0) {
	while (my ($value, $additional) = $settings->fetchrow_array){
	    Exim::log_write ("parameter ".$parameter." found for ".$local_part."@".$domain." (".$description.") based on default settings, returned value is ".$value.", additional is ".$additional);
	    
	    if (($value==1) && ($additional ne "")) {
		return $additional;
	    } else {
		return $value;
	    }
	}
    }

    Exim::log_write ("no spam settings found for ".$local_part."@".$domain)." (".$description.")";
    return 0;
}

sub isunderobservation {
    my ($host_address,$message_id,$message_size,$recipient_list) = @_;
    my $count=0;

    #Exim::log_write ($recipient_list);
    @recipients=split(/,/,$recipient_list);

    # connect to database
    my $dbh = DBI->connect ("dbi:$datenbank:host=$mysql_host;database=$mysql_db",$mysql_user,$mysql_passwd);

    my $query="select WatchValue from ".$db_table_watchlist." where active=1";
    
    foreach $address (@recipients) {
	if (!$count) {
	    $query=$query." and (";
	} else {
	    $query=$query." or ";
	}
	
	$query=$query." WatchValue='".$address."'";
	
	$count++;
    }

    $query=$query." or WatchValue='".$host_address."'";

    if ($count) {
	$query=$query.")";
    }
    
    #Exim::log_write ($query);
    
    my $sth=$dbh->prepare ($query);
    $sth->execute;

    if ($sth->rows>0) {
	while (my ($BlockValue) = $sth->fetchrow_array){
	    Exim::log_write ("observation activated based on entry in ".$db_table_watchlist." [".$BlockValue."]");
	    my $message_body=Exim::expand_string('$message_body');
	    my $message_header=Exim::expand_string('$message_headers');

            $sqlsafe_message_body = $message_body;
            $sqlsafe_message_header = $message_header;

	    $sqlsafe_message_body =~ s/\"/ /g;
	    $sqlsafe_message_body =~ s/\'/ /g;
	    $sqlsafe_message_header =~ s/\"/ /g;
            $sqlsafe_massage_header =~ s/\'/ /g;

	    my $query="insert into ".$db_table_watchlist_maillog." (sender_IP,message_size,message_id, message_header,message_body) values ('".$host_address."',".$message_size.",'".$message_id."','".$sqlsafe_message_header."','".$sqlsafe_message_body."')";
	    #Exim::log_write ($query);   
	    my $sth=$dbh->prepare ($query);
	    $sth->execute;
	    
	    umask(000); # UNIX file permission junk
	    mkdir($observation_path."/".$BlockValue) unless (-d $observation_path."/".$BlockValue);
	    #copy ($message_input_path."/".$message_id."-H",$observation_path."/".$BlockValue."/".$message_id."-H");
	    copy ($message_input_path."/".$message_id."-D",$observation_path."/".$BlockValue."/".$message_id."-D");
	}
	
	return 1;
    }

    return 0;    
}
