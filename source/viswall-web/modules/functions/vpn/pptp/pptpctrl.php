<?php
		if (module_security() == true)
		{
?>
<?php
        $path = new path;
        include($path->path_modules_functions."/vpn/pptp/pptpconfig.php");
        $sql_db_local = new sql_db_local;
        include($path->path_modules_functions."/vpn/pptp/pptplib.php");
?>
<?php
		if (!isset($_GET['action']) or $_GET['action'] == "list")
		{
			# Show Strategies (Default Mode)
			# -----------------------------------
			show_serverinfo("pptp", "STRATEGY | <B>VPN - PPTP</B>", $sql_db_local->sql_db_table_pptp_options, $sql_db_local->sql_db_table_users, $sql_db_local->sql_db_table_pptp_online);
		}
		elseif ($_GET['action'] == "add")
		{
			# Add Main Object
			# ------------------
			add_user("pptp", "STRATEGY | <B>VPN - PPTP</B>", $sql_db_local->sql_db_table_users, $sql_db_local->sql_db_table_pptp_options, $sql_db_local->sql_db_table_pptp_layers, $sql_db_local->sql_db_table_hosts, $GLOBALS['status'], $GLOBALS['error'], $sql_db_local->sql_db_table_pptp_options, $sql_db_local->sql_db_table_users, $sql_db_local->sql_db_table_pptp_online);
		}
			
			
		elseif (substr($_GET['action'],0 ,4) == "edit")
		{
			if(substr($_GET['action'], 4)=="server")
			{
				edit_server("pptp", "STRATEGY | <B>VPN - PPTP</B>", $sql_db_local->sql_db_table_pptp_options, $GLOBALS['status'], $GLOBALS['id'], $sql_db_local->sql_db_table_users, $sql_db_local->sql_db_table_pptp_online);
			}
			elseif(substr($_GET['action'],4)=="user")
			{
				print_edit_html("pptp", "STRATEGY | <B>VPN - PPTP</B>", $sql_db_local->sql_db_table_pptp_layers, $sql_db_local->sql_db_table_pptp_options, $GLOBALS['id'], $GLOBALS['field'],$sql_db_local->sql_db_table_users, $sql_db_local->sql_db_table_pptp_online);
			}
			
		}
		elseif ($_GET['action'] == "delete")
		{
				# Delete Main Object
				# ---------------------
				del_user("pptp", "STRATEGY | <B>VPN - PPTP</B>", $sql_db_local->sql_db_table_pptp_layers, $GLOBALS['id'], $sql_db_local->sql_db_table_pptp_options, $sql_db_local->sql_db_table_users, $sql_db_local->sql_db_table_pptp_online);
		}
		elseif ($_GET['action'] == "setstatus")
		{
			if($_GET['field']=="server")
            {
                status_pptp("pptp", "STRATEGY | <B>VPN - PPTP</B>", $sql_db_local->sql_db_table_pptp_options, $GLOBALS['id'], $sql_db_local->sql_db_table_users, $sql_db_local->sql_db_table_pptp_online);
            }
            elseif($_GET['field']=="user")
            {
                status_pptp("pptp", "STRATEGY | <B>VPN - PPTP</B>", $sql_db_local->sql_db_table_pptp_layers, $GLOBALS['id'], $sql_db_local->sql_db_table_users, $sql_db_local->sql_db_table_pptp_online);                
            }
		}
		elseif ($_GET['action'] == "pool")
		{
			protalizer("cbq", "STRATEGY | <B>QoS - CBQ</B>", $sql_db_local->sql_db_table_cbq_rules, $GLOBALS['id'], $sql_db_local->sql_db_table_no_hosts, $sql_db_local->sql_db_table_no_networks, $GLOBALS['method']);
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
