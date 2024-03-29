<?php
		///////////////////////////////////////////////////////
		//                 --> vis|wall <--                  //
		///////////////////////////////////////////////////////
		//																//
		// MainGroup   : Interface                             //
		//																//
		// Name			: Module - Interfaces       			//
		// Date			: 01.02.2002							//
		// Comment  	: Object Interfaces					//
		//																//
		///////////////////////////////////////////////////////
        
		function getGWConfig () {
			exec ("/sbin/route -n |/usr/bin/egrep -e '^0.0.0.0' |/bin/cut -d ' ' -f 10", $ausgabe);
			
			if (!trim ($ausgabe[0])) {
			    return "N/A";
			}
			
			return $ausgabe[0];			
		}
		
		function getIPConfig ($interface) {
			exec("/sbin/ifconfig ".$interface." |/bin/grep 'inet addr' |/bin/cut -d':' -f 2,4 |/usr/bin/sed 's/  Bcast:/\//g'",$ausgabe);
			
			if (!trim ($ausgabe[0])) {
			    return "N/A";
			}
			
			return $ausgabe[0];
		}

       	// ---------------------------------
		// | show objects interfaces (Main)|
		// ---------------------------------
		// | Last Change : 12.02.2002	   |
		// ---------------------------------
		// | Status : Enabled		   |
		// ---------------------------------
		function show_objects_interfaces($type, $section, $section2, $tablename)
		{
			$result = mysql_query("select * from ".$tablename." order by id");
			$number = mysql_num_rows($result);
			
			echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
                        echo "			<tr valign=\"top\">\n";
                        echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                        echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
			echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
			echo " 	  				".$section2." (".$number.") &nbsp;</td>\n";
			echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                        echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
			echo "			</tr>\n";
			echo "		</table>\n";
			
			echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
			echo "			<tr>\n";
			echo "				<td height=\"20px\" colspan=\"2\">\n";
			echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
			echo "			</tr>\n";
			echo "			<tr>\n";
			echo "				<td align=\"left\" width=\"40px\">\n";
			echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
			echo "				<td align=\"left\">\n";
			
			// Display-Type (Simple, Advanced)
			switch ($type)
			{
				// Display Simple
				case 0:
				{
					// Generate Table-Header
					echo "<TABLE cellSpacing=1 cellPadding=0 width=911 border=0>\n";
					echo "<TBODY>\n";
					echo "<TR class=tablehead bgColor=#565656>\n";
					echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;NAME</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"250\" height=\"22\"><FONT color=#ffffff>&nbsp;NOTE</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"260\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"110\" height=\"22\"><FONT color=#ffffff>&nbsp;IP</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"110\" height=\"22\"><FONT color=#ffffff>&nbsp;NETMASK</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;ACTION</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"211\" height=\"22\"><FONT color=#ffffff>&nbsp;CURRENT IP</FONT><br>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
					echo "</TR>\n";
					
					// Read and Display Database Entries					
					for ($i=0; $i < $number; $i++)
					{
						$row = mysql_fetch_array($result);
						
						if (is_float(($i/2)) == false)
							echo "						<tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
						else
							echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
						
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['name']."</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['note']."</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['ip']."</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['netmask']."</TD>\n";
						echo "<TD vAlign=middle align=middle width=\"\" height=\"22\">\n";
						echo "&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=interfaces&action=edit&sid=".$row['id']."\"><IMG SRC=\"./images/icons/edit_gr.gif\" WIDTH=\"22\" HEIGHT=\"16\" BORDER=0 ALT=\"edit\"></a>\n";
						
						if ($row['sticky'] == 1)
						{
							echo "&nbsp;</TD>\n";
						}
						else
						{
							echo "<a href=\"".$_SERVER['PHP_SELF']."?module=interfaces&action=delete&sid=".$row['id']."&sd_override=no\"><IMG SRC=\"./images/icons/delete.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=0 ALT=\"delete\"></a>&nbsp;</TD>\n";
						}
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".getIPConfig($row['name'])."</TD>\n";
						
						echo "</TR>\n";
					}
					
					echo "					<tr bgcolor=\"#565656\">\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "					</tr>\n";
					echo "					<TR>\n";
					echo "						<td valign=bottom align=left height=20 colspan=\"4\">&nbsp;</td>\n";
					echo "						<td valign=bottom align=center height=20><a href=\"".$_SERVER['PHP_SELF']."?module=interfaces&action=add\"><IMG SRC=\"./images/add_entry_gr.gif\" BORDER=0 ALT=\"add entry\"></a></td>\n";
					echo "						<td valign=bottom align=center height=20><a href=\"".$_SERVER['PHP_SELF']."?module=activate&g_module=".$section."&action=activate&params=execute\"><IMG SRC=\"images/activate.gif\" BORDER=\"0\" ALT=\"activate\"></a></td>\n";
					echo "					</TR>\n";
					echo "					</table>\n";
					echo "					</tbody>\n";
					echo "				</td>\n";
					echo "			</tr>\n";
					echo "		</table>\n";
					echo "	<br><br><br>\n";
					break;
				}
			}
			show_gateway($section,$tablename);
		}
		
		// ---------------------------------
		// | show Gateway (Sub,Main)       |
		// ---------------------------------
		// | Last Change : 12.02.2002	   |
		// ---------------------------------
		// | Status : Enabled		   |
		// ---------------------------------
		function show_gateway($section,$tablename)
		{
		    # get gateway information
		    $result = mysql_query("SELECT * FROM io_gateway");
		    $row = mysql_fetch_array($result);
		    
			echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\">\n";
			echo "			<tr>\n";
			echo "				<td align=\"left\" width=\"40px\">\n";
			echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
			echo "				<td align=\"left\">\n";
			
			# Generate Table-Header #
			echo "					<table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"530px\" height=\"\">\n";
			echo "						<tr bgcolor=\"#565656\" class=\"tablehead\">\n";
			echo "							<td valign=\"bottom\" align=\"left\" width=\"130\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;</font>\n";
			echo "								<img src=\"images/border_orange.gif\" width=\"130\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"left\" width=\"150\" height=\"22\">\n";
			echo "   								<font color=\"#ffffff\">&nbsp;VALUE</font>\n";
			echo "   								<img src=\"images/border_orange.gif\" WIDTH=\"150\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"left\" width=\"100\" height=\"22\">\n";
			echo "   								<font color=\"#ffffff\">&nbsp;ADMINISTRATE</font>\n";
			echo "   								<img src=\"images/border_orange.gif\" WIDTH=\"100\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"left\" width=\"150\" height=\"22\">\n";
			echo "   								<font color=\"#ffffff\">&nbsp;CURRENT VALUE</font>\n";
			echo "   								<img src=\"images/border_orange.gif\" WIDTH=\"150\" height=\"6\" border=\"0\"></td>\n";
			echo " 						</tr>\n";
			#  Generate table data
			echo "						<tr bgcolor=\"#d5d5d5\">\n";
			echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">&nbsp;default Gateway:</td>\n";
			echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">".$row['adress']."</td>\n";
			echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editgw\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</td>\n";
			echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">".getGWConfig()."</td>\n";
			echo "						</tr>";
            # Generate table footer
            echo "					<tr bgcolor=\"#565656\">\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "					</tr>";
		}
		
		// ---------------------------------
		// | Edit Interfaces Gateway (Main)|
		// ---------------------------------
		// | Last Change : 12.02.2002	   |
		// ---------------------------------
		// | Status : Enabled		   |
		// ---------------------------------
		function edit_objects_interfaces_gw($type, $section, $section2, $tablename, $status)
		{
		    if(!(isset($status))||($status=="ER"))
		    {
			    echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
			    echo "			<tr valign=\"top\">\n";
			    echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
			    echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
			    echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
			    echo " 	  				".$section2." | <i>".$tablename."</i> (".$id.") &nbsp;</td>\n";
			    echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
			    echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
			    echo "			</tr>\n";
			    echo "		</table>\n";
			    echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editgw\" name=\"submitform\">";
			    echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
			    echo "			<tr>\n";
				echo "				<td height=\"20px\" colspan=\"2\">\n";
				echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
				echo "			</tr>\n";
				echo "			<tr>\n";
				echo "				<td align=\"left\" width=\"40px\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\">\n";
				echo "					<TABLE cellSpacing=1 cellPadding=0 border=0>\n";
				echo "						<TBODY>\n";
				echo "							<TR bgcolor=\"#565656\">\n";
				echo "								<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD&nbsp;</font>\n";
				echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
				echo "								<TD vAlign=bottom align=left width=\"160\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE&nbsp;</font>\n";
				echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"160\" border=0></TD>\n";
				if ($status=="ER") {
				    echo "								<TD vAlign=bottom align=left width=\"50\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
				    echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"50\" border=0></TD>\n";
                                }
                                echo "							</TR>\n";
				echo "							<TR bgcolor=\"#d5d5d5\">";
				echo "								<TD vAlign=middle align=left width=\"100\" height=\"22\">&nbsp;default Gateway:\n";
				echo "								</TD>";
				echo "								<TD vAlign=middle align=left width=\"150\" height=\"22\">\n";
				$result = mysql_query("SELECT * FROM ".$tablename);
				$row = mysql_fetch_array($result);
				echo "								&nbsp;<input type=\"text\" size=\"20\" maxlength=\"15\" name=\"address\" value=\"".$row['adress']."\">";
				echo "								</td>\n";
        			IF ($status=="ER") {
                                        echo "                                                          <TD valign=middle align=center width=\"\" height=\"22\"><a title=\"Invalid Gateway. Please enter a valid IP Address.\"><img src=\"./images/error.gif\" border=\"0\"></a></td>\n";
				}
                                echo "								</tr>\n";
				echo "							<TR bgcolor=\"#d5d5d5\">\n";
				echo "								<td align=\"right\" colspan=\"2\">\n";
				echo "									<input type=\"hidden\" value=\"".$row['id']."\" name=\"id\">\n";
				echo "									<input type=\"hidden\" value=\"io_submit\" name=\"status\">\n";
				echo "										<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
				echo "										<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
				echo "										<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."\"><img src=\"./images/cancel.gif\" border=\"0\"></a>&nbsp;\n";				
				echo "								</td>\n";
				echo "							</tr>\n";
				echo "					</table>\n";
				echo "			</tr>\n";
				echo "	</table>\n";
                    }
	            elseif($status=="io_submit")
		    {
		     $status="ER";
		     if(ip_address_check($_POST['address'])) {
                             $status="OK";
                     }
		     if($status=="OK") {
                             $result=mysql_query("UPDATE ".$tablename." SET adress='".$_POST['address']."' WHERE id='".$_POST['id']."'") or die (mysql_error());
		             show_objects_interfaces($type, $section, $section2, "io_interfaces");
		     } else {
		             edit_objects_interfaces_gw($type, $section, $section2, $tablename, $status);
		     }
		    }
		}
		
		// ---------------------------------
		// | add Objects Interfaces (Main) |
		// ---------------------------------
		// | Last Change : 12.02.2002	   |
		// ---------------------------------
		// | Status : Enabled		   |
		// ---------------------------------
		function add_objects_interfaces($type, $section, $section2, $tablename, $status)
		{
			# Add Objects #
			if (!isset($status))
			{
				echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
				echo "			<tr valign=\"top\">\n";
				echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo " 	  				".$section2." | <i>ADD ENTRY</i> &nbsp;</td>\n";
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
				
				# Add-Type (Interface) #
				switch ($type)
				{
					# Add Type Selection #
					case 0:
					{
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"300\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"220\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"220\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\" valign=\"middle\">\n";
						#echo "<input type=\"text\" name=\"name\" size=\"40\">&nbsp;</TD>\n";
						# <Interface Wizard start>
						echo "&nbsp;<SELECT name=\"rootname\">";
						$query_iface="SELECT id,name FROM io_interfaces WHERE sticky='1'";
						$result_iface=mysql_query($query_iface);
						$num_iface=mysql_num_rows($result_iface);
						for($i=0;$i<$num_iface;$i++)
						{
							$row_iface=mysql_fetch_array($result_iface);
							echo "<option value=\"".$row_iface['id']."\">".$row_iface['name']."";
						}
						echo "</SELECT>";
						echo "&nbsp;<font size=\"4\">:</font>&nbsp;";
						echo "<SELECT name=\"childname\">";
						for($i=1;$i<256;$i++)
						{
							echo "<OPTION value=\"".$i."\">".$i."";
						}
						echo "</SELECT>";
						# <Interface Wizard end>
						echo "</TD></TR>\n";
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "&nbsp;<input type=\"text\" name=\"note\" size=\"30\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IP</TD>\n";
						echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
						echo "&nbsp;<input type=text name=\"ip\" size=\"30\" maxlength=\"15\">";
                                                echo "</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETMASK</TD>\n";
						echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
						echo "&nbsp;<input type=text name=\"netmask\" size=\"30\" maxlength=\"15\">";
                                                echo "</TD>\n";
                                                echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						//echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\" size=\"40\">\n";
						echo "<input type=\"hidden\" name=\"io_submit\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/add.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$_SERVER['PHP_SELF']."?module=interfaces\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
						echo "</TD>\n";
						echo "</TR>\n";
						
						echo "					</tbody>\n";						
						echo "					</table>\n";
						echo "				</td>\n";
						echo "			</tr>\n";
						echo "		</table>\n";
						echo "		</form>\n";
						echo "	<br><br><br>\n";
						break;
						
					}
				}
			}
			elseif (substr($status,0,5) == 'error')
			{
				echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
				echo "			<tr valign=\"top\">\n";
				echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo " 	  				".$section2." | <i>ADD ENTRY</i> &nbsp;</td>\n";
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
				
				echo "<TABLE cellSpacing=1 cellPadding=0 width=\"350\" border=0>\n";
				echo "<TBODY>\n";
				echo "<TR bgcolor=\"#565656\">\n";
				echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"220\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"220\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"50\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"50\" border=0></TD>\n";
				echo "</TR>\n";
				
				switch ($type)
				{
					case 0:
					{
						if (substr($status,6,4) == 'jona') # Documentated by Christian Leitner: Name is OK
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
							#echo "<input type=\"text\" value=\"".$GLOBALS['name']."\" name=\"name\" size=\"40\">&nbsp;</TD>\n";
							$Rinterface=substr($GLOBALS['iname'],0,strpos($GLOBALS['iname'],":")); # get root IFace name
							$Cinterface=substr(strstr($GLOBALS['iname'],":"),1); # get child IFace name
							# <Interface Wizard start>
							echo "&nbsp;<SELECT name=\"rootname\">";
							$query_iface="SELECT id FROM io_interfaces WHERE name='".$Rinterface."'";
							$result_iface=mysql_query($query_iface);
							$row_iface=mysql_fetch_array($result_iface);
							$query_Rifaces="SELECT id,name FROM io_interfaces WHERE sticky='1'";
							$result_Rifaces=mysql_query($query_Rifaces);
							$num_Rifaces=mysql_num_rows($result_Rifaces);
							for($i=0;$i<$num_Rifaces;$i++)
							{
							    $row_Rifaces=mysql_fetch_array($result_Rifaces);
							    issel($row_Rifaces['id'],$row_iface['id']);
							    echo $row_Rifaces['name']."</option>";
							}
							echo "</SELECT>";
							echo "&nbsp;<font size=\"4\">:</font>&nbsp;";
							echo "<SELECT name=\"childname\">";
							for($i=1;$i<256;$i++)
							{
							    issel($i,$Cinterface);
							    echo $i."</option>";
							}
							echo "</SELECT>";
							# <Interface Wizard end>							
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,6,4) == 'nona') # Documentated by Christian Leitner: Name is invalid
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
							#echo "<input type=\"text\" value=\"".$GLOBALS['name']."\" name=\"name\" size=\"40\">&nbsp;</TD>\n";
							$Rinterface=substr($GLOBALS['iname'],0,strpos($GLOBALS['iname'],":")); # get root IFace name
							$Cinterface=substr(strstr($GLOBALS['iname'],":"),1); # get child IFace name
							# <Interface Wizard start>
							echo "&nbsp;<SELECT name=\"rootname\">";
							$query_iface="SELECT id FROM io_interfaces WHERE name='".$Rinterface."'";
							$result_iface=mysql_query($query_iface);
							$row_iface=mysql_fetch_array($result_iface);
							$query_Rifaces="SELECT id,name FROM io_interfaces WHERE sticky='1'";
							$result_Rifaces=mysql_query($query_Rifaces);
							$num_Rifaces=mysql_num_rows($result_Rifaces);
							for($i=0;$i<$num_Rifaces;$i++)
							{
							    $row_Rifaces=mysql_fetch_array($result_Rifaces);
							    issel($row_Rifaces['id'],$row_iface['id']);
							    echo $row_Rifaces['name']."</option>";
							}
							echo "</SELECT>";
							echo "&nbsp;<font size=\"4\">:</font>&nbsp;";
							echo "<SELECT name=\"childname\">";
							for($i=1;$i<256;$i++)
							{
							    issel($i,$Cinterface);
							    echo $i."</option>";
							}
							echo "</SELECT>";
							# <Interface Wizard end>							
							echo "<td valign=middle align=center width=\"\" height=\"22\"><a title=\"Interface already declared! Please select another virtual interface.\"><img src=\"./images/error.gif\" border=\"0\"></a></td>\n";
							echo "</TR>\n";
						}
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTE</TD>\n";
						echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
						echo "&nbsp;<input type=text value=\"".$_POST['note']."\" name=\"note\" size=\"30\" maxlength=\"255\"></TD>\n";
						echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
						echo "</TR>\n";
						
						if (substr($status,11,4) == 'jope') # Documentated by Christian Leitner: IP Adress is OK
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IP</TD>\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
							echo "&nbsp;<input type=\"text\" value=\"".$_POST['ip']."\" name=\"ip\" size=\"30\" maxlength=\"15\"></TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,11,4) == 'nope') # Documentated by Christian Leitner: IP Adress is invalid
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IP</TD>\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
							echo "&nbsp;<input type=\"text\" value=\"".$_POST['ip']."\" name=\"ip\" size=\"30\" maxlength=\"15\"></TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><a title=\"The entered IP Address is invalid.\"><img src=\"./images/error.gif\" border=\"0\"></a></td>\n";
							echo "</TR>\n";
						}
						
						if (substr($status,16,4) == 'jops') # Documentated by Christian Leitner: Network Mask is OK
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETMASK</TD>\n";
							echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
							echo "&nbsp;<input type=text value=\"".$_POST['netmask']."\" name=\"netmask\" size=\"30\" maxlength=\"15\"></TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,16,4) == 'nops') # Documentated by Christian Leitner: Network Mask is invalid
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETMASK</TD>\n";
							echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
							echo "&nbsp;<input type=text value=\"".$_POST['netmask']."\" name=\"netmask\" size=\"30\" maxlength=\"15\"></TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><a title=\"The entered Netmask is invalid.\"><img src=\"./images/error.gif\" border=\"0\"></a></td>\n";
							echo "</TR>\n";
						}
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						//echo "<input type=\"hidden\" value=\"".$_POST['id']."\" name=\"id\" size=\"40\">\n";
						echo "<input type=\"hidden\" name=\"io_submit\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/add.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$_SERVER['PHP_SELF']."?module=interfaces\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
						echo "</TD>\n";
						echo "</TR>\n";
						
						echo "					</tbody>\n";						
						echo "					</table>\n";
						echo "				</td>\n";
						echo "			</tr>\n";
						echo "		</table>\n";
						echo "		</form>\n";
						echo "	<br><br><br>\n";
						
						break;
					}
				}
			}
			else
			{
				switch ($type)
				{
					case 0:
					{
						if ($_POST['magic'] == $GLOBALS['lastmagic'])
						{
							show_objects_interfaces($type, $section, $section2, $tablename);
						}
						else
						{
							$GLOBALS['lastmagic'] = $_POST['magic'];
							$field1 = "nona";
							$field2 = "nope";
							$field3 = "nops";
																														
							if (!empty($_POST['rootname'])) $field1 = "jona";
                                                        if (!(empty($_POST['ip'])) AND (ip_address_check($_POST['ip'])) AND (chk_duplicate_ips($tablename, $_POST['ip'], 0))) $field2 = "jope";
							if (!empty($_POST['netmask']) AND (netmask_check($_POST['netmask']))) $field3 = "jops";
							
							# Time to get the Real Interface Name
							$queryRN="SELECT name from ".$tablename." WHERE ID=".$_POST['rootname']."";
							$resultRN=mysql_query($queryRN);
							$rowRN=mysql_fetch_array($resultRN);
							$GLOBALS['iname'] = $rowRN['name'].":".$_POST['childname'];
							# Now check if interface is already in use
                                                        $queryCHK="SELECT id from ".$tablename." WHERE name='".$GLOBALS['iname']."'";
							$resultCHK=mysql_query($queryCHK) or die (mysql_error());
							$numCHK=mysql_num_rows($resultCHK);
							if ($numCHK!=0) {
							        $field1 = "nona";
							}
							mysql_free_result($resultCHK);
							
							if (($field1 == 'jona') and ($field2 == 'jope') and ($field3 == 'jops')) //update the DB
							{
								$data = "'','".$GLOBALS['iname']."','".$_POST['note']."','".$_POST['ip']."','0','".$_POST['netmask']."'";
								$fields = "id,name,note,ip,sticky,netmask";
								$query = mysql_query("insert into ".$tablename." (".$fields.") values(".$data.")") or die(mysql_error());

								
								show_objects_interfaces($type, $section, $section2, $tablename);
							}
							else //seems to be an error
							{
								add_objects_interfaces($type, $section, $section2, $tablename, "error|".$field1."_".$field2."_".$field3);
							}
						}
						break;
					}
				}
			}
		}
		
                // ---------------------------------
		// | edit_objects_interfaces (Main)|
		// ---------------------------------
		// | Last Change : 12.02.2002	   |
		// ---------------------------------
		// | Status : Enabled		   |
		// ---------------------------------		
		function edit_objects_interfaces($type, $section, $section2, $tablename, $id, $status)
		{
			// Open Object Database
			$result = mysql_query("select * from ".$tablename." where(id='".$id."')");
			$number = mysql_num_rows($result);
			
			// Read and Display Database Entries					
			$row = mysql_fetch_array($result);
			
			if (!isset($status))
			{
				echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
				echo "			<tr valign=\"top\">\n";
				echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo " 	  				".$section2." | <i>".$row['name']."</i> (".$row['id'].") &nbsp;</td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
				echo "			</tr>\n";
				echo "		</table>\n";
				
				echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$_GET['sid']."\" name=\"submitform\">";
				echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
				echo "			<tr>\n";
				echo "				<td height=\"20px\" colspan=\"2\">\n";
				echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
				echo "			</tr>\n";
				echo "			<tr>\n";
				echo "				<td align=\"left\" width=\"40px\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\">\n";
				
				# Edit-Type 
				switch ($type)
				{
					// Edit Type Selection
					case 0:
					{
						# Interfaces (Edit)
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"300\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;NAME</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"220\" height=\"22\"><FONT color=#ffffff>&nbsp;".$row['name']."</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"220\" border=0></TD>\n";
						echo "</TR>\n";
						# Replaced with 'Chris Interface Wizard' 31.05.2002
						/*if ($row['sticky'] == 1)
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$row['name']."\" name=\"name\" size=\"40\" readonly>&nbsp;</TD>\n";
							echo "</TR>\n";
						}
						else
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$row['name']."\" name=\"name\" size=\"40\">&nbsp;</TD>\n";
							echo "</TR>\n";
						}*/
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "&nbsp;<input type=\"text\" value=\"".$row['note']."\" name=\"note\" size=\"30\" maxlength=\"255\">&nbsp;</TD>\n";
						echo "</TR>\n";
						# IP Address Input Mask by Christian Leitner <14.04.2003>
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IP</TD>\n";
						echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
						echo "&nbsp;<input type=text value=\"".$row['ip']."\" name=\"ip\" size=\"30\" maxlength=\"15\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETMASK</TD>\n";
						echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
						echo "&nbsp;<input type=text value=\"".$row['netmask']."\" name=\"netmask\" size=\"30\" maxlength=\"15\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\" size=\"40\">\n";
						echo "<input type=\"hidden\" name=\"io_change\">";
						echo "<input type=\"hidden\" name=\"sticky\" value=\"".$row['sticky']."\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$_SERVER['PHP_SELF']."?module=interfaces\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
						echo "</TD>\n";
						echo "</TR>\n";
						
						echo "					</tbody>\n";						
						echo "					</table>\n";
						echo "				</td>\n";
						echo "			</tr>\n";
						echo "		</table>\n";
						echo "		</form>\n";
						echo "	<br><br><br>\n";
						break;
					}
					default:
					{
						errorcode(7,0);
						break;
					}
				}
				
				echo "</form>";
			}
			elseif (substr($status,0,5) == 'error')
			{
				echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
				echo "			<tr valign=\"top\">\n";
				echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo " 	  				".$section2." | <i>".$row['name']."</i> (".$row['id'].") &nbsp;</td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
				echo "			</tr>\n";
				echo "		</table>\n";
				
				echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$_GET['sid']."\" name=\"submitform\">";
				echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
				echo "			<tr>\n";
				echo "				<td height=\"20px\" colspan=\"2\">\n";
				echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
				echo "			</tr>\n";
				echo "			<tr>\n";
				echo "				<td align=\"left\" width=\"40px\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\">\n";
				
				echo "<TABLE cellSpacing=1 cellPadding=0 width=\"350\" border=0>\n";
				echo "<TBODY>\n";
				echo "<TR bgcolor=\"#565656\">\n";
				echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;NAME</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"220\" height=\"22\"><FONT color=#ffffff>&nbsp;".$row['name']."</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"220\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"50\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"50\" border=0></TD>\n";
				echo "</TR>\n";
				
				switch ($type)
				{
					case 0:
					{
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTE</TD>\n";
						echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
						echo "&nbsp;<input type=text value=\"".$_POST['note']."\" name=\"note\" size=\"30\" maxlength=\"255\">&nbsp;</TD>\n";
						echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
						echo "</TR>\n";
						
						if (substr($status,11,4) == 'jope')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IP</TD>\n";
							echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
							echo "&nbsp;<input type=text value=\"".$_POST['ip']."\" name=\"ip\" size=\"30\" maxlength=\"15\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,11,4) == 'nope')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IP</TD>\n";
							echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
							echo "&nbsp;<input type=text value=\"".$_POST['ip']."\" name=\"ip\" size=\"30\" maxlength=\"15\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						
						if (substr($status,16,4) == 'jops')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETMASK</TD>\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
							echo "&nbsp;<input type=\"text\" value=\"".$_POST['netmask']."\" name=\"netmask\" size=\"30\" maxlength=\"15\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,16,4) == 'nops')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETMASK</TD>\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
							echo "&nbsp;<input type=\"text\" value=\"".$_POST['netmask']."\" name=\"netmask\" size=\"30\" maxlength=\"15\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" name=\"io_change\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$_SERVER['PHP_SELF']."?module=interfaces\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
						echo "</TD>\n";
						echo "</TR>\n";
						
						echo "					</tbody>\n";						
						echo "					</table>\n";
						echo "				</td>\n";
						echo "			</tr>\n";
						echo "		</table>\n";
						echo "		</form>\n";
						echo "	<br><br><br>\n";
						
						break;
					}
				}
			}
			else
			{
				switch ($type)
				{
					case 0:
					{
						if ($_POST['magic'] == $GLOBALS['lastmagic'])
						{
							show_objects_interfaces($type, $section, $section2, $tablename);
						}
						else
						{
							$GLOBALS['lastmagic'] = $_POST['magic'];
                                                        $field1 = "jona";
							$field2 = "nope";
							$field3 = "nops";
							
							//if (!empty($_POST['rootname'])) $field1 = "jona"; Changed by Christian Leitner <15.04.2003> - Interface names are no longer editable
							if (!empty($_POST['netmask']) and (netmask_check($_POST['netmask']))) $field3 = "jops";
							if (!empty($_POST['ip']) and (ip_address_check($_POST['ip'])) and (chk_duplicate_ips($tablename, $_POST['ip'], $_GET['sid']))) $field2 = "jope";
														
                                                        if (($field1 == 'jona') and ($field2 == 'jope') and ($field3 == 'jops'))
    							{
								$result_old = mysql_query("select * from ".$tablename." WHERE id='".$_GET['sid']."'");

								$result = mysql_query("update ".$tablename." set note='".$_POST['note']."' where(id='".$_GET['sid']."')");
								$result = mysql_query("update ".$tablename." set netmask='".$_POST['netmask']."' where(id='".$_GET['sid']."')");
								$result = mysql_query("update ".$tablename." set ip='".$_POST['ip']."' where(id='".$_GET['sid']."')");
								//enzi update 
								//enzi update
								while ($temp_data = mysql_fetch_array($result_old))
								{
									$result = mysql_query("update no_hosts set hostip='".$_POST['ip']."' WHERE hostip='".$temp_data['ip']."'");
								}
								show_objects_interfaces($type, $section, $section2, $tablename);
							}
							else
							{
								edit_objects_interfaces($type, $section, $section2, $tablename, $_GET['sid'], "error|".$field1."_".$field2."_".$field3);
							}
						}
						break;
					}
				}
			}
		}	
		
		// ---------------------------------
		// | check if seleceted (Sub,Main) |
		// ---------------------------------
		// | Last Change : 12.02.2002	   |
		// ---------------------------------
		// | Status : Enabled		   |
		// ---------------------------------
		function issel($suffix, $compstr){
					if($suffix==$compstr) {
						echo "<option selected value=".$suffix.">";
					} else {
						echo "<option value=".$suffix.">";
					}
		}
		
		// ---------------------------------
		// |check if ip is already assigned|
		// ---------------------------------
		// | Last Change : 12.02.2002	   |
		// ---------------------------------
		// | Status : Enabled		   |
		// ---------------------------------
		function chk_duplicate_ips($tablename, $ip, $editid){
		        $result = mysql_query("select * from ".$tablename." where ip='".$ip."'");
			$number = mysql_num_rows($result);
			if($number==0) { // no such address assigned
                                return true;
			} elseif ($number>=2) { // address already assigned (2 times)
			        return false;
			}

			$result = mysql_query("select * from ".$tablename." order by id");
			$number = mysql_num_rows($result);
			
			$ip_long = ip2long($ip);
			for ($i=0;$i < $number; $i++)
			{
				$row = mysql_fetch_array($result);
                                if ($ip_long == (ip2long($row['ip'])))
				{
					if (($editid!=0) and ($editid==$row['id'])) {
                                                return true;
                                        } else {
                                                return false;
                                        }
				}
			}
		}

?>
