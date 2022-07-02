<?php
		if (module_security() == true)
		{
?>
<?PHP
        $path = new path;
        include($path->path_modules_functions."/mss/rules/mss_rulesconfig.php");
        $sql_db_local = new sql_db_local;
        include($path->path_modules_functions."/mss/rules/mss_ruleslib.php");
?>
<?php
//Here comes the content
	if (!isset($GLOBALS['action']) or $GLOBALS['action'] == "list")
    {
            # Show Strategies (Default Mode)
            # -----------------------------------
            show_rules("mss_rules", "STRATEGY | <B>MailScanner - Filename rules</B>", $sql_db_local->sql_db_table_mss_filename_rules);
    }
	elseif($GLOBALS['action']=="delrule")
	{
		delrule("mss_rules", "STRATEGY | <B>MailScanner - Filename rules</B>", $sql_db_local->sql_db_table_mss_filename_rules, $GLOBALS['id']);
	}
	elseif($GLOBALS['action']=="addrule")
	{
		addrule("mss_rules", "STRATEGY | <B>MailScanner - Filename rules</B>", $sql_db_local->sql_db_table_mss_filename_rules, $GLOBALS['status']);
	}
	elseif($GLOBALS['action']=="setstatus")
	{
		setstatus("mss_rules", "STRATEGY | <B>MailScanner - Filename rules</B>", $sql_db_local->sql_db_table_mss_filename_rules, $GLOBALS['id']);
	}
	elseif(substr($GLOBALS['action'],0,6)=="change")
	{
		if(substr($GLOBALS['action'], 6)=="logtxt")
		{
			changetext("mss_rules", "STRATEGY | <B>MailScanner - Filename rules</B>", $sql_db_local->sql_db_table_mss_filename_rules, $GLOBALS['id'], "logtxt", $GLOBALS['status']);
		}
		elseif(substr($GLOBALS['action'], 6)=="usertext")
		{
			changetext("mss_rules", "STRATEGY | <B>MailScanner - Filename rules</B>", $sql_db_local->sql_db_table_mss_filename_rules, $GLOBALS['id'], "usertext", $GLOBALS['status']);
		}
	}
?>
<?php
		}
		else
		{
			include($path->path_modules_auth."/authctrl.php");
		}
		
?>
