#!/usr/bin/perl
my $configfile = "/viswall/config"
my $datenbank="mysql";
my $db_table_deliver="mss_deliveroptions";
my $db_table_domainlist="mss_domainlist";
my $db_table_filename_rules="mss_filename_rules";
my $db_table_general="mss_general";
my $db_table_control="control_mss";
my $db_table_signoptions="mss_signoptions";
my $db_table_spamblockoptions="mss_spamblockoptions";
# output conf files
my $path_output="/opt/mailscanner/etc/mailscanner.conf";
my $path_deleted_filename="/opt/mailscanner/deleted.filename.message.txt";
my $path_deleted_message="/opt/mailscanner/deleted.virus.message.txt";
my $path_disinfected_report="/opt/mailscanner/disinfected.report.txt";
my $path_stored_filename="/opt/mailscanner/stored.filename.message.txt";
my $path_virus_message="/opt/mailscanner/stored.virus.message.txt";
my $path_attachment_warning="/opt/mailscanner/viruswarning.txt";
my $path_sender_virus_report="/opt/mailscanner/sender.virus.report.txt";
my $path_sender_filename_report="/opt/mailscanner/sender.filename.report.txt";
my $path_sender_error_report="/opt/mailscanner/sender.error.report.txt";
# domains list conf files
my $path_domains2scan="/opt/mailscanner/domains.to.scan.conf";
my $path_localdomains="/opt/mailscanner/localdomains.conf";
my $path_whitelist="/opt/mailscanner/spam.whitelist.conf";
# filename rules file
my $path_filename_rules="/opt/mailscanner/filename.rules.conf";
my $first="";

use DBI;
use Config::File;

my $config_hash = Config::File::read_config_file($configfile);

my $mysql_db = $config_hash->{DB_NAME_SPAMASSASSIN};
my $mysql_host = $config_hash->{DB_HOST};
my $mysql_user = $config_hash->{DB_USER};
my $mysql_passwd = $config_hash->{DB_PASS};


#Description
sub headwrite_mss{
$first=$first."#!/bin/bash\n";
$first=$first."###########################################\n";
$first=$first."# Created by Viswall                      #\n";
$first=$first."# MAILSCANNER CONFIGURE SCRIPT	          #\n";
$first=$first."# TIMESTAMP: ".localtime()."     #\n";
$first=$first."###########################################\n";
return $first;
}


