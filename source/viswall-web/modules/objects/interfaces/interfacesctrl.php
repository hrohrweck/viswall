<?php
		if (module_security() == true)
		{
?>
<?php
        $path = new path;
        include($path->path_modules_objects."/interfaces/interfacesconfig.php");
        $sql_db_local = new sql_db_local;
        include($path->path_modules_objects."/interfaces/interfaceslib.php");
?>
<?php
		if (!isset($_GET['action']) or $GLOBALS['action'] == "list")
		{
			# List & Show Objects #
			show_objects_interfaces(0, "interfaces", "OBJECTS | <b> INTERFACES </b>", $sql_db_local->sql_db_table_io_interfaces);
		}
		elseif ($_GET['action'] == "add")
		{
			# Add new Object #
			add_objects_interfaces(0, "interfaces", "OBJECTS | <b> INTERFACES </b>", $sql_db_local->sql_db_table_io_interfaces, $_POST['io_submit']);
		}
		elseif($_GET['action'] == "edit")
		{
			# Edit Object #
			edit_objects_interfaces(0, "interfaces", "OBJECTS | <b> INTERFACES </b>", $sql_db_local->sql_db_table_io_interfaces, $_GET['sid'], $_POST['io_change']);
		}
		elseif($_GET['action'] == "editgw")
		{
			# Edit Gateway Object #
			edit_objects_interfaces_gw(0, "interfaces", "OBJECTS | <b> INTERFACES </b>", $sql_db_local->sql_db_table_io_gateway, $_POST['status']);
		}
		elseif($_GET['action'] == "delete")
		{
		    secure_delete("interfaces", $sql_db_local->sql_db_table_io_interfaces, $_GET['sid'], $_GET['sd_override']);
		}
		elseif($_GET['action'] == "test")
		{
            gateipcompare();
		}
?>
<?php
		}
		else
		{
			include($path->path_modules_auth."/authctrl.php");
		}
?>
