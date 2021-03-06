<?php
		if (module_security() == true)
		{
?>
<?php
        $path = new path;
        include($path->path_modules_functions."/qos/cbq/cbqconfig.php");
        $sql_db_local = new sql_db_local;
        include($path->path_modules_functions."/qos/cbq/cbqlib.php");
?>
<?php
		if (!isset($GLOBALS['action']) or $GLOBALS['action'] == "list")
		{
			# Show Strategies (Default Mode)
			# -----------------------------------
			show_cbq("cbq", "STRATEGY | <B>QoS - CBQ</B>", $sql_db_local->sql_db_table_strategies_cbq);
		}
		elseif ($GLOBALS['action'] == "add")
		{
			# Add Main Object
			# ------------------
			add_cbq("cbq", "STRATEGY | <B>QoS - CBQ</B>", $sql_db_local->sql_db_table_strategies_cbq, $sql_db_local->sql_db_table_io_interfaces, $GLOBALS['id'], $GLOBALS['position']);
		}
		
		elseif ($GLOBALS['action'] == "edit")
		{
			# Edit Main Object
			# ------------------
				edit_cbq("cbq", "STRATEGY | <B>QoS - CBQ</B>", $sql_db_local->sql_db_table_strategies_cbq, $sql_db_local->sql_db_table_no_networks, $sql_db_local->sql_db_table_no_hosts, $sql_db_local->sql_db_table_io_interfaces, $GLOBALS['id'], $GLOBALS['field']);
		}
		elseif ($GLOBALS['action'] == "delete")
		{
			# Delete Main Object
			# ---------------------
			delete_cbq("cbq", "STRATEGY | <B>QoS - CBQ</B>", $sql_db_local->sql_db_table_strategies_cbq, $GLOBALS['id'], $GLOBALS['c'], $GLOBALS['id']);
		}
		elseif ($GLOBALS['action'] == "setstatus")
		{
			status_cbq("cbq", "STRATEGY | <B>QoS - CBQ</B>", $sql_db_local->sql_db_table_strategies_cbq, $GLOBALS['id'], $GLOBALS['field']);
		}
		elseif ($GLOBALS['action'] == "pool")
		{
			pool("cbq", "STRATEGY | <B>QoS - CBQ</B>", $sql_db_local->sql_db_table_cbq_rules, $GLOBALS['id'], $sql_db_local->sql_db_table_no_hosts, $sql_db_local->sql_db_table_no_networks, $GLOBALS['method']);
		}
		elseif($GLOBALS['action'] == "activate")
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