# first write general options
sub write_main{
    my ($path_output,$dbh,$db_table_general,$db_table_deliver,$db_table_domainlist,$db_table_filename_rules,$db_table_signoptions,$db_table_control)=@_;
    my $head=headwrite_mss();
    %control=get_control($dbh,$db_table_control);
    %general=get_general($dbh,$db_table_general);
    %deliver=get_deliveroptions($dbh,$db_table_deliver);
    %sign=get_signoptions($dbh,$db_table_signoptions,$path_deleted_filename,$path_deleted_message,$path_disinfected_report,$path_stored_filename,$path_virus_message,$path_attachment_warning,$path_sender_virus_report,$path_sender_filename_report,$path_sender_error_report);
    get_domainlists($dbh,$db_table_domainlist,$path_domains2scan,$path_localdomains,$path_whitelist);
    get_filename_rules($dbh,$db_table_filename_rules,$path_filename_rules);

    open (OUTPUT,">$path_output"); 
    
    print OUTPUT "Virus Scanning = ".$control{virus_scanning}."\n";    
    print OUTPUT "Spam Checks = ".$control{spam_checking}."\n";
    print OUTPUT "Action = ".$general{action}."\n";
    print OUTPUT "Hostname = ".$general{hostname}."\n";
    print OUTPUT "Local postmaster = ".$general{local_postmaster}."\n";
    print OUTPUT "Restart every = ".$general{restart_every}."\n";
    print OUTPUT "Scanning by domain = ".$general{scanning_by_domain}."\n";
    print OUTPUT "Virus scanner timeout = ".$general{virus_scanner_timeout}."\n";
    print OUTPUT "Deliver disinfected file = ".$deliver{deliver_disinfected_file}."\n";
    print OUTPUT "Deliver from local domains = ".$deliver{deliver_from_local_domains}."\n";
    print OUTPUT "Deliver to recipients = ".$deliver{deliver_to_recipients}."\n";
    print OUTPUT "Deliver unparseable TNEF = ".$deliver{deliver_unparseable_TNEF}."\n";
    print OUTPUT "Notify local postmaster = ".$deliver{notify_local_postmaster}."\n";
    print OUTPUT "Notify sender = ".$deliver{notify_sender}."\n";
    print OUTPUT "Postmaster gets full header = ".$deliver{postmaster_gets_full_header}."\n";
    print OUTPUT "Clean header = ".$sign{clean_header}."\n";
    print OUTPUT "Disinfected_header = ".$sign{disinfected_header}."\n";
    print OUTPUT "Infected header = ".$sign{infected_header}."\n";    

    my $counter=0;
    my $stop=0;
    my $one_line="";
    do {
        $counter=get_cutvalue($sign{inline_html_signature});
        $stop = $counter;
        $one_line=cutstring($sign{inline_html_signature},0,$stop==-1?$stop=length($sign{inline_html_signature}):$stop);
        print OUTPUT "Inline html signature = ".$one_line."\n";
        $sign{inline_html_signature}=substr($sign{inline_html_signature},$counter+1);
    } until($counter==-1);
    $counter=0;
    $stop=0;
    $one_line="";
    do {
        $counter=get_cutvalue($sign{inline_html_warning});
        $stop = $counter;
        $one_line=cutstring($sign{inline_html_warning},0,$stop==-1?$stop=length($sign{inline_html_warning}):$stop);
        print OUTPUT "Inline html warning = ".$one_line."\n";
        $sign{inline_html_warning}=substr($sign{inline_html_warning},$counter+1);
    } until($counter==-1);
    $counter=0;
    $stop=0;
    $one_line="";
    do {
        $counter=get_cutvalue($sign{inline_text_signature});
        $stop = $counter;
        $one_line=cutstring($sign{inline_text_signature},0,$stop==-1?$stop=length($sign{inline_text_signature}):$stop);
        print OUTPUT "Inline text signature = ".$one_line."\n";
        $sign{inline_text_signature}=substr($sign{inline_text_signature},$counter+1);
    } until($counter==-1);
    $counter=0;
    $stop=0;
    $one_line="";
    do {
        $counter=get_cutvalue($sign{inline_text_warning});
        $stop = $counter;
        $one_line=cutstring($sign{inline_text_warning},0,$stop==-1?$stop=length($sign{inline_text_warning}):$stop);
        print OUTPUT "Inline text warning = ".$one_line."\n";
        $sign{inline_text_warning}=substr($sign{inline_text_warning},$counter+1);
    } until($counter==-1);

    print OUTPUT "Mail Header = ".$sign{mail_header}."\n";
    print OUTPUT "Mark infected messages = ".$sign{mark_infected_messages}."\n";
    print OUTPUT "Sign clean messages = ".$sign{sign_clean_messages}."\n";    
    print OUTPUT "Sign unscanned messages = ".$sign{sign_unscanned_messages}."\n";
    print OUTPUT "Spam modify subject = ".$sign{spam_modify_subject}."\n";    
    print OUTPUT "Spam subject text = ".$sign{spam_subject_text}."\n";
    print OUTPUT "Unscanned header = ".$sign{unscanned_header}."\n";
    # now print the hard-coded things
    print OUTPUT "Max Safe   Messages Per Scan = 500"."\n";
    print OUTPUT "Max Unsafe Messages Per Scan = 100"."\n";
    print OUTPUT "Max Safe   Bytes Per Scan = 100000000"."\n";
    print OUTPUT "Max Unsafe Bytes Per Scan = 50000000"."\n";
    print OUTPUT "Incoming Work Dir  = /var/spool/MailScanner/incoming"."\n";
    print OUTPUT "Quarantine Dir     = /var/spool/MailScanner/quarantine"."\n";
    print OUTPUT "Pid File           = /opt/mailscanner/var/virus.pid"."\n";
    print OUTPUT "Filename Rules     = /opt/mailscanner/etc/filename.rules.conf"."\n";
    print OUTPUT "Stored Virus Message Report  = /opt/mailscanner/etc/stored.virus.message.txt"."\n";
    print OUTPUT "Stored Bad Filename Message Report  = /opt/mailscanner/etc/stored.filename.message.txt"."\n";
    print OUTPUT "Deleted Virus Message Report = /opt/mailscanner/etc/deleted.virus.message.txt"."\n";
    print OUTPUT "Deleted Bad Filename Message Report = /opt/mailscanner/etc/deleted.filename.message.txt"."\n";
    print OUTPUT "Disinfected Report = /opt/mailscanner/etc/disinfected.report.txt"."\n";
    print OUTPUT "Incoming Queue Dir = /var/spool/mqueue.in"."\n";
    print OUTPUT "Outgoing Queue Dir = /var/spool/mqueue"."\n";
    print OUTPUT "MTA                = sendmail"."\n";
    print OUTPUT "Sendmail           = /usr/sbin/sendmail"."\n";
    print OUTPUT "Virus Scanner      = f-prot"."\n";
    print OUTPUT "Sweep = /opt/f-prot/f-protwrapper"."\n";
    #Expand TNEF only 'no' with SOPHOS
    print OUTPUT "Expand TNEF        = yes"."\n";
    print OUTPUT "Scan All Messages = yes"."\n";
    print OUTPUT "Sender Virus Report        = /opt/mailscanner/etc/sender.virus.report.txt"."\n";
    print OUTPUT "Sender Bad Filename Report = /opt/mailscanner/etc/sender.filename.report.txt"."\n";
    print OUTPUT "Sender Error Report        = /opt/mailscanner/etc/sender.error.report.txt"."\n";
    print OUTPUT "Local Domains = /opt/mailscanner/etc/localdomains.conf"."\n";
    print OUTPUT "Use SpamAssassin = no"."\n";
    print OUTPUT "Spam White List = /opt/mailscanner/etc/spam.whitelist.conf"."\n";
    print OUTPUT "Debug = 0"."\n";
    print OUTPUT "Delivery Method = batch"."\n";
    print OUTPUT "Multiple Headers = append"."\n";
    print OUTPUT "Deliver In Background = no"."\n";
    print OUTPUT "Minimum Code Status = supported"."\n";
    print OUTPUT "High SpamAssassin Score = "."\n";
    print OUTPUT "High Scoring Spam Action = deliver"."\n";
    print OUTPUT "Notify senders = no"."\n";
    print OUTPUT "Log Facility = mail"."\n";
    print OUTPUT "Virused To Quietly Delete = "."\n";
    print OUTPUT "SpamAssassin Auto Whitelist = no"."\n";

    close (OUTPUT2);
}

