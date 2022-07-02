<?php
		if (module_security() == true)
		{
			$path = new path;
			include($path->path_modules_functions."/routing/routingconfig.php");
			$sql_db_local = new sql_db_local;
			include($path->path_modules_functions."/routing/routinglib.php");

			if (!isset($_GET['action']) or $_GET['action'] == "list")
			{
				show_strategies(0, "routing", "STRATEGY | <B>ROUTING</B>", $sql_db_local->sql_db_table_strategies);
			}
			elseif ($_GET['action'] == "add")
			{
				add_strategies("routing", $sql_db_local->sql_db_table_strategies);
			}
			elseif($_GET['action'] == "edit")
			{
				edit_strategies("routing", "STRATEGY | <B>ROUTING</B>", $sql_db_local->sql_db_table_strategies, $_GET['sid'], $_GET['field']);
			}
			elseif($_GET['action'] == "setstatus")
			{
				change_strategies_status("routing", $sql_db_local->sql_db_table_strategies, $_GET['sid'], $_GET['field']);
			}
			elseif($_GET['action'] == "delete")
			{
				$result = mysql_query("delete from ".$sql_db_local->sql_db_table_strategies." where (id=\"".$_GET['sid']."\")");
				show_strategies(0, "routing", "STRATEGY | <B>ROUTING</B>", $sql_db_local->sql_db_table_strategies);
			}
			elseif($_GET['action'] == "activate")
			{
				activate_rules();
				show_strategies(0, "routing", "STRATEGY | <B>ROUTING</B>", $sql_db_local->sql_db_table_strategies);
			}
			else
			{
				show_strategies(0, "routing", "STRATEGY | <B>ROUTING</B>", $sql_db_local->sql_db_table_strategies);
			}
		}
		else
		{
			include($path->path_modules_auth."/authctrl.php");
		}
?>
