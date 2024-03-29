<?php
		////////////////////////////////////////////////
		//               --> vis|wall <--             //
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
		function add_strategies_simple($section, $tablename)
		{
			# Open Database #
			$result = mysql_query("select * from ".$tablename." order by id");
			$number = mysql_num_rows($result);
			
			# Create new Default Entry #
			$data = "'','*','*','*','*','*','*','*','*','0','0','*','*','".$number."','0'";
			$fields = "id,stype,sid,satype,said,dtype,did,datype,daid,direction,baction,siface,diface,priority,status";
			$query = mysql_query("insert into ".$tablename." (".$fields.") values(".$data.")") or die(mysql_error());
			
			# Show Strategies (Default Mode)
			correct_priorities($section, $tablename);
			show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
		}
		
		// -----------------------------------------------
		// | Guardian Style - Add Strategie Before/After |
		// -----------------------------------------------
		// | Last Change : 27.03.2002			 |
		// -----------------------------------------------
		// | Status : Enable				 |
		// -----------------------------------------------
		function add_strategies_baf($section, $tablename, $sid, $field, $status)
		{
			# Open Database #
			$result = mysql_query("select * from ".$tablename." where (id='".$sid."')");
			$row = mysql_fetch_array($result);
			
			# Create new Default Entry #
			if ($status == 0)
			{
				$data = "'','*','*','*','*','*','*','*','*','0','0','*','*','".($row['priority']+1)."','0'";
				$fields = "id,stype,sid,satype,said,dtype,did,datype,daid,direction,baction,siface,diface,priority,status";
				$query = mysql_query("insert into ".$tablename." (".$fields.") values(".$data.")") or die(mysql_error());
			}
			else
			{
				$data = "'','*','*','*','*','*','*','*','*','0','0','*','*','".($row['priority']-1)."','0'";
				$fields = "id,stype,sid,satype,said,dtype,did,datype,daid,direction,baction,siface,diface,priority,status";
				$query = mysql_query("insert into ".$tablename." (".$fields.") values(".$data.")") or die(mysql_error());
			}
			
			# Show Strategies (Default Mode)
			correct_priorities($section, $tablename);
			show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
		}
		
		// -------------------------------------
		// | Edit Filter Strategies (Advanced) |
		// -------------------------------------
		// | Last Change : 17.06.2005		   |
		// -------------------------------------
		// | Status : Enabled				   |
		// -------------------------------------
		function edit_strategies_simple($section, $section2, $tablename, $id, $field)
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
					case 'source':
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
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=filter&action=editsimple&sid=".$id."\" name=\"submitform\">";
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
						echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font><BR>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;SOURCE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<select name=\"sources\">\n";
						
						# Generate Any Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Internet <--- </option>\n";
						if ($row['stype'] == '*')
						{
							echo "<option value=\"*\" name=\"any\" selected> Any </option>\n";
						}
						else
						{
							echo "<option value=\"*\" name=\"any\"> Any </option>\n";
						}
						
						# Generate Existing Host Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Hosts <--- </option>\n";
						$result_hosts = mysql_query("select * from no_hosts order by id");
						$number_hosts = mysql_num_rows($result_hosts);
						for ($i=0;$i<$number_hosts;$i++)
						{
							$row_hosts=mysql_fetch_array($result_hosts);
							if (($row['sid']) == $row_hosts['id'])
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
							if ($row['sid'] == $row_networks['id'])
							{
								echo "<option value=\"2".$row_networks['id']."|".$row_networks['name']."\" name=\"network".$row_networks['id']."\" selected> ".$row_networks['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"2".$row_networks['id']."|".$row_networks['name']."\" name=\"network".$row_networks['id']."\"> ".$row_networks['name']." </option>\n";
							}
						}
						
						# Generate Existing Ranges Addresses #
						echo "<option value=\"-\" name=\"dummy\"> ---> Ranges <--- </option>\n";
						$result_ranges = mysql_query("select * from no_ranges order by id");
						$number_ranges = mysql_num_rows($result_ranges);
						for ($i=0;$i<$number_ranges;$i++)
						{
							$row_ranges=mysql_fetch_array($result_ranges);
							if ($row['sid'] == $row_ranges['id'])
							{
								echo "<option value=\"3".$row_ranges['id']."|".$row_ranges['name']."\" name=\"ranges".$row_ranges['id']."\" selected> ".$row_ranges['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"3".$row_ranges['id']."|".$row_ranges['name']."\" name=\"ranges".$row_ranges['id']."\"> ".$row_ranges['name']." </option>\n";
							}
						}
						
						echo "</select></TD></TR>\n";
						
						// Submit Event for Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						//echo "<input type=\"hidden\" value=\"".$id."\" name=\"hiddenid\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$_SERVER['PHP_SELF']."?module=filter\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					// Strategie for Destination
					case 'destination':
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
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=filter&action=editsimple&sid=".$id."\" name=\"submitform\">";
						echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
						echo "			<tr>\n";
						echo "				<td height=\"20px\" colspan=\"2\">\n";
						echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
						echo "			</tr>\n";
						echo "			<tr>\n";
						echo "				<td align=\"left\" width=\"40px\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\">\n";
						
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"230\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font><BR>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;SOURCE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<select name=\"sources\">\n";
						
						// Generate Any Entrys
						echo "<option value=\"-\" name=\"dummy\"> ---> Internet <--- </option>\n";
						if ($row['did'] == '*')
						{
							echo "<option value=\"*\" name=\"any\" selected> Any </option>\n";
						}
						else
						{
							echo "<option value=\"*\" name=\"any\"> Any </option>\n";
						}
						
						// Generate Existing Host Entrys
						echo "<option value=\"-\" name=\"dummy\"> ---> Hosts <--- </option>\n";
						$result_hosts = mysql_query("select * from no_hosts order by id");
						$number_hosts = mysql_num_rows($result_hosts);
						for ($i=0;$i<$number_hosts;$i++)
						{
							$row_hosts=mysql_fetch_array($result_hosts);
							if ($row['did'] == $row_hosts['id'])
							{
								echo "<option value=\"1".$row_hosts['id']."|".$row_hosts['name']."\" name=\"host".$row_hosts['id']."\" selected> ".$row_hosts['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"1".$row_hosts['id']."|".$row_hosts['name']."\" name=\"host".$row_hosts['id']."\"> ".$row_hosts['name']." </option>\n";
							}								
						}
						
						// Generate Existing Network Entrys
						echo "<option value=\"-\" name=\"dummy\"> ---> Networks <--- </option>\n";
						$result_networks = mysql_query("select * from no_networks order by id");
						$number_networks = mysql_num_rows($result_networks);
						for ($i=0;$i<$number_networks;$i++)
						{
							$row_networks=mysql_fetch_array($result_networks);
							if ($row['did'] == $row_networks['id'])
							{
								echo "<option value=\"2".$row_networks['id']."|".$row_networks['name']."\" name=\"network".$row_networks['id']."\" selected> ".$row_networks['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"2".$row_networks['id']."|".$row_networks['name']."\" name=\"network".$row_networks['id']."\"> ".$row_networks['name']." </option>\n";
							}
						}

						# Generate Existing Ranges Addresses #
						echo "<option value=\"-\" name=\"dummy\"> ---> Ranges <--- </option>\n";
						$result_ranges = mysql_query("select * from no_ranges order by id");
						$number_ranges = mysql_num_rows($result_ranges);
						for ($i=0;$i<$number_ranges;$i++)
						{
							$row_ranges=mysql_fetch_array($result_ranges);
							if ($row['sid'] == $row_ranges['id'])
							{
								echo "<option value=\"3".$row_ranges['id']."|".$row_ranges['name']."\" name=\"ranges".$row_ranges['id']."\" selected> ".$row_ranges['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"3".$row_ranges['id']."|".$row_ranges['name']."\" name=\"ranges".$row_ranges['id']."\"> ".$row_ranges['name']." </option>\n";
							}
						}
						
						echo "</select></TD></TR>\n";
						
						// Submit Event for Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						//echo "<input type=\"hidden\" value=\"".$id."\" name=\"hiddenid\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$_SERVER['PHP_SELF']."?module=filter\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					# Strategie for Destination Service #
					case 'datype':
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
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=filter&action=editsimple&sid=".$id."\" name=\"submitform\">";
						echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
						echo "			<tr>\n";
						echo "				<td height=\"20px\" colspan=\"2\">\n";
						echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
						echo "			</tr>\n";
						echo "			<tr>\n";
						echo "				<td align=\"left\" width=\"40px\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\">\n";
						
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"230\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;SERVICE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<select name=\"sources\">\n";
						
						# Generate Any Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Internet <--- </option>\n";
						if ($row['datype'] == '*')
						{
							echo "<option value=\"*\" name=\"any\" selected> Any </option>\n";
						}
						else
						{
							echo "<option value=\"*\" name=\"any\"> Any </option>\n";
						}
						
						# Generate Existing Service Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Services <--- </option>\n";
						$result_services = mysql_query("select * from so_services order by id");
						$number_services = mysql_num_rows($result_services);
						for ($i=0;$i<$number_services;$i++)
						{
							$row_services=mysql_fetch_array($result_services);
							if ($row['daid'] == $row_services['id'])
							{
								echo "<option value=\"1".$row_services['id']."|".$row_services['name']."\" name=\"host".$row_services['id']."\" selected> ".$row_services['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"1".$row_services['id']."|".$row_services['name']."\" name=\"host".$row_services['id']."\"> ".$row_services['name']." </option>\n";
							}								
						}
						
						echo "</select></TD></TR>\n";
						
						// Submit Event for Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						//echo "<input type=\"hidden\" value=\"".$id."\" name=\"hiddenid\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$_SERVER['PHP_SELF']."?module=filter\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'satype':
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
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=filter&action=editsimple&sid=".$id."\" name=\"submitform\">";
						echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
						echo "			<tr>\n";
						echo "				<td height=\"20px\" colspan=\"2\">\n";
						echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
						echo "			</tr>\n";
						echo "			<tr>\n";
						echo "				<td align=\"left\" width=\"40px\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\">\n";
						
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"300\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;SERVICE OR PROTOCOL</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<select name=\"sources\">\n";
						
						# Generate Any Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Internet <--- </option>\n";
						if ($row['satype'] == '*')
						{
							echo "<option value=\"*\" name=\"any\" selected> Any </option>\n";
						}
						else
						{
							echo "<option value=\"*\" name=\"any\"> Any </option>\n";
						}
						
						# Generate Existing Service Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Services <--- </option>\n";
						$result_services = mysql_query("select * from so_services order by id");
						$number_services = mysql_num_rows($result_services);
						for ($i=0;$i<$number_services;$i++)
						{
							$row_services=mysql_fetch_array($result_services);
							if (($row['satype']==1) and ($row['said'] == $row_services['id']))
							{
								echo "<option value=\"1".$row_services['id']."|".$row_services['name']."\" name=\"host".$row_services['id']."\" selected> ".$row_services['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"1".$row_services['id']."|".$row_services['name']."\" name=\"host".$row_services['id']."\"> ".$row_services['name']." </option>\n";
							}								
						}
						echo "<option value=\"-\" name=\"dummy\"> ---> Protocols <--- </option>\n";
						$result_protocols = mysql_query("select * from po_protocols order by id");
						$number_protocols = mysql_num_rows($result_protocols);
						for ($i=0;$i<$number_protocols;$i++)
						{
							$row_protocols=mysql_fetch_array($result_protocols);
							if (($row['satype']==2) and ($row['said'] == $row_protocols['id']))
							{
								echo "<option value=\"2".$row_protocols['id']."|".$row_protocols['pr_keyword']."\" name=\"host".$row_protocols['id']."\" selected> ".$row_protocols['pr_keyword']." </option>\n";
							}
							else
							{
								echo "<option value=\"2".$row_protocols['id']."|".$row_protocols['pr_keyword']."\" name=\"host".$row_protocols['id']."\"> ".$row_protocols['pr_keyword']." </option>\n";
							}								
						}
						echo "</select></TD></TR>\n";
						
						// Submit Event for Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						//echo "<input type=\"hidden\" value=\"".$id."\" name=\"hiddenid\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$_SERVER['PHP_SELF']."?module=filter\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'bactionstatus':
					{
						if ($row['baction'] == 0) # Drop + Not Log
						{
							$result = mysql_query("update $tablename set baction='2' where(id='$id')") or die(mysql_error());
						}
						elseif ($row['baction'] == 1) # Drop + Log
						{
							$result = mysql_query("update $tablename set baction='3' where(id='$id')") or die(mysql_error());
						}
						elseif ($row['baction'] == 2) # Pass + Not Log
						{
							$result = mysql_query("update $tablename set baction='0' where(id='$id')") or die(mysql_error());
						}
						elseif ($row['baction'] == 3) # Pass + Log
						{
							$result = mysql_query("update $tablename set baction='1' where(id='$id')") or die(mysql_error());
						}
						
						correct_priorities($section, $tablename);
						show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
						break;
					}
					case 'bactionlog':
					{
						if ($row['baction'] == 0) # Drop + Not Log
						{
							$result = mysql_query("update $tablename set baction='1' where(id='$id')") or die(mysql_error());
						}
						elseif ($row['baction'] == 1) # Drop + Log
						{
							$result = mysql_query("update $tablename set baction='0' where(id='$id')") or die(mysql_error());
						}
						elseif ($row['baction'] == 2) # Pass + Not Log
						{
							$result = mysql_query("update $tablename set baction='3' where(id='$id')") or die(mysql_error());
						}
						elseif ($row['baction'] == 3) # Pass + Log
						{
							$result = mysql_query("update $tablename set baction='2' where(id='$id')") or die(mysql_error());
						}
						
						correct_priorities($section, $tablename);
						show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
						break;
					}
					case 'siface':
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
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=filter&action=editsimple&sid=".$id."\" name=\"submitform\">";
						echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
						echo "			<tr>\n";
						echo "				<td height=\"20px\" colspan=\"2\">\n";
						echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
						echo "			</tr>\n";
						echo "			<tr>\n";
						echo "				<td align=\"left\" width=\"40px\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\">\n";
						
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"320\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"240\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"240\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;INTERFACE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						
						echo "<select name=\"sinterfaces\">\n";
						
						$fdata = mysql_query("select siface from $tablename where(id=$id)");
						$row_fdata = mysql_fetch_array($fdata);
						
						$result_interfaces = mysql_query("select * from io_interfaces order by id");
						$number_interfaces = mysql_num_rows($result_interfaces);
						
						for ($i=0;$i<$number_interfaces;$i++)
						{
							$row_interfaces=mysql_fetch_array($result_interfaces);
							
							if ($row_fdata['siface'] == ($row_interfaces['id'] ))
							{
								echo "<option value=\"".$row_interfaces['id']."|".$row_interfaces['name']."\" name=\"sinterfaces".$row_interfaces['id']."\" selected> ".$row_interfaces['note']." (".$row_interfaces['name'].") </option>\n";
							}
							else
							{
								echo "<option value=\"".$row_interfaces['id']."|".$row_interfaces['name']."\" name=\"sinterfaces".$row_interfaces['id']."\"> ".$row_interfaces['note']." (".$row_interfaces['name'].") </option>\n";
							}
						}
						
						if ($row_fdata['siface'] == '*')
						{
							echo "<option value=\"*|all\ name=\"sinterfaces\" selected> all interfaces </option>\n";
						}
						else
						{
							echo "<option value=\"*|all\ name=\"sinterfaces\"> all </option>\n";
						}
						
						# Submit Event Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						//echo "<input type=\"hidden\" value=\"".$sid."\" name=\"hiddenid\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"".$_SERVER['PHP_SELF']."?module=filter\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'diface':
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
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=filter&action=editsimple&sid=".$id."\" name=\"submitform\">";
						echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
						echo "			<tr>\n";
						echo "				<td height=\"20px\" colspan=\"2\">\n";
						echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
						echo "			</tr>\n";
						echo "			<tr>\n";
						echo "				<td align=\"left\" width=\"40px\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\">\n";
						
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"320\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"240\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"240\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;INTERFACE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						
						echo "<select name=\"dinterfaces\">\n";
						
						$fdata = mysql_query("select diface from $tablename where(id=".$id.")");
						$row_fdata = mysql_fetch_array($fdata);
						
						$result_interfaces = mysql_query("select * from io_interfaces order by id");
						$number_interfaces = mysql_num_rows($result_interfaces);
						
						for ($i=0;$i<$number_interfaces;$i++)
						{
							$row_interfaces=mysql_fetch_array($result_interfaces);
							
							if ($row_fdata['diface'] == ($row_interfaces['id'] ))
							{
								echo "<option value=\"".$row_interfaces['id']."|".$row_interfaces['name']."\" name=\"dinterfaces".$row_interfaces['id']."\" selected> ".$row_interfaces['note']." (".$row_interfaces['name'].") </option>\n";
							}
							else
							{
								echo "<option value=\"".$row_interfaces['id']."|".$row_interfaces['name']."\" name=\"dinterfaces".$row_interfaces['id']."\"> ".$row_interfaces['note']." (".$row_interfaces['name'].") </option>\n";
							}
						}
						
						if ($row_fdata['diface'] == '*')
						{
							echo "<option value=\"*|all\ name=\"dinterfaces\" selected> all interfaces </option>\n";
						}
						else
						{
							echo "<option value=\"*|all\ name=\"dinterfaces\"> all </option>\n";
						}
						
						# Submit Event Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						//echo "<input type=\"hidden\" value=\"".$sid."\" name=\"hiddenid\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"".$_SERVER['PHP_SELF']."?module=filter\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case "protopt":
					{
					
						// Get Protocol Option Type
						$sql_db_local = new dbvars;
                                                $result_protopt_type=mysql_query("SELECT id,pr_decimal FROM ".$sql_db_local->sql_db_table_po_protocols." WHERE id=".$row['said']) or die(mysql_error());
						$result_protopt_type=mysql_fetch_array($result_protopt_type);
						switch ($result_protopt_type['pr_decimal']) {
						        case 1: // At the moment only ICMP has options
					                        $list_delimiter = " ---> ICMP_Type <--- ";
					                        $db_table = "icmp_types";
					                        $result_protopt = mysql_query("SELECT * FROM ".$db_table) or die(mysql_error());
					                        $number_protopt = mysql_num_rows($result_protopt);
					                        $db_field1 = "id";
					                        $db_field2 = "icmp_type";
					                        $db_field3 = "icmp_name";
                                                                break;
                                                        default:
                                                        errorcode(7,0);
                                                        break;

						}

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
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$id."\" name=\"submitform\">";
						echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
						echo "			<tr>\n";
						echo "				<td height=\"20px\" colspan=\"2\">\n";
						echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
						echo "			</tr>\n";
						echo "			<tr>\n";
						echo "				<td align=\"left\" width=\"40px\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\">\n";
						
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"330\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"130\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"130\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"200\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"200\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PROTOCOL OPTION:</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<select name=\"sources\">\n";
						
						# Generate Any Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Internet <--- </option>\n";
						if ($row['datype'] == '*')
						{
							echo "<option value=\"*\" name=\"any\" selected> Any </option>\n";
						}
						else
						{
							echo "<option value=\"*\" name=\"any\"> Any </option>\n";
						}
						
						# Generate Existing Service Entrys #
						echo "<option value=\"-\" name=\"dummy\">".$list_delimiter."</option>\n";
						for ($i=0;$i<$number_protopt;$i++)
						{
                                                        $row_protopt = mysql_fetch_array($result_protopt);
                                                        if ($row['daid'] == $row_protopt[$db_field1])
							{
								echo "<option value=\"".$row_protopt[$db_field1]."\" name=\"option".$row_protopt[$db_field1]."\" selected> ".$row_protopt[$db_field3]." </option>\n";
							}
							else
							{
								echo "<option value=\"".$row_protopt[$db_field1]."\" name=\"option".$row_protopt[$db_field1]."\"> ".$row_protopt[$db_field3]." </option>\n";
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
    					        echo "<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
				if (isset($_POST['sinterfaces']))
				{
					$fdata = mysql_query("update strategies_filter set siface='".substr($_POST['sinterfaces'],0,strpos($_POST['sinterfaces'],'|'))."' where(id='".$_GET['sid']."')");
					correct_priorities($section, $tablename);
					show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
				}
				elseif (isset($_POST['dinterfaces']))
				{
					$fdata = mysql_query("update strategies_filter set diface='".substr($_POST['dinterfaces'],0,strpos($_POST['dinterfaces'],'|'))."' where(id='".$_GET['sid']."')");
					correct_priorities($section, $tablename);
					show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
				}
				else
				{
					if ($_POST['hiddenfield'] == 'satype')
					{
						switch(substr($_POST['sources'],0,1))
						{
							case '-':
							{
								# Show Strategies (Default Mode)
								correct_priorities($section, $tablename);
								show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
								break;
							}
							case '*':
							{
								//$result = mysql_query("update $tablename set ".$hiddenfield."='any' where(id='$hiddenid')") or die(mysql_error());
								$result = mysql_query("update ".$tablename." set satype='*' where(id='".$_GET['sid']."')") or die(mysql_error());
								$result = mysql_query("update ".$tablename." set said='*' where(id='".$_GET['sid']."')") or die(mysql_error());
								
								# Show Strategies (Default Mode)
								correct_priorities($section, $tablename);
								show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
								break;
							}
							case '1':
							        $result = mysql_query("update ".$tablename." set satype='".substr($_POST['sources'],0,1)."' where(id='".$_GET['sid']."')") or die(mysql_error());
								$result = mysql_query("update ".$tablename." set said='".substr($_POST['sources'],1,strpos($_POST['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(mysql_error());
								
								# Show Strategies (Default Mode)
								correct_priorities($section, $tablename);
								show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
								break;
							case '2':
							{
                                                                $result = mysql_query("update ".$tablename." set satype='".substr($_POST['sources'],0,1)."' where(id='".$_GET['sid']."')") or die(mysql_error());
								$result = mysql_query("update ".$tablename." set said='".substr($_POST['sources'],1,strpos($_POST['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(mysql_error());
								$result2 = mysql_query("UPDATE ".$tablename." SET datype='*' WHERE id='".$_GET['sid']."'");
								$result2 = mysql_query("UPDATE ".$tablename." SET daid='*' WHERE id='".$_GET['sid']."'");
								# Show Strategies (Default Mode)
								correct_priorities($section, $tablename);
								show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
								break;
							}
							case '3':
							{
                                $result = mysql_query("update ".$tablename." set satype='".substr($_POST['sources'],0,1)."' where(id='".$_GET['sid']."')") or die(mysql_error());
								$result = mysql_query("update ".$tablename." set said='".substr($_POST['sources'],1,strpos($_POST['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(mysql_error());
								$result2 = mysql_query("UPDATE ".$tablename." SET datype='*' WHERE id='".$_GET['sid']."'");
								$result2 = mysql_query("UPDATE ".$tablename." SET daid='*' WHERE id='".$_GET['sid']."'");
								# Show Strategies (Default Mode)
								correct_priorities($section, $tablename);
								show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
								break;
							}
						}
					}
					elseif ($_POST['hiddenfield'] == 'datype')
					{
						switch(substr($_POST['sources'],0,1))
						{
							case '-':
							{
								# Show Strategies (Default Mode)
								correct_priorities($section, $tablename);
								show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
								break;
							}
							case '*':
							{
								//$result = mysql_query("update $tablename set ".$hiddenfield."='any' where(id='$hiddenid')") or die(mysql_error());
								$result = mysql_query("update ".$tablename." set datype='*' where(id='".$_GET['sid']."')") or die(mysql_error());
								$result = mysql_query("update ".$tablename." set daid='*' where(id='".$_GET['sid']."')") or die(mysql_error());
								
								# Show Strategies (Default Mode)
								correct_priorities($section, $tablename);
								show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
								break;
							}
							case '1':
							case '2':
							case '3':
							{
								$result = mysql_query("update ".$tablename." set datype='".substr($GLOBALS['sources'],0,1)."' where(id='".$_GET['sid']."')") or die(mysql_error());
								$result = mysql_query("update ".$tablename." set daid='".substr($GLOBALS['sources'],1,strpos($GLOBALS['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(mysql_error());
								
								# Show Strategies (Default Mode)
								correct_priorities($section, $tablename);
								show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
								break;
							}
						}
					}
					elseif ($_POST['hiddenfield'] == 'source')
					{
					        switch(substr($_POST['sources'],0,1))
						{
							case '-':
							{
								# Show Strategies (Default Mode)
								correct_priorities($section, $tablename);
								show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
								break;
							}
							case '*':
							{
								//$result = mysql_query("update $tablename set ".$hiddenfield."='any' where(id='$hiddenid')") or die(mysql_error());
								$result = mysql_query("update ".$tablename." set stype='*' where(id='".$_GET['sid']."')") or die(mysql_error());
								$result = mysql_query("update ".$tablename." set sid='*' where(id='".$_GET['sid']."')") or die(mysql_error());
								
								# Show Strategies (Default Mode)
								correct_priorities($section, $tablename);
								show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
								break;
							}
							case '1':
							case '2':
							case '3':
							{
								$result = mysql_query("update ".$tablename." set stype='".substr($_POST['sources'],0,1)."' where(id='".$_GET['sid']."')") or die(mysql_error());
								$result = mysql_query("update ".$tablename." set sid='".substr($_POST['sources'],1,strpos($_POST['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(mysql_error());
								
								# Show Strategies (Default Mode)
								correct_priorities($section, $tablename);
								show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
								break;
							}
						}
					}
					elseif ($_POST['hiddenfield'] == 'destination')
					{
						switch(substr($_POST['sources'],0,1))
						{
							case '-':
							{
								# Show Strategies (Default Mode)
								correct_priorities($section, $tablename);
								show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
								break;
							}
							case '*':
							{
								//$result = mysql_query("update $tablename set ".$hiddenfield."='any' where(id='$hiddenid')") or die(mysql_error());
								$result = mysql_query("update ".$tablename." set dtype='*' where(id='".$_GET['sid']."')") or die(mysql_error());
								$result = mysql_query("update ".$tablename." set did='*' where(id='".$_GET['sid']."')") or die(mysql_error());
								
								# Show Strategies (Default Mode)
								correct_priorities($section, $tablename);
								show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
								break;
							}
							case '1':
							case '2':
							case '3':
							{
								$result = mysql_query("update ".$tablename." set dtype='".substr($_POST['sources'],0,1)."' where(id='".$_GET['sid']."')") or die(mysql_error());
								$result = mysql_query("update ".$tablename." set did='".substr($_POST['sources'],1,strpos($_POST['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(mysql_error());
								
								# Show Strategies (Default Mode)
								correct_priorities($section, $tablename);
								show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
								break;
							}
						}
					}
					elseif ($_POST['hiddenfield'] == 'protopt')
					{
                        if($_POST['sources']!="-")
                            $result = mysql_query("UPDATE ".$tablename." SET daid='".$_POST['sources']."' WHERE id=".$_GET['sid']) or die("error while updating protocol option type: ".mysql_error());
					
                        show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
				    }
				}
			}
		}			
		
		// ----------------------------------
		// | Default Style - Show Strategie |
		// ----------------------------------
		// | Last Change : 17.06.2005		|
		// ----------------------------------
		// | Status : Enabled				|
		// ----------------------------------
		function show_strategies($type, $section, $section2, $tablename)
		{
			$result = mysql_query("select * from ".$tablename." order by priority") or die(mysql_error());
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
					$result2 = mysql_query("select * from strategies_filter_default order BY chainname") or die(mysql_error());
					$number2 = mysql_num_rows($result2);
					
					echo "					<table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"350px\" height=\"\">\n";
					echo "						<tr bgcolor=\"#565656\" class=\"tablehead\">\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"200\" height=\"22\">\n";
					echo "								<font color=\"#ffffff\">&nbsp;CHAIN</font>\n";
					echo "								<img src=\"images/border_orange.gif\" width=\"200\" height=\"6\" border=\"0\"></td>\n";
					echo "  						<td valign=\"bottom\" align=\"middle\" width=\"150\" height=\"22\">\n";
					echo "   							<font color=\"#ffffff\">&nbsp;DEFAULT POLICY</font>\n";
					echo "   							<img src=\"images/border_orange.gif\" WIDTH=\"150\" height=\"6\" border=\"0\"></td>\n";
					echo " 						</tr>\n";
					
					# Read and Display Database Entries #				
					for ($i=0; $i < $number2; $i++)
					{
						$row2 = mysql_fetch_array($result2);
						
						if (is_float(($i/2)) == false)
							echo "						<tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
						else
							echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
						
						echo "						<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">&nbsp;".$row2['chainname']."</td>\n";
						echo "						<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">\n";
						
						if ($row2['chainvalue'] == 0)
							echo "							&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=chains&sid=".$row2['id']."&value=1\" title=\"Change default Policy to PASS\"><IMG SRC=\"images/icons/drop.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"drop\"></a>";
						elseif ($row2['chainvalue'] == 1)
							echo "							&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=chains&sid=".$row2['id']."&value=0\" title=\"Change default Policy to DROP\"><IMG SRC=\"images/icons/pass.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"pass\"></a>";
						
						echo "					</tr>\n";
					}
					
					echo "						<tr bgcolor=\"#565656\">\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						</tr>\n";
					echo "						<tr>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						</tr>\n";
					echo "						<tr>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						</tr>\n";					
					echo "					</table>\n";
					
					# Generate Table-Header #
					echo "					<table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"911px\" height=\"\">\n";
					echo "						<tr bgcolor=\"#565656\" class=\"tablehead\">\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"32\" height=\"22\">\n";
					echo "								<font color=\"#ffffff\">&nbsp;</font>\n";
					echo "								<img src=\"images/border_orange.gif\" width=\"32\" height=\"6\" border=\"0\"></td>\n";
					echo "  						<td colspan=\"2\" valign=\"bottom\" align=\"left\" width=\"247\" height=\"22\">\n";
					echo "   							<font color=\"#ffffff\">&nbsp;SOURCE</font>\n";
					echo "   							<img src=\"images/border_orange.gif\" WIDTH=\"247\" height=\"6\" border=\"0\"></td>\n";
					echo "  						<td valign=\"bottom\" align=\"center\" width=\"75\" height=\"22\">\n\n";
					echo "   							<font color=\"#ffffff\">DIRECTION</font>\n";
					echo "  							<img src=\"images/border_orange.gif\" WIDTH=\"75\" height=\"6\" border=\"0\"></td>\n";
					echo "  						<td colspan=\"2\" valign=\"bottom\" align=\"left\" width=\"247\" height=\"22\">\n\n";
					echo "   							<font color=\"#ffffff\">&nbsp;DESTINATION</font>\n";
					echo "  							<img src=\"images/border_orange.gif\" WIDTH=\"247\" height=\"6\" border=\"0\"></td>\n";
                                        echo "  						<td valign=\"bottom\" align=\"center\" width=\"70\" height=\"22\">\n";
					echo "   							<font color=\"#ffffff\">STATES</font>\n";
					echo "   							<img src=\"images/border_orange.gif\" WIDTH=\"70\" height=\"6\" border=\"0\"></td>\n";
					echo "  						<td valign=\"bottom\" align=\"center\" width=\"70\" height=\"22\">\n";
					echo "   							<font color=\"#ffffff\">POLICY</font>\n";
					echo "   							<img src=\"images/border_orange.gif\" WIDTH=\"70\" height=\"6\" border=\"0\"></td>\n";
					echo " 							<td valign=\"bottom\" align=\"center\" width=\"110\" height=\"22\">\n";
					echo "   							<font color=\"#ffffff\">ACTION</font>\n";
					echo "   							<img src=\"images/border_orange.gif\" WIDTH=\"110\" height=\"6\" border=\"0\"></td>\n";
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
							
							echo "							<td rowspan=\"2\" valign=\"top\" align=\"center\" width=\"\" height=\"20\">";
							if ($row['status'])
								echo "								&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setstatus&sid=".$row['id']."&field=status\" title=\"deactivate rule\"><IMG SRC=\"images/icons/on.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"on\"></a>&nbsp;</td>";
							else
								echo "								&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setstatus&sid=".$row['id']."&field=status\" title=\"activate rule\"><IMG SRC=\"images/icons/off.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"off\"></a>&nbsp;</td>";
							
							switch ($row['stype'])
							{
								# Any #
								case '*':
								{
									echo "							<td colspan=\"2\" valign=\"top\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=source\" title=\"select source host/network/range\">";
									echo "											&nbsp;<IMG SRC=\"images/icons/inet.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"any\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=source\" title=\"select source host/network/range\">";
									echo "							 				any</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
								# Hosts #
								case '1':
								{
									$result2= mysql_query("select * from no_hosts where (id=".$row['sid'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td colspan=\"2\" valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=source\" title=\"select source host/network/range\">";
									echo "								&nbsp;<IMG SRC=\"images/icons/host.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"host\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=source\" title=\"select source host/network/range\">";
									echo "								".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}					
								# Networks #
								case '2':
								{
									$result2 = mysql_query("select * from no_networks where (id=".$row['sid'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td colspan=\"2\" valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=source\" title=\"select source host/network/range\">";
									echo "								&nbsp;<IMG SRC=\"images/icons/network.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=source\" title=\"select source host/network/range\">";
									echo "								".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
								# Ranges #
								case '3':
								{
									$result2 = mysql_query("select * from no_ranges where (id=".$row['sid'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td colspan=\"2\" valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=source\" title=\"select source host/network/range\">";
									echo "								&nbsp;<IMG SRC=\"images/icons/network.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=source\" title=\"select source host/network/range\">";
									echo "								".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
							}
							
							if ($row['direction'] == 0)
							{
								echo "							<td rowspan=\"2\" valign=\"top\" align=\"center\" width=\"\" height=\"20\">\n";
								echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
								echo "									<tr valign=\"top\">\n";
								echo "										<td align=\"left\">\n";
								echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setdirection&sid=".$row['id']."&direction=0\" title=\"packet direction INCOMING\">";
								echo "								&nbsp;<IMG SRC=\"images/icons/input.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
								echo "										</td>\n";
								echo "										<td align=\"left\">\n";
								echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setdirection&sid=".$row['id']."&direction=1\" title=\"packet direction FORWARD\">";
								echo "								<IMG SRC=\"images/icons/forward_off.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
								echo "										</td>\n";
								echo "										<td align=\"left\">\n";
								echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setdirection&sid=".$row['id']."&direction=2\" title=\"packet direction OUTGOING\">";
								echo "								<IMG SRC=\"images/icons/output_off.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
								echo "										</td>\n";
								echo "									</tr>\n";
								echo "								</table>\n";
								echo "							</td>\n";
							}
							elseif ($row['direction'] == 1)
							{
								echo "							<td rowspan=\"2\" valign=\"top\" align=\"center\" width=\"\" height=\"20\">\n";
								echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
								echo "									<tr valign=\"top\">\n";
								echo "										<td align=\"left\">\n";
								echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setdirection&sid=".$row['id']."&direction=0\" title=\"packet direction INCOMING\">";
								echo "								&nbsp;<IMG SRC=\"images/icons/input_off.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
								echo "										</td>\n";
								echo "										<td align=\"left\">\n";
								echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setdirection&sid=".$row['id']."&direction=1\" title=\"packet direction FORWARD\">";
								echo "								<IMG SRC=\"images/icons/forward.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
								echo "										</td>\n";
								echo "										<td align=\"left\">\n";
								echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setdirection&sid=".$row['id']."&direction=2\" title=\"packet direction OUTGOING\">";
								echo "								<IMG SRC=\"images/icons/output_off.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
								echo "										</td>\n";
								echo "									</tr>\n";
								echo "								</table>\n";
								echo "							</td>\n";
							}
							elseif ($row['direction'] == 2)
							{
								echo "							<td rowspan=\"2\" valign=\"top\" align=\"center\" width=\"\" height=\"20\">\n";
								echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
								echo "									<tr valign=\"top\">\n";
								echo "										<td align=\"left\">\n";
								echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setdirection&sid=".$row['id']."&direction=0\" title=\"packet direction INCOMING\">";
								echo "								&nbsp;<IMG SRC=\"images/icons/input_off.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
								echo "										</td>\n";
								echo "										<td align=\"left\">\n";
								echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setdirection&sid=".$row['id']."&direction=1\" title=\"packet direction FORWARD\">";
								echo "								<IMG SRC=\"images/icons/forward_off.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
								echo "										</td>\n";
								echo "										<td align=\"left\">\n";
								echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setdirection&sid=".$row['id']."&direction=2\" title=\"packet direction OUTGOING\">";
								echo "								<IMG SRC=\"images/icons/output.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
								echo "										</td>\n";
								echo "									</tr>\n";
								echo "								</table>\n";
								echo "							</td>\n";
							}
							else
							{
								echo "							<td rowspan=\"2\" valign=\"middle\" align=\"center\" width=\"\" height=\"20\">\n";
								echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
								echo "									<tr valign=\"middle\">\n";
								echo "										<td align=\"left\">\n";
								echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setdirection&sid=".$row['id']."&direction=0\" title=\"packet direction INCOMING\">";
								echo "								&nbsp;<IMG SRC=\"images/icons/input_off.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
								echo "										</td>\n";
								echo "										<td align=\"left\">\n";
								echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setdirection&sid=".$row['id']."&direction=1\" title=\"packet direction FORWARD\">";
								echo "								<IMG SRC=\"images/icons/forward_off.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
								echo "										</td>\n";
								echo "										<td align=\"left\">\n";
								echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setdirection&sid=".$row['id']."&direction=3\" title=\"packet direction OUTGOING\">";
								echo "								<IMG SRC=\"images/icons/output_off.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
								echo "										</td>\n";
								echo "									</tr>\n";
								echo "								</table>\n";
								echo "							</td>\n";
							}
							
							switch ($row['dtype'])
							{
								# Any #
								case '*':
								{
									echo "							<td colspan=\"2\" valign=\"top\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=destination\" title=\"select destination host/network/ranges\">";
									echo "											&nbsp;<IMG SRC=\"images/icons/inet.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"any\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=destination\" title=\"select destination host/network/ranges\">";
									echo "							 				any</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
								# Hosts #
								case '1':
								{
									$result2 = mysql_query("select * from no_hosts where (id=".$row['did'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td colspan=\"2\" valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "								&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=destination\" title=\"select destination host/network/ranges\">";
									echo "								<IMG SRC=\"images/icons/host.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=destination\" title=\"select destination host/network/ranges\">";
									echo "								".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}	
								# Networks #
								case '2':
								{
									$result2= mysql_query("select * from no_networks where (id=".$row['did'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td colspan=\"2\" valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=destination\" title=\"select destination host/network/ranges\">";
									echo "								&nbsp;<IMG SRC=\"images/icons/network.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=destination\" title=\"select destination host/network/ranges\">";
									echo "								".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
								# Ranges #
								case '3':
								{
									$result2= mysql_query("select * from no_ranges where (id=".$row['did'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td colspan=\"2\" valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=destination\" title=\"select destination host/network/ranges\">";
									echo "								&nbsp;<IMG SRC=\"images/icons/network.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=destination\" title=\"select destination host/network/ranges\">";
									echo "								".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
							}
							
							echo "						<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">\n";
                            echo "                                                  <table border=\"0\" cellspacing=\"0\" cellpadding=\"0\" height=\"100%\" width=\"100%\" align=\"center\" valign=\"middle\">";
                            echo "                                                          <tr align=\"center\" valign=\"top\">";
                            echo "                                                                  <td width=\"100%\" align=\"center\" valign=\"middle\">";
                            echo "                                                                    <a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setstate&sid=".$row['id']."&field=new\" title=\"connection state NEW\"><img src=\"images/icons/new_".check_states($tablename, "new", $row['id']).".gif\" border=\"0\"></a>&nbsp;&nbsp;\n";
                            echo "                                                                    <a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setstate&sid=".$row['id']."&field=established\" title=\"connection state ESTABLISHED\"><img src=\"images/icons/established_".check_states($tablename, "established", $row['id']).".gif\" border=\"0\"></a><br>\n";
                            echo "                                                                  </td>";
							echo "                                                          </tr>";
							echo "                                                   </table>";
							echo "                                          </td>";

                            echo "						<td rowspan=\"2\" valign=\"top\" align=\"middle\" width=\"\" height=\"20\">\n";
							if ($row['baction'] == 0)
								echo "							&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=bactionstatus\" title=\"action to perform (DROP)\"><IMG SRC=\"images/icons/drop.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"drop\"></a>&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=bactionlog\" title=\"turn ON logging\"><IMG SRC=\"images/icons/notlog.gif\" ALT=\"log\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\"></a>";
							elseif ($row['baction'] == 1)
								echo "							&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=bactionstatus\" title=\"action to perform (DROP)\"><IMG SRC=\"images/icons/drop.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"drop\"></a>&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=bactionlog\" title=\"turn OFF logging\"><IMG SRC=\"images/icons/log.gif\" ALT=\"log\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\"></a>";
							elseif ($row['baction'] == 2)
								echo "							&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=bactionstatus\" title=\"action to perform (PASS)\"><IMG SRC=\"images/icons/pass.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"pass\"></a>&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=bactionlog\" title=\"turn ON logging\"><IMG SRC=\"images/icons/notlog.gif\" ALT=\"log\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\"></a>";
							elseif ($row['baction'] == 3)
								echo "							&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=bactionstatus\" title=\"action to perform (PASS)\"><IMG SRC=\"images/icons/pass.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"pass\"></a>&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=bactionlog\" title=\"turn OFF logging\"><IMG SRC=\"images/icons/log.gif\" ALT=\"log\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\"></a>";
							
							//echo "							<IMG SRC=\"images/icons/time_off.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"\"></td>\n";
							
							echo "						<td rowspan=\"2\" valign=\"top\" align=\"middle\" width=\"\" height=\"20\">\n";
							echo "							&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=priorityup&sid=".$row['id']."&field=priority\" title=\"priority: UP\"><IMG SRC=\"images/icons/up.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"up\"></a>";
							echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=prioritydown&sid=".$row['id']."&field=priority\" title=\"priority: DOWN\"><IMG SRC=\"images/icons/down.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"down\"></a>";
							echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=delete&sid=".$row['id']."\" title=\"delete rule\"><IMG SRC=\"images/icons/delete.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\ ALT=\"delete\"></a>";
							echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=addafter&sid=".$row['id']."&field=status\" title=\"add: AFTER\"><IMG SRC=\"images/icons/add_after.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"add after\"></a>";
							echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=addbefore&sid=".$row['id']."&field=status\" title=\"add: BEFORE\"><IMG SRC=\"images/icons/add_before.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"add before\"></a>&nbsp;</td>\n";
							
							echo "					</tr>\n";
							
							if (is_float(($i/2)) == false)
								echo "						<tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
							else
								echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
							
							switch ($row['satype'])
							{
								# Any #
								case '*':
								{
									echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\">&nbsp;\n";
									echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=satype\" title=\"source service\">any</a>";
									echo "							</td>\n";
									break;
								}
								# Services #
								case '1':
								{
                                                                	$result2 = mysql_query("select * from so_services where (id=".$row['said'].")");
									$gather = mysql_fetch_array($result2);
									echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\">&nbsp;\n";
									echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=satype\" title=\"source service\">".$gather['name']."</a>";
									echo "							</td>\n";
									break;
								}
								case '2':
								{
								        $result2 = mysql_query("SELECT * FROM po_protocols WHERE (id=".$row['said'].")");
									$gather = mysql_fetch_array($result2);
									echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\" class=\"textred\">&nbsp;\n";
									echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=satype\" title=\"source PROTOCOL\">".$gather['pr_keyword']."</a>";
									echo "							</td>\n";
									break;
								}
							}
							
							if ($row['direction'] == 0)
							{
								if ($row['siface'] != '*')
								{
									$result2= mysql_query("select * from io_interfaces where (id=".$row['siface'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td valign=\"middle\" align=\"left\" width=\"80px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td valign=\"middle\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=siface\" title=\"source interface\"><img src=\"./images/icons/interface.gif\" border=\"0\"></a></td>";
									echo "										<td valign=\"middle\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=siface\" title=\"source interface\">".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								}
								else
								{
									echo "							<td valign=\"middle\" align=\"left\" width=\"80px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td valign=\"middle\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=siface\" title=\"source interface\"><img src=\"./images/icons/interface.gif\" border=\"0\"></a></td>";
									echo "										<td valign=\"middle\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=siface\" title=\"source interface\">all</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								}
							}
							elseif ($row['direction'] == 1)
							{
								if ($row['siface'] != '*')
								{
									$result2= mysql_query("select * from io_interfaces where (id=".$row['siface'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td valign=\"middle\" align=\"left\" width=\"80px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td valign=\"middle\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=siface\" title=\"source interface\"><img src=\"./images/icons/interface.gif\" border=\"0\"></a></td>";
									echo "										<td valign=\"middle\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=siface\" title=\"source interface\">".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								}
								else
								{
									echo "							<td valign=\"middle\" align=\"left\" width=\"80px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td valign=\"middle\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=siface\" title=\"source interface\"><img src=\"./images/icons/interface.gif\" border=\"0\"></a></td>";
									echo "										<td valign=\"middle\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=siface\" title=\"source interface\">all</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								}
							}
							elseif ($row['direction'] == 2)
							{
								if ($row['siface'] != '*')
								{
									$result2= mysql_query("select * from io_interfaces where (id=".$row['siface'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td valign=\"middle\" align=\"left\" width=\"80px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td valign=\"middle\" align=\"left\">\n";
									echo "											&nbsp;<img src=\"./images/icons/interface.gif\" border=\"0\"></td>\n";
									echo "										<td valign=\"middle\" align=\"left\">\n";
									echo "											&nbsp;-</td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								}
								else
								{
									echo "							<td valign=\"middle\" align=\"left\" width=\"80px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\" valign=\"middle\">\n";
									echo "											&nbsp;<img src=\"./images/icons/interface.gif\" border=\"0\"></td>\n";
									echo "										<td align=\"left\" valign=\"middle\">\n";
									echo "											&nbsp;-</td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								}
							}
							
							switch ($row['datype'])
							{
							# Any #
								case '*':
								{
								        if ($row['satype']!=2) {
									       echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\">&nbsp;\n";
                                                                               echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=datype\" title=\"destination service\">any</a>";
									} elseif ($row['satype']==2) {
								                echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\" class=\"textred\">&nbsp;\n";
                                                                                parse_protocol_options($tablename, $row['id'], $section);
                                                                               //echo "							-"; // Case all
									}
								        break;
								}
								# Services #
								case '1':
								{
									$result2 = mysql_query("select * from so_services where (id=".$row['daid'].")");
									$gather = mysql_fetch_array($result2);
									echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\">&nbsp;\n";
                                                                        echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=datype\" title=\"destination service\">".$gather['name']."</a>";
									break;
								}
								# Protocols #
								case '2':
								{
								        echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\" class=\"textred\">&nbsp;\n";
								        if ($row['satype']==2) {
                                                                                echo "&nbsp;".parse_protocol_options($tablename, $row['id'], $section);
                                                                        } else {
                                                                                echo "&nbsp;parse error";
                                                                        }
                                                                        
								}
							}
							echo "							</td>\n";
							if ($row['direction'] == 0)
							{
								if ($row['diface'] != '*')
								{
									$result2= mysql_query("select * from io_interfaces where (id=".$row['diface'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td valign=\"middle\" align=\"left\" width=\"80px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "											&nbsp;<img src=\"./images/icons/interface.gif\" border=\"0\"></td>\n";
									echo "										<td align=\"left\">\n";
									echo "											-</td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								}
								else
								{
									echo "							<td valign=\"middle\" align=\"left\" width=\"80px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "											&nbsp;<img src=\"./images/icons/interface.gif\" border=\"0\"></td>\n";
									echo "										<td align=\"left\">\n";
									echo "											&nbsp;-</td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								}
							}
							elseif ($row['direction'] == 1)
							{
								if ($row['diface'] != '*')
								{
									$result2= mysql_query("select * from io_interfaces where (id=".$row['diface'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td valign=\"middle\" align=\"left\" width=\"80px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=diface\" title=\"destination interface\"><img src=\"./images/icons/interface.gif\" border=\"0\"></a></td>\n";
									echo "										<td align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=diface\" title=\"destination interface\">".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								}
								else
								{
									echo "							<td valign=\"middle\" align=\"left\" width=\"80px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=diface\" title=\"destination interface\"><img src=\"./images/icons/interface.gif\" border=\"0\"></a></td>\n";
									echo "										<td align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=diface\" title=\"destination interface\">all</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								}
							}
							elseif ($row['direction'] == 2)
							{
								if ($row['diface'] != '*')
								{
									$result2= mysql_query("select * from io_interfaces where (id=".$row['diface'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td valign=\"middle\" align=\"left\" width=\"80px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=diface\" title=\"destination interface\"><img src=\"./images/icons/interface.gif\" border=\"0\"></a></td>\n";
									echo "										<td align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=diface\" title=\"destination interface\">".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								}
								else
								{
									echo "							<td valign=\"middle\" align=\"left\" width=\"80px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=diface\" title=\"destination interface\"><img src=\"./images/icons/interface.gif\" border=\"0\"></a></td>\n";
									echo "										<td align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$row['id']."&field=diface\" title=\"destination interface\">all</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								}
							}

							echo "						<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">\n";
                            echo "                                                  <table border=\"0\" cellspacing=\"0\" cellpadding=\"0\" height=\"100%\" width=\"100%\" align=\"center\" valign=\"middle\">";
                            echo "                                                          <tr align=\"center\" valign=\"bottom\">";
                            echo "                                                                  <td width=\"100%\" align=\"center\" valign=\"bottom\">";
                            echo "                                                                    <a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setstate&sid=".$row['id']."&field=related\" title=\"connection state RELATED\"><img src=\"images/icons/related_".check_states($tablename, "related", $row['id']).".gif\" border=\"0\"></a>&nbsp;&nbsp;\n";
                            echo "                                                                    <a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setstate&sid=".$row['id']."&field=invalid\" title=\"connection state INVALID\"><img src=\"images/icons/invalid_".check_states($tablename, "invalid", $row['id']).".gif\" border=\"0\"></a></td>\n";
                            echo "                                                                  </td>";
                            echo "                                                          </tr>";
							echo "                                                   </table>";
							echo "                                          </td>";

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
						echo "						<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">-\n";
						echo "							</td>\n";
						echo "						<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">\n";
						echo "							-</td>\n";
						echo "						<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">\n";
						echo "							-</td>\n";
						echo "						<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">\n";
						echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=addafter&sid=".$row['id']."&field=status\"><IMG SRC=\"images/add_entry_gr.gif\" BORDER=\"0\" ALT=\"add after\"></a></td>";
						echo "					</tr>\n";
					}
					
					echo "						<tr bgcolor=\"#565656\">\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
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
		
		
		// -------------------------------------
		// | Guardian Style - Priority Changer |
		// -------------------------------------
		// | Last Change : 17.01.2002		   |
		// -------------------------------------
		// | Status : Enabled				   |
		// -------------------------------------
		function change_strategies_priority($section, $tablename, $id, $field, $priority, $status)
		{
			# Open Database #
			$result = mysql_query("select * from ".$tablename." order by id");
			$number = mysql_num_rows($result);
			
			# Open Database #
			$result = mysql_query("select * from ".$tablename." where (id='".$id."')");
			$row = mysql_fetch_array($result);
			
			# Priority Logic #
			if ($priority == 0)
			{
				$result = mysql_query("update ".$tablename." set priority='".($row['priority']-11)."' where(id='".(((int)($row['id'])))."')");
				correct_priorities($section, $tablename);
				show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
				//if ((((int)($row['priority']))-1) >= 0)
				//{
					//$result = mysql_query("update ".$tablename." set priority='-1' where(priority='".(((int)($row['priority'])))."')");
					//$result = mysql_query("update ".$tablename." set priority='-2' where(priority='".(((int)($row['priority']))-1)."')");
					//$result = mysql_query("update ".$tablename." set priority='".(((int)($row['priority']))-11)."' where(priority='-1')");
					//$result = mysql_query("update ".$tablename." set priority='".(((int)($row['priority'])))."' where(priority='-2')");
				//}
			}
			elseif ($priority == 1)
			{
				$result = mysql_query("update ".$tablename." set priority='".($row['priority']+11)."' where(id='".(((int)($row['id'])))."')");
				correct_priorities($section, $tablename);
				show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
				//if ((((int)($row['priority']))+1) < ((int)($number)))
				//{
				//	$result = mysql_query("update ".$tablename." set priority='-1' where(priority='".(((int)($row['priority'])))."')");
				//	$result = mysql_query("update ".$tablename." set priority='-2' where(priority='".(((int)($row['priority']))+1)."')");
				//	$result = mysql_query("update ".$tablename." set priority='".(((int)($row['priority']))+11)."' where(priority='-1')");
				//	$result = mysql_query("update ".$tablename." set priority='".(((int)($row['priority'])))."' where(priority='-2')");
				//}					
			}
			elseif ($priority == 2)
			{
				if (!isset($status))
				{
					# Show Edit Boxes + Create Form #
					echo "&nbsp;<b>Aktive Sektion : ".$section." | <b> Prioritaet aendern</b>&nbsp;";
					echo "</td><td width='20%' height='20' valign='middle' align='right' bgcolor='#e2e3df'>";
					echo "&nbsp;<a href=\"javascript:history.back(1)\">..:: Back ::..</a>&nbsp;";
					echo "</td></tr></table>";
					
					echo "<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=filter&action=priorityedit&sid=".$id."&field=priority&status=true";
					echo "<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" >";
					echo "<tr height=100% valign=middle><td width=100% align=center>";
					echo " <table border=\"1\" cellpadding=\"2\" cellspacing=\"0\" bordercolor=\"#000000\" bgcolor=\"#c2d0f9\">";
					
					echo "<tr><td>old priority</td><td>".$row['priority']."</td></tr>\n";
					echo "<tr><td>new priority</td><td><input type=\"text\" name=\"prioritynumber\" size=\"40\" value=\"".$row['priority']."\"></td></tr>\n";
					
					echo "<tr><td>&nbsp;</td><td><input type=\"submit\" value=\"submit\" name=\"submit\">&nbsp;<input type=\"button\" value=\"clear\"></td></tr>";
					echo "</table></td></tr></table>";
				}
				else
				{
					# Update submitted Options #
					$result = mysql_query("update ".$tablename." set priority='".$GLOBALS['prioritynumber']."' where(id='".$id."')");
					correct_priorities($section, $tablename);
					show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
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
				$result = mysql_query("update ".$tablename." set status='1' where(id='".$id."')");
				correct_priorities($section, $tablename);
				show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
			}
			elseif (((int)($row['status'])) == 1)
			{
				$result = mysql_query("update ".$tablename." set status='0' where(id='".$id."')");
				correct_priorities($section, $tablename);
				show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
			}
		}
		
		// -----------------------------------
		// | Linux Style - Direction Changer  |
		// -----------------------------------
		// | Last Change : 15.03.2002	      |
		// -----------------------------------
		// | Status : Enabled		      |
		// -----------------------------------
		function change_strategies_direction($section, $tablename, $id, $direction)
		{
			# Open Database #
			$result = mysql_query("select * from ".$tablename." where(id='".$id."')");
			$row = mysql_fetch_array($result);
			
			if ($direction == 0)
			{
				$result = mysql_query("update ".$tablename." set direction='0' where(id='".$id."')");
				correct_priorities($section, $tablename);
				show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
			}
			elseif ($direction == 1)
			{
				$result = mysql_query("update ".$tablename." set direction='1' where(id='".$id."')");
				correct_priorities($section, $tablename);
				show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
			}
			elseif ($direction == 2)
			{
				$result = mysql_query("update ".$tablename." set direction='2' where(id='".$id."')");
				correct_priorities($section, $tablename);
				show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
			}
		}
		
		// -----------------------------------
		// | Check State - On or Off          |
                // -----------------------------------
		// | Last Change : 31.03.2003	      |
		// -----------------------------------
		// | Status : Enabled		      |
		// -----------------------------------
                function check_states($tablename, $section, $id){
                        $result=mysql_query("SELECT state_".$section." from $tablename WHERE id=".$id."");
                        $row=mysql_fetch_array($result);

                        if ($row["state_".$section]==1) {
                                return "on";
                        } else {
                                return "off";
                        }
                        
                }
                
                // -----------------------------------
		// | change Connection States         |
		// -----------------------------------
		// | Last Change : 01.04.2003	      |
		// -----------------------------------
		// | Status : Enabled		      |
		// -----------------------------------
		function change_states($section, $tablename, $id, $field)
		{
			# Open Database #
			$result = mysql_query("select * from ".$tablename." where(id=".$id.")");
			$row = mysql_fetch_array($result);
			
			if (((int)($row['state_'.$field])) == 0)
			{
				$result = mysql_query("update ".$tablename." set state_".$field."='1' where(id='".$id."')");
				show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
			}
			elseif (((int)($row['state_'.$field])) == 1)
			{
				$result = mysql_query("update ".$tablename." set state_".$field."='0' where(id='".$id."')");
				show_strategies(0, $section, "STRATEGY | <B>FIREWALL</B>", $tablename);
			}
		}

                // -----------------------------------
		// | parse protocol options           |
		// -----------------------------------
		// | Last Change : 02.04.2003	      |
		// -----------------------------------
		// | Status : Enabled		      |
		// -----------------------------------
		function parse_protocol_options($tablename, $id, $section)
                {
                        $sql_db_local = new dbvars;
                        $result_filter=mysql_query("SELECT satype,said,datype,daid FROM ".$tablename." WHERE id=".$id) or die (mysql_error());
                        $row_filter=mysql_fetch_array($result_filter);
                        if (($row_filter['satype']=="*") or ($row_filter['datype']==1)) {
                                return;
                        }
                        $result_protocol=mysql_query("SELECT id,pr_decimal FROM ".$sql_db_local->sql_db_table_po_protocols." WHERE id=".$row_filter['said']) or die(mysql_error());
                        $row_protocol=mysql_fetch_array($result_protocol);
                        switch ($row_protocol['pr_decimal']) {
                                case 1: //Case protocol 1 = ICMP
                                        if ($row_filter['daid']=='*') {
                                                echo "<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$id."&field=protopt\" title=\"ICMP type\">any type</a>";
                                                return;
                                                
                                        }
                                        $result_icmp=mysql_query("SELECT icmp_name FROM icmp_types WHERE id=".$row_filter['daid']);
                                        $row_icmp=mysql_fetch_array($result_icmp);
                                        echo "<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=editsimple&sid=".$id."&field=protopt\" title=\"ICMP type\">".$row_icmp['icmp_name']."</a>";
                                        return;
                                break;
                                default:
                                        echo "-";
                                        return;
                        }
                        
                }
?>
