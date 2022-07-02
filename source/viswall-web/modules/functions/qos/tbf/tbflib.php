<?php
		////////////////////////////////////////////////////
		//  --> ITSoft <--> 2001/02/03 <--> vis|wall <--  //
		////////////////////////////////////////////////////
		//                                                //
		// MainGroup   : Interface                        //
		//                                                //
		// Name			: Module - QoS (TBF)              //
		// Date			: 10.06.2002					  //
		// Comment  	: Tocken Bucket Functions 		  //
		//												  //
		////////////////////////////////////////////////////
        
		// -------------------------------------
		// | Add TBF Entry (Sub,Main)           |
		// -------------------------------------
		// | Last Change : 10.01.2002           |
		// -------------------------------------
		// | Status : Enabled                   |
		// -------------------------------------
		function add_tbf($section, $section2, $tablename, $tablename2, $sid)
		{
            # Get Highest Priority
        	$result = mysql_query("select * from ".$tablename." order by id");
            $number = mysql_num_rows($result);
			
			$result_if = mysql_query("select * from io_interfaces where(name='eth0')");
			$row_if = mysql_fetch_array($result_if);
			
			# Create new Default Entry #
			$data = "'','0','0','1500','64','0','100','".(int)($row_if['id'])."','Empty','0'";
			$fields = "id,rate,burst,latency_limit,mpu,peakrate,mtu,iid,name,status";
			$query = mysql_query("insert into ".$tablename." (".$fields.") values(".$data.")");
			
			# Show Strategies (Default Mode)
            show_tbf($section, $section2, $tablename);
		}
        
        // -------------------------------------
		// | Delete NAT Entry (Sub,Main)   |
		// -------------------------------------
		// | Last Change : 10.01.2002       |
		// -------------------------------------
		// | Status : Enabled                   |
		// -------------------------------------
		function delete_tbf($section, $section2, $tablename, $tablename2, $sid)
		{
            $result_delete = mysql_query("delete from ".$tablename." where(id=\"".$sid."\")");
			show_tbf($section, $section2, $tablename);
		}
		
        // -------------------------------------
		// | Edit NAT Entry (Sub,Main)       |
		// -------------------------------------
		// | Last Change : 12.02.2002       |
		// -------------------------------------
		// | Status : Enabled                   |
		// -------------------------------------
		function edit_tbf($section, $section2, $tablename, $tablename2, $sid, $field, $fdata)
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
					case 'latency_limit':
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
						
						echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=tbf&action=edit\" name=\"submitform\">";
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
						echo "<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"230\" height=\"22\"><FONT color=#ffffff>&nbsp;".$id."</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"230\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;LATENCY / LIMIT</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "&nbsp;&nbsp;<input type=text name=\"latency_limit\" value=\"".substr($row['latency_limit'],1)."\">\n";
						echo "&nbsp;&nbsp;<select name=\"ll_param\">";
						
						if (substr($row['latency_limit'],0,1) == 1)
						{
							echo "<option value=\"1\" selected>ms</option>\n";
							echo "<option value=\"2\">byte</option>\n";
						}
						else
						{
							echo "<option value=\"1\">ms</option>\n";
							echo "<option value=\"2\" selected>byte</option>\n";
						}
						
						# Submit Event Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$sid."\" name=\"hiddenid\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"".$PHP_SELF."?module=tbf\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'name':
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
						
						echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=tbf&action=edit\" name=\"submitform\">";
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
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<input type=text name=\"name\" value=\"".$row['name']."\">\n";
						
						# Submit Event Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$sid."\" name=\"hiddenid\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"".$PHP_SELF."?module=tbf\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'rate':
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
						
						echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=tbf&action=edit\" name=\"submitform\">";
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
						echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"220\" height=\"22\"><FONT color=#ffffff>&nbsp;".$id."</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"220\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;RATE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						
						if ($row['rate'] > 1024)
						{
							if ($row['rate'] > 1048576)
							{
								if ($row['rate'] > 1073741824)
								{
									echo "<input type=text name=\"rate\" value=\"".((int)($row['rate'])/(1073741824))."\">";
									echo "&nbsp;&nbsp;&nbsp;&nbsp;<select name=\"size_param\">";
									echo "<option value=\"1\">bps</option>";
									echo "<option value=\"1024\">kbps</option>";
									echo "<option value=\"1048576\">mbps</option>";
									echo "<option value=\"1073741824\" selected>gbps</option>";
								}
								else
								{
									echo "<input type=text name=\"rate\" value=\"".((int)($row['rate'])/(1048576))."\">";
									echo "&nbsp;&nbsp;&nbsp;&nbsp;<select name=\"size_param\">";
									echo "<option value=\"1\">bps</option>";
									echo "<option value=\"1024\">kbps</option>";
									echo "<option value=\"1048576\" selected>mbps</option>";
									echo "<option value=\"1073741824\">gbps</option>";
								}
							}
							else
							{
								echo "<input type=text name=\"rate\" value=\"".((int)($row['rate'])/(1024))."\">";
								echo "&nbsp;&nbsp;&nbsp;&nbsp;<select name=\"size_param\">";
								echo "<option value=\"1\">bps</option>";
								echo "<option value=\"1024\" selected>kbps</option>";
								echo "<option value=\"1048576\">mbps</option>";
								echo "<option value=\"1073741824\">gbps</option>";
							}
						}
						else
						{
							echo "<input type=text name=\"rate\" value=\"".((int)($row['rate'])/(1))."\">";
							echo "&nbsp;&nbsp;&nbsp;&nbsp;<select name=\"size_param\">";
							echo "<option value=\"1\" selected>bps</option>";
							echo "<option value=\"1024\">kbps</option>";
							echo "<option value=\"1048576\">mbps</option>";
							echo "<option value=\"1073741824\">gbps</option>";
							echo "<option value=\"1\" selected>bps</option>";
						}
						
						echo "</select>\n";
						
						# Submit Event Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$sid."\" name=\"hiddenid\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"".$PHP_SELF."?module=tbf\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'burst':
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
						
						echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=tbf&action=edit\" name=\"submitform\">";
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
						echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"220\" height=\"22\"><FONT color=#ffffff>&nbsp;".$id."</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"220\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;BURST</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						
						if ($row['rate'] > 1024)
						{
							if ($row['rate'] > 1048576)
							{
								if ($row['rate'] > 1073741824)
								{
									echo "<input type=text name=\"burst\" value=\"".((int)($row['burst'])/(1073741824))."\">";
									echo "&nbsp;&nbsp;&nbsp;&nbsp;<select name=\"size_param\">";
									echo "<option value=\"1\">bps</option>";
									echo "<option value=\"1024\">kbps</option>";
									echo "<option value=\"1048576\">mbps</option>";
									echo "<option value=\"1073741824\" selected>gbps</option>";
								}
								else
								{
									echo "<input type=text name=\"burst\" value=\"".((int)($row['burst'])/(1048576))."\">";
									echo "&nbsp;&nbsp;&nbsp;&nbsp;<select name=\"size_param\">";
									echo "<option value=\"1\">bps</option>";
									echo "<option value=\"1024\">kbps</option>";
									echo "<option value=\"1048576\" selected>mbps</option>";
									echo "<option value=\"1073741824\">gbps</option>";
								}
							}
							else
							{
								echo "<input type=text name=\"burst\" value=\"".((int)($row['burst'])/(1024))."\">";
								echo "&nbsp;&nbsp;&nbsp;&nbsp;<select name=\"size_param\">";
								echo "<option value=\"1\">bps</option>";
								echo "<option value=\"1024\" selected>kbps</option>";
								echo "<option value=\"1048576\">mbps</option>";
								echo "<option value=\"1073741824\">gbps</option>";
							}
						}
						else
						{
							echo "<input type=text name=\"burst\" value=\"".((int)($row['burst'])/(1))."\">";
							echo "&nbsp;&nbsp;&nbsp;&nbsp;<select name=\"size_param\">";
							echo "<option value=\"1\" selected>bps</option>";
							echo "<option value=\"1024\">kbps</option>";
							echo "<option value=\"1048576\">mbps</option>";
							echo "<option value=\"1073741824\">gbps</option>";
							echo "<option value=\"1\" selected>bps</option>";
						}
						
						echo "</select>\n";
						
						# Submit Event Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$sid."\" name=\"hiddenid\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"".$PHP_SELF."?module=tbf\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'iface':
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
						
						echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=tbf&action=edit\" name=\"submitform\">";
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
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;INTERFACE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						
						echo "<select name=\"interfaces\">\n";
						
						$result_interfaces = mysql_query("select * from io_interfaces order by id");
						$number_interfaces = mysql_num_rows($result_interfaces);
						for ($i=0;$i<$number_interfaces;$i++)
						{
							$row_interfaces=mysql_fetch_array($result_interfaces);
							if ($fdata == ($row_interfaces['id']))
							{
								echo "<option value=\"".$row_interfaces['id']."|".$row_interfaces['name']."\" name=\"interfaces".$row_interfaces['id']."\" selected> ".$row_interfaces['name']." </option>\n";
							}
							else
							{
								echo "<option value=\"".$row_interfaces['id']."|".$row_interfaces['name']."\" name=\"interfaces".$row_interfaces['id']."\"> ".$row_interfaces['name']." </option>\n";
							}								
						}
						
						# Submit Event Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$sid."\" name=\"hiddenid\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"".$PHP_SELF."?module=tbf\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 'peakrate':
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
						
						echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=tbf&action=edit\" name=\"submitform\">";
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
						echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"220\" height=\"22\"><FONT color=#ffffff>&nbsp;".$id."</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"220\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PEAKRATE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						
						if ($row['peakrate'] > 1024)
						{
							if ($row['peakrate'] > 1048576)
							{
								echo "<input type=text name=\"peakrate\" value=\"".((int)($row['peakrate'])/(1048576))."\">";
								echo "&nbsp;&nbsp;&nbsp;&nbsp;<select name=\"size_param\">";
								echo "<option value=\"1\">bit/s</option>";
								echo "<option value=\"1024\">kbit/s</option>";
								echo "<option value=\"1048576\" selected>mbit/s</option>";
							}
							else
							{
								echo "<input type=text name=\"peakrate\" value=\"".((int)($row['peakrate'])/(1024))."\">";
								echo "&nbsp;&nbsp;&nbsp;&nbsp;<select name=\"size_param\">";
								echo "<option value=\"1\">bit/s</option>";
								echo "<option value=\"1024\" selected>kbit/s</option>";
								echo "<option value=\"1048576\">mbit/s</option>";
							}
						}
						else
						{
							echo "<input type=text name=\"peakrate\" value=\"".((int)($row['peakrate'])/(1))."\">";
							echo "&nbsp;&nbsp;&nbsp;&nbsp;<select name=\"size_param\">";
							echo "<option value=\"1\" selected>bit/s</option>";
							echo "<option value=\"1024\">kbit/s</option>";
							echo "<option value=\"1048576\">mbit/s</option>";
						}
						
						echo "</select>\n";
						
						# Submit Event Data
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$sid."\" name=\"hiddenid\">\n";
						echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
						echo "<input type=\"hidden\" name=\"rsubmit\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"".$PHP_SELF."?module=tbf\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
						break;
					}
				}
			}
			else
			{
				switch ($GLOBALS['hiddenfield'])
				{
					case 'name':
					{
						$result = mysql_query("update ".$tablename." set name='".$GLOBALS['name']."' where(id='".$GLOBALS['hiddenid']."')") or die(mysql_error());
						
						# Show Strategies (Default Mode)
						# -----------------------------------
						show_tbf($section, $section2, $tablename);
						break;
					}
					case 'latency_limit':
					{
						$result = mysql_query("update ".$tablename." set latency_limit='".$GLOBALS['ll_param'].$GLOBALS['latency_limit']."' where(id='".$GLOBALS['hiddenid']."')") or die(mysql_error());
						
						# Show Strategies (Default Mode)
						# -----------------------------------
						show_tbf($section, $section2, $tablename);
						break;
					}
					case 'peakrate':
					{
						$result = mysql_query("update ".$tablename." set peakrate='".((int)($GLOBALS['size_param'])*(int)($GLOBALS['peakrate']))."' where(id='".$GLOBALS['hiddenid']."')") or die(mysql_error());
						
						# Show Strategies (Default Mode)
						# -----------------------------------
						show_tbf($section, $section2, $tablename);
						break;
					}
					case 'rate':
					{
					    if ($GLOBALS['rate'] == 0)
                        {
                            $result2 = mysql_query("update ".$tablename." set status=0 where (id='".$GLOBALS['hiddenid']."')") or die(mysql_error());
                        }
                        
						$result = mysql_query("update ".$tablename." set rate='".((int)($GLOBALS['size_param'])*(int)($GLOBALS['rate']))."' where(id='".$GLOBALS['hiddenid']."')") or die(mysql_error());
						
						# Show Strategies (Default Mode)
						# -----------------------------------
						show_tbf($section, $section2, $tablename);
						break;
					}
					case 'burst':
					{
					    if ($GLOBALS['burst'] == 0)
					    {
                            $result2 = mysql_query("update ".$tablename." set status=0 where (id='".$GLOBALS['hiddenid']."')") or die(mysql_error());
                        }
                        
						$result = mysql_query("update ".$tablename." set burst='".((int)($GLOBALS['size_param'])*(int)($GLOBALS['burst']))."' where(id='".$GLOBALS['hiddenid']."')") or die(mysql_error());
						
						# Show Strategies (Default Mode)
						# -----------------------------------
						show_tbf($section, $section2, $tablename);
						break;
					}
					case 'iface':
					{
						$result = mysql_query("update ".$tablename." set iid='".substr ($GLOBALS['interfaces'], 0, strpos($GLOBALS['interfaces'], "|"))."' where(id='".$GLOBALS['hiddenid']."')") or die(mysql_error());
						show_tbf($section, $section2, $tablename);
						break;
					}
					default :
					{
						break;
						# Select Type of Entry
						# ----------------------
						switch(substr($GLOBALS['sources'],0,1))
						{
							# Incorrect Value or Entry #
							case '-':
							{
								# Show Strategies (Default Mode)
								# -----------------------------------
								correct_priorities($section, $tablename);
								show_nat(0, $section, $section2, $tablename);
								break;
							}
							# Any #
							case '0':
							{
								# Update Entry for Any
								# -----------------------
								
								if (check_nat($tablename, $GLOBALS['hiddenfield'], $GLOBALS['sources'], $GLOBALS['hiddenid']) == 0)
								{
									$result = mysql_query("update ".$tablename." set ".substr($GLOBALS['hiddenfield'],0,1)."type='0' where(id='".$GLOBALS['hiddenid']."')") or die(mysql_error());
								}
								else
								{
									if (substr($GLOBALS['hiddenfield'],0,1) == 's')
										$result = mysql_query("update ".$tablename." set dtype='3' where(id='".$GLOBALS['hiddenid']."')") or die(mysql_error());
									else
										$result = mysql_query("update ".$tablename." set stype='3' where(id='".$GLOBALS['hiddenid']."')") or die(mysql_error());
										
									$result = mysql_query("update ".$tablename." set ".substr($GLOBALS['hiddenfield'],0,1)."type='0' where(id='".$GLOBALS['hiddenid']."')") or die(mysql_error());
								}
								
								# Show Strategies (Default Mode)
								# -----------------------------------
								correct_priorities($section, $tablename);
								show_nat(0, $section, $section2, $tablename);
								break;
							}
							# Network or Host #
							case '1':
							case '2':
							{
								# Update Entry for Network/Host
								# -----------------------------------
								
								if (check_nat($tablename, $GLOBALS['hiddenfield'], $GLOBALS['sources'], $GLOBALS['hiddenid']) == 0)
								{
									$result = mysql_query("delete from nat_layers where(pid='".$GLOBALS['hiddenid']."')");
									$result = mysql_query("update ".$tablename." set ".substr($GLOBALS['hiddenfield'],0,1)."type='".substr($GLOBALS['sources'],0,strpos($GLOBALS['sources'],"|"))."' where(id='".$GLOBALS['hiddenid']."')") or die(mysql_error());
								}
								else
								{
									if (substr($GLOBALS['hiddenfield'],0,1) == 's')
										$result = mysql_query("update ".$tablename." set dtype='3' where(id='".$GLOBALS['hiddenid']."')") or die(mysql_error());
									else
										$result = mysql_query("update ".$tablename." set stype='3' where(id='".$GLOBALS['hiddenid']."')") or die(mysql_error());
										
									$result = mysql_query("update ".$tablename." set ".substr($GLOBALS['hiddenfield'],0,1)."type='".substr($GLOBALS['sources'],0,strpos($GLOBALS['sources'],"|"))."' where(id='".$GLOBALS['hiddenid']."')") or die(mysql_error());
								}
								
								# Show Strategies (Default Mode)
								# -----------------------------------
								correct_priorities($section, $tablename);
								show_nat(0, $section, $section2, $tablename);
								break;
							}
						}
					}
				}
			}
		}
		
        // -------------------------------------
		// | Show QoS Entry					   |
		// -------------------------------------
		// | Last Change : 08.02.2002       |
		// -------------------------------------
		// | Status : Enabled                   |
		// -------------------------------------
		function show_tbf($section, $section2, $tablename)
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
			
			# Generate Table-Header #
			echo "					<table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"680px\" height=\"\">\n";
			echo "						<tr bgcolor=\"#565656\" class=\"tablehead\">\n";
			echo "							<td valign=\"bottom\" align=\"left\" width=\"50\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;STATUS</font>\n";
			echo "								<img src=\"images/border_orange.gif\" width=\"50\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"left\" width=\"230\" height=\"22\">\n\n";
			echo "   								<font color=\"#ffffff\">&nbsp;NAME</font>\n";
			echo "  								<img src=\"images/border_orange.gif\" WIDTH=\"230\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"left\" width=\"75\" height=\"22\">\n";
			echo "  								<font color=\"#ffffff\">&nbsp;RATE</font>\n";
			echo "  								 <img src=\"images/border_orange.gif\" WIDTH=\"75\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"left\" width=\"75\" height=\"22\">\n";
			echo "  								<font color=\"#ffffff\">&nbsp;BURST</font>\n";
			echo "  								 <img src=\"images/border_orange.gif\" WIDTH=\"75\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"left\" width=\"75\" height=\"22\">\n";
			echo "  								<font color=\"#ffffff\">&nbsp;LATENCY</font>\n";
			echo "  								 <img src=\"images/border_orange.gif\" WIDTH=\"75\" height=\"6\" border=\"0\"></td>\n";					
			//echo "  							<td valign=\"bottom\" align=\"left\" width=\"40\" height=\"22\">\n";
			//echo "  								<font color=\"#ffffff\">&nbsp;MPU</font>\n";
			//echo "  								 <img src=\"images/border_orange.gif\" WIDTH=\"40\" height=\"6\" border=\"0\"></td>\n";
			//echo "  							<td valign=\"bottom\" align=\"left\" width=\"62\" height=\"22\">\n";
			//echo "  								<font color=\"#ffffff\">&nbsp;PEAKRATE</font>\n";
			//echo "  								 <img src=\"images/border_orange.gif\" WIDTH=\"62\" height=\"6\" border=\"0\"></td>\n";					
			//echo " 							<td valign=\"bottom\" align=\"left\" width=\"50\" height=\"22\">\n";
			//echo "  								<font color=\"#ffffff\">&nbsp;MTU</font>\n";
			//echo "  								 <img src=\"images/border_orange.gif\" WIDTH=\"50\" height=\"6\" border=\"0\"></td>\n";					
			echo " 							<td valign=\"bottom\" align=\"left\" width=\"100\" height=\"22\">\n";
			echo "  								<font color=\"#ffffff\">&nbsp;IFACE</font>\n";
			echo "  								 <img src=\"images/border_orange.gif\" WIDTH=\"100\" height=\"6\" border=\"0\"></td>\n";					
			echo " 							<td valign=\"bottom\" align=\"left\" width=\"75\" height=\"22\">\n";
			echo "   								<font color=\"#ffffff\">&nbsp;FUNCTION</font>\n";
			echo "   								<img src=\"images/border_orange.gif\" WIDTH=\"75\" height=\"6\" border=\"0\"></td>\n";
			echo " 						</tr>\n";
			
			if ($number != 0)
			{
				# Read and Display Database Entries #
				$result = mysql_query("select * from ".$tablename." order by id") or die(mysql_error());
				$number = mysql_num_rows($result);
				for ($i=0; $i < $number; $i++)
				{
					$row = mysql_fetch_array($result);
					
					echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
					echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">";
					
					if ($row['status'] == 1)
						echo "								&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=setstatus&sid=".$row['id']."&field=status\"><IMG SRC=\"images/icons/on.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"on\"></a>&nbsp;</td>";
					else
						echo "							    &nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=setstatus&sid=".$row['id']."&field=status\"><IMG SRC=\"images/icons/off.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"off\"></a>&nbsp;</td>";
					
					
					echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">";
					echo "								&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=edit&sid=".$row['id']."&field=name\">".$row['name']."&nbsp;</a></td>";
					echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">";
					echo "								&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=edit&sid=".$row['id']."&field=rate\">";
					
					if ($row['rate'] > 1024)
					{
						if ($row['rate'] > 1048576)
						{
							if ($row['rate'] > 1073741824)
							{
								echo ((int)($row['rate'])/(1073741824))."gbps";
							}
							else
							{
								echo ((int)($row['rate'])/(1048576))."mbps";
							}
						}
						else
						{
							echo ((int)($row['rate'])/(1024))."kbps";
						}
					}
					else
					{
						echo ((int)($row['rate'])/(1))."bps";
					}
					
					echo "&nbsp;</a></td>";
					echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">";
					echo "								&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=edit&sid=".$row['id']."&field=burst\">";
					
					if ($row['burst'] > 1024)
					{
						if ($row['burst'] > 1048576)
						{
							if ($row['burst'] > 1073741824)
							{
								echo ((int)($row['burst'])/(1073741824))."gbps";
							}
							else
							{
								echo ((int)($row['burst'])/(1048576))."mbps";
							}
						}
						else
						{
							echo ((int)($row['burst'])/(1024))."kbps";
						}
					}
					else
					{
						echo ((int)($row['burst'])/(1))."bps";
					}
					
					echo "&nbsp;</a></td>";
					echo "							<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">";
					echo "								&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=edit&sid=".$row['id']."&field=latency_limit\">";
					echo substr($row['latency_limit'],1);
					if (substr($row['latency_limit'],0,1) == 1)
					{
						echo "ms</a></td>";
					}
					else
					{
						echo "byte</a></td>";
					}
					
					//echo "							<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">";
					//echo "								&nbsp;".$row['mpu']."&nbsp;</td>";
					/*echo "							<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">";
					echo "								&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=edit&sid=".$row['id']."&field=peakrate\">";
					if ($row['peakrate'] > 1024)
					{
						if ($row['peakrate'] > 1048576)
						{
							echo ((int)($row['peakrate'])/(1048576))."mbit/s";
						}
						else
						{
							echo ((int)($row['peakrate'])/(1024))."kbit/s";
						}
					}
					else
					{
						echo ((int)($row['peakrate'])/(1))."bit/s";
					}
					echo "&nbsp;</a></td>";*/
					
					//echo "							<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">";
					//echo "								&nbsp;".$row['mtu']."&nbsp;</td>";
					echo "							<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">";
					
					$db_local = new sql_db_local;
					$result_local = mysql_query("select * from ".$db_local->sql_db_table_io_interfaces." where(id='".$row['iid']."')") or die(mysql_error());
					$row_local = mysql_fetch_array($result_local);
					echo "								&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=edit&sid=".$row['id']."&field=iface&fid=".$row_local['id']."\">".$row_local['name']."&nbsp;</a></td>";
					
					echo "						<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">\n";
					echo "							<a href=\"".$PHP_SELF."?module=".$section."&action=add&sid=".$row['id']."\"><IMG SRC=\"images/neu.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\ ALT=\"add main\"></a>";
					echo "							<a href=\"".$PHP_SELF."?module=".$section."&action=delete&sid=".$row['id']."\"><IMG SRC=\"images/icons/delete.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\ ALT=\"delete main\"></a>";
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
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "					</tr>\n";
				echo "					<tr>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "					</tr>\n";
				echo "					<tr valign=\"middle\">\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";					
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">\n";
				echo "							<a href=\"".$PHP_SELF."?module=activate&g_module=".$section."&action=activate&params=execute\"><IMG SRC=\"images/activate.gif\" BORDER=\"0\" ALT=\"activate\"></a></td>";	
				echo "					</tr>\n";
				echo "					</table>\n";
				echo "				</td>\n";
				echo "			</tr>\n";
				echo "		</table>\n";
				echo "	<br><br><br>\n";
			}
			else
			{
				echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
				echo "						<td valign=\"middle\" align=\"left\" width=\"\" height=\"12\">&nbsp;-</td>\n";
				echo "						<td valign=\"middle\" align=\"left\" width=\"\" height=\"12\">&nbsp;-</td>\n";
				echo "						<td valign=\"middle\" align=\"left\" width=\"\" height=\"12\">&nbsp;-</td>\n";
				echo "						<td valign=\"middle\" align=\"left\" width=\"\" height=\"12\">&nbsp;-</td>\n";
				echo "						<td valign=\"middle\" align=\"left\" width=\"\" height=\"12\">&nbsp;-</td>\n";
				echo "						<td valign=\"middle\" align=\"left\" width=\"\" height=\"12\">&nbsp;-</td>\n";
				echo "						<td valign=\"middle\" align=\"center\" width=\"\" height=\"12\">";
				echo "							<a href=\"".$PHP_SELF."?module=".$section."&action=add\"><IMG SRC=\"images/add_entry_gr.gif\" BORDER=\"0\ ALT=\"add main\"></a>&nbsp;</td>\n";
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "					</tr>\n";
				
				echo "					<tr bgcolor=\"#565656\">\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "					</tr>\n";
				echo "					<tr>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "					</tr>\n";
				echo "					<tr>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";					
				echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				//echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "						<td valign=\"bottom\" align=\"center\" width=\"\" height=\"12\">";
				echo "							<a href=\"".$PHP_SELF."?module=activate&g_module=".$section."&action=activate&params=execute\"><IMG SRC=\"images/activate.gif\" BORDER=\"0\" ALT=\"activate\"></a></td>";	
				echo "					</tr>\n";
				echo "					</table>\n";
				echo "				</td>\n";
				echo "			</tr>\n";
				echo "		</table>\n";
				echo "	<br><br><br>\n";
			}
		}
		
        // -------------------------------------
		// | Change NAT Status (Sub,Main) |
		// -------------------------------------
		// | Last Change : 10.01.2002       |
		// -------------------------------------
		// | Status : Enabled                   |
		// -------------------------------------
		function status_tbf($section, $section2, $tablename, $tablename2, $id)
		{
			# Changes the status (without prompt) of the selected
			# NAT Entry. No Return Value. Redirects to rearrange function.
			$result = mysql_query("select * from ".$tablename." where (id='".$id."')") or die(mysql_error());
			
			# Get Currente Status of Entry
			# ---------------------------------
			$row = mysql_fetch_array($result);
			
			# Select Status of Entry
			# -------------------------
			if ($row['status'] == 0)
			{
			    if (($row['burst'] != 0) && ($row['rate'] != 0))
			    {
				    # Set Status of Entry == 1
				    # ---------------------------
				    $result = mysql_query("update ".$tablename." set status=1 where (id='".$id."')") or die(mysql_error());
				}
			}
			else
			{
				# Set Status of Entry == 0
				# ---------------------------
				$result = mysql_query("update ".$tablename." set status=0 where (id='".$id."')") or die(mysql_error());
			}
			
			show_tbf($section, $section2, $tablename);
		}
		
?>
