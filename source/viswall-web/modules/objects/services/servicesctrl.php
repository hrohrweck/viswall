<?php
		if (module_security() == true)
		{
?>
<?php
        $path = new path;
        include($path->path_modules_objects."/services/servicesconfig.php");
        $sql_db_local = new sql_db_local;
        include($path->path_modules_objects."/services/serviceslib.php");
?>
<?php
		if (!isset($_GET['action']) or $_GET['action'] == "list")
		{
			# List & Show Objects #
			show_objects_services(0, "services", "OBJECTS | <B>SERVICES</B>", $sql_db_local->sql_db_table_so_services);
		}
		elseif ($_GET['action'] == "add")
		{
			# Add new Object #
			add_objects_services(0,"services", "OBJECTS | <B>SERVICES</B>", $sql_db_local->sql_db_table_so_services, $_POST['so_submit']);
		}
		elseif($_GET['action'] == "edit")
		{
			# Edit Object #
			edit_objects_services(0, "services", "OBJECTS | <B>SERVICES</B>", $sql_db_local->sql_db_table_so_services, $_GET['sid'], $_POST['so_change']);
		}
		elseif($_GET['action'] == "delete")
		{
			# Secure Delete Object #
			secure_delete("services", $sql_db_local->sql_db_table_so_services, $_GET['sid'], $_GET['sd_override']);
		}
		elseif($_GET['action'] == "show")
		{
			# Protocol Analyzer and Editor #
			protalizer("services", "OBJECTS | <B>SERVICES</B>", $sql_db_local->sql_db_table_po_layers, $_GET['sid'], $sql_db_local->sql_db_table_po_protocols, $GLOBALS['method']);
		}
?>
<?php
		}
		else
		{
			include($path->path_modules_auth."/authctrl.php");
		}
?>
