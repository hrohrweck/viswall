<?php
		///////////////////////////////////////////
		// ---> DOMedia - vis|wall Firewall <--- //
		///////////////////////////////////////////
		// Date : 07.03.2002					 //
		///////////////////////////////////////////
		
		$GLOBALS['path'] = new path;
		include($GLOBALS['path']->path_modules_auth."/authconfig.php");
		$sql_db_local = new sql_db_local;
		include($GLOBALS['path']->path_modules_auth."/authlib.php");
?>
<?php
	if (!isset($_POST['auth_hidden']))
		generate_logonpage();
	else
		check_logonpage();
?>