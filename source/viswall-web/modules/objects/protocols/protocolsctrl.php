<?php
		if (module_security() == true)
		{
?>
<?php
        $path = new path;
        include($path->path_modules_objects."/protocols/protocolsconfig.php");
        $sql_db_local = new sql_db_local;
        include($path->path_modules_objects."/protocols/protocolslib.php");
?>
<?php
		if (!isset($_GET['action']) or $_GET['action'] == "list")
		{
			# List & Show Objects #
			show_objects_protocols(0, "protocols", "OBJECTS | <B>PROTOCOLS</B>", $sql_db_local->sql_db_table_po_protocols);
		}
		elseif ($_GET['action'] == "add")
		{
			# Add new Object #
			add_objects_protocols(0,"protocols", "OBJECTS | <B>PROTOCOLS</B>", $sql_db_local->sql_db_table_po_protocols, $_POST['po_submit']);
		}
		elseif($_GET['action'] == "edit")
		{
			# Edit Object #
			edit_objects_protocols(0, "protocols", "OBJECTS | <B>PROTOCOLS</B>", $sql_db_local->sql_db_table_po_protocols, $_GET['pid'], $_POST['po_change']);
		}
		elseif($_GET['action'] == "delete")
		{
			# Secure Delete Object #
			secure_delete("protocols", $sql_db_local->sql_db_table_po_protocols, $_GET['pid'], $_GET['sd_override']);
		}
		elseif($_GET['action'] == "show")
		{
			# Protocol Analyzer and Editor #
			protalizer("services", "OBJECTS | <B>SERVICES</B>", $sql_db_local->sql_db_table_po_layers, $GLOBALS['sid'], $sql_db_local->sql_db_table_po_protocols, $GLOBALS['method']);
		}
?>
<?php
		}
		else
		{
			include($path->path_modules_auth."/authctrl.php");
		}
?>
