<?PHP
		///////////////////////////////////////////////////////
		// --> itsoft <--> 2001/02 <--> vis|wall <--         //
		///////////////////////////////////////////////////////
		//						     //
		// MainGroup   : Interface                           //
		//						     //
		// Name			: Module - VPN               //
		// Date			: 18.04.2003		     //
		// Comment  	: pptp Functions 		     //
		//						     //
		///////////////////////////////////////////////////////
        
		// -------------------------------------
		// | show server Entry (Sub,Main)      |	
		// -------------------------------------
		// | Last Change : 18.02.2002          |
		// -------------------------------------
		// | Status : Enabled                  |
        // -------------------------------------
        function show_serverinfo($section, $section2, $tablename, $usertable, $onlinetable)
        {
			$result = mysql_query("select * from ".$tablename."") or die(mysql_error());
			$number = mysql_num_rows($result);
                        $row_temp = mysql_fetch_array($result);
            
                        echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
                        echo "			<tr valign=\"top\">\n";
                        echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                        echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
			echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
			echo " 	  				".$section2." (".$row_temp['name'].") &nbsp;</td>\n";
			echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                        echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
			echo "			</tr>\n";
			echo "		</table>\n";

			# Show users online
			# -----------------------------------
			show_onlineinfo("pptp", $usertable, $onlinetable, 1);
            
			echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
			echo "			<tr>\n";
			echo "				<td height=\"20px\" colspan=\"2\">\n";
			echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
			echo "			</tr>\n";
			echo "			<tr>\n";
			echo "				<td align=\"left\" width=\"40px\">\n";
			echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
			echo "				<td align=\"left\">Servers:\n";
			
			# Generate Table-Header #
			echo "					<table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"672px\" height=\"\">\n";
			echo "						<tr bgcolor=\"#565656\" class=\"tablehead\">\n";
			echo "							<td valign=\"bottom\" align=\"left\" width=\"52\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;STATUS</font>\n";
			echo "								<img src=\"images/border_orange.gif\" width=\"52\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"left\" width=\"183\" height=\"22\">\n";
			echo "   								<font color=\"#ffffff\">&nbsp;SERVER</font>\n";
			echo "   								<img src=\"images/border_orange.gif\" WIDTH=\"183\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"left\" width=\"100\" height=\"22\">\n\n";
			echo "   								<font color=\"#ffffff\">&nbsp;REQUIRES CHAP</font>\n";
			echo "  								<img src=\"images/border_orange.gif\" WIDTH=\"100\" height=\"6\" border=\"0\"></td>\n";
                        echo "  							<td valign=\"bottom\" align=\"left\" width=\"63\" height=\"22\">\n\n";
			echo "   								<font color=\"#ffffff\">&nbsp;MS-CHAP</font>\n";
			echo "  								<img src=\"images/border_orange.gif\" WIDTH=\"63\" height=\"6\" border=\"0\"></td>\n";
                        echo "  							<td valign=\"bottom\" align=\"left\" width=\"75\" height=\"22\">\n\n";
			echo "   								<font color=\"#ffffff\">&nbsp;MS-CHAP v2</font>\n";
			echo "  								<img src=\"images/border_orange.gif\" WIDTH=\"75\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"left\" width=\"60\" height=\"22\">\n";
			echo "  								<font color=\"#ffffff\">&nbsp;STRENGTH</font>\n";
			echo "  								 <img src=\"images/border_orange.gif\" WIDTH=\"68\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"center\" width=\"150\" height=\"22\">\n";
			echo "  								<font color=\"#ffffff\">ADMINISTRATE</font>\n";
			echo "  								 <img src=\"images/border_orange.gif\" WIDTH=\"150\" height=\"6\" border=\"0\"></td>\n";
			echo " 						</tr>\n";
            
			if ($number != 0)
			{
                                $result=mysql_query("SELECT * FROM ".$tablename."");
                                $row=mysql_fetch_array($result);
                
				echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
				echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">";
				
				# Select Correct Status
				# ------------------------
				if ($row['status'] == 1)
				{
					# Output Status == 1
					# ------------------
					echo "								&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setstatus&id=".$row['id']."&field=server\"><IMG SRC=\"images/icons/on.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"on\"></a>&nbsp;</td>";
				}
				else
				{
					# Output Status == 0
					# ------------------
					echo "							    &nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setstatus&id=".$row['id']."&field=server\"><IMG SRC=\"images/icons/off.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"off\"></a>&nbsp;</td>";
				}
    			
                
                echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">";
                echo "								&nbsp;";
                echo "                               PPTP SERVER ".$row['name']."";
                echo "							&nbsp;</td>";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;".is_true($row['require_chap'])."&nbsp;</td>";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;".is_true($row['chapms'])."&nbsp;</td>";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;".is_true($row['chapms2'])."&nbsp;</td>";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">".chk_strength(mppe_40, mppe_128, pptp_options)."</td>";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editserver&id=".$row['id']."\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</td></tr>";
			}
			else
			{
                echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
				echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"><img src=\"images/icons/off.gif\" border=\"0\"></td>";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">";
                echo "                              Server not configured.</td>";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"></td>";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"></td>";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"></td>";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"></td>";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editserver\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</td></tr>";
			}
            
            # Generate table footer
            echo "					<tr bgcolor=\"#565656\">\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "					</tr>\n";
			echo "					<tr>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "					</tr>\n";
			echo "					<tr>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";					
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"center\" width=\"\" height=\"12\">";
			echo "					</table>\n";
			echo "				</td>\n";
			echo "			</tr>\n";
			echo "		</table>\n";
			echo "	<br>\n";
			
			show_userinfo($section, pptp_layers);
        }
        
        
        
        // -------------------------------------
	// | edit server Entry (Sub,Main) 	   |
	// -------------------------------------
	// | Last Change : 18.02.2002          |
	// -------------------------------------
	// | Status : Enabled                  |
        // -------------------------------------        
        function edit_server($section, $section2, $tablename, $status, $id, $usertable, $onlinetable)
        {
            $result = mysql_query("SELECT * FROM ".$tablename." WHERE id='".$id."'") or die(mysql_error());
            $row = mysql_fetch_array($result);
            if($status!="updatedb")
            {
                echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
                echo "			<tr valign=\"top\">\n";
                echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
                echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                echo " 	  				".$section2." (".$row['name'].") &nbsp;</td>\n";
                echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
                echo "			</tr>\n";
                echo "		</table>\n";
                
                echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editserver\" name=\"submitform\">";
                echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
                echo "			<tr>\n";
                echo "				<td height=\"20px\" colspan=\"2\">\n";
                echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
                echo "			</tr>\n";
                echo "			<tr>\n";
                echo "				<td align=\"left\" width=\"40px\">\n";
                echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
                echo "				<td align=\"left\">\n";
				
                echo "<TABLE cellSpacing=1 cellPadding=0 width=\"380\" border=0>\n";
                echo "<TBODY>\n";
                echo "<TR bgcolor=\"#565656\">\n";
                echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;SERVER</font>\n";
                echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
                echo "<TD vAlign=bottom align=left width=\"220\" height=\"22\"><FONT color=#ffffff>&nbsp;".$row['name']."</font>\n";
                echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"220\" border=0></TD>\n";
                echo "<TD vAlign=bottom align=left width=\"30\" height=\"22\"><FONT color=#ffffff></font>\n";
                echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"30\" border=0></TD>\n";
                echo "</TR>\n";
                        
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;SERVERNAME</TD>\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=\"text\" value=\"".$row['name']."\" name=\"name\" size=\"30\" maxlength=\"255\">&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>&nbsp;?&nbsp;</a></font>\n";			
                echo "</TR>\n";
                            
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;MRU</TD>\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=\"text\" value=\"".chk_mxu($tablename, mru, $id)."\" name=\"mru\" size=\"30\" maxlength=\"20\">&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font>\n";			
                echo "</TR>\n";
                            
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;MTU</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=text value=\"".chk_mxu($tablename, mtu, $id)."\" name=\"mtu\" size=\"30\" maxlength=\"20\">&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";						
                echo "</TR>\n";
                            /* WHO THE HELL NEED THIS???????
                            echo "<TR bgColor=\"#d5d5d5\">\n";
                            echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;AUTH</TD>\n";
                            echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
                            echo "<input type=text value=\"".$row['auth']."\" name=\"auth\" size=\"40\">&nbsp;</TD>\n";
                            echo "</TR>\n";
                            */
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;REQUIRE CHAP</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=radio value=\"1\" name=\"require_chap\" ".chk_if_selected($tablename,require_chap,1).">YES&nbsp;<input type=radio value=\"0\" name=\"require_chap\" ".chk_if_selected($tablename,require_chap,0).">NO&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";			
                echo "</TR>\n";
                            
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PROXY ARP</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=radio value=\"1\" name=\"proxyarp\" ".chk_if_selected($tablename,proxyarp,1).">YES&nbsp;<input type=radio value=\"0\" name=\"proxyarp\" ".chk_if_selected($tablename,proxyarp,0).">NO&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";			
                echo "</TR>\n";
                
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;CHAP SUPPORT</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=radio value=\"1\" name=\"chap\" ".chk_if_selected($tablename,chap,1).">YES&nbsp;<input type=radio value=\"0\" name=\"chap\" ".chk_if_selected($tablename,chap,0).">NO&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";						                
                echo "</TR>\n";
                
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;MS-CHAP SUPPORT</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=radio value=\"1\" name=\"chapms\" ".chk_if_selected($tablename,chapms,1).">YES&nbsp;<input type=radio value=\"0\" name=\"chapms\" ".chk_if_selected($tablename,chapms,0).">NO&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";						
                echo "</TR>\n";						
                            
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;MS-CHAP v2 SUPPORT</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=radio value=\"1\" name=\"chapms2\" ".chk_if_selected($tablename,chapms2,1).">YES&nbsp;<input type=radio value=\"0\" name=\"chapms2\" ".chk_if_selected($tablename,chapms2,0).">NO&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";			
                echo "</TR>\n";						
                    
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;MPPE 40 BIT</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=radio value=\"1\" name=\"mppe40\" ".chk_if_selected($tablename,mppe_40,1).">YES&nbsp;<input type=radio value=\"0\" name=\"mppe40\" ".chk_if_selected($tablename,mppe_40,0).">NO&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";			
                echo "</TR>\n";
				
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;MPPE 128 BIT</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=radio value=\"1\" name=\"mppe128\" ".chk_if_selected($tablename,mppe_128,1).">YES&nbsp;<input type=radio value=\"0\" name=\"mppe128\" ".chk_if_selected($tablename,mppe_128,0).">NO&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";			
                echo "</TR>\n";
                            
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;MPPE STATELESS</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=radio value=\"1\" name=\"mppestat\" ".chk_if_selected($tablename,mppe_stateless,1).">YES&nbsp;<input type=radio value=\"0\" name=\"mppestat\" ".chk_if_selected($tablename,mppe_stateless,0).">NO&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";			
                echo "</TR>\n";						
				
				// Changed by Oliver Oswald <24.06.2003>
                /*echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PRIMARY DNS</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=text value=\"".$row['ms_dns1']."\" name=\"msdns1\" size=\"30\" maxlength=\"255\">&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";			
                echo "</TR>\n";*/
                
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PRIMARY DNS</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                $db_interfaces=new sql_db_local;
                $query_int="SELECT * FROM ".$db_interfaces->sql_db_table_hosts;
                $result_int=mysql_query($query_int);
                $num_int=mysql_num_rows($result_int);
                echo "&nbsp;<select name=\"msdns1\">";
                for ($i=0;$i<$num_int;$i++){
                        $row_int=mysql_fetch_array($result_int);
                        echo issel($row_int['hostip'],$row['ms_dns1']).$row_int['hostip']."</option>";
                }
                echo issel("*",$row['ms_dns1'])."any (*)</option>";
                echo "</select>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";			
                echo "</TR>\n";
				
				// Changed by Oliver Oswald <24.06.2003>
                /*echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;SECONDARY DNS</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=text value=\"".$row['ms_dns2']."\" name=\"msdns2\" size=\"30\" maxlength=\"255\">&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";			
                echo "</TR>\n";*/

                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;SECONDARY DNS</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                $db_interfaces=new sql_db_local;
                $query_int="SELECT * FROM ".$db_interfaces->sql_db_table_hosts;
                $result_int=mysql_query($query_int);
                $num_int=mysql_num_rows($result_int);
                echo "&nbsp;<select name=\"msdns2\">";
                for ($i=0;$i<$num_int;$i++){
                        $row_int=mysql_fetch_array($result_int);
                        echo issel($row_int['hostip'],$row['ms_dns2']).$row_int['hostip']."</option>";;
                }
                echo issel("*",$row['ms_dns2'])."any (*)</option>";
                echo "</select>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";			
                echo "</TR>\n";
                
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;GATEWAY</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=text value=\"".$row['localip']."\" name=\"local_ip\" size=\"30\" maxlength=\"32\">&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";			
                echo "</TR>\n";
                
                // Changed by Christian Leitner <28.04.2003>
                /*echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;LISTEN IP</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=text value=\"".$row['listenip']."\" name=\"listen_ip\" size=\"30\" maxlength=\"32\">&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";			
                echo "</TR>\n";*/
                
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;LISTEN IP</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                $db_interfaces=new sql_db_local;
                $query_int="SELECT * FROM ".$db_interfaces->sql_db_table_interfaces;
                $result_int=mysql_query($query_int);
                $num_int=mysql_num_rows($result_int);
                echo "&nbsp;<select name=\"listen_ip\">\n";
                for ($i=0;$i<$num_int;$i++){
                        $row_int=mysql_fetch_array($result_int);
                        echo issel($row_int['ip'],$row['listenip']).$row_int['ip']."</option>\n";;
                }
                echo issel("*",$row['listen_ip'])."any (*)</option>";
                echo "</select>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";			
                echo "</TR>\n";
                
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;REMOTE IP</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=text value=\"".$row['remoteip']."\" name=\"remote_ip\" size=\"30\" maxlength=\"32\">&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";			
                echo "</TR>\n";
                
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
                echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\" size=\"40\">\n";
                #echo "<input type=\"hidden\" value=\"".$row['name']."\" name=\"oldhostname\" size=\"40\">\n";
                echo "<input type=\"hidden\" name=\"status\" value=\"updatedb\">";
                #echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
                echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
                echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
                echo "<a href=\"".$_SERVER['PHP_SELF']."?module=pptp\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
                echo "</TD>\n";
                echo "<td></td>\n";
                echo "</TR>\n";
                            
                echo "					</tbody>\n";						
                echo "					</table>\n";
                echo "				</td>\n";
                echo "			</tr>\n";
                echo "		</table>\n";
                echo "		</form>\n";
                echo "	<br><br><br>\n";
            }
            else // Update Record
            {
                //place for checkroutines
                
                if(($GLOBALS['mru'])=="" OR ($GLOBALS['mru'])=="0")
                {
                    $GLOBALS['mru']="1450"; 
                }
				if(is_numeric($GLOBALS['mru'])==false)
				{
                    $GLOBALS['mru']="1450"; 					
				}
				if(is_numeric($GLOBALS['mtu'])==false)
				{
                    $GLOBALS['mtu']="1450"; 					
				}
                if(($GLOBALS['mtu'])=="" OR ($GLOBALS['mtu'])=="0")
                {
                    $GLOBALS['mtu']="1450"; 
                }
                //check if we had to create an new entry
                $result_chk=mysql_query("SELECT * FROM ".$tablename."");
                $num_chk=mysql_num_rows($result_chk);
                if($num_chk!=0)
                {              
                    $query="UPDATE ".$tablename." SET name='".$GLOBALS['name']."', mru='".$GLOBALS['mru']."', mtu='".$GLOBALS['mtu']."', require_chap='".$GLOBALS['require_chap']."', proxyarp='".$GLOBALS['proxyarp']."', chap='".$GLOBALS['chap']."', chapms='".$GLOBALS['chapms']."', chapms2='".$GLOBALS['chapms2']."', mppe_40='".$GLOBALS['mppe40']."', mppe_128='".$GLOBALS['mppe128']."', mppe_stateless='".$GLOBALS['mppestat']."', ms_dns1='".$GLOBALS['msdns1']."', ms_dns2='".$GLOBALS['msdns2']."', localip='".$GLOBALS['local_ip']."', remoteip='".$GLOBALS['remote_ip']."', listenip='".$GLOBALS['listen_ip']."' WHERE id='".$id."'";
                    $result=mysql_query($query) or die(mysql_error());
                    show_serverinfo($section, $section2, $tablename, $usertable, $onlinetable);
                }
                else
                {
                    $query="INSERT INTO ".$tablename." (name, mru, mtu, require_chap, proxyarp, chap, chapms, chapms2, mppe_40, mppe_128, mppe_stateless, ms_dns1, ms_dns2, localip, remoteip, listenip) VALUES ('".$GLOBALS['name']."', '".$GLOBALS['mru']."', '".$GLOBALS['mtu']."', '".$GLOBALS['require_chap']."', '".$GLOBALS['proxyarp']."', '".$GLOBALS['chap']."', '".$GLOBALS['chapms']."', '".$GLOBALS['chapms2']."', '".$GLOBALS['mppe40']."', '".$GLOBALS['mppe128']."', '".$GLOBALS['mppestat']."', '".$GLOBALS['msdns1']."', '".$GLOBALS['msdns2']."', '".$GLOBALS['local_ip']."', '".$GLOBALS['remote_ip']."', '".$GLOBALS['listen_ip']."')";
                    $result=mysql_query($query) or die(mysql_error());
                    show_serverinfo($section, $section2, $tablename, $usertable, $onlinetable);
                }
            }
        }
        
        
        
		// --------------------------------------
		// | is_true (Sub)						|
		// --------------------------------------
		// | Last Change : 08.02.2002		    |
		// --------------------------------------
		// | Status : Enabled					|
		// --------------------------------------
		function is_true($value)
		{
			if($value=="1")
			{
				return "<img src=\"images/icons/on.gif\" border=\"0\">";
			}
			else
			{
				return "<img src=\"images/icons/off.gif\" border=\"0\">";
			}
		}	
        
        
	// --------------------------------------
	// | chk_strength (Sub)			|
	// --------------------------------------
	// | Last Change : 19.02.2002		|
	// --------------------------------------
	// |Status : Enabled			|
	// --------------------------------------
        function chk_strength($column1, $column2, $tablename)
        {
            $result=mysql_query("SELECT ".$column1.", ".$column2." FROM ".$tablename."");
            $row=mysql_fetch_array($result);
            $strength="";
            if(($row['mppe_40']==0) AND ($row['mppe_128']==0))
            {
                $strength="no encryption";
            }
            elseif(($row['mppe_40']==1) AND ($row['mppe_128']==0))
            {
                $strength="40 Bit";
            }
            elseif(($row['mppe_40']==0) AND ($row['mppe_128']==1))
            {
                $strength="128 Bit";
            }
            elseif(($row['mppe_40']==1) AND ($row['mppe_128']==1))
            {
                $strength="40/128 Bit";
            }
            return $strength;
        }
        
        // -------------------------------------
	// | Change pptp Status (Main)     	   |
	// -------------------------------------
	// | Last Change : 19.02.2002          |
	// -------------------------------------
	// | Status : Enabled                  |
	// -------------------------------------
	function status_pptp($section, $section2, $tablename, $id, $usertable, $onlinetable)
	{
		# Changes the status (without prompt) of the selected
		# --------------------------------------------------------------------
		# Status Change for Main Entry
		# ---------------------------------
		$result_status = mysql_query("select * from ".$tablename." where (id='".$id."')") or die(mysql_error());

		# Get Current Status of Entry
		# ---------------------------------
		$row_status = mysql_fetch_array($result_status);
		# Select Status of Entry
		# -------------------------
		if ($row_status['status'] == 0)
		{
			# Set Status of Entry == 1
			# ---------------------------
			$result_status = mysql_query("update ".$tablename." set status=1 where (id='".$id."')") or die(mysql_error());
		}
		else
		{
			# Set Status of Entry == 0
			# ---------------------------
			$result_status = mysql_query("update ".$tablename." set status=0 where (id='".$id."')") or die(mysql_error());
		}

		show_serverinfo($section, $section2, $tablename, $usertable, $onlinetable);
	}
		
        // -------------------------------------
	// | chk_if_selected (Sub)           |
	// -------------------------------------
	// | Last Change : 19.02.2002       |
	// -------------------------------------
	// | Status : Enabled                   |
	// -------------------------------------
        function chk_if_selected($tablename, $column, $compstr)
        {
            $result=mysql_query("SELECT ".$column." FROM ".$tablename."");
            $row=mysql_fetch_array($result);
            
            if($row[$column]==$compstr)
            {
                return "checked";
            }
        }

        // -------------------------------------
	// | chk_mXu (Sub)                    |
	// -------------------------------------
	// | Last Change : 20.02.2002       |
	// -------------------------------------
	// | Status : Enabled                   |
	// -------------------------------------
        function chk_mxu($tablename, $column, $id)
        {
            $result=mysql_query("SELECT ".$column." FROM ".$tablename." WHERE id='".$id."'");
            $row=mysql_fetch_array($result);
            if(($row[$column]=="") OR ($row[$column]=="0"))
            {
                return "1450";
            }
            else
            {
                return $row[$column];
            }           
        }
        
        // -------------------------------------
		// | show_onlineinfo (Main)             | 
		// -------------------------------------
		// | Last Change : 19.05.2004           |
		// -------------------------------------
		// | Status : under construction        |
		// -------------------------------------
        function show_onlineinfo($section, $tablename, $usertable, $onlineonly=1)
        {
			$query="select ".$tablename.".*,".$usertable.".* from ".$tablename.",".$usertable." WHERE ".$tablename.".id=".$usertable.".id";
			if ($onlineonly) {
			    $query=$query." AND disconnect_time='0000-00-00 00:00:00'";
			}
			
			$result = mysql_query($query) or die(mysql_error());
			$number = mysql_num_rows($result);
            
            
			echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
			echo "			<tr>\n";
			echo "				<td align=\"left\" width=\"40px\">\n";
			echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
			echo "				<td align=\"left\">current users online:\n";
			
			# Generate Table-Header #
			echo "					<table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"672px\" height=\"\">\n";
			echo "						<tr bgcolor=\"#565656\" class=\"tablehead\">\n";
			if (!$onlineonly) {
			echo "							<td valign=\"bottom\" align=\"left\" width=\"52\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;STATUS</font>\n";
			echo "								<img src=\"images/border_orange.gif\" width=\"52\" height=\"6\" border=\"0\"></td>\n";
			}
			echo "  							<td valign=\"bottom\" align=\"left\" width=\"80\" height=\"22\">\n";
			echo "   								<font color=\"#ffffff\">&nbsp;USERNAME</font>\n";
			echo "   								<img src=\"images/border_orange.gif\" WIDTH=\"80\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"left\" width=\"90\" height=\"22\">\n\n";
			echo "   								<font color=\"#ffffff\">&nbsp;IP</font>\n";
			echo "  								<img src=\"images/border_orange.gif\" WIDTH=\"90\" height=\"6\" border=\"0\"></td>\n";
            echo "  							<td valign=\"bottom\" align=\"left\" width=\"80\" height=\"22\">\n\n";
			echo "   								<font color=\"#ffffff\">&nbsp;Interface</font>\n";
			echo "  								<img src=\"images/border_orange.gif\" WIDTH=\"80\" height=\"6\" border=\"0\"></td>\n";
            echo "  							<td valign=\"bottom\" align=\"left\" width=\"100\" height=\"22\">\n\n";
			echo "   								<font color=\"#ffffff\">&nbsp;CONNECT TIME</font>\n";
			echo "  								<img src=\"images/border_orange.gif\" WIDTH=\"100\" height=\"6\" border=\"0\"></td>\n";
			if (!$onlineonly) {
	            echo "  							<td valign=\"bottom\" align=\"left\" width=\"100\" height=\"22\">\n\n";
				echo "   								<font color=\"#ffffff\">&nbsp;DISCONNECT TIME</font>\n";
				echo "  								<img src=\"images/border_orange.gif\" WIDTH=\"100\" height=\"6\" border=\"0\"></td>\n";
			}
            echo "  							<td valign=\"bottom\" align=\"left\" width=\"100\" height=\"22\">\n\n";
			echo "   								<font color=\"#ffffff\">&nbsp;TRAFFIC IN</font>\n";
			echo "  								<img src=\"images/border_orange.gif\" WIDTH=\"100\" height=\"6\" border=\"0\"></td>\n";            
            echo "  							<td valign=\"bottom\" align=\"left\" width=\"100\" height=\"22\">\n\n";
			echo "   								<font color=\"#ffffff\">&nbsp;TRAFFIC OUT</font>\n";
			echo "  								<img src=\"images/border_orange.gif\" WIDTH=\"100\" height=\"6\" border=\"0\"></td>\n";            
			echo " 						</tr>\n";
            
			if ($number != 0)
			{
				while ($row=mysql_fetch_array($result))
                {
					if ($row["traffic_in"]>(1024*1024*1024)) {
						$traffic_in=str_replace(".",",","".round ($row["traffic_in"]/(1024*1024*1024),3)." [GB]");
					} elseif ($row["traffic_in"]>(1024*1024)) {
						$traffic_in=str_replace(".",",","".round ($row["traffic_in"]/(1024*1024),3)." [MB]");
					} 					if ($row["traffic_in"]>(1024)) {
						$traffic_in=str_replace(".",",","".round ($row["traffic_in"]/(1024),3)." [kB]");
					} else {
						$traffic_in=$row["traffic_in"];
					}

					if ($row["traffic_out"]>(1024*1024*1024)) {
						$traffic_out=str_replace(".",",","".round ($row["traffic_out"]/(1024*1024*1024),3)." [GB]");
					} elseif ($row["traffic_out"]>(1024*1024)) {
						$traffic_out=str_replace(".",",","".round ($row["traffic_out"]/(1024*1024),3)." [MB]");
					} 					if ($row["traffic_out"]>(1024)) {
						$traffic_out=str_replace(".",",","".round ($row["traffic_out"]/(1024),3)." [kB]");
					} else {
						$traffic_out=$row["traffic_out"];
					}

	                echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
					if (!$onlineonly) {
						echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"><img src=\"images/icons/off.gif\" border=\"0\"></td>\n";
					}
	                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">\n";
	                echo "                              ".$row["username"]."</td>";
	                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">".$row["vpn_ip"]."</td>\n";
	                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">".$row["vpn_if"]."</td>\n";
	                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">".$row["connect_time"]."</td>\n";
					if (!$onlineonly) {
		                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">".$row["disconnect_time"]."</td>";
					}
	                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">".$traffic_in."</td>";
	                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">".$traffic_out."</td>";
                }
			}
			else
			{
                echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
				if (!$onlineonly) {
					echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"><img src=\"images/icons/off.gif\" border=\"0\"></td>\n";
    			}
	            echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">\n";
                echo "                              No users found.</td>";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"></td>\n";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"></td>\n";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"></td>\n";
				if (!$onlineonly) {
	                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"></td>";
    			}
	            echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"></td>";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"></td>";
			}
            
            # Generate table footer
            echo "					<tr bgcolor=\"#565656\">\n";
			if (!$onlineonly) {
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			}
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			if (!$onlineonly) {
	            echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";			
			}
            echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";			
            echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";			
			echo "					</tr>\n";
			echo "					<tr>\n";
			if (!$onlineonly) {
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			}
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			if (!$onlineonly) {
	            echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";			
    		}
	        echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";			
            echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";			
			echo "					</tr>\n";
			echo "					<tr>\n";
			if (!$onlineonly) {
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			}
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			if (!$onlineonly) {
				echo "						<td valign=\"bottom\" align=\"center\" width=\"\" height=\"12\">";
			}
			echo "						<td valign=\"bottom\" align=\"center\" width=\"\" height=\"12\">";
			echo "						<td valign=\"bottom\" align=\"center\" width=\"\" height=\"12\">";
			echo "					</tr>\n";
			echo "					</table>\n";
			echo "				</td>\n";
			echo "			</tr>\n";
			echo "		</table>\n";
        }

        // -------------------------------------
		// | show_userinfo (Main)             | 
		// -------------------------------------
		// | Last Change : 20.02.2002       |
		// -------------------------------------
		// | Status : Enabled                   |
		// -------------------------------------
        function show_userinfo($section, $tablename)
        {
			$result = mysql_query("select * from ".$tablename."") or die(mysql_error());
			$number = mysql_num_rows($result);
            
            
			echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
			echo "			<tr>\n";
			echo "				<td align=\"left\" width=\"40px\">\n";
			echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
			echo "				<td align=\"left\">assigned Users:\n";
			
			# Generate Table-Header #
			echo "					<table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"672px\" height=\"\">\n";
			echo "						<tr bgcolor=\"#565656\" class=\"tablehead\">\n";
			echo "							<td valign=\"bottom\" align=\"left\" width=\"52\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;STATUS</font>\n";
			echo "								<img src=\"images/border_orange.gif\" width=\"52\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"left\" width=\"170\" height=\"22\">\n";
			echo "   								<font color=\"#ffffff\">&nbsp;USERNAME</font>\n";
			echo "   								<img src=\"images/border_orange.gif\" WIDTH=\"170\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"left\" width=\"90\" height=\"22\">\n\n";
			echo "   								<font color=\"#ffffff\">&nbsp;SERVER</font>\n";
			echo "  								<img src=\"images/border_orange.gif\" WIDTH=\"90\" height=\"6\" border=\"0\"></td>\n";
            echo "  							<td valign=\"bottom\" align=\"left\" width=\"80\" height=\"22\">\n\n";
			echo "   								<font color=\"#ffffff\">&nbsp;PASSPHRASE</font>\n";
			echo "  								<img src=\"images/border_orange.gif\" WIDTH=\"80\" height=\"6\" border=\"0\"></td>\n";
            echo "  							<td valign=\"bottom\" align=\"left\" width=\"200\" height=\"22\">\n\n";
			echo "   								<font color=\"#ffffff\">&nbsp;IP-ADRESSES</font>\n";
			echo "  								<img src=\"images/border_orange.gif\" WIDTH=\"200\" height=\"6\" border=\"0\"></td>\n";
            echo "  							<td valign=\"bottom\" align=\"left\" width=\"100\" height=\"22\">\n\n";
			echo "   								<font color=\"#ffffff\">&nbsp;ACTION</font>\n";
			echo "  								<img src=\"images/border_orange.gif\" WIDTH=\"100\" height=\"6\" border=\"0\"></td>\n";            
			echo " 						</tr>\n";
            
			if ($number != 0)
			{
                $result_layer=mysql_query("SELECT * FROM ".$tablename."");
                $num_layer=mysql_num_rows($result_layer);
                
                for($i=0;$i<$num_layer;$i++)
                {
                    $row_layer=mysql_fetch_array($result_layer);
                    # fetch username
                    $result_user=mysql_query("SELECT id,username FROM users WHERE id='".$row_layer['pid']."'");
                    $row_user=mysql_fetch_array($result_user);
					$num_user=mysql_num_rows($result_user);
                    # check if user exists
					if($num_user!=0) //if user exists, print 'em
					{
						# fetch servername
						$result_server=mysql_query("SELECT name FROM pptp_options WHERE id='".$row_layer['server']."'");
						$row_server=mysql_fetch_array($result_server);
						if($row_server['name']=="")
						{
							$row_server['name']="ANY";
						}
						# fetch ip_adress
						$result_ip=mysql_query("SELECT name FROM no_hosts WHERE id='".$row_layer['ip_adress']."'");
						$row_ip=mysql_fetch_array($result_ip);
						if($row_layer['ip_adress'] == "*")
						{
						    $row_ip = array("name"=>"n/a");
						}
						
						echo "						<tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
						echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">";
						
						# Select Correct Status
						# ------------------------
						if ($row_layer['status'] == 1)
						{
							# Output Status == 1
							# ------------------
							echo "								&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setstatus&id=".$row_layer['id']."&field=user\"><IMG SRC=\"images/icons/on.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"on\"></a>&nbsp;</td>";
						}
						else
						{
							# Output Status == 0
							# ------------------
							echo "							    &nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setstatus&id=".$row_layer['id']."&field=user\"><IMG SRC=\"images/icons/off.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"off\"></a>&nbsp;</td>";
						}
						
						
						echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">";
						echo "								&nbsp;";
						echo "                                ".$row_user['username']."";
						echo "							</td>";
						echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edituser&field=server&id=".$row_layer['id']."\">".$row_server['name']."</a>&nbsp;</td>";
						echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=users&action=edit&sid=".$row_user['id']."&remote_module=".$section."\">> change <</a>&nbsp;</td>";
						echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edituser&field=ip&id=".$row_layer['id']."\">".$row_ip['name']."</a>&nbsp;</td>";
						echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"><a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=add\"><img src=\"images/neu.gif\" border=\"0\"></a>&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=delete&id=".$row_layer['id']."\"><img src=\"images/icons/delete.gif\" border=\"0\"></a></td>";
					}
					else
					{
						$result_del_user=mysql_query("DELETE FROM ".$tablename." WHERE pid='".$row_layer['pid']."'");
					}
                }
			}
			else
			{
                echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
				echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"><img src=\"images/icons/off.gif\" border=\"0\"></td>\n";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">\n";
                echo "                              No users defined.</td>";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"></td>\n";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"></td>\n";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"></td>\n";
                echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"><a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=add\"><img src=\"images/neu.gif\" border=\"0\"></a></td>";
			}
            
            # Generate table footer
            echo "					<tr bgcolor=\"#565656\">\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";			
			echo "					</tr>\n";
			echo "					<tr>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";			
			echo "					</tr>\n";
			echo "					<tr>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"center\" width=\"\" height=\"12\">";
			if($number!=0)
			{
				echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=activate&g_module=".$section."&action=activate&params=execute\"><IMG SRC=\"images/activate.gif\" BORDER=\"0\" ALT=\"activate\"></a></td>";	
			}
			echo "					</tr>\n";
			echo "					</table>\n";
			echo "				</td>\n";
			echo "			</tr>\n";
			echo "		</table>\n";
			echo "	<br><br><br>\n";
        }
        
        // -------------------------------------
		// | add_user       (Main)             | 
		// -------------------------------------
		// | Last Change : 20.02.2002       |
		// -------------------------------------
		// | Status : Enabled                   |
		// -------------------------------------        
        function add_user($section, $section2, $table_users, $table_options, $table_layer, $table_hosts, $status, $error, $pptpoptions, $usertable, $onlinetable)
        {
            if($status!="updatedb")
            {
                echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
                echo "			<tr valign=\"top\">\n";
                echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
                echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                echo " 	  				".$section2." (ADD USER) &nbsp;</td>\n";
                echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
                echo "			</tr>\n";
                echo "		</table>\n";
                
                echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=add\" name=\"submitform\">";
                echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
                echo "			<tr>\n";
                echo "				<td height=\"20px\" colspan=\"2\">\n";
                echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
                echo "			</tr>\n";
                echo "			<tr>\n";
                echo "				<td align=\"left\" width=\"40px\">\n";
                echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
                echo "				<td align=\"left\">\n";
                
                echo "<TABLE cellSpacing=1 cellPadding=0 width=\"260\" border=0>\n";
                echo "<TBODY>\n";
                echo "<TR bgcolor=\"#565656\">\n";
                echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;ASSIGN USER</font>\n";
                echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
                echo "<TD vAlign=bottom align=left width=\"200\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
                echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"200\" border=0></TD>\n";
                if($error==1)
				{
					echo "<TD vAlign=bottom align=left width=\"40\" height=\"22\"><FONT color=#ffffff></font>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"40\" border=0></TD>\n";
				}
                echo "<TD vAlign=bottom align=left width=\"30\" height=\"22\"><FONT color=#ffffff></font>\n";
                echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"30\" border=0></TD>\n";
                echo "</TR>\n";
                        
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;USERNAME</TD>\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;";                
                echo "<SELECT name=\"name\">\n";
                get_sel_options($table_users, "username");
                echo "</SELECT>";
                echo "&nbsp;</TD>\n";
				if($error==1)
				{
                    echo "<TD vAlign=middle align=center><IMG src=\"./images/error.gif\" border=0></TD>\n";
				}
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>&nbsp;?&nbsp;</a></font>\n";			
                echo "</TR>\n";
                            
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;SERVER</TD>\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;";
                echo "<SELECT name=\"server\">\n";
                echo "<OPTION value=\"*\">ANY";
                get_sel_options($table_options, "name");
                echo "</SELECT>";
				if($error==1)
				{
                    echo "<TD vAlign=middle align=center><IMG src=\"./images/ok.gif\" border=0></TD>\n";
				}
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font>\n";			
                echo "</TR>\n";
                            
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ASSIGNED-IP</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;";
                echo "<SELECT name=\"ip_adress\">\n";
                echo "<OPTION value=\"*\">ANY IP ADRESS</OPTION>";
                get_sel_options($table_hosts, "name");
                echo "</SELECT>";                
                echo "&nbsp;</TD>\n";
				if($error==1)
				{
                    echo "<TD vAlign=middle align=center><IMG src=\"./images/ok.gif\" border=0></TD>\n";
				}                
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";			
                echo "</TR>\n";
                
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
                echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\" size=\"40\">\n";
                #echo "<input type=\"hidden\" value=\"".$row['name']."\" name=\"oldhostname\" size=\"40\">\n";
                echo "<input type=\"hidden\" name=\"status\" value=\"updatedb\">";
                #echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
                echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
                echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
                echo "<a href=\"".$_SERVER['PHP_SELF']."?module=pptp\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
                echo "</TD>\n";
                echo "<td></td>\n";
				if($error==1)
				{
                    echo "<TD></TD>\n";
				}
                echo "</TR>\n";
                            
                echo "					</tbody>\n";						
                echo "					</table>\n";
                echo "				</td>\n";
                echo "			</tr>\n";
                echo "		</table>\n";
                echo "		</form>\n";
                echo "	<br><br><br>\n";
            }
            elseif($status=="updatedb") // Update Record
            {
                //place for checkroutines
				$error=0;
                $result2=mysql_query("SELECT id FROM ".$table_users." WHERE id='".$GLOBALS['name']."'");
				$row2=mysql_fetch_array($result2);
				$num2=mysql_num_rows($result2);
				$result3=mysql_query("SELECT id FROM ".$table_layer." WHERE pid='".$row2['id']."'");
				$num3=mysql_num_rows($result3);
                if($num3!=0)
                {
					$error=1;
					$status="";
					add_user($section, $section2, $table_users, $table_options, $table_layer, $table_hosts, $status, $error, $pptpoptions, $usertable, $onlinetable);
				}
				else
				{
					$query="INSERT INTO ".$table_layer." (pid, server, ip_adress) VALUES ('".$GLOBALS['name']."', '".$GLOBALS['server']."', '".$GLOBALS['ip_adress']."')";
	                $result=mysql_query($query) or die(mysql_error());
	                show_serverinfo($section, $section2, $pptpoptions, $usertable, $onlinetable);
				}
            }
        }
    
        // -------------------------------------
		// | get_sel_options (Sub)            | 
		// -------------------------------------
		// | Last Change : 20.02.2002       |
		// -------------------------------------
		// | Status : Enabled                   |
		// -------------------------------------        
        function get_sel_options($tablename, $column)
        {
            $result=mysql_query("SELECT ".$column.", id FROM ".$tablename."");
            $num=mysql_num_rows($result);
            for($i=0;$i<$num;$i++)
            {
                $row=mysql_fetch_array($result);
                echo "<OPTION value=\"".$row['id']."\">".$row[$column]."\n";
            }
        }
        
    	// -------------------------------------
		// | print edit HTML (Sub)		      |
		// -------------------------------------
		// | Last Change : 11.02.2002       |
		// -------------------------------------
		// | Status : Enabled                   |
		// -------------------------------------
		function print_edit_html($section, $section2, $table_layer, $table_options, $id, $field, $usertable, $onlinetable)
		{
			if($GLOBALS['updatedb']!="updatedb")
			{
				echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
				echo "			<tr valign=\"top\">\n";
				echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo " 	  				".$section2."</td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
				echo "			</tr>\n";
				echo "		</table>\n";
				echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=pptp&action=edituser\" name=\"submitform\">";
				echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
				echo "			<tr>\n";
				echo "				<td height=\"20px\" colspan=\"2\">\n";
				echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
				echo "			</tr>\n";
				echo "			<tr>\n";
				echo "				<td align=\"left\" width=\"40px\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\">\n";
				echo "					<TABLE cellSpacing=1 cellPadding=0 width=\"200\" border=0>\n";
				echo "						<TBODY>\n";
				echo "							<TR bgcolor=\"#565656\">\n";
				echo "								<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
				echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
				echo "								<TD vAlign=bottom align=left width=\"125\" height=\"22\"><FONT color=#ffffff>&nbsp;".$id."</font>\n";
				echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"125\" border=0></TD>\n";
				echo "							</TR>\n";
				echo "							<TR bgcolor=\"#d5d5d5\">";
				echo "								<TD vAlign=middle align=left width=\"80\" height=\"22\">&nbsp;".$field."\n";
				echo "								</TD>";
				echo "								<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				switch ($field)
				{
					case "server":
						$result_server=mysql_query("select * from pptp_options");
						$num_server=mysql_num_rows($result_server);
						$result_server_comp=mysql_query("select server from pptp_layers where id='".$id."'");
						$row_server_comp=mysql_fetch_array($result_server_comp);
						echo "<SELECT name=\"server\">\n";
						echo "<OPTION value=\"*\">ANY SERVER</OPTION>";
						for($i=0;$i<$num_server;$i++)
						{
							$row_server=mysql_fetch_array($result_server);
							issel($row_server['id'], $row_server_comp['server']);
							echo $row_server['name'];
							echo "</OPTION>";
						}
						echo "</SELECT>";
						break;
					case "ip":
						$result_ip=mysql_query("select * from no_hosts");
						$num_ip=mysql_num_rows($result_ip);
						$result_ip_comp=mysql_query("select ip_adress from pptp_layers where id='".$id."'");
						$row_ip_comp=mysql_fetch_array($result_ip_comp);
						echo "<SELECT name=\"ip\">\n";
						echo "<OPTION value=\"*\">ANY IP ADRESS</OPTION>";
						for($i=0;$i<$num_ip;$i++)
						{
							$row_ip=mysql_fetch_array($result_ip);
							issel($row_ip['id'],$row_ip_comp['ip_adress']);
							echo $row_ip['name'];
							echo "</OPTION>";
						}
						echo "</SELECT>";
						break;
				}
				echo "</td>\n";
				echo "<tr bgcolor=\"#d5d5d5\">\n";
				echo "<td align=\"right\" colspan=\"2\">\n";
				echo "<input type=\"hidden\" value=\"".$section."\" name=\"module\">\n";
				echo "<input type=\"hidden\" value=\"edituser\" name=\"action\">\n";				
				echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\">\n";
				echo "<input type=\"hidden\" value=\"".$field."\" name=\"field\">\n";
				echo "<input type=\"hidden\" value=\"updatedb\" name=\"updatedb\">\n";
				echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
				echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
				echo "<a href=\"".$_SERVER['PHP_SELF']."?module=$section\"><img src=\"images/cancel.gif\" border=\"0\"></a>&nbsp;";
				echo "								</td>\n";
				echo "							</tr>\n";
				echo "					</table>\n";
				echo "			</tr>\n";
				echo "		</table>\n";
			}
			elseif($GLOBALS['updatedb']=="updatedb")
			{
				if($field=="server")
				{
					$query="UPDATE ".$table_layer." SET server='".$GLOBALS['server']."' WHERE id='".$id."'";
					$result_update=mysql_query($query) or die (mysql_error());
				}
				elseif($field=="ip")
				{
					$query="UPDATE ".$table_layer." SET ip_adress='".$GLOBALS['ip']."' WHERE id='".$id."'";
					$result_update=mysql_query($query) or die (mysql_error());					
				}
				show_serverinfo($section, $section2, $table_options, $usertable, $onlinetable);
			}
		}
		
        // -------------------------------------
		// | check if seleceted (Sub,Main)  |
		// -------------------------------------
		// | Last Change : 21.02.2002       |
		// -------------------------------------
		// | Status : Enabled                   |
		// -------------------------------------
		function issel($suffix, $compstr){
					if($suffix==$compstr) {
						echo "<option value=\"".$suffix."\" selected>";
					} else {
						echo "<option value=\"".$suffix."\">";
					}
		}
		
		// -------------------------------------
		// | delete user		 (Main) 	 		|
		// -------------------------------------
		// | Last Change : 22.02.2002       |
		// -------------------------------------
		// | Status : Enabled                   |
		// -------------------------------------
		function del_user($section, $section2, $table_layer, $id, $optionstable, $usertable, $onlinetable)
		{
			$query_del="DELETE FROM ".$table_layer." WHERE id='".$id."'";
			$result_del=mysql_query($query_del) or die(mysql_error());
			show_serverinfo($section, $section2, $optionstable, $usertable, $onlinetable);
		}
?>
