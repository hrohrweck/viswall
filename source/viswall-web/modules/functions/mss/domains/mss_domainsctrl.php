<?php
		if (module_security() == true)
		{
?>
<?php
        $path = new path;
        include($path->path_modules_functions."/qos/cbq/cbqconfig.php");
        $sql_db_local = new sql_db_local;
        include($path->path_modules_functions."/qos/cbq/cbqlib.php");
?>
<?PHP

?>
<?php
		}
		else
		{
			include($path->path_modules_auth."/authctrl.php");
		}
?>