sub cutstring {
    my($string,$start,$stop)=@_;
    my $restring=substr($string,$start,$stop);
    return $restring;
}

sub get_cutvalue {
    my($input)=@_;
    my $counter=index($input,"\n");
    return $counter;
}

sub get_control{ # funtion to getting Mailscanner status
    my($dbh,$db_table_control)=@_;
    my $sth1=$dbh->prepare ("Select * from ".$db_table_control."");
    $sth1->execute;
    my($virus_scanning,$spam_checking,$status)=$sth1->fetchrow_array;
    if($status==0)
    {
        $virus_scanning=0;
        $spam_checking=0;
    }
    %control = ("virus_scanning" => $virus_scanning,"spam_checking" => $spam_checking);
    return %control;    
}
   
sub get_general{ # function for getting information from general-DB
    my($dbh,$db_table_general)=@_;
    my $sth1=$dbh->prepare ("Select * from ".$db_table_general."");
    $sth1->execute;
    my($id,$scanning_by_domain,$virus_scanner_timeout,$restart_every,$hostname,$action,$local_postmaster)=$sth1->fetchrow_array;
    $scanning_by_domain=is_true($scanning_by_domain);
    $action=chk_action($action);
    %general = ("scanning_by_domain" => $scanning_by_domain, "virus_scanner_timeout" => $virus_scanner_timeout, "restart_every" => $restart_every, "hostname" => $hostname, "action" => $action, "local_postmaster" => $local_postmaster);
    return %general;
}

sub get_deliveroptions{ # function for getting information from deliveroptions-DB
    my($dbh,$db_table_deliver)=@_;
    my $sth1=$dbh->prepare ("Select * from ".$db_table_deliver."");
    $sth1->execute;
    my($id,$postmaster_gets_full_header,$deliver_from_local_domains,$deliver_unparseable_TNEF,$deliver_to_recipients,$deliver_disinfected_file,$notify_sender,$notify_local_postmaster)=$sth1->fetchrow_array;
    
    $postmaster_gets_full_header=is_true($postmaster_gets_full_header);
    $deliver_from_local_domains=is_true($deliver_from_local_domains);
    $deliver_unparseable_TNEF=is_true($deliver_unparseable_TNEF);
    $deliver_to_recipients=is_true($deliver_to_recipients);
    $deliver_disinfected_file=is_true($deliver_disinfected_file);
    $notify_sender=is_true($notify_sender);
    $notify_local_postmaster=is_true($notify_local_postmaster);
    
    %deliver = ("postmaster_gets_full_header" => $postmaster_gets_full_header, "deliver_from_local_domains" => $deliver_from_local_domains, "deliver_unparseable_TNEF" => $deliver_unparseable_TNEF, "deliver_to_recipients" => $deliver_to_recipients, "deliver_disinfected_file" => $deliver_disinfected_file, "notify_sender" => $notify_sender, "notify_local_postmaster" => $notify_local_postmaster);    
    return %deliver;
}

