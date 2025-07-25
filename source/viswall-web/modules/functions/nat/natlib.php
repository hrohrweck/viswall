<?php

		////////////////////////////////////////////////
		//              --> vis|wall <--              //
		////////////////////////////////////////////////
		//                				              //
		// MainGroup   : Interface        		      //
		//											  //
		// Name			: Module - NAT				  //
		// Date			: 27.04.2002				  //
		// Comment  	: NAT Functions 			  //
		//											  //
		////////////////////////////////////////////////
		
		// ----------------------------
		// | getPriorityByID (Sub)   |
		// ----------------------------
		// | Last Change : 04.06.2007 |
		// ----------------------------
		// | Status : Enabled	      |
		// ----------------------------
		function getPriorityByID ($id, $tablename) {
	        $result = mysql_query("select priority from ".$tablename." where id='".$id."' order by priority") or die(mysql_error());
	        $number = mysql_num_rows($result);
			
			if ($number) {
			    $row=mysql_fetch_array($result);
				return $row["priority"];
			}
			
			return 0;
		}

		// ----------------------------
		// | getNewPriority (Sub)     |
		// ----------------------------
		// | Last Change : 04.06.2007 |
		// ----------------------------
		// | Status : Enabled	      |
		// ----------------------------
		function getNewPriority ($priority, $tablename) {
			if (!$priority) {
				$result = mysql_query("select * from ".$tablename." order by priority DESC LIMIT 1") or die(mysql_error());
				$number = mysql_num_rows($result);
				
				if ($number) {
					$row=mysql_fetch_array($result);
					return $row["priority"]+10;
				}
			} else {
				$result = mysql_query("update ".$tablename." set priority=priority+10 where priority>='".$priority."'") or die (mysql_error());
				return $priority;
			}
			
			return 10;
		}
		
		// ----------------------------
		// | change_nat_priority      |
		// ----------------------------
		// | Last Change : 04.06.2007 |
		// ----------------------------
		// | Status : Enabled	      |
		// ----------------------------
		function change_nat_priority ($section, $section2, $tablename, $id, $status) {
			$priority=getPriorityByID($id,$tablename);
			$highestprio=getNewPriority(0,$tablename)-10;

			if ($status) {
				if ($priority<$highestprio) {
				    $priority=getNewPriority($priority+20, $tablename);

			        $result = mysql_query("update ".$tablename." set priority='".$priority."' where id='".$id."'") or die(mysql_error());
				}			
			} else {
				if ($priority>10) {
				    $priority=getNewPriority($priority-10, $tablename);

			        $result = mysql_query("update ".$tablename." set priority='".$priority."' where id='".$id."'") or die(mysql_error());
				}
			}
            show_nat(0, $section, $section2, $tablename);
			correct_priorities($section, $tablename,1);
			
			return 0;
		}

		// ----------------------------
		// | Add NAT Entry (Sub,Main) |
		// ----------------------------
		// | Last Change : 04.06.2007 |
		// ----------------------------
		// | Status : Enabled	      |
		// ----------------------------
		function add_nat($type, $section, $section2, $tablename, $tablename2, $id, $status=0)
		{
			switch ($type)
			{
				case 0:
				{
					break;
				}
				case 1:
				{
					$priority=0;
					
					if ($id) {
					    $priority=getPriorityByID($id,$tablename);
					} 
					
					if ($status) {
						$priority=getNewPriority($priority, $tablename);
					} else $priority=getNewPriority ($priority+10, $tablename);

					# Create new Default Entry #
					$data = "'','*','*','*','*','0','*','*','*','*','*','*','*','*','*','0','0','0','0','0','".$priority."'";
					$fields = "id,stype,sid,satype,said,ntype,dtype,did,datype,daid,totype,toid,topid,iiface,oiface,state_new,state_established,state_related,state_invalid,status,priority";
					$query = mysql_query("insert into ".$tablename." (".$fields.") values(".$data.")") or die(mysql_error());
					
        			# Show Strategies (Default Mode)
                    show_nat(0, $section, $section2, $tablename);
					correct_priorities($section, $tablename,1);
					
					/*# Create new Default Entry #
					if ($status == 0)
					{
						$data = "'','0','0','0','0','".($row['priority']+1)."','0'";
						$fields = "id,stype,dtype,atype,baction,priority,status";
						$query = mysql_query("insert into ".$tablename." (".$fields.") values(".$data.")") or die(mysql_error());
					}
					else
					{
						$data = "'','0','0','0','0','".($row['priority']-1)."','0'";
						$fields = "id,stype,dtype,atype,baction,priority,status";
						$query = mysql_query("insert into ".$tablename." (".$fields.") values(".$data.")") or die(mysql_error());
					}
					
					# Show Strategies (Default Mode)
					correct_priorities($section, $tablename);*/
					break;
        			}
				case 2:
				{
					/*$data = "'','".$sid."','0','0'";
					$fields = "id,pid,portin,portout";
					$query = mysql_query("insert into ".$tablename2." (".$fields.") values(".$data.")") or die(mysql_error());

        				# Show Strategies (Default Mode)
					correct_priorities($section, $tablename);
					show_nat(0, $section, $section2, $tablename);
                    */
					break;
				}
				default:
				{
					// Error Routine
					errorcode(7,0);
					break;
				}
			}
		}

        // --------------------------------
		// | Delete NAT Entry (Sub, Main) |
		// --------------------------------
		// | Last Change : 18.04.2003     |
		// --------------------------------
		// | Status : Enabled             |
		// --------------------------------
		function delete_nat($type, $section, $section2, $tablename, $tablename2, $sid)
        {
            mysql_query("delete from ".$tablename." where(id=\"".$sid."\")") or die(errorcode(8,mysql_error()));
            correct_priorities($section, $tablename);
			show_nat(0, $section, $section2, $tablename);
		}

        // ----------------------------
		// | Edit NAT Entry			  |
		// ----------------------------
		// | Last Change : 18.04.2003 |
		// ----------------------------
		// | Status : Enabled		  |
		// ----------------------------
		function edit_nat($type, $section, $section2, $tablename, $tablename2, $sid, $field, $fdata)
		{
			# Open Database #
			$result = mysql_query("select * from ".$tablename." where(id='".$sid."')");
			$number = mysql_num_rows($result);
			
			# Read and Display Database Entries #
			$row = mysql_fetch_array($result);
			
			# Check if Information is already submitted #
			if (!isset($GLOBALS['rsubmit']))
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
						echo " 	  				".$section2." | <i>".$tablename."</i> (".$sid.") &nbsp;</td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
						echo "			</tr>\n";
						echo "		</table>\n";
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=nat&action=edit&sid=".$sid."\" name=\"submitform\">";
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
						
						# Generate Any Entries #
						echo "<option value=\"-\" name=\"dummy\"> ---> Internet <--- </option>\n";
						if (($row['sid'] == '*') and ($row['stype'] == '*'))
						{
							echo "<option value=\"**|any\" name=\"any\" selected> Any </option>\n";
						}
						else
						{
							echo "<option value=\"**|any\" name=\"any\"> Any </option>\n";
						}
						
						# Generate Existing Host Entries #
						echo "<option value=\"-\" name=\"dummy\"> ---> Hosts <--- </option>\n";
						$result_hosts = mysql_query("select * from no_hosts order by id");
						$number_hosts = mysql_num_rows($result_hosts);
						for ($i=0;$i<$number_hosts;$i++)
						{
							$row_hosts=mysql_fetch_array($result_hosts);
							if (($row['sid'] == $row_hosts['id']) and ($row['stype'] == '1'))
							{
								echo "<option value=\"1".$row_hosts['id']."|".$row_hosts['name']."\" name=\"host".$row_hosts['id']."\" selected> ".$row_hosts['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"1".$row_hosts['id']."|".$row_hosts['name']."\" name=\"host".$row_hosts['id']."\"> ".$row_hosts['name']." </option>\n";
							}
						}
						
						# Generate Existing Network Entries #
						echo "<option value=\"-\" name=\"dummy\"> ---> Networks <--- </option>\n";
						$result_networks = mysql_query("select * from no_networks order by id");
						$number_networks = mysql_num_rows($result_networks);
						for ($i=0;$i<$number_networks;$i++)
						{
							$row_networks=mysql_fetch_array($result_networks);
							if (($row['sid'] == $row_networks['id']) and ($row['stype'] == '2'))
							{
								echo "<option value=\"2".$row_networks['id']."|".$row_networks['name']."\" name=\"network".$row_networks['id']."\" selected> ".$row_networks['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"2".$row_networks['id']."|".$row_networks['name']."\" name=\"network".$row_networks['id']."\"> ".$row_networks['name']." </option>\n";
							}
						}
						
						# Generate Existing Range Entries #
						echo "<option value=\"-\" name=\"dummy\"> ---> Ranges <--- </option>\n";
						$result_ranges = mysql_query("select * from no_ranges order by id");
						$number_ranges = mysql_num_rows($result_ranges);
						for ($i=0;$i<$number_ranges;$i++)
						{
							$row_ranges=mysql_fetch_array($result_ranges);
							if (($row['sid'] == $row_ranges['id']) and ($row['stype'] == '2'))
							{
								echo "<option value=\"3".$row_ranges['id']."|".$row_ranges['name']."\" name=\"ranges".$row_ranges['id']."\" selected> ".$row_ranges['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"3".$row_ranges['id']."|".$row_ranges['name']."\" name=\"ranges".$row_ranges['id']."\"> ".$row_ranges['name']." </option>\n";
							}
						}

						echo "</select></TD></TR>\n";
						
						# Submit Event Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"".$_SERVER['PHP_SELF']."?module=nat\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'destination':
					{
						echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
						echo "			<tr valign=\"top\">\n";
						echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo " 	  				".$section2." | <i>".$tablename."</i> (".$sid.") &nbsp;</td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
						echo "			</tr>\n";
						echo "		</table>\n";
					
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=nat&action=edit&sid=".$sid."\" name=\"submitform\">";
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
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;DESTINATION</TD>\n";
        					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<select name=\"sources\">\n";
						
						# Generate Any Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Internet <--- </option>\n";
						if (($row['did'] == '*') and ($row['dtype'] == '*'))
						{
							echo "<option value=\"**|any\" name=\"any\" selected> Any </option>\n";
						}
                				else
        					{
							echo "<option value=\"**|any\" name=\"any\"> Any </option>\n";
						}
						
						# Generate Existing Host Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Hosts <--- </option>\n";
						$result_hosts = mysql_query("select * from no_hosts order by id");
						$number_hosts = mysql_num_rows($result_hosts);
						for ($i=0;$i<$number_hosts;$i++)
						{
							$row_hosts=mysql_fetch_array($result_hosts);
							if (($row['dtype'] == '1') and ($row['did'] == $row_hosts['id']))
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
							if (($row['dtype'] == '2') and($row['did'] == $row_networks['id']))
							{
								echo "<option value=\"2".$row_networks['id']."|".$row_networks['name']."\" name=\"network".$row_networks['id']."\" selected> ".$row_networks['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"2".$row_networks['id']."|".$row_networks['name']."\" name=\"network".$row_networks['id']."\"> ".$row_networks['name']." </option>\n";
							}
						}

						# Generate Existing Ranges Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Ranges <--- </option>\n";
						$result_ranges = mysql_query("select * from no_ranges order by id");
						$number_ranges = mysql_num_rows($result_ranges);
						for ($i=0;$i<$number_ranges;$i++)
						{
							$row_ranges=mysql_fetch_array($result_ranges);
							if (($row['dtype'] == '2') and($row['did'] == $row_ranges['id']))
							{
								echo "<option value=\"3".$row_ranges['id']."|".$row_ranges['name']."\" name=\"ranges".$row_ranges['id']."\" selected> ".$row_ranges['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"3".$row_ranges['id']."|".$row_ranges['name']."\" name=\"ranges".$row_ranges['id']."\"> ".$row_ranges['name']." </option>\n";
							}
						}
						
						echo "</select></TD></TR>\n";
						
						# Submit Event Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"".$_SERVER['PHP_SELF']."?module=nat\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'toip':
					{
						echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
						echo "			<tr valign=\"top\">\n";
						echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo " 	  				".$section2." | <i>".$tablename."</i> (".$sid.") &nbsp;</td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
						echo "			</tr>\n";
						echo "		</table>\n";
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=nat&action=edit&sid=".$sid."\" name=\"submitform\">";
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
						echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;".$id."</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;DESTINATION</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<select name=\"sources\">\n";
						
						# Generate Existing Host Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Hosts <--- </option>\n";
						$result_hosts = mysql_query("select * from no_hosts order by id");
						$number_hosts = mysql_num_rows($result_hosts);
						for ($i=0;$i<$number_hosts;$i++)
						{
							$row_hosts=mysql_fetch_array($result_hosts);
							if (($row['totype'] == '1') and ($row['toid'] == $row_hosts['id']))
							{
								echo "<option value=\"1".$row_hosts['id']."|".$row_hosts['name']."\" name=\"host".$row_hosts['id']."\" selected> ".$row_hosts['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"1".$row_hosts['id']."|".$row_hosts['name']."\" name=\"host".$row_hosts['id']."\"> ".$row_hosts['name']." </option>\n";
							}								
						}
						
        					echo "</select></TD></TR>\n";
						
						# Submit Event Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"".$_SERVER['PHP_SELF']."?module=nat\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
						echo " 	  				".$section2." | <i>".$tablename."</i> (".$sid.") &nbsp;</td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
						echo "			</tr>\n";
						echo "		</table>\n";

						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=nat&action=edit&sid=".$sid."\" name=\"submitform\">";
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
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;TYPE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<select name=\"sources\">\n";
						
						# Generate Any Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Internet <--- </option>\n";
						if ($row['satype'] == '*')
							echo "<option value=\"*|any\" name=\"any\" selected> Any </option>\n";
						else
							echo "<option value=\"*|any\" name=\"any\"> Any </option>\n";
						
						# Generate Existing Service Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Services <--- </option>\n";
						$result_services = mysql_query("select * from so_services order by id");
						$number_services = mysql_num_rows($result_services);
						for ($i = 0; $i < $number_services; $i++)
						{
							$row_services = mysql_fetch_array($result_services);
							
							if (($row['satype'] == 1) && ($row['said'] == $row_services['id']))
								echo "<option value=\"1".$row_services['id']."|".$row_services['name']."\" name=\"host".$row_services['id']."\" selected> ".$row_services['name']." </option>\n";
							else
								echo "<option value=\"1".$row_services['id']."|".$row_services['name']."\" name=\"host".$row_services['id']."\"> ".$row_services['name']." </option>\n";
						}

                        # Generate Existing Protocol Entrys #
                        echo "<option value=\"-\" name=\"dummy\"> ---> Protocols <--- </option>\n";
						$result_protocols = mysql_query("select * from po_protocols order by id");
						$number_protocols = mysql_num_rows($result_protocols);
						for ($i = 0; $i < $number_protocols; $i++)
						{
							$row_protocols=mysql_fetch_array($result_protocols);
							
							if (($row['satype'] == 2) && ($row['said'] == $row_protocols['id']))
								echo "<option value=\"2".$row_protocols['id']."|".$row_protocols['pr_keyword']."\" name=\"host".$row_protocols['id']."\" selected> ".$row_protocols['pr_keyword']." </option>\n";
							else
								echo "<option value=\"2".$row_protocols['id']."|".$row_protocols['pr_keyword']."\" name=\"host".$row_protocols['id']."\"> ".$row_protocols['pr_keyword']." </option>\n";
						}
        				
						// Submit Event for Data
                        echo "</select></TD></TR>\n";
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
            			echo "<a href=\"".$_SERVER['PHP_SELF']."?module=nat\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'datype':
					{
						echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
						echo "			<tr valign=\"top\">\n";
						echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo " 	  				".$section2." | <i>".$tablename."</i> (".$sid.") &nbsp;</td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
						echo "			</tr>\n";
						echo "		</table>\n";
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=nat&action=edit&sid=".$sid."\" name=\"submitform\">";
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
						echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;".$sid."</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
       					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;SERVICE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<select name=\"sources\">\n";
						

						# Generate Any Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Internet <--- </option>\n";
						if ($row['daid'] == '*')
						{
							echo "<option value=\"*|any\" name=\"any\" selected> Any </option>\n";
						}
						else
						{
							echo "<option value=\"*|any\" name=\"any\"> Any </option>\n";
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
						//echo "<input type=\"hidden\" value=\"".$sid."\" name=\"hiddenid\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
       					echo "<a href=\"".$_SERVER['PHP_SELF']."?module=nat\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'topid':
					{
						echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
						echo "			<tr valign=\"top\">\n";
						echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo " 	  				".$section2." | <i>".$tablename."</i> (".$sid.") &nbsp;</td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
						echo "			</tr>\n";
						echo "		</table>\n";
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=nat&action=edit&sid=".$sid."\" name=\"submitform\">";
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
						echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;".$sid."</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;SERVICE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<select name=\"sources\">\n";
						
						# Generate Any Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Internet <--- </option>\n";
						if ($row['topid'] == '*')
						{
							echo "<option value=\"*|any\" name=\"any\" selected> Any </option>\n";
						}
						else
						{
							echo "<option value=\"*|any\" name=\"any\"> Any </option>\n";
						}
						
						# Generate Existing Service Entrys #
						echo "<option value=\"-\" name=\"dummy\"> ---> Services <--- </option>\n";
						$result_services = mysql_query("select * from so_services order by id");
						$number_services = mysql_num_rows($result_services);

        					for ($i=0;$i<$number_services;$i++)
						{
							$row_services=mysql_fetch_array($result_services);
							if ($row['topid'] == $row_services['id'])
							{
								echo "<option value=\"".$row_services['id']."|".$row_services['name']."\" name=\"host".$row_services['id']."\" selected> ".$row_services['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"".$row_services['id']."|".$row_services['name']."\" name=\"host".$row_services['id']."\"> ".$row_services['name']." </option>\n";
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
            			echo "<a href=\"".$_SERVER['PHP_SELF']."?module=nat\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'iiface':
					{
						echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
						echo "			<tr valign=\"top\">\n";
						echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo " 	  				".$section2." | <i>".$tablename."</i> (".$sid.") &nbsp;</td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
						echo "			</tr>\n";
						echo "		</table>\n";
						
	            		echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=nat&action=edit&sid=".$sid."\" name=\"submitform\">";
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
						echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;".$sid."</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
        				echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;INTERFACE</TD>\n";
        				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						
						echo "<select name=\"sources\">\n";
						
						$fdata = mysql_query("select iiface from $tablename where(id=$sid)");
						$row_fdata = mysql_fetch_array($fdata);
					
						$result_interfaces = mysql_query("select * from io_interfaces order by id");
						$number_interfaces = mysql_num_rows($result_interfaces);
						
						for ($i=0;$i<$number_interfaces;$i++)
						{
							$row_interfaces=mysql_fetch_array($result_interfaces);
							
							if ($row_fdata['iiface'] == ($row_interfaces['id'] ))
							{
								echo "<option value=\"".$row_interfaces['id']."|".$row_interfaces['name']."\" name=\"sources".$row_interfaces['id']."\" selected> ".$row_interfaces['name']." </option>\n";
							}
        						else
							{
								echo "<option value=\"".$row_interfaces['id']."|".$row_interfaces['name']."\" name=\"sources".$row_interfaces['id']."\"> ".$row_interfaces['name']." </option>\n";
							}
						}
						
						if ($row_fdata['iiface'] == '*')
						{
							echo "<option value=\"*|all\ name=\"sources\" selected> all </option>\n";
						}
						else
						{
							echo "<option value=\"*|all\ name=\"sources\"> all </option>\n";
						}
						
						# Submit Event Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"".$_SERVER['PHP_SELF']."?module=nat\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'oiface':
					{
						echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
						echo "			<tr valign=\"top\">\n";
						echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo " 	  				".$section2." | <i>".$tablename."</i> (".$sid.") &nbsp;</td>\n";
						echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
						echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
						echo "			</tr>\n";
						echo "		</table>\n";
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=nat&action=edit&sid=".$sid."\" name=\"submitform\">";
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
						echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;".$sid."</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;INTERFACE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						
						echo "<select name=\"sources\">\n";
						
						$fdata = mysql_query("select iiface from $tablename where(id=$sid)");
						$row_fdata = mysql_fetch_array($fdata);
						
						$result_interfaces = mysql_query("select * from io_interfaces order by id");
						$number_interfaces = mysql_num_rows($result_interfaces);
						
						for ($i=0;$i<$number_interfaces;$i++)
						{
							$row_interfaces=mysql_fetch_array($result_interfaces);
							
							if ($row_fdata['oiface'] == ($row_interfaces['id'] ))
							{
								echo "<option value=\"".$row_interfaces['id']."|".$row_interfaces['name']."\" name=\"sources".$row_interfaces['id']."\" selected> ".$row_interfaces['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"".$row_interfaces['id']."|".$row_interfaces['name']."\" name=\"sources".$row_interfaces['id']."\"> ".$row_interfaces['name']." </option>\n";
							}
						}
						
						if ($row_fdata['oiface'] == '*')
						{
							echo "<option value=\"*|all\ name=\"sources\" selected> all </option>\n";
						}
						else
						{
							echo "<option value=\"*|all\ name=\"sources\"> all </option>\n";
						}
						
						# Submit Event Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
        				echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
	               		echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"".$_SERVER['PHP_SELF']."?module=nat\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
                        $result_protopt_type = mysql_query("SELECT id,pr_decimal FROM ".$sql_db_local->sql_db_table_po_protocols." WHERE id=".$row['said']) or die(mysql_error());
						$result_protopt_type = mysql_fetch_array($result_protopt_type);
						
						switch ($result_protopt_type['pr_decimal'])
                        {
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
						
						echo "		<form method=\"post\" action=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$sid."\" name=\"submitform\">";
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
				switch ($_POST['hiddenfield'])
				{
					case 'source':
					{
						if (substr($_POST['sources'],0,1) != "-")
						{
                            $result = mysql_query("update ".$tablename." set stype='".substr($_POST['sources'],0,1)."' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                            $result = mysql_query("update ".$tablename." set sid='".substr($_POST['sources'],1,strpos($_POST['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                        }
						break;
					}
					case 'destination':
					{
						if (substr($_POST['sources'],0,1) != "-")
						{
        					$result = mysql_query("update ".$tablename." set dtype='".substr($_POST['sources'],0,1)."' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
        					$result = mysql_query("update ".$tablename." set did='".substr($_POST['sources'],1,strpos($_POST['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
        				}
						break;
					}
					case 'toip':
					{
						if (substr($_POST['sources'],0,1) != "-")
                        {
                            $result = mysql_query("update ".$tablename." set totype='".substr($_POST['sources'],0,1)."' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                            $result = mysql_query("update ".$tablename." set toid='".substr($_POST['sources'],1,strpos($_POST['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                        }
						break;
        			}
	              	case 'satype':
        			{
						if (substr($_POST['sources'],0,1) != "-")
                        {
                            switch (substr($_POST['sources'],0,1))
                            {
                                case '*':
                                {
                                    $result = mysql_query("update ".$tablename." set satype='*' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                                    $result = mysql_query("update ".$tablename." set said='*' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                                    break;
                                }
                                case 1:
                                {
                                    $result = mysql_query("update ".$tablename." set satype=1 where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                                    $result = mysql_query("update ".$tablename." set said='".substr($_POST['sources'],1,strpos($_POST['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                                    break;
                                }
                                case 2:
                                {
                                    $result = mysql_query("update ".$tablename." set satype=2 where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                                    $result = mysql_query("update ".$tablename." set said='".substr($_POST['sources'],1,strpos($_POST['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
								    $result2 = mysql_query("UPDATE ".$tablename." SET datype='*' WHERE id='".$_GET['sid']."'");
								    $result2 = mysql_query("UPDATE ".$tablename." SET daid='*' WHERE id='".$_GET['sid']."'");
                                    break;
                                }
                                case 3:
                                {
                                    $result = mysql_query("update ".$tablename." set satype=3 where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                                    $result = mysql_query("update ".$tablename." set said='".substr($_POST['sources'],1,strpos($_POST['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
								    $result2 = mysql_query("UPDATE ".$tablename." SET datype='*' WHERE id='".$_GET['sid']."'");
								    $result2 = mysql_query("UPDATE ".$tablename." SET daid='*' WHERE id='".$_GET['sid']."'");
                                    break;
                                }
                                default:
                                {
                                    errorcode(7);
                                    break;
                                }
                            }
						}
						break;
					}
					case 'datype':
					{
						if (substr($_POST['sources'],0,1) != "-")
                        {
                            switch (substr($_POST['sources'],0,1))
                            {
                                case '*':
                                {
                                    $result = mysql_query("update ".$tablename." set datype='*' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                                    $result = mysql_query("update ".$tablename." set daid='*' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                                    break;
                                }
						        case 1:
						        {
                                    $result = mysql_query("update ".$tablename." set datype='1' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                                    $result = mysql_query("update ".$tablename." set daid='".substr($_POST['sources'],1,strpos($_POST['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                                    break;
                                }
						        case 2:
						        {
                                    $result = mysql_query("update ".$tablename." set datype='2' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                                    $result = mysql_query("update ".$tablename." set daid='".substr($_POST['sources'],1,strpos($_POST['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                                    break;
                                }
						        case 3:
						        {
                                    $result = mysql_query("update ".$tablename." set datype='3' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                                    $result = mysql_query("update ".$tablename." set daid='".substr($_POST['sources'],1,strpos($_POST['sources'],"|")-1)."' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
                                    break;
                                }
                                default:
                                {
                                    errorcode(7);
                                    break;
                                }
                            }
						}
						break;
					}
					case 'topid':
					{
						if (substr($_POST['sources'],0,1) != "-")
                            $result = mysql_query("update ".$tablename." set topid='".substr($_POST['sources'],0,strpos($_POST['sources'],"|"))."' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
						break;
					}
					case 'iiface':
					{
						if (substr($_POST['sources'],0,1) != "-")
                            $result = mysql_query("update ".$tablename." set iiface='".substr($_POST['sources'],0,strpos($_POST['sources'],"|"))."' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
						break;
					}
					case 'oiface':
					{
						if (substr($_POST['sources'],0,1) != "-")
                            $result = mysql_query("update ".$tablename." set oiface='".substr($_POST['sources'],0,strpos($_POST['sources'],"|"))."' where(id='".$_GET['sid']."')") or die(errorcode(8,mysql_error()));
						break;
					}
					case 'protopt':
					{
                        if($_POST['sources']!="-")
                            $result = mysql_query("UPDATE ".$tablename." SET daid='".$_POST['sources']."' WHERE id=".$_GET['sid']) or die("error while updating protocol option type: ".mysql_error());

                        break;
					}
				}
				
				# Show Strategies (Default Mode)
				# ------------------------------
				correct_priorities($section, $tablename);
				show_nat(0, $section, $section2, $tablename);
			}
		}
		
        // -----------------------------
		// | Show NAT Entry 		   |
		// -----------------------------
		// | Last Change : 29.03.2002  |
		// -----------------------------
		// | Status : Enabled		   |
		// -----------------------------
		function show_nat($type, $section, $section2, $tablename)
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
					echo "					<table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"911px\" height=\"\">\n";
					echo "						<tr bgcolor=\"#565656\" class=\"tablehead\">\n";
					echo "							<td valign=\"bottom\" align=\"left\" width=\"32\" height=\"22\">\n";
					echo "								<font color=\"#ffffff\">&nbsp;</font><br>\n";
					echo "								<img src=\"images/border_orange.gif\" width=\"32\" height=\"6\" border=\"0\"></td>\n";
					echo "  						<td colspan=\"2\" valign=\"bottom\" align=\"left\" width=\"247\" height=\"22\">\n";
					echo "   							<font color=\"#ffffff\">&nbsp;SOURCE</font><br>\n";
        			echo "   							<img src=\"images/border_orange.gif\" WIDTH=\"247\" height=\"6\" border=\"0\"></td>\n";
					echo "  						<td valign=\"bottom\" align=\"left\" width=\"55\" height=\"22\">\n\n";
					echo "   							<font color=\"#ffffff\">&nbsp;METHOD</font><br>\n";
					echo "  							<img src=\"images/border_orange.gif\" WIDTH=\"55\" height=\"6\" border=\"0\"></td>\n";
					echo "  						<td colspan=\"2\" valign=\"bottom\" align=\"left\" width=\"247\" height=\"22\">\n";
					echo "  							<font color=\"#ffffff\">&nbsp;DESTINATION</font><br>\n";
					echo "  							<img src=\"images/border_orange.gif\" WIDTH=\"247\" height=\"6\" border=\"0\"></td>\n";
					echo "  						<td valign=\"bottom\" align=\"left\" width=\"150\" height=\"22\">\n";
					echo "  							<font color=\"#ffffff\">&nbsp;TO IP</font><br>\n";
					echo "  							<img src=\"images/border_orange.gif\" WIDTH=\"150\" height=\"6\" border=\"0\"></td>\n";
					echo " 							<td valign=\"bottom\" align=\"center\" width=\"70\" height=\"22\">\n";
					echo "   							<font color=\"#ffffff\">STATES</font><br>\n";
					echo "   							<img src=\"images/border_orange.gif\" WIDTH=\"70\" height=\"6\" border=\"0\"></td>\n";
                    echo " 							<td valign=\"bottom\" align=\"center\" width=\"110\" height=\"22\">\n";
					echo "   							<font color=\"#ffffff\">ACTION</font><br>\n";
					echo "   							<img src=\"images/border_orange.gif\" WIDTH=\"110\" height=\"6\" border=\"0\"></td>\n";
					echo " 						</tr>\n";
					
					if ($number != 0)
					{
						# Read and Display Database Entries #				
						for ($i=0; $i < $number; $i++)
						{
							$row = mysql_fetch_array($result);
							
							if (is_float(($i/2)) == false)
								echo "						<tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
							else
								echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
							echo "								<td rowspan=\"2\" valign=\"middle\" align=\"center\" width=\"\" height=\"20\">";
							
							if ($row['status'] == 1)
								echo "								&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setstatus&sid=".$row['id']."&field=status\"><IMG SRC=\"images/icons/on.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"on\"></a>&nbsp;</td>";
							else
								echo "							    &nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setstatus&sid=".$row['id']."&field=status\"><IMG SRC=\"images/icons/off.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"off\"></a>&nbsp;</td>";
							
							switch ($row['stype'])
							{
								case '*':
								{
									echo "							<td colspan=\"2\"valign=\"top\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=source&fid=".$row['stype'].$row['sid']."\">";
									echo "											&nbsp;<IMG SRC=\"images/icons/inet.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"any\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=source&fid=".$row['stype'].$row['sid']."\">";
									echo "							 				any</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";	
									echo "							</td>\n";
									break;
								}
								case 1:
								{
									$result2= mysql_query("select * from no_hosts where (id=".$row['sid'].")");
									$gather = mysql_fetch_array($result2);
        							echo "							<td colspan=\"2\" valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
        							echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=source&fid=".$row['stype'].$row['sid']."\">";
									echo "								&nbsp;<IMG SRC=\"images/icons/host.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"host\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=source&fid=".$row['stype'].$row['sid']."\">";
									echo "								".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
								case 2:
								{
									$result2 = mysql_query("select * from no_networks where (id=".$row['sid'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td colspan=\"2\" valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=source&fid=".$row['stype'].$row['sid']."\">";
									echo "								&nbsp;<IMG SRC=\"images/icons/network.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
									echo "										</td>\n";
        							echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=source&fid=".$row['stype'].$row['sid']."\">";
									echo "								".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
								case 3:
								{
									$result2 = mysql_query("select * from no_ranges where (id=".$row['sid'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td colspan=\"2\" valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=source&fid=".$row['stype'].$row['sid']."\">";
									echo "								&nbsp;<IMG SRC=\"images/icons/ranges.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"ranges\"></a>&nbsp;";
									echo "										</td>\n";
        							echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=source&fid=".$row['stype'].$row['sid']."\">";
									echo "								".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
							}
							
        					switch ($row['ntype'])
							{
								case '0':
								{
									echo "							<td rowspan=\"2\" valign=\"middle\" align=\"center\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"center\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setmethod&sid=".$row['id']."&field=method&fid=".$row['ntype']."\"><IMG SRC=\"images/snat.gif\" BORDER=\"0\" ALT=\"SNAT\"></a>";
									echo "										</td>\n";
									echo "									</tr>\n";
        							echo "								</table>\n";
									echo "							</td>\n";
									break;
        							}
								case '1':
								{
									echo "							<td rowspan=\"2\" valign=\"middle\" align=\"center\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"center\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setmethod&sid=".$row['id']."&field=method&fid=".$row['ntype']."\"><IMG SRC=\"images/dnat.gif\" BORDER=\"0\" ALT=\"DNAT\"></a>";
									echo "										</td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
        							echo "							</td>\n";
									break;
								}
								case '2':
								{
									echo "							<td rowspan=\"2\" valign=\"middle\" align=\"center\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"center\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setmethod&sid=".$row['id']."&field=method&fid=".$row['ntype']."\"><IMG SRC=\"images/masq.gif\" BORDER=\"0\" ALT=\"Masquerading\"></a>";
									echo "										</td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
								case '3':
								{
									echo "							<td rowspan=\"2\" valign=\"middle\" align=\"center\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"center\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setmethod&sid=".$row['id']."&field=method&fid=".$row['ntype']."\"><IMG SRC=\"images/redir.gif\" BORDER=\"0\" ALT=\"Redirection\"></a>";
        							echo "										</td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
								case '4':
								{
									echo "							<td rowspan=\"2\" valign=\"middle\" align=\"center\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"center\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setmethod&sid=".$row['id']."&field=method&fid=".$row['ntype']."\"><IMG SRC=\"images/preaccept.gif\" BORDER=\"0\" ALT=\"PREACCEPT\"></a>";
									echo "										</td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
        							echo "							</td>\n";
									break;
								}
								case '5':
								{
									echo "							<td rowspan=\"2\" valign=\"middle\" align=\"center\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"center\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=setmethod&sid=".$row['id']."&field=method&fid=".$row['ntype']."\"><IMG SRC=\"images/postaccept.gif\" BORDER=\"0\" ALT=\"POSTACCEPT\"></a>";
									echo "										</td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
        							echo "							</td>\n";
									break;
								}
							}
							
							switch ($row['dtype'])
							{
								case '*':
								{
									echo "							<td colspan=\"2\" valign=\"top\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=destination&fid=".$row['dtype'].$row['did']."\">";
									echo "											&nbsp;<IMG SRC=\"images/icons/inet.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"any\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
        							echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=destination&fid=".$row['dtype'].$row['did']."\">";
									echo "							 				any</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";	
        							echo "							</td>\n";
									break;
        							}
								case '1':
								{
									$result2 = mysql_query("select * from no_hosts where (id=".$row['did'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td colspan=\"2\" valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=destination&fid=".$row['dtype'].$row['did']."\">";
									echo "								&nbsp;<IMG SRC=\"images/icons/host.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"host\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=destination&fid=".$row['dtype'].$row['did']."\">";
									echo "								".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
								case '2':
								{
									$result2 = mysql_query("select * from no_networks where (id=".$row['did'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td colspan=\"2\" valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=destination&fid=".$row['dtype'].$row['did']."\">";
									echo "								&nbsp;<IMG SRC=\"images/icons/network.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=destination&fid=".$row['dtype'].$row['did']."\">";
									echo "								".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
								case '3':
								{
									$result2 = mysql_query("select * from no_ranges where (id=".$row['did'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td colspan=\"2\" valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr valign=\"middle\">\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=destination&fid=".$row['dtype'].$row['did']."\">";
									echo "								&nbsp;<IMG SRC=\"images/icons/ranges.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"ranges\"></a>&nbsp;";
									echo "										</td>\n";
									echo "										<td align=\"left\">\n";
									echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=destination&fid=".$row['dtype'].$row['did']."\">";
									echo "								".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
							}
							
							if ($row['ntype'] < 2)
							{
								switch ($row['totype'])
								{
           							case 0:
									{
										echo "							<td valign=\"top\" align=\"left\" width=\"\" height=\"20\">\n";
										echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
										echo "									<tr valign=\"middle\">\n";
										echo "										<td align=\"left\">\n";
										echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=toip&fid=".$row['totype'].$row['toid']."\">";
										echo "											&nbsp;";
										echo "										</td>\n";
										echo "										<td align=\"left\">\n";
										echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=toip&fid=".$row['totype'].$row['toid']."\">";
										echo "							 				N/A</a></td>\n";
										echo "									</tr>\n";
										echo "								</table>\n";	
										echo "							</td>\n";
										break;
									}
              						case 1:
									{
										$result2 = mysql_query("select * from no_hosts where (id=".$row['toid'].")");
										$gather = mysql_fetch_array($result2);
										echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
       									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
										echo "									<tr valign=\"middle\">\n";
										echo "										<td align=\"left\">\n";
										echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=toip&fid=".$row['totype'].$row['toid']."\">";
										echo "								&nbsp;<IMG SRC=\"images/icons/host.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"host\"></a>&nbsp;";
										echo "										</td>\n";
										echo "										<td align=\"left\">\n";
           								echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=toip&fid=".$row['totype'].$row['toid']."\">";
										echo "								".$gather['name']."</a></td>\n";
										echo "									</tr>\n";
										echo "								</table>\n";
										echo "							</td>\n";
										break;
									}
									case 2:
									{
					          			$result2 = mysql_query("select * from no_networks where (id=".$row['toid'].")");
										$gather = mysql_fetch_array($result2);
										echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
										echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
										echo "									<tr valign=\"middle\">\n";
										echo "										<td align=\"left\">\n";
										echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=toip&fid=".$row['totype'].$row['toid']."\">";
										echo "								&nbsp;<IMG SRC=\"images/icons/network.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"network\"></a>&nbsp;";
										echo "										</td>\n";
										echo "										<td align=\"left\">\n";
										echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=toip&fid=".$row['totype'].$row['toid']."\">";
										echo "								".$gather['name']."</a></td>\n";
              							echo "									</tr>\n";
										echo "								</table>\n";
										echo "							</td>\n";
										break;
									}
									case 3:
									{
					          			$result2 = mysql_query("select * from no_ranges where (id=".$row['toid'].")");
										$gather = mysql_fetch_array($result2);
										echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
										echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
										echo "									<tr valign=\"middle\">\n";
										echo "										<td align=\"left\">\n";
										echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=toip&fid=".$row['totype'].$row['toid']."\">";
										echo "								&nbsp;<IMG SRC=\"images/icons/ranges.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"ranges\"></a>&nbsp;";
										echo "										</td>\n";
										echo "										<td align=\"left\">\n";
										echo "								<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=toip&fid=".$row['totype'].$row['toid']."\">";
										echo "								".$gather['name']."</a></td>\n";
              							echo "									</tr>\n";
										echo "								</table>\n";
										echo "							</td>\n";
										break;
									}
								}
							}
							else
							{
								echo "							<td valign=\"top\" align=\"left\" width=\"\" height=\"20\">\n";
								echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
               					echo "									<tr valign=\"middle\">\n";
      							echo "										<td align=\"left\">\n";
								echo "											&nbsp;";
								echo "										</td>\n";
								echo "										<td align=\"left\">\n";
								echo "											&nbsp;-</td>\n";
								echo "									</tr>\n";
								echo "								</table>\n";	
								echo "							</td>\n";
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
														
							echo "						<td rowspan=\"2\" valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">\n";
							echo "							&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=priorityup&sid=".$row['id']."&field=priority\" title=\"priority: UP\"><IMG SRC=\"images/icons/up.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"up\"></a>";
							echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=prioritydown&sid=".$row['id']."&field=priority\" title=\"priority: DOWN\"><IMG SRC=\"images/icons/down.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"down\"></a>";
							echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=delete&sid=".$row['id']."\" title=\"delete rule\"><IMG SRC=\"images/icons/delete.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\ ALT=\"delete\"></a>";
							echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=addafter&sid=".$row['id']."&field=status\" title=\"add: AFTER\"><IMG SRC=\"images/icons/add_after.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"add after\"></a>";
							echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=addbefore&sid=".$row['id']."&field=status\" title=\"add: BEFORE\"><IMG SRC=\"images/icons/add_before.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"add before\"></a>&nbsp;</td>\n";

/*							echo "						<td rowspan=\"2\" valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">\n";
							echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=add&type=main&sid=".$row['id']."\" title=\"add entry\"><IMG SRC=\"images/neu.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\ ALT=\"add\"></a>";
							echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=delete&type=main&sid=".$row['id']."\" title=\"delete entry\"><IMG SRC=\"images/icons/delete.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\ ALT=\"delete\"></a>";
							*/
							echo "					</tr>\n";
							
							if (is_float(($i/2)) == false)
								echo "						<tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
							else
								echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
							
							switch ($row['satype'])
							{
        						case '*':
								{
									echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\">&nbsp;\n";
									echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=satype\" title=\"source service\">any</a>";
									echo "							</td>\n";
									break;
								}
								case '1':
								{
								
									$result2 = mysql_query("select * from so_services where (id=".$row['said'].")");
									$gather = mysql_fetch_array($result2);
									echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\">&nbsp;\n";
									echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=satype\" title=\"source service\">".$gather['name']."</a>";
									echo "						</td>\n";
								    break;
								}
								case '2':
								{
									$result2 = mysql_query("select * from po_protocols where (id=".$row['said'].")");
									$gather = mysql_fetch_array($result2);
			                        echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\" class=\"textred\">&nbsp;\n";
									echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=satype\" title=\"source PROTOCOL\">".$gather['pr_keyword']."</a>";
									echo "						</td>\n";
								    break;
								}
								case '3':
								{
									$result2 = mysql_query("select * from so_services where (id=".$row['said'].")");
									$gather = mysql_fetch_array($result2);
			                        echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\" class=\"textred\">&nbsp;\n";
									echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=satype\" title=\"source PROTOCOL\">".$gather['pr_keyword']."</a>";
									echo "						</td>\n";
								    break;
								}
								default:
								{
								    break;
								}
							}
							
							if (($row['ntype'] == 1) or ($row['ntype'] == 3))
							{
								if ($row['iiface'] != '*')
								{
									$result2= mysql_query("select * from io_interfaces where (id=".$row['iiface'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td valign=\"bottom\" align=\"left\" width=\"80px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr>\n";
									echo "										<td valign=\"bottom\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=iiface\"><img src=\"./images/icons/interface.gif\" border=\"0\"></a></td>";
									echo "										<td valign=\"middle\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=iiface\">".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								}
								else
								{
									echo "							<td valign=\"bottom\" align=\"left\" width=\"80px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr>\n";
									echo "										<td valign=\"bottom\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=iiface\"><img src=\"./images/icons/interface.gif\" border=\"0\"></a></td>";
									echo "										<td valign=\"middle\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=iiface\">all</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								}
							}
							else
							{
								echo "							<td valign=\"bottom\" align=\"left\" width=\"80px\" height=\"20\">\n";
								echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
								echo "									<tr>\n";
								echo "										<td valign=\"bottom\" align=\"left\">\n";
								echo "											&nbsp;</td>";
								echo "										<td valign=\"middle\" align=\"left\">\n";
								echo "											&nbsp;-</td>\n";
								echo "									</tr>\n";
								echo "								</table>\n";
								echo "							</td>\n";
							}
							
							switch ($row['datype'])
							{
								case '*':
								{
								    if ($row['satype'] != 2)
                                    {
                                        echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\">&nbsp;\n";
                                        echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=datype\" title=\"destination service\">any</a>";
									}
                                    elseif ($row['satype'] == 2)
                                    {
                                        echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\" class=\"textred\">&nbsp;\n";
                                        parse_protocol_options($tablename, $row['id'], $section);
									}

                                    break;
								}
								case '1':
								{
									$result2 = mysql_query("select * from so_services where (id=".$row['daid'].")");
									$gather = mysql_fetch_array($result2);
									echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\">&nbsp;\n";
									echo "							&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=datype\">".$gather['name']."</a>";
									echo "						</td>\n";
									break;
								}
								case '2':
								{
								    echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\" class=\"textred\">&nbsp;\n";
								    if ($row['satype'] == 2)
                                    {
                                        echo "&nbsp;".parse_protocol_options($tablename, $row['id'], $section);
                                    }
                                    else
                                    {
                                        echo "&nbsp;parse error";
                                    }
								}
								case '3':
								{
									$result2 = mysql_query("select * from so_services where (id=".$row['daid'].")");
									$gather = mysql_fetch_array($result2);
									echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\">&nbsp;\n";
									echo "							&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=datype\">".$gather['name']."</a>";
									echo "						</td>\n";
									break;
								}
    						}
							
							if (($row['ntype'] == 0) or ($row['ntype'] == 2))
							{
								if ($row['oiface'] != '*')
								{
									$result2= mysql_query("select * from io_interfaces where (id=".$row['oiface'].")");
									$gather = mysql_fetch_array($result2);
									echo "							<td valign=\"bottom\" align=\"left\" width=\"80px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";

        								echo "									<tr>\n";
	               							echo "										<td valign=\"bottom\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=oiface\"><img src=\"./images/icons/interface.gif\" border=\"0\"></a></td>\n";
									echo "										<td valign=\"middle\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=oiface\">".$gather['name']."</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								}
								else
								{
									echo "							<td valign=\"bottom\" align=\"left\" width=\"80px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr>\n";
									echo "										<td valign=\"bottom\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=oiface\"><img src=\"./images/icons/interface.gif\" border=\"0\"></a></td>\n";
									echo "										<td valign=\"middle\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=oiface\">all</a></td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
								}
							}
							else
							{
							        echo "							<td valign=\"bottom\" align=\"left\" width=\"80px\" height=\"20\">\n";
							        echo "							<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
								echo "									<tr>\n";
								echo "										<td valign=\"bottom\" align=\"left\">\n";
								echo "											&nbsp;</td>\n";
								echo "										<td valign=\"middle\" align=\"left\">\n";
								echo "											&nbsp;-</td>\n";
								echo "									</tr>\n";
								echo "								</table>\n";
								echo "							</td>\n";
							}
							
							switch ($row['topid'])
							{
								case '*':
								{
									echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr>\n";
									echo "										<td valign=\"bottom\" align=\"left\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=topid\">";
        								echo "											&nbsp;<IMG SRC=\"images/icons/blitz.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\"></a>";
	               							echo "										</td>\n";
									echo "										<td valign=\"middle\" align=\"left\">\n";
									echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=topid\">any</a>";
									echo "										</td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
								}
								default:
								{
									$result2 = mysql_query("select * from so_services where (id=".$row['topid'].")");
									$gather = mysql_fetch_array($result2);
									echo "						<td valign=\"middle\" align=\"left\" width=\"110px\" height=\"20\">\n";
									echo "								<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" height=\"100%\">\n";
									echo "									<tr>\n";
									echo "										<td valign=\"bottom\" align=\"left\">\n";
									echo "											<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=topid\">";
									echo "											&nbsp;<IMG SRC=\"images/icons/blitz.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\"></a>";
									echo "										</td>\n";
									echo "										<td valign=\"middle\" align=\"left\">\n";
        								echo "											&nbsp;<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$row['id']."&field=topid\">".$gather['name']."</a>";
									echo "										</td>\n";
									echo "									</tr>\n";
									echo "								</table>\n";
									echo "							</td>\n";
									break;
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
						echo "						<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
						echo "							&nbsp;-</td>\n";
						echo "						<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
						echo "							&nbsp;-</td>\n";
						echo "						<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
						echo "							&nbsp;-</td>\n";
					        echo "						<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">\n";
						echo "							&nbsp;-</td>\n";
						echo "						<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">\n";
						echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=addafter&sid=".$row['id']."&field=status\"><IMG SRC=\"images/add_entry_gr.gif\" BORDER=\"0\" ALT=\"add after\"></a></td>";
//						echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=add&type=main&sid=".$row['id']."\"><IMG SRC=\"images/neu.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\ ALT=\"add main\"></a></td>";
						echo "					</tr>\n";
					}
					echo "					<tr bgcolor=\"#565656\">\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
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
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						<td valign=\"bottom\" align=\"center\" width=\"\" height=\"12\">";
					echo "							<a href=\"".$_SERVER['PHP_SELF']."?module=activate&g_module=".$section."&action=activate&params=execute\"><IMG SRC=\"images/activate.gif\" BORDER=\"0\" ALT=\"activate\"></a></td>";	
        				echo "					</tr>\n";
					echo "					</table>\n";
					echo "				</td>\n";
					echo "			</tr>\n";
					echo "		</table>\n";
					echo "	<br><br><br>\n";
					break;
				}
			}
		}
		
		// ----------------------------
		// | Change NAT Status		  |
		// ----------------------------
        	// | Last Change : 29.03.2002 |
		// ----------------------------
		// | Status : Enabled		  |
		// ----------------------------
		function status_nat($type, $section, $section2, $tablename, $tablename2, $id)
		{
			# Changes the status (without prompt) of the selected
			# NAT Entry. No Return Value. Redirects to rearrange function.
			# --------------------------------------------------------------------
			$result = mysql_query("select * from ".$tablename." where (id='".$id."')") or die(mysql_error());
			
			# Get Currente Status of Entry
        		# ---------------------------------
			$row = mysql_fetch_array($result);
			
			# Select Status of Entry
			# -------------------------
			
			if ($row['totype'] != '*' or $row['ntype'] > 1)
			{
				if ($row['status'] == 0)
				{
					# Set Status of Entry == 1
					# ---------------------------
					$result = mysql_query("update ".$tablename." set status=1 where (id='".$id."')") or die(mysql_error());
				}
				else
        			{
					# Set Status of Entry == 0
					# ---------------------------
					$result = mysql_query("update ".$tablename." set status=0 where (id='".$id."')") or die(mysql_error());
				}
			}
	
			# Change Priorities (if changed)
        		# Show Strategies (Default Mode)
			# ---------------------------------
			correct_priorities($section, $tablename);
			show_nat(0, $section, $section2, $tablename);
		}

		

		// ----------------------------
        // | Change NAT Method		  |
		// ----------------------------
		// | Last Change : 29.03.2002 |
		// ----------------------------
		// | Status : Enabled		  |
		// ----------------------------
		function method_nat($type, $section, $section2, $tablename, $tablename2, $id)
		{
			# Changes the method (without prompt) of the selected
			# NAT Entry. No Return Value. Redirects to rearrange function.
			# --------------------------------------------------------------------
			switch ($type)
			{
				case 0:
				{
					# Status Change for Main Entry
					# ---------------------------------
					$result = mysql_query("select * from ".$tablename." where (id='".$id."')") or die(mysql_error());
					
					# Get Currente Status of Entry
					# ---------------------------------
					$row = mysql_fetch_array($result);
					
					# Select Status of Entry
					# -------------------------
					switch($row['ntype'])
					{
					    case '0':
					    {
					        if ($row['status'] == 0)
					        {
					            $result = mysql_query("update ".$tablename." set ntype=1 where (id='".$id."')") or die(mysql_error());
					        }
					        
					        break;
                        }
                        case '1':
                        {
                            $result = mysql_query("update ".$tablename." set ntype=2 where (id='".$id."')") or die(mysql_error());

                            break;
                        }
                        case '2':
                        {
                            $result = mysql_query("update ".$tablename." set ntype=3 where (id='".$id."')") or die(mysql_error());

                            break;
                        }
                        case '3':
                        {
                            $result = mysql_query("update ".$tablename." set ntype=4 where (id='".$id."')") or die(mysql_error());

                            break;
                        }
                        case '4':
                        {
                            $result = mysql_query("update ".$tablename." set ntype=5 where (id='".$id."')") or die(mysql_error());

                            break;
                        }
			case '5':
			{
                            if ($row['status'] == 0)
                            {
                                $result = mysql_query("update ".$tablename." set ntype=0 where (id='".$id."')") or die(mysql_error());
                            }
					
			    break;
                        }
                    }
				}
			}
			
			# Change Priorities (if changed)
			# Show Strategies (Default Mode)
			# ---------------------------------
			correct_priorities($section, $tablename);
			show_nat(0, $section, $section2, $tablename);
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
            $result_filter = mysql_query("SELECT satype,said,datype,daid FROM ".$tablename." WHERE id=".$id) or die (mysql_error());
            $row_filter = mysql_fetch_array($result_filter);

            if (($row_filter['satype'] == "*") or ($row_filter['datype'] == 1))
            {
                return;
            }

            $result_protocol = mysql_query("SELECT id,pr_decimal FROM ".$sql_db_local->sql_db_table_po_protocols." WHERE id=".$row_filter['said']) or die(mysql_error());
            $row_protocol = mysql_fetch_array($result_protocol);

            switch ($row_protocol['pr_decimal'])
            {
                case 1: //Case protocol 1 = ICMP
                {
                    if ($row_filter['daid']=='*')
                    {
                        echo "<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$id."&field=protopt\" title=\"ICMP type\">any type</a>";
                        return;
                    }

                    $result_icmp=mysql_query("SELECT icmp_name FROM icmp_types WHERE id=".$row_filter['daid']);
                    $row_icmp=mysql_fetch_array($result_icmp);

                    echo "<a href=\"".$_SERVER['PHP_SELF']."?module=".$section."&action=edit&sid=".$id."&field=protopt\" title=\"ICMP type\">".$row_icmp['icmp_name']."</a>";
                    return;

                    break;
                }
                default:
                {
                    echo "-";
                    return;
                    
                    break;
                }
            }
        }
                
        // -----------------------------------
		// | change Connection States         |
		// -----------------------------------
		// | Last Change : 01.04.2003	      |
		// -----------------------------------
		// | Status : Enabled		      |
		// -----------------------------------
		function change_states($section, $section2, $tablename, $id, $field)
		{
			# Open Database #
			$result = mysql_query("select * from ".$tablename." where(id=".$id.")");
			$row = mysql_fetch_array($result);
			
			if (((int)($row['state_'.$field])) == 0)
			{
				$result = mysql_query("update ".$tablename." set state_".$field."='1' where(id='".$id."')");
				show_nat(0, $section, $section2, $tablename);
			}
			elseif (((int)($row['state_'.$field])) == 1)
			{
				$result = mysql_query("update ".$tablename." set state_".$field."='0' where(id='".$id."')");
				show_nat(0, $section, $section2, $tablename);
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

?>

