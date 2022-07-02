<?php
		////////////////////////////////////////////////
		// --> DOMedia <--> 2001/02 <--> vis|wall <-- //
		////////////////////////////////////////////////
		//											  //
		// MainGroup	: Interface					  //
		//											  //
		// Name			: Module Authentication		  //
		// Date			: 06.03.2002				  //
		// Comment		: Authentication Module		  //
		//											  //
		////////////////////////////////////////////////
		
		// ---------------------------------
		// | Generate LogonPage (Template) |
		// ---------------------------------
		// | Last Change : 06.03.2002	   |
		// ---------------------------------
		// | Status : Enabled			   |
		// ---------------------------------
		function generate_logonpage()
		{
			include("./templates/logonpage.html");
		}
		
		// ----------------------------
		// | Check LogonPage		  |
		// ----------------------------
		// | Last Change : 06.03.2002 |
		// ----------------------------
		// | Status : Enabled		  |
		// ----------------------------
		function check_logonpage()
		{
      $query = mysql_query("select * from ".$GLOBALS['sql_db_local']->sql_db_table_users." where (username='".$_POST['auth_user']."' and password='".$_POST['auth_password']."' and isroot='1')");
			$row = mysql_fetch_array($query);
		
			if (!empty($row))
			{
				# Workaround for PopUp Issue
				generate_html(1);
				
				# Valid UserData
				$session_magic = generate_session_magic();
				$username = $_POST['auth_user'];
				$database = $GLOBALS['sql_db_local']->sql_db_table_users;
				$query = mysql_query("update ".$GLOBALS['sql_db_local']->sql_db_table_users." set magic='".$session_magic."' where (username='".$_POST['auth_user']."' and password='".$_POST['auth_password']."')");
				
				$_SESSION['session_magic'] = $session_magic;
				$_SESSION['username'] = $username;
				$_SESSION['database'] = $database;
			}
			else
			{
				# Invalid UserData
				include("./templates/logonpage.html");
			}
		}
		
		// ------------------------------
		// | Generate Session Magic Key |
		// ------------------------------
		// | Last Change : 06.03.2002	|
		// ------------------------------
		// | Status : Enabled			|
		// ------------------------------
		function generate_session_magic()
		{
			list($usec, $sec) = explode(" ",microtime());
			return md5(((float)$usec + (float)$sec)*10000); 
		}
?>
