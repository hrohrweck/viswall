<?php
		if (module_security() == true)
		{
?>
<?php
        $path = new path;
        include($path->path_modules_objects."/ranges/rangesconfig.php");
        $sql_db_local = new sql_db_local;
        include($path->path_modules_objects."/ranges/rangeslib.php");
?>
<?php
		if ((!isset($_GET['action'])) or ($_GET['action'] == "list"))
		{
			# List & Show Objects #
			show_objects_rangesobjects(1, "ranges", "OBJECTS | <B>ranges</B>", $sql_db_local->sql_db_table_no_ranges);
		}
		elseif ($_GET['action'] == "add")
		{
			# Add new Object #
			add_objects_rangesobjects(1,"ranges",  "OBJECTS | <B>ranges</B>", $sql_db_local->sql_db_table_no_ranges, $_POST['no_submit']);
		}
		elseif($_GET['action'] == "edit")
		{
			# Edit Object #
			edit_objects_rangesobjects(1, "ranges", "OBJECTS | <B>ranges</B>", $sql_db_local->sql_db_table_no_ranges, $_GET['sid'], $_POST['no_change']);
		}
		elseif($_GET['action'] == "delete")
		{
			# Secure Delete Object #
			secure_delete("ranges", $sql_db_local->sql_db_table_no_ranges, $_GET['sid'], $_GET['sd_override']);
		}				
?>
<?php
		}
		else
		{
			include($path->path_modules_auth."/authctrl.php");
		}
?>