sub get_signoptions{ # getting information from signoptions-DB and write files
    my($dbh,$db_table_signoptions,$path_deleted_filename,$path_deleted_message,$path_disinfected_report,$path_stored_filename,$path_virus_message,$path_attachment_warning,$path_sender_virus_report,$path_sender_filename_report,$path_sender_error_report)=@_;
    my $sth1=$dbh->prepare ("Select * from ".$db_table_signoptions."");
    $sth1->execute;
    my($id,$sign_unscanned_messages,$unscanned_header,$sign_clean_messages,$inline_text_signature,$inline_html_signature,$mark_infected_messages,$inline_text_warning,$inline_html_warning,$mail_header,$clean_header,$infected_header,$disinfected_header,$stored_virus_message,$stored_bad_filename_message,$deleted_virus_message,$deleted_bad_filename_message,$disinfected_mail_message,$attachment_warning,$spam_modify_subject,$spam_subject_text,$sender_virus_report,$sender_filename_report,$sender_error_report)=$sth1->fetchrow_array;
    $sign_unscanned_messages=is_true($sign_unscanned_messages);
    $sign_clean_messages=is_true($sign_clean_messages);
    $mark_infected_messages=is_true($mark_infected_messages);
    $spam_modify_subject=is_true($spam_modify_subject);
    %sign = ("sign_unscanned_messages" => $sign_unscanned_messages, "unscanned_header" => $unscanned_header, "sign_clean_messages" => $sign_clean_messages, "inline_text_signature" => $inline_text_signature, "inline_html_signature" => $inline_html_signature, "mark_infected_messages" => $mark_infected_messages, "inline_text_warning" => $inline_text_warning, "inline_html_warning" => $inline_html_warning, "mail_header" => $mail_header, "clean_header" => $clean_header, "infected_header" => $infected_header, "disinfected_header" => $disinfected_header, "attachment_warning" => $attachment_warning, "spam_modify_subject" => $spam_modify_subject, "spam_subject_text" => $spam_subject_text);
    # Now write the files
    writefile($path_virus_message,$stored_virus_message);
    writefile($path_stored_filename,$stored_bad_filename_message);
    writefile($path_deleted_message,$deleted_virus_message);
    writefile($path_deleted_filename,$deleted_bad_filename_message);
    writefile($path_disinfected_report,$disinfected_mail_message);
    writefile($path_attachment_warning,$attachment_warning);
    writefile($path_sender_virus_report,$sender_virus_report);
    writefile($path_sender_filename_report,$sender_filename_report);
    writefile($path_sender_error_report,$sender_error_report);
    
    return %sign; # return array
}
sub get_domainlists{ # getting domainslists
    my($dbh,$db_table_domainlist,$path_domains2scan,$path_localdomains,$path_whitelist)=@_;
    my $i=1;
    my $path_target;
    my $output;
    for($i=1;$i<=3;$i++) { # Loop for getting localdomains, domains2scan and whitelist
        if($i==1){ # If type=domain2scan
            $path_target=$path_domains2scan;
        }
        elsif($i==2){ # If type=localdomains
            $path_target=$path_localdomains;
        }
        elsif($i==3){ # If type=spam whitelist
            $path_target=$path_whitelist;
        }
        my $sth1=$dbh->prepare("SELECT name FROM ".$db_table_domainlist." WHERE type='".$i."'");
        $sth1->execute;
        while(my($name)=$sth1->fetchrow_array){
            $output=$output.$name."\n";
        }
        writefile($path_target,$output);
        undef($sth1);
        $output="";
        $path_target="";
    }
}
sub get_filename_rules{ # function for parsing filename ruls
    my($dbh,$db_table_filename_rules,$path_filename_rules)=@_;
    my $output;
    my $sth3=$dbh->prepare("SELECT * from ".$db_table_filename_rules."");
    $sth3->execute;
    while(my($id,$action,$expr,$logtext,$usertext)=$sth3->fetchrow_array){;
        $output=$output.allow_deny($action)."\t".$expr."\t".$logtext."\t".$usertext."\n";
    }
    writefile($path_filename_rules,$output);
}
sub is_true{ # Convert Bit-Value to logical value
    my($input)=@_;
    if($input==1) {
        return "yes";
    }
    else
    {
        return "no";        
    }
}
sub allow_deny{ # Convert Bit-Value in Allow - Deny value
    my($input)=@_;
    if($input==0){ # If we should deny it
        return "deny";
    }
    elsif($input==1){ # If we should allow it
        return "allow";
    }
}
sub writefile{ # sub for generation of mailscanner etc conf files
    my($file,$value)=@_;
    open (OUTPUT2,">$file"); 
    print OUTPUT2 $value;
    close (OUTPUT2);
}

sub chk_action{ # Convert Bit-Action to logical Action
    my ($input)=@_;
    if($input==1) {
        return "keep";
    }
    elsif($input==0)
    {
        return "delete";        
    }
}



#Load Kernel Modules

# connect to database
my $dbh = DBI->connect ("dbi:$datenbank:host=$mysql_host;database=$mysql_db",$mysql_user,$mysql_passwd);


# call write function
write_main($path_output,$dbh,$db_table_general,$db_table_deliver,$db_table_domainlist,$db_table_filename_rules,$db_table_signoptions,$db_table_control);
