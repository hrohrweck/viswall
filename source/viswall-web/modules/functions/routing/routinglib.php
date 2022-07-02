<?php
		////////////////////////////////////////////////
		// --> itsoft <--> 2001/02 <--> vis|wall <-- //
		////////////////////////////////////////////////
		//											  //
		// MainGroup   : Interface					  //
		//											  //
		// Name			: Module - Rules			  //
		// Date			: 27.03.2002				  //
		// Comment  	: Filter Rules	 			  //
		//											  //
		////////////////////////////////////////////////
		
		// ----------------------------------
		// | Guardian Style - Add Strategie |
		// ----------------------------------
		// | Last Change : 27.03.2002       |
		// ----------------------------------
		// | Status : Enabled               |
		// ----------------------------------
		function add_strategies($section, $tablename)
		{
			# Open Database #
			$result = mysql_query("select * from ".$tablename." order by id");
			$number = mysql_num_rows($result);
			
			# Create new Default Entry #
			$data = "'','*','*','*','0','*','0'";
			$fields = "id,type,did,gateway,metric,iid,status";
			$query = mysql_query("insert into ".$tablename." (".$fields.") values(".$data.")") or die(mysql_error());
			
			# Show Strategies (Default Mode)
			show_strategies(0, $section, "STRATEGY | <B>ROUTING</B>", $tablename);
		}
		
		// -------------------------------------
		// | Edit Filter Strategies (Advanced) |
		// -------------------------------------
		// | Last Change : 27.03.2002		   |
		// -------------------------------------
		// | Status : Enabled				   |
		// -------------------------------------
		function edit_strategies($section, $section2, $tablename, $id, $field)
		{
			global $rsubmit, $sources, $hiddenfield;
			# Open Database #
			$result = mysql_query("select * from ".$tablename." where(id='".$id."')");
			$number = mysql_num_rows($result);
			
			# Read and Display Database Entries #
			$row = mysql_fetch_array($result);
			
			# Check if Information is already submitted #
			if (!isset($_POST['rsubmit']))
			{
				# Decide which field is selected #
				switch ($field)
				{
					# Strategie for Source #
					case 'destination':
					{
						echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
						echo "			<tr valign=\"top\">\n";
						echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo " 	  				".$section2." | <i>".$tablename."</i></td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
						echo "			</tr>\n";
						echo "		</table>\n";
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=routing&action=edit&sid=".$id."\" name=\"submitform\">";
						echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
						echo "			<tr>\n";
						echo "				<td height=\"20px\" colspan=\"2\">\n";
						echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
						echo "			</tr>\n";
						echo "			<tr>\n";
						echo "				<td align=\"left\" width=\"40px\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\">\n";
						
						# Hosts (Edit)
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"230\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"250\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"250\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;DESTINATION</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<select name=\"sources\">\n";
						
						# Generate Any Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Various <--- </option>\n";
						if ($row['type'] == '*')
						{
							echo "<option value=\"*\" name=\"any\" selected> Not Defined </option>\n";
						}
						else
						{
							echo "<option value=\"*\" name=\"any\"> Not Defined </option>\n";
						}
						
						# Generate Existing Host Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Hosts <--- </option>\n";
						$result_hosts = mysql_query("select * from no_hosts order by id");
						$number_hosts = mysql_num_rows($result_hosts);
						for ($i=0;$i<$number_hosts;$i++)
						{
							$row_hosts=mysql_fetch_array($result_hosts);
							if (($row['type'] == 1) and ($row['did'] == $row_hosts['id']))
							{
								echo "<option value=\"1".$row_hosts['id']."|".$row_hosts['name']."\" name=\"host".$row_hosts['id']."\" selected> ".$row_hosts['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"1".$row_hosts['id']."|".$row_hosts['name']."\" name=\"host".$row_hosts['id']."\"> ".$row_hosts['name']." </option>\n";
							}								
						}
						
						# Generate Existing Network Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Networks <--- </option>\n";
						$result_networks = mysql_query("select * from no_networks order by id");
						$number_networks = mysql_num_rows($result_networks);
						for ($i=0;$i<$number_networks;$i++)
						{
							$row_networks=mysql_fetch_array($result_networks);
							if (($row['type'] == 2) and ($row['did'] == $row_networks['id']))
							{
								echo "<option value=\"2".$row_networks['id']."|".$row_networks['name']."\" name=\"network".$row_networks['id']."\" selected> ".$row_networks['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"2".$row_networks['id']."|".$row_networks['name']."\" name=\"network".$row_networks['id']."\"> ".$row_networks['name']." </option>\n";
							}
						}
						
						echo "</select></TD></TR>\n";
						
						// Submit Event for Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					echo "<a href=\"".$_SERVER['PHP_SELF']."?module=routing\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'gateway':
					{
						echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
						echo "			<tr valign=\"top\">\n";
						echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo " 	  				".$section2." | <i>".$tablename."</i></td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
						echo "			</tr>\n";
						echo "		</table>\n";
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=routing&action=edit&sid=".$id."\" name=\"submitform\">";
						echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
						echo "			<tr>\n";
						echo "				<td height=\"20px\" colspan=\"2\">\n";
						echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
						echo "			</tr>\n";
						echo "			<tr>\n";
						echo "				<td align=\"left\" width=\"40px\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\">\n";
						
						# Hosts (Edit)
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"230\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"250\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"250\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;GATEWAY</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<select name=\"sources\">\n";
						
						# Generate Any Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Various <--- </option>\n";
						if ($row['type'] == '*')
						{
							echo "<option value=\"*\" name=\"any\" selected> Not Defined </option>\n";
						}
						else
						{
							echo "<option value=\"*\" name=\"any\"> Not Defined </option>\n";
						}
						
						# Generate Existing Host Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Hosts <--- </option>\n";
						$result_hosts = mysql_query("select * from no_hosts order by id");
						$number_hosts = mysql_num_rows($result_hosts);
						for ($i=0;$i<$number_hosts;$i++)
						{
							$row_hosts=mysql_fetch_array($result_hosts);
							if (($row['gateway'] == $row_hosts['id']))
							{
								echo "<option value=\"1".$row_hosts['id']."|".$row_hosts['name']."\" name=\"host".$row_hosts['id']."\" selected> ".$row_hosts['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"1".$row_hosts['id']."|".$row_hosts['name']."\" name=\"host".$row_hosts['id']."\"> ".$row_hosts['name']." </option>\n";
							}								
						}
						
						echo "</select></TD></TR>\n";
						
						// Submit Event for Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					echo "<a href=\"".$_SERVER['PHP_SELF']."?module=routing\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'interface':
					{
						echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
						echo "			<tr valign=\"top\">\n";
						echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo " 	  				".$section2." | <i>".$tablename."</i></td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
						echo "			</tr>\n";
						echo "		</table>\n";
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=routing&action=edit&sid=".$id."\" name=\"submitform\">";
						echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
						echo "			<tr>\n";
						echo "				<td height=\"20px\" colspan=\"2\">\n";
						echo "			 		<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
						echo "			</tr>\n";
						echo "			<tr>\n";
						echo "				<td align=\"left\" width=\"40px\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\">\n";
						
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"320\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"2450\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"250\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;INTERFACE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						
						echo "<select name=\"sinterfaces\">\n";
						
						$fdata = mysql_query("select iid from $tablename where(id=$id)");
						$row_fdata = mysql_fetch_array($fdata);
						
						$result_interfaces = mysql_query("select * from io_interfaces order by id");
						$number_interfaces = mysql_num_rows($result_interfaces);
						
						for ($i=0;$i<$number_interfaces;$i++)
						{
							$row_interfaces=mysql_fetch_array($result_interfaces);
							
							if ($row_fdata['iid'] == ($row_interfaces['id'] ))
							{
								echo "<option value=\"".$row_interfaces['id']."|".$row_interfaces['name']."\" name=\"sinterfaces".$row_interfaces['id']."\" selected> ".$row_interfaces['note']." (".$row_interfaces['name'].") </option>\n";
							}
							else
							{
								echo "<option value=\"".$row_interfaces['id']."|".$row_interfaces['name']."\" name=\"sinterfaces".$row_interfaces['id']."\"> ".$row_interfaces['note']." (".$row_interfaces['name'].") </option>\n";
							}
						}
						
						if ($row_fdata['iid'] == '*')
						{
							echo "<option value=\"*|all\" name=\"sinterfaces\" selected> all interfaces </option>\n";
						}
						else
						{
							echo "<option value=\"*|all\" name=\"sinterfaces\"> all </option>\n";
						}
						
						# Submit Event Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						//echo "<input type=\"hidden\" value=\"".$sid."\" name=\"hiddenid\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"".$_SERVER['PHP_SELF']."?module=routing\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'metric':
					{
						echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
						echo "			<tr valign=\"top\">\n";
						echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo " 	  				".$section2." | <i>".$tablename."</i></td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
						echo "			</tr>\n";
						echo "		</table>\n";
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=routing&action=edit&sid=".$id."\" name=\"submitform\">";
						echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
						echo "			<tr>\n";
						echo "				<td height=\"20px\" colspan=\"2\">\n";
						echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
						echo "			</tr>\n";
						echo "			<tr>\n";
						echo "				<td align=\"left\" width=\"40px\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\">\n";
						
						# Hosts (Edit)
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"230\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"250\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"250\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;METRIC</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" name=\"metric\" value=\"".$row['metric']."\">\n";
						echo "</TD></TR>\n";
						
						// Submit Event for Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					echo "<a href=\"".$_SERVER['PHP_SELF']."?module=routing\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
				if ($_POST['hiddenfield'] == 'destination')
				{
					switch(substr($_POST['sources'],0,1))
					{
						case '-':
						{
							# Show Strategies (Default Mode)
							show_strategies(0, $section, "STRATEGY | <B>ROUTING</B>", $tablename);
							break;
						}
						case '*':
						{
							$result = mysql_query("update ".$tablename." set type='*' where(id='".$_GET['sid']."')") or die(mysql_error());
							$result = mysql_query("update ".$tablename." set did='*' where(id='".$_GET['sid']."')") or die(mysql_error());
							
							# Show Strategies (Default Mode)
							show_strategies(0, $section, "STRATEGY | <B>ROUTING</B>", $tablename);
							break;
						}
						case '1':
						case '2':
						{
                            $result = mysql_query("update ".$tablename." set type='".substr($_POST['sources'],0,1)."' where(id='".$_GET['sid']."')") or die(mysql_error());
							$result = mysql_query("update ".$tablename." set did='".substr($_POST['sources'],1,strpos($_POST['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(mysql_error());
								# Show Strategies (Default Mode)
							show_strategies(0, $section, "STRATEGY | <B>ROUTING</B>", $tablename);
							break;
						}
					}
				}
				
                if ($_POST['hiddenfield'] == 'gateway')
				{
				    switch(substr($_POST['sources'],0,1))
				    {
				        case '-':
				        {
    						# Show Strategies (Default Mode)
    						show_strategies(0, $section, "STRATEGY | <B>ROUTING</B>", $tablename);
    						break;
    				    }
    				    case '*':
    				    {
    				        $result = mysql_query("update ".$tablename." set gateway='*' where(id='".$_GET['sid']."')") or die(mysql_error());
    				        
    						show_strategies(0, $section, "STRATEGY | <B>ROUTING</B>", $tablename);
    						break;
    					}
    					default:
    					{
                            $result = mysql_query("update ".$tablename." set gateway='".substr($_POST['sources'],1,strpos($_POST['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(mysql_error());

    						show_strategies(0, $section, "STRATEGY | <B>ROUTING</B>", $tablename);
    						break;
    					}
    				}
				}
				
                if ($_POST['hiddenfield'] == 'interface')
				{
				    switch(substr($_POST['sinterfaces'],0,1))
				    {
				        case '-':
				        {
    						# Show Strategies (Default Mode)
    						show_strategies(0, $section, "STRATEGY | <B>ROUTING</B>", $tablename);
    						break;
    				    }
    				    case '*':
    				    {
    				        $result = mysql_query("update ".$tablename." set iid='*' where(id='".$_GET['sid']."')") or die(mysql_error());
    				
    						show_strategies(0, $section, "STRATEGY | <B>ROUTING</B>", $tablename);
    						break;
    					}
    					default:
    					{
    					    $result = mysql_query("update ".$tablename." set iid='".substr($_POST['sinterfaces'],0,strpos($_POST['sinterfaces'],"|"))."' where(id='".$_GET['sid']."')") or die(mysql_error());
    					    
    						show_strategies(0, $section, "STRATEGY | <B>ROUTING</B>", $tablename);
    						break;
                        }
				    }
				}
				
				if ($_POST['hiddenfield'] == 'metric')
				{
				    $result = mysql_query("update ".$tablename." set metric='".$_POST['metric']."' where(id='".$_GET['sid']."')") or die(mysql_error());
				    
				    show_strategies(0, $section, "STRATEGY | <B>ROUTING</B>", $tablename);
				}
			}
		}			
		
		// ----------------------------------
		// | Default Style - Show Strategie |
		// ----------------------------------
		// | Last Change : 29.04.2002		|
		// ----------------------------------
		// | Status : Enabled				|
		// ----------------------------------
		function show_strategies($type, $section, $section2, $tablename)
		{
			$result = mysql_query("select * from ".$tablename." order by id") or die(mysql_error());
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
			
			# Display-Type (Simple, Advanced) #
			switch ($type)
			{
				# Display Simple #
				case 0:
				{
					# Generate Table-Header #
					echo "					<table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"682px\" height=\"\">\n";
					echo "						<tr bgcolor=\"#565656\" class=\"tablehead\">\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"32\" height=\"22\">\n";
					echo "								<font color=\"#ffffff\">&nbsp;</font>\n";
					echo "								<img src=\"images/border_orange.gif\" width=\"32\" height=\"6\" border=\"0\"></td>\n";
					echo "  						<td valign=\"bottom\" align=\"left\" width=\"165\" height=\"22\">\n";
					echo "   							<font color=\"#ffffff\">&nbsp;DESTINATION</font>\n";
					echo "   							<img src=\"images/border_orange.gif\" WIDTH=\"165\" height=\"6\" border=\"0\"></td>\n";
					echo "  						<td valign=\"bottom\" align=\"left\" width=\"150\" height=\"22\">\n\n";
					echo "   							<font color=\"#ffffff\">&nbsp;GATEWAY</font>\n";
					echo "  							<img src=\"images/border_orange.gif\" WIDTH=\"150\" height=\"6\" border=\"0\"></td>\n";
					echo "  						<td valign=\"bottom\" align=\"left\" width=\"165\" height=\"22\">\n\n";
					echo "   							<font color=\"#ffffff\">&nbsp;METRIC</font>\n";
					echo "  							<img src=\"images/border_orange.gif\" WIDTH=\"165\" height=\"6\" border=\"0\"></td>\n";
                    echo "  						<td valign=\"bottom\" align=\"left\" width=\"70\" height=\"22\">\n";
					echo "   							<font color=\"#ffffff\">&nbsp;INTERFACE</font>\n";
					echo "   							<img src=\"images/border_orange.gif\" WIDTH=\"70\" height=\"6\" border=\"0\"></td>\n";
					echo " 							<td valign=\"bottom\" align=\"center\" width=\"115\" height=\"22\">\n";
					echo "   							<font color=\"#ffffff\">&nbsp;FUNCTION</font>\n";
					echo "   							<img src=\"images/border_orange.gif\" WIDTH=\"115\" height=\"6\" border=\"0\"></td>\n";
					echo " 						</tr>\n";
					
					if ($number != 0)
					{
						# Read and Display Database Entries #				
						for ($i=0; $i < $number; $i++)
						{
							$row = mysql_fetch_array($result);
							
							if (is_float(($i/2)))
								echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
							else
								echo "						<tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
							
							echo "							<td valign=\"top\" align=\"center\" width=\"\" height=\"20\">";
							if ($row['status'])
								echo "								&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setstatus&sid=".$row['id']."&field=status\" title=\"deactivate rule\"><IMG SRC=\"images/icons/on.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"on\"></a>&nbsp;</td>";
							else
								echo "								&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setstatus&sid=".$row['id']."&field=status\" title=\"activate rule\"><IMG SRC=\"images/icons/off.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"off\"></a>&nbsp;</td>";
							
							switch ($row['type'])
							{
								# Any #
								case '*':
								{
									echo "							<td valign=\"top\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=destination\" title=\"select source host/network\">";
									echo "											&nbsp;<IMG SRC=\"images/icons/inet.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"any\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=destination\" title=\"select source host/network\">";
									echo "							 				not defined</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
								# Hosts #
								case '1':
								{
									$result2= mysql_query("select * from no_hosts where (id=".$row['did'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=destination\" title=\"select source host/network\">";
									echo "								&nbsp;<IMG SRC=\"images/icons/host.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"host\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=destination\" title=\"select source host/network\">";
									echo "								".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}					
								# Networks #
								case '2':
								{
									$result2 = mysql_query("select * from no_networks where (id=".$row['did'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=destination\" title=\"select source host/network\">";
									echo "								&nbsp;<IMG SRC=\"images/icons/network.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=destination\" title=\"select source host/network\">";
									echo "								".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
							}
							
							switch ($row['gateway'])
							{
								# Any #
								case '*':
								{
									echo "							<td valign=\"top\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=gateway\" title=\"select gateway host/network\">";
									echo "											&nbsp;<IMG SRC=\"images/icons/inet.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"not defined\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=gateway\" title=\"select gateway host/network\">";
									echo "							 				not defined</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								
                                    break;
                                }
                                default:
								{
                                    $result2 = mysql_query("select * from no_hosts where (id=".$row['gateway'].")");
                                    $gather = mysql_fetch_array($result2);
                                    echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
                                    echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
                                    echo "									<tr valign=\"middle\">\n";
                                    echo "										<td align=\"left\">\n";
                                    echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=gateway\" title=\"select destination host/networks\">";
                                    echo "								&nbsp;<IMG SRC=\"images/icons/host.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\"></a>&nbsp;";
                                    echo "										</td>\n";
                                    echo "										<td align=\"left\">\n";
                                    echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=gateway\" title=\"select destination host/networks\">";
                                    echo "								".$gather['name']."</a></td>\n";
                                    echo "									</tr>\n";
                                    echo "								</table>\n";
                                    echo "							</td>\n";

                                    break;
                                }
                            }

                            echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
                            echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
                            echo "									<tr valign=\"middle\">\n";
                            echo "										<td align=\"left\">\n";
                            echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=metric\" title=\"select destination host/networks\">";
                            echo "								&nbsp;".$row['metric']."</a></td>\n";
                            echo "									</tr>\n";
                            echo "								</table>\n";
                            echo "							</td>\n";
							
							if ($row['iid'] > 0)
							{
                                $result2 = mysql_query("select * from io_interfaces where (id=".$row['iid'].")");
                                $gather = mysql_fetch_array($result2);
                                echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
			 	       			echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
			     				echo "									<tr valign=\"middle\">\n";
                                echo "										<td align=\"left\">\n";
                                echo "								&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=interface\" title=\"select destination host/networks\">";
                                echo "								<IMG SRC=\"images/icons/interface.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\"></a>&nbsp;";
                                echo "										</td>\n";
                                echo "										<td align=\"left\">\n";
                                echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=interface\" title=\"select destination host/networks\">";
                                echo "								".$gather['name']."</a></td>\n";
                                echo "									</tr>\n";
                                echo "								</table>\n";
                                echo "							</td>\n";
                            }
                            else
                            {
                                echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
			 	       			echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
			     				echo "									<tr valign=\"middle\">\n";
                                echo "										<td align=\"left\">\n";
                                echo "								&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=interface\" title=\"select destination host/networks\">";
                                echo "								<IMG SRC=\"images/icons/inet.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\"></a>&nbsp;";
                                echo "										</td>\n";
                                echo "										<td align=\"left\">\n";
                                echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=interface\" title=\"select destination host/networks\">";
                                echo "								auto</a></td>\n";
                                echo "									</tr>\n";
                                echo "								</table>\n";
                                echo "							</td>\n";
                            }
					   		
					   		echo "						<td valign=\"top\" align=\"middle\" width=\"\" height=\"20\">\n";
					   		echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=add&sid=".$row['id']."\" title=\"delete rule\"><IMG SRC=\"images/icons/neu.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\ ALT=\"delete\"></a>";
							echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=delete&sid=".$row['id']."\" title=\"delete rule\"><IMG SRC=\"images/icons/delete.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\ ALT=\"delete\"></a>";
							echo "					</tr>\n";
    					}
					}
					else
					{
						echo "						<tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
						echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">&nbsp;-</td>";
						echo "							<td valign=\"top\" align=\"left\" width=\"\" height=\"20\">\n";
						echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
						echo "									<tr valign=\"middle\">\n";
						echo "										<td align=\"left\">\n";
						echo "											&nbsp;-";
						echo "										</td>\n";
						echo "									</tr>\n";
						echo "								</table>\n";
						echo "							</td>\n";
						echo "							<td valign=\"top\" align=\"left\" width=\"\" height=\"20\">\n";
						echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
						echo "									<tr valign=\"middle\">\n";
						echo "										<td align=\"left\">\n";
						echo "											&nbsp;-";
						echo "										</td>\n";
						echo "									</tr>\n";
						echo "								</table>\n";
						echo "							</td>\n";
						echo "						<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">&nbsp;-\n";
						echo "							</td>\n";
						echo "						<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">&nbsp;-\n";
						echo "							</td>\n";
						echo "						<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">\n";
						echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=add&sid=".$row['id']."&field=status\"><IMG SRC=\"images/add_entry_gr.gif\" BORDER=\"0\" ALT=\"add after\"></a></td>";
						echo "					</tr>\n";
					}
					
					echo "						<tr bgcolor=\"#565656\">\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						</tr>\n";
					echo "						<tr>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						</tr>\n";
					echo "						<tr>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"center\" width=\"\" height=\"12\">";
					echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=activate&g_module=".$section."&action=activate&params=execute\"><IMG SRC=\"images/activate.gif\" BORDER=\"0\" ALT=\"activate\"></a></td>";
					echo "						</tr\n";
					echo "					</table>\n";
					
					echo "				</td>\n";
					echo "			</tr>\n";
					echo "		</table>\n";
					echo "	<br><br><br>\n";
					break;
				}
			}
		}
		
		// -----------------------------------
		// | Guardian Style - Status Changer |
		// -----------------------------------
		// | Last Change : 17.01.2002		 |
		// -----------------------------------
		// | Status : Enabled				 |
		// -----------------------------------
		function change_strategies_status($section, $tablename, $id, $field)
		{
			# Open Database #
			$result = mysql_query("select * from ".$tablename." where(id='".$id."')");
			$row = mysql_fetch_array($result);
			
			if (((int)($row['status'])) == 0)
			{
			    if (($row['did'] != '*') && ($row['gateway'] != '*'))
				    $result = mysql_query("update ".$tablename." set status='1' where(id='".$id."')");

				show_strategies(0, $section, "STRATEGY | <B>ROUTING</B>", $tablename);
			}
			elseif (((int)($row['status'])) == 1)
			{
				$result = mysql_query("update ".$tablename." set status='0' where(id='".$id."')");
				show_strategies(0, $section, "STRATEGY | <B>ROUTING</B>", $tablename);
			}
		}
?>
