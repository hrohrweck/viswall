<?php
		if (module_security() == true)
		{
?>
<?php        
			$path = new path;
			include($path->path_modules_objects."/users/usersconfig.php");
			$sql_db_local = new sql_db_local;
			include($path->path_modules_objects."/users/userslib.php");
?>
<?php
			if ((!isset($_GET['action'])) or ($_GET['action'] == "list"))
			{
				# List & Show Objects #
				show_users("users", "OBJECTS | <B>USERS</B>", $sql_db_local->sql_db_table_users);
			}
			elseif ($_GET['action'] == "add")
			{
				# Add new Object #
				add_users("users",  "OBJECTS | <B>USERS</B>", $sql_db_local->sql_db_table_users, $_POST['users_submit']);
			}
			elseif($_GET['action'] == "edit")
			{
				# Edit Object #
				edit_users("users", "OBJECTS | <B>USERS</B>", $sql_db_local->sql_db_table_users, $_GET['sid'], $_POST['users_change'], $GLOBALS['remote_module']);
			}
			elseif($_GET['action'] == "delete")
			{
				# Secure Delete Object #
				secure_delete("users", $sql_db_local->sql_db_table_users, $_GET['sid'], $_GET['sd_override']);
			}				
			elseif($_GET['action'] == "setroot")
			{
				$result = mysql_query("select * from ".$sql_db_local->sql_db_table_users." where (id='".$_GET['sid']."')");
				$row = mysql_fetch_array($result);
				
				if ($row['issticky'] != 1)
				{
					$result = mysql_query("update ".$sql_db_local->sql_db_table_users." set isroot='".$_GET['root']."' where (id='".$_GET['sid']."')");
					$result = mysql_query("update ".$sql_db_local->sql_db_table_users." set magic='".generate_magic()."' where (id='".$_GET['sid']."')");
				}
				
				show_users("users", "OBJECTS | <B>USERS</B>", $sql_db_local->sql_db_table_users);
			}
?>
<?php
		}
		else
		{
			include($path->path_modules_auth."/authctrl.php");
		}
?>
