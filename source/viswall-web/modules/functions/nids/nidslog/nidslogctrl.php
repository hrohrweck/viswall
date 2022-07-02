<?php
		if (module_security() == true)
		{
?>
<?php
		//////////////////////////////////////////////
		// ---> DOMedia - vis|wall Firewall <--- //
		//////////////////////////////////////////////
		// Date			: 28.02.2002				 //
    	//////////////////////////////////////////////
    	
        $path = new path;
        include($path->path_modules_functions."/nids/nidslog/nidslogconfig.php");
        $sql_db_local = new sql_db_local;
        include($path->path_modules_functions."/nids/nidslog/nidsloglib.php");
        
        // Open Snort Related DB
        open_db_nids();
?>
<?php
		if (!isset($GLOBALS['action']) or $GLOBALS['action'] == "list")
		{
			show_nidslog("nidslog", "LOG | <B>IDS</B>", "SUMMARY");
		}
		elseif ($GLOBALS['action'] == "tcpprobe")
		{
			show_nidslog("nidslog", "LOG | <B>IDS</B>", "TCP PROBE");
		}
		elseif ($GLOBALS['action'] == "udpprobe")
		{
			show_nidslog("nidslog", "LOG | <B>IDS</B>", "UDP PROBE");
		}
		elseif ($GLOBALS['action'] == "icmpprobe")
		{
			show_nidslog("nidslog", "LOG | <B>IDS</B>", "ICMP PROBE");
		}
		elseif ($GLOBALS['action'] == "signaturereport")
		{
			show_nidslog("nidslog", "LOG | <B>IDS</B>", "ATTACK STATISTIC");
		}
		elseif ($GLOBALS['action'] == "suspiciousreport")
		{
			show_nidslog("nidslog", "LOG | <B>IDS</B>", "SUSPICIOUS IPs");
		}
		elseif ($GLOBALS['action'] == "signaturelist")
		{
			signaturelist();
		}
		elseif ($GLOBALS['action'] == "more")
		{
			more();
		}
		elseif ($GLOBALS['action'] == "detail")
		{
			detail();
		}
		elseif ($GLOBALS['action'] == "edit")
		{
			//edit_squid("squid", "STRATEGY | <B>SQUID</B>", $sql_db_local->sql_db_table_strategies_squid, $GLOBALS['sid']);
		}
		elseif ($GLOBALS['action'] == "delete")
		{
			//delete_tbf("tbf", "STRATEGY | <B>QoS - TBF</B>", $sql_db_local->sql_db_table_strategies_tbf, $sql_db_local->sql_db_table_tbf_rules, $GLOBALS['sid']);
		}
		elseif ($GLOBALS['action'] == "setstatus")
		{
			//status_tbf("tbf", "STRATEGY | <B>QoS - TBF</B>", $sql_db_local->sql_db_table_strategies_tbf, $sql_db_local->sql_db_table_tbf_rules, $GLOBALS['sid']);
		}
		else
		{
			# Error Routine
		}
?>
<?php
		}
		else
		{
			include($path->path_modules_auth."/authctrl.php");
		}
?>
