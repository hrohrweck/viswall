<?php
		if (module_security() == true)
		{
?>
<?php
        $path = new path;
        include($path->path_modules_objects."/networks/networksconfig.php");
        $sql_db_local = new sql_db_local;
        include($path->path_modules_objects."/networks/networkslib.php");
?>
<?php
		if ((!isset($_GET['action'])) or ($_GET['action'] == "list"))
		{
			# List & Show Objects #
			show_objects_networkobjects(1, "networks", "OBJECTS | <B>NETWORKS</B>", $sql_db_local->sql_db_table_no_networks);
		}
		elseif ($_GET['action'] == "add")
		{
			# Add new Object #
			add_objects_networkobjects(1,"networks",  "OBJECTS | <B>NETWORKS</B>", $sql_db_local->sql_db_table_no_networks, $_POST['no_submit']);
		}
		elseif($_GET['action'] == "edit")
		{
			# Edit Object #
			edit_objects_networkobjects(1, "networks", "OBJECTS | <B>NETWORKS</B>", $sql_db_local->sql_db_table_no_networks, $_GET['sid'], $_POST['no_change']);
		}
		elseif($_GET['action'] == "delete")
		{
			# Secure Delete Object #
			secure_delete("networks", $sql_db_local->sql_db_table_no_networks, $_GET['sid'], $_GET['sd_override']);
		}				
?>
<?php
		}
		else
		{
			include($path->path_modules_auth."/authctrl.php");
		}
?>
