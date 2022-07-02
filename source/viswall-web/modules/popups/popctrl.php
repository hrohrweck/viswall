<?php
		///////////////////////////////////////////
		// ---> DOMedia - vis|wall Firewall <--- //
		///////////////////////////////////////////
		// Date			: 04.03.2002			 //
    	///////////////////////////////////////////

        $path = new path;
        include($path->path_modules_popups."/popconfig.php");
        $sql_db_local = new sql_db_local;
        include($path->path_modules_popups."/poplib.php");

        switch($action)
        {
            case example:
                include($path->path_modules_popups."/example/example.php");
                break;
        	default:
                //include($path->path_modules_auth."/authctrl.php");
                break;
        }
?>