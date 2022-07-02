<?php
		if (module_security() == true)
		{
			$path = new path;
			include($path->path_modules_functions."/filter/filterconfig.php");
			$sql_db_local = new sql_db_local;
			include($path->path_modules_functions."/filter/filterlib.php");
      
			if (!isset($_GET['action']) or $_GET['action'] == "list")
			{
				show_strategies(0, "filter", "STRATEGY | <B>FIREWALL</B>", $sql_db_local->sql_db_table_strategies_guardian);
			}
			elseif ($_GET['action'] == "sort")
			{
				correct_priorities("filter", $sql_db_local->sql_db_table_strategies_guardian, $_GET['field']);
				show_strategies(0, "filter", "STRATEGY | <B>FIREWALL</B>", $sql_db_local->sql_db_table_strategies_guardian);
			}
			elseif ($_GET['action'] == "addsimple")
			{
				add_strategies_simple("filter", $sql_db_local->sql_db_table_strategies_guardian);
			}
			elseif ($_GET['action'] == "addbefore")
			{
				add_strategies_baf("filter", $sql_db_local->sql_db_table_strategies_guardian, $_GET['sid'], $_GET['field'], 1);
			}
			elseif ($_GET['action'] == "addafter")
			{
				add_strategies_baf("filter", $sql_db_local->sql_db_table_strategies_guardian, $_GET['sid'], $_GET['field'], 0);
			}
			elseif($_GET['action'] == "editsimple")
			{
				edit_strategies_simple("filter", "STRATEGY | <B>FIREWALL</B>", $sql_db_local->sql_db_table_strategies_guardian, $_GET['sid'], $_GET['field']);
			}
			elseif($_GET['action'] == "priorityup")
			{
				change_strategies_priority("filter", $sql_db_local->sql_db_table_strategies_guardian, $_GET['sid'], $_GET['field'], 0, $_POST['status']);
			}
			elseif($_GET['action'] == "prioritydown")
			{
				change_strategies_priority("filter", $sql_db_local->sql_db_table_strategies_guardian, $_GET['sid'], $_GET['field'], 1, $_POST['status']);
			}
			elseif($_GET['action'] == "priorityedit")
			{
				change_strategies_priority("filter", $sql_db_local->sql_db_table_strategies_guardian, $_GET['sid'], $_GET['field'], 2, $_POST['status']);
			}
			elseif($_GET['action'] == "setstatus")
			{
				change_strategies_status("filter", $sql_db_local->sql_db_table_strategies_guardian, $_GET['sid'], $_GET['field']);
			}
			elseif($_GET['action'] == "setstate")
                        {
                                change_states("filter", $sql_db_local->sql_db_table_strategies_guardian, $_GET['sid'], $_GET['field']);
			}
                        elseif($_GET['action'] == "setdirection")
			{
				change_strategies_direction("filter", $sql_db_local->sql_db_table_strategies_guardian, $_GET['sid'], $_GET['direction']);
			}
			elseif($_GET['action'] == "delete")
			{
				$result = mysql_query("delete from ".$sql_db_local->sql_db_table_strategies_guardian." where (id=\"".$_GET['sid']."\")");
				
				correct_priorities("filter", $sql_db_local->sql_db_table_strategies_guardian);
				show_strategies(0, "filter", "STRATEGY | <B>FIREWALL</B>", $sql_db_local->sql_db_table_strategies_guardian);
			}
			elseif($_GET['action'] == "activate")
			{
				activate_rules();
				show_strategies(0, "filter", "STRATEGY | <B>FIREWALL</B>", $sql_db_local->sql_db_table_strategies_guardian);
			}
			elseif($_GET['action'] == "chains")
			{
				$result = mysql_query("update strategies_filter_default set chainvalue='".$_GET['value']."' where(id='".$_GET['sid']."')");
				correct_priorities("filter", $sql_db_local->sql_db_table_strategies_guardian);
				show_strategies(0, "filter", "STRATEGY | <B>FIREWALL</B>", $sql_db_local->sql_db_table_strategies_guardian);
			}
			else
			{
				correct_priorities("filter", $sql_db_local->sql_db_table_strategies_guardian);
				show_strategies(0, "filter", "STRATEGY | <B>FIREWALL</B>", $sql_db_local->sql_db_table_strategies_guardian);
			}
		}
		else
		{
			include($path->path_modules_auth."/authctrl.php");
		}
?>
