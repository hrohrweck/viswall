<?php
		if (module_security() == true)
		{
?>
<?php
        $path = new path;
        include($path->path_modules_functions."/squid/squidconfig.php");
        $sql_db_local = new sql_db_local;
        include($path->path_modules_functions."/squid/squidlib.php");
?>
<?php
		if (!isset($GLOBALS['action']) or $GLOBALS['action'] == "list")
		{
			show_squid("squid", "STRATEGY | <B>PROXY</B>", $sql_db_local->sql_db_table_strategies_squid);
		}
		elseif ($GLOBALS['action'] == "add")
		{
			//add_squid("squid", "STRATEGY | <B>PROXY</B>", $sql_db_local->sql_db_table_strategies_squid, $sql_db_local->sql_db_table_squid_rules, $GLOBALS['sid']);
		}
		elseif ($GLOBALS['action'] == "edit")
		{
			edit_squid("squid", "STRATEGY | <B>PROXY</B>", $sql_db_local->sql_db_table_strategies_squid, $GLOBALS['sid']);
		}
		elseif ($GLOBALS['action'] == "delete")
		{
			//delete_tbf("tbf", "STRATEGY | <B>PROXY</B>", $sql_db_local->sql_db_table_strategies_tbf, $sql_db_local->sql_db_table_tbf_rules, $GLOBALS['sid']);
		}
		
		elseif($_GET['action'] == "activate")
                        {
                                activate_rules();
                                show_strategies(0, "squid", "STRATEGY | <B>SQUID</B>",$sql_db_local->sql_db_table_strategies);
                        }
		elseif ($GLOBALS['action'] == "setstatus")
		{
			status_proxy("squid", "STRATEGY | <B>PROXY</B>", $sql_db_local->sql_db_table_strategies_squid, $GLOBALS['sid']);
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
