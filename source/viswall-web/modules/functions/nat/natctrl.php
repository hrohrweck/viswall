<?php
		if (module_security() == true)
		{
?>
<?php
        $path = new path;
        include($path->path_modules_functions."/nat/natconfig.php");
        $sql_db_local = new sql_db_local;
        include($path->path_modules_functions."/nat/natlib.php");
?>
<?php
		if (!isset($_GET['action']) or $_GET['action'] == "list")
			show_nat(0, "nat", "STRATEGY | <B>N.A.T.</B>", $sql_db_local->sql_db_table_strategies_nat);
		elseif ($_GET['action'] == "addbefore")
			add_nat(1, "nat", "STRATEGY | <B>N.A.T.</B>", $sql_db_local->sql_db_table_strategies_nat, $sql_db_local->sql_db_table_nat_layers, $_GET['sid'], 1);
		elseif ($_GET['action'] == "addafter")
			add_nat(1, "nat", "STRATEGY | <B>N.A.T.</B>", $sql_db_local->sql_db_table_strategies_nat, $sql_db_local->sql_db_table_nat_layers, $_GET['sid'], 0);
		elseif($_GET['action'] == "priorityup")
			change_nat_priority("nat", "STRATEGY | <B>N.A.T.</B>", $sql_db_local->sql_db_table_strategies_nat, $_GET['sid'], 0);
		elseif($_GET['action'] == "prioritydown")
			change_nat_priority("nat", "STRATEGY | <B>N.A.T.</B>", $sql_db_local->sql_db_table_strategies_nat, $_GET['sid'], 1);
		elseif ($_GET['action'] == "edit")
			edit_nat(1, "nat", "STRATEGY | <B>N.A.T.</B>", $sql_db_local->sql_db_table_strategies_nat, $sql_db_local->sql_db_table_nat_layers, $_GET['sid'], $_GET['field'], $_GET['fid']);
		elseif ($_GET['action'] == "delete")
			delete_nat(1, "nat", "STRATEGY | <B>N.A.T.</B>", $sql_db_local->sql_db_table_strategies_nat, $sql_db_local->sql_db_table_nat_layers, $_GET['sid']);
		elseif ($_GET['action'] == "setstatus")
			status_nat(0, "nat", "STRATEGY | <B>N.A.T.</B>", $sql_db_local->sql_db_table_strategies_nat, $sql_db_local->sql_db_table_nat_layers, $_GET['sid']);
		elseif ($_GET['action'] == "setmethod")
			method_nat(0, "nat", "STRATEGY | <B>N.A.T.</B>", $sql_db_local->sql_db_table_strategies_nat, $sql_db_local->sql_db_table_nat_layers, $_GET['sid']);
		elseif ($_GET['action'] == "setstate")
                        change_states("nat", "STRATEGY | <B>N.A.T.</B>", $sql_db_local->sql_db_table_strategies_nat, $_GET['sid'], $_GET['field']);
        elseif ($_GET['action'] == "activate")
		{
			activate_rules();
			show_nat(0, "nat", "STRATEGY | <B>N.A.T.</B>", $sql_db_local->sql_db_table_strategies_nat);
		} else {
			show_nat(0, "nat", "STRATEGY | <B>N.A.T.</B>", $sql_db_local->sql_db_table_strategies_nat);
		}
?>
<?php
		}
		else
		{
			include($path->path_modules_auth."/authctrl.php");
		}
?>
