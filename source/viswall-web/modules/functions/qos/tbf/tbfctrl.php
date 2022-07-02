<?php
		if (module_security() == true)
		{
?>
<?php
        $path = new path;
        include($path->path_modules_functions."/qos/tbf/tbfconfig.php");
        $sql_db_local = new sql_db_local;
        include($path->path_modules_functions."/qos/tbf/tbflib.php");
?>
<?php
		if (!isset($GLOBALS['action']) or $GLOBALS['action'] == "list")
		{
			show_tbf("tbf", "STRATEGY | <B>QoS - TBF</B>", $sql_db_local->sql_db_table_strategies_tbf);
		}
		elseif ($GLOBALS['action'] == "add")
		{
			add_tbf("tbf", "STRATEGY | <B>QoS - TBF</B>", $sql_db_local->sql_db_table_strategies_tbf, $sql_db_local->sql_db_table_tbf_rules, $GLOBALS['sid']);
		}
		elseif ($GLOBALS['action'] == "edit")
		{
			edit_tbf("tbf", "STRATEGY | <B>QoS - TBF</B>", $sql_db_local->sql_db_table_strategies_tbf, $sql_db_local->sql_db_table_io_interfaces, $GLOBALS['sid'], $GLOBALS['field'], $GLOBALS['fid']);
		}
		elseif ($GLOBALS['action'] == "delete")
		{
			delete_tbf("tbf", "STRATEGY | <B>QoS - TBF</B>", $sql_db_local->sql_db_table_strategies_tbf, $sql_db_local->sql_db_table_tbf_rules, $GLOBALS['sid']);
		}
		elseif ($GLOBALS['action'] == "setstatus")
		{
			status_tbf("tbf", "STRATEGY | <B>QoS - TBF</B>", $sql_db_local->sql_db_table_strategies_tbf, $sql_db_local->sql_db_table_tbf_rules, $GLOBALS['sid']);
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