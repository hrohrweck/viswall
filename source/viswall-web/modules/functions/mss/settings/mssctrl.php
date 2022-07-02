<?php
		if (module_security() == true)
		{
?>
<?php
        $path = new path;
        include($path->path_modules_functions."/mss/settings/mssconfig.php");
        $sql_db_local = new sql_db_local;
        include($path->path_modules_functions."/mss/settings/msslib.php");
?>
<?PHP
        if (!isset($_GET['action']) or $_GET['action'] == "list")
        {
            # Show Strategies (Default Mode)
            # -----------------------------------
            show_serverinfo("mss", "STRATEGY | <B>MailScanner - Settings</B>", $sql_db_local->sql_db_table_mss_general, $sql_db_local->sql_db_table_control_mss);
        }
        elseif ($_GET['action'] == "add")
        {
            # Add Main Object
            # ------------------
            add_cbq("cbq", "STRATEGY | <B>QoS - CBQ</B>", $sql_db_local->sql_db_table_strategies_cbq, $sql_db_local->sql_db_table_io_interfaces, $GLOBALS['id'], $GLOBALS['position']);
        }
        elseif (substr($_GET['action'],0 ,4) == "edit")
        {
            if(substr($_GET['action'], 4)=="server")
            {
                edit_server("mss", "STRATEGY | <B>MailScanner - Settings</B>", $sql_db_local->sql_db_table_mss_general, $GLOBALS['status'], $GLOBALS['id']);
            }
            elseif(substr($_GET['action'],4)=="settings")
            {
                if($_GET['field']=="signopt")
                {
                    print_edit_html("mss", "STRATEGY | <B>MailScanner - Settings</B>", $sql_db_local->sql_db_table_mss_signoptions, $GLOBALS['field']);
                }
                elseif($_GET['field']=="notifyopt")
                {
                    print_edit_html("mss", "STRATEGY | <B>MailScanner - Settings</B>", $sql_db_local->sql_db_table_mss_deliveroptions, $GLOBALS['field']);
                }
                elseif($_GET['field']=="notifymes")
                {
                    print_edit_html("mss", "STRATEGY | <B>MailScanner - Settings</B>", $sql_db_local->sql_db_table_mss_signoptions, $GLOBALS['field']);
                }
            }
            elseif(substr($_GET['action'], 4)=="lists")
            {
                if($_GET['field']=="domains2scan")
                {
                   show_domain_list("mss", "STRATEGY | <B>MailScanner - Settings</B>", $sql_db_local->sql_db_table_mss_domainlist, "1");
                }
                elseif($_GET['field']=="localdomain")
                {
                   show_domain_list("mss", "STRATEGY | <B>MailScanner - Settings</B>", $sql_db_local->sql_db_table_mss_domainlist, "2");
                }
                elseif($_GET['field']=="spamwhite")
                {
                   show_domain_list("mss", "STRATEGY | <B>MailScanner - Settings</B>", $sql_db_local->sql_db_table_mss_domainlist, "3");
                }
            }
        }
        elseif ($_GET['action'] == "delete")
        {
                # Delete Main Object
                # ---------------------
                delete_cbq("cbq", "STRATEGY | <B>QoS - CBQ</B>", $sql_db_local->sql_db_table_strategies_cbq, $GLOBALS['id'], $GLOBALS['c'], "0");
        }
        elseif ($GLOBALS['action'] == "setstatus")
        {
            status_mss("mss", "STRATEGY | <B>MailScanner - Settings</B>", $sql_db_local->sql_db_table_control_mss, $GLOBALS['id'], $GLOBALS['field']);
        }
        elseif ($_GET['action'] == "popup")
        {
                if($GLOBALS['type']==0)
                {
                   popup_enter_text($GLOBALS['field'], $sql_db_local->sql_db_table_mss_signoptions);
                }
                elseif($GLOBALS['type']==1)
                {
                   popup_enter_line($GLOBALS['field'], $sql_db_local->sql_db_table_mss_signoptions);
                }
        }
        elseif (substr($_GET['action'],0,6)=="change")
        {
                if(substr($_GET['action'],6,12)=="mail_headers")
                {
                   changepopup_text("clean_header", $sql_db_local->sql_db_table_mss_signoptions, $GLOBALS['clean_header'], $GLOBALS['type'], $GLOBALS['infected_header'], $GLOBALS['disinfected_header'], "infected_header", "disinfected_header");
                }
                else//if(substr($_GET['action'],6)=="")
                {
                   changepopup_text($_GET['field'], $sql_db_local->sql_db_table_mss_signoptions, $GLOBALS['text'], $GLOBALS['type']);
                }
        }
		elseif ($_GET['action'] == "adddomain")
        {
                add_domain("mss", "STRATEGY | <B>MailScanner - Settings</B>", $sql_db_local->sql_db_table_mss_domainlist, $GLOBALS['type'], $GLOBALS['status']);
        }
        elseif ($_GET['action'] == "deldomain")
        {
                del_domain("mss", "STRATEGY | <B>MailScanner - Settings</B>", $sql_db_local->sql_db_table_mss_domainlist, $GLOBALS['id'], $GLOBALS['type']);
        }
        elseif($_GET['action'] == "activate")
        {
            activate_rules();
            show_nat(0, "nat", "STRATEGY | <B>N.A.T.</B>", $sql_db_local->sql_db_table_strategies_nat);
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