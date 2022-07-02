<?php
		///////////////////////////////////////////////////////
		// --> DOMedia <--> 2001/02 <--> vis|wall <--  //
		///////////////////////////////////////////////////////
		//																//
		// MainGroup   : Interface                             //
		//																//
		// Name			: Module - Hosts		       			//
		// Date			: 04.02.2002							//
		// Comment  	: Object Hosts							//
		//																//
		///////////////////////////////////////////////////////
		
		function show_objects_networkobjects($type, $section, $section2, $tablename)
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
			
			/*echo "   &nbsp;<b>Aktive Sektion : ".$section." | Anzahl der Eintraege : ".$number."</b>&nbsp;\n";
			echo "  </td>\n";
			echo "  <td width=\"20%\" valign=\"middle\" align=\"right\" bgcolor=\"#e2e3df\">\n";
			echo "   &nbsp;<a href=\"".$PHP_SELF."?mainsection=t_objects&section=t_objects_overview\">..:: back ::..</a>&nbsp;\n";
			echo "  </td>\n";
			echo " </tr>\n";
			echo "</table>\n";*/
			/*echo "<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" >\n";
			echo " <tr height=\"100%\" valign=\"middle\">\n";
			echo "  <td width=\"100%\" align=\"center\">\n";
			echo "   &nbsp;<br><a href=\"".$PHP_SELF."?mainsection=t_objects&section=t_objects_item&subsection=".$section."&action=add\">..:: add entry ::..</a>&nbsp;\n";
			echo "   <table border=\"1\" cellpadding=\"2\" cellspacing=\"0\" bordercolor=\"#000000\" bgcolor=\"#c2d0f9\">\n";*/
			echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
			echo "			<tr>\n";
			echo "				<td height=\"20px\" colspan=\"2\">\n";
			echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
			echo "			</tr>\n";
			echo "			<tr>\n";
			echo "				<td align=\"left\" width=\"40px\">\n";
			echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
			echo "				<td align=\"left\">\n";
			
			// Display-Type (Hosts, Networks, Ranges)
			switch ($type)
			{
				// Display Hosts
				case 0:
				{
					// Generate Table-Header
					echo "<TABLE cellSpacing=1 cellPadding=0 width=672 border=0>\n";
					echo "<TBODY>\n";
					echo "<TR class=tablehead bgColor=#565656>\n";
					echo "<TD vAlign=bottom align=left width=\"226\" height=\"22\"><FONT color=#ffffff>&nbsp;HOSTNAME</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"226\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"226\" height=\"22\"><FONT color=#ffffff>&nbsp;NOTES</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"226\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"120\" height=\"22\"><FONT color=#ffffff>&nbsp;IP ADDRESS</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"120\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"94\" height=\"22\"><FONT color=#ffffff>&nbsp;ADMINISTRATE</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"94\" border=0></TD>\n";
					echo "</TR>\n";
					
					/*echo "  <tr>\n";
					//echo "   <th width=\"25px\" align=\"left\">\n";
					//echo "    <p>id</p>\n";
					//echo "   </th>\n";
					echo "   <th width=\"100px\" align=\"left\">\n";
					echo "    <p>hostname</p>\n";
					echo "   </th>\n";
					echo "   <th width=\"250px\" align=\"left\">\n";
					echo "    <p>notes</p>\n";
					echo "   </th>\n";
					echo "   <th width=\"100px\" align=\"left\">\n";
					echo "    <p>ip address</p>\n";
					echo "   </th>\n";
					echo "   <th width=\"100px\" align=\"left\">\n";
					echo "    <p>administrate</p>\n";
					echo "   </th>\n";
					echo "  </tr>\n";*/
					
					// Read and Display Database Entries					
					for ($i=0; $i < $number; $i++)
					{
						$row = mysql_fetch_array($result);
						
						if (is_float(($i/2)) == false)
						{
							echo "						<tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
						}
						else
						{
							echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
						}
						
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['name']."</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['note']."</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['hostip']."</TD>\n";
						echo "<TD vAlign=middle align=center width=\"\" height=\"22\">\n";
						echo "&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=edit&sid=".$row['id']."\"><IMG SRC=\"./images/icons/edit_gr.gif\" WIDTH=\"22\" HEIGHT=\"16\" BORDER=0 ALT=\"edit\"></a>\n";
						echo "<a href=\"".$PHP_SELF."?module=".$section."&action=delete&sid=".$row['id']."&sd_override=no\"><IMG SRC=\"./images/icons/delete.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=0 ALT=\"delete\"></a>&nbsp;</TD>\n";
						echo "</TR>\n";
						
					}
					
					echo "					<tr bgcolor=\"#565656\">\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "					</tr>\n";
					echo "					<TR>\n";
					echo "						<TD vAlign=bottom align=left height=12 colspan=\"3\">&nbsp;</TD>\n";
					echo "						<TD vAlign=bottom align=middle height=20>&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=add\"><IMG SRC=\"./images/add_entry_gr.gif\" WIDTH=\"50\" HEIGHT=\"16\" BORDER=0 ALT=\"add entry\"></a>&nbsp;</TD>\n";
					echo "					</TR>\n";
					echo "					</table>\n";
					echo "					</tbody>\n";
					echo "				</td>\n";
					echo "			</tr>\n";
					echo "		</table>\n";
					echo "	<br><br><br>\n";
					break;
				}
				case 1:
				{
					// Generate Table-Header
					echo "<TABLE cellSpacing=1 cellPadding=0 width=672 border=0>\n";
					echo "<TBODY>\n";
					echo "<TR class=tablehead bgColor=#565656>\n";
					echo "<TD vAlign=bottom align=left width=\"190\" height=\"22\"><FONT color=#ffffff>&nbsp;NAME</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"200\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"190\" height=\"22\"><FONT color=#ffffff>&nbsp;NOTES</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"200\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;IP ADDRESS</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;MASK ADDRESS</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"92\" height=\"22\"><FONT color=#ffffff>&nbsp;ADMINISTRATE</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"92\" border=0></TD>\n";
					echo "</TR>\n";
					
					// Read and Display Database Entries					
					for ($i=0; $i < $number; $i++)
					{
						$row = mysql_fetch_array($result);
						
						if (is_float(($i/2)) == false)
						{
							echo "						<tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
						}
						else
						{
							echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
						}
						
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['name']."</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['note']."</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['networkip']."</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['networkmask']."</TD>\n";
						echo "<TD vAlign=middle align=middle width=\"\" height=\"22\">\n";
						echo "&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=edit&sid=".$row['id']."\"><IMG SRC=\"images/icons/edit_gr.gif\" WIDTH=\"22\" HEIGHT=\"16\" BORDER=0 ALT=\"edit\"></a>\n";
						echo "<a href=\"".$PHP_SELF."?module=".$section."&action=delete&sid=".$row['id']."&sd_override=no\"><IMG SRC=\"images/icons/delete.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=0 ALT=\"delete\"></a>&nbsp;</TD>\n";
						echo "</TR>\n";
					}
					
					echo "					<tr bgcolor=\"#565656\">\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
					echo "					</tr>\n";
					echo "					<TR>\n";
					echo "						<TD vAlign=bottom align=left height=12 colspan=\"4\">&nbsp;</TD>\n";
					echo "						<TD vAlign=bottom align=middle height=20>&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=add\"><IMG SRC=\"./images/add_entry_gr.gif\" WIDTH=\"50\" HEIGHT=\"16\" BORDER=0 ALT=\"add entry\"></a>&nbsp;</TD>\n";
					echo "					</TR>\n";
					echo "					</table>\n";
					echo "					</tbody>\n";
					echo "				</td>\n";
					echo "			</tr>\n";
					echo "		</table>\n";
					echo "	<br><br><br>\n";
					break;
				}
				case 2:
				{
					// Generate Table-Header
					echo "  <tr>\n";
					//echo "   <th width=\"25px\" align=\"left\">\n";
					//echo "    <p>id</p>\n";
					//echo "   </th>\n";
					echo "   <th width=\"100px\" align=\"left\">\n";
					echo "    <p>name</p>\n";
					echo "   </th>\n";
					echo "   <th width=\"250px\" align=\"left\">\n";
					echo "    <p>notes</p>\n";
					echo "   </th>\n";
					echo "   <th width=\"100px\" align=\"left\">\n";
					echo "    <p>ip start</p>\n";
					echo "   </th>\n";
					echo "   <th width=\"100px\" align=\"left\">\n";
					echo "    <p>ip end</p>\n";
					echo "   </th>\n";
					echo "   <th width=\"100px\" align=\"left\">\n";
					echo "    <p>mask</p>\n";
					echo "   </th>\n";
					echo "   <th width=\"100px\" align=\"left\">\n";
					echo "    <p>administrate</p>\n";
					echo "   </th>\n";
					echo "  </tr>\n";
					
					// Read and Display Database Entries					
					for ($i=0; $i < $number; $i++)
					{
						$row = mysql_fetch_array($result);
						
						echo "  <tr>\n";
						//echo "   <td align=\"left\">\n";
						//echo $row['id'];
						//echo "   </td>\n";
						echo "   <td align=\"left\">\n";
						echo $row['name'];
						echo "   </td>\n";
						echo "   <td align=\"left\">\n";
						echo $row['note'];
						echo "   </td>\n";
						echo "   <td align=\"left\">\n";
						echo $row['rangeipstart'];
						echo "   </td>\n";
						echo "   <td align=\"left\">\n";
						echo $row['rangeipend'];
						echo "   </td>\n";
						echo "   <td align=\"left\">\n";
						echo $row['rangemask'];
						echo "   </td>\n";
						echo "   <td align=\"left\">\n";
						echo "    <a href=\"".$PHP_SELF."?module=".$section."&action=edit&sid=".$row['id']."\">edit</a>&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=delete&sid=".$row['id']."\">delete</a>\n";
						echo "   </td>\n";
						echo "  </tr>\n";
					}
					
					echo "</table></td></tr></table>";					
					break;
				}
				// Display Groups
				case 3:
				{
					// Generate Table-Header
					echo "  <tr>\n";
					echo "   <th width=\"25px\" align=\"left\">\n";
					echo "    <p>id</p>\n";
					echo "   </th>\n";
					echo "   <th width=\"100px\" align=\"left\">\n";
					echo "    <p>name</p>\n";
					echo "   </th>\n";
					echo "   <th width=\"250px\" align=\"left\">\n";
					echo "    <p>note</p>\n";
					echo "   </th>\n";
					echo "   <th width=\"100px\" align=\"left\">\n";
					echo "    <p>administrate</p>\n";
					echo "   </th>\n";
					echo "  </tr>\n";
					
					// Read and Display Database Entries					
					for ($i=0; $i < $number; $i++)
					{
						$row = mysql_fetch_array($result);
						
						echo "  <tr>\n";
						echo "   <td align=\"left\">\n";
						echo $row['id'];
						echo "   </td>\n";
						echo "   <td align=\"left\">\n";
						echo $row['name'];
						echo "   </td>\n";
						echo "   <td align=\"left\">\n";
						echo $row['note'];
						echo "   </td>\n";
						echo "   <td align=\"left\">\n";
						echo "    <a href=\"".$PHP_SELF."?module=".$section."&action=edit&sid=".$row['id']."\">edit</a>&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=modify&sid=".$row['id']."\">modify</a>&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=delete&sid=".$row['id']."\">delete</a>\n";
						echo "   </td>\n";
						echo "  </tr>\n";
					}
					
					echo "</table></td></tr></table>";					
					break;
				}
				default:
				{
					errorcode(7,0);
					break;
				}
			}
		}
		// ----------------------------------------
		// | Objects - Networkobjects (Edit)  |
		// ----------------------------------------
		// | Last Change : 27.11.2001          |
		// ----------------------------------------
		// | Status : Enabled                       |
		// ----------------------------------------
		function edit_objects_networkobjects($type, $section, $section2, $tablename, $id, $status)
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
				
				echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=edit\" name=\"submitform\">";
				echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
				echo "			<tr>\n";
				echo "				<td height=\"20px\" colspan=\"2\">\n";
				echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
				echo "			</tr>\n";
				echo "			<tr>\n";
				echo "				<td align=\"left\" width=\"40px\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\">\n";
				
				// Edit-Type (Hosts, Networks)
				switch ($type)
				{
					// Edit Type Selection
					case 0:
					{
						# Hosts (Edit)
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"280\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"270\" height=\"22\"><FONT color=#ffffff>&nbsp;".$id."</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"270\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;HOSTNAME</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$row['name']."\" name=\"hostname\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTE</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$row['note']."\" name=\"note\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IP</TD>\n";
						echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
						echo "<input type=text value=\"".$row['hostip']."\" name=\"hostip\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\" size=\"40\">\n";
						echo "<input type=\"hidden\" value=\"".$row['name']."\" name=\"oldhostname\" size=\"40\">\n";
						echo "<input type=\"hidden\" name=\"no_change\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					echo "<a href=\"".$PHP_SELF."?module=".$section."\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 1:
					{
						# Networks (Edit) #
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"280\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"270\" height=\"22\"><FONT color=#ffffff>&nbsp;".$id."</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"270\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$row['name']."\" name=\"hostname\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTE</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$row['note']."\" name=\"note\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETWORKIP</TD>\n";
						echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
						echo "<input type=text value=\"".$row['networkip']."\" name=\"networkip\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETMASK</TD>\n";
						echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
						echo "<input type=text value=\"".$row['networkmask']."\" name=\"networkmask\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\" size=\"40\">\n";
						echo "<input type=\"hidden\" value=\"".$row['name']."\" name=\"oldhostname\" size=\"40\">\n";
						echo "<input type=\"hidden\" name=\"no_change\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					echo "<a href=\"".$PHP_SELF."?module=hosts\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 2:
					{
						break;
					}
					case 3:
					{
						break;
					}
					default:
					{
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
				
				echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=edit\"  name=\"submitform\">";
				echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
				echo "			<tr>\n";
				echo "				<td height=\"20px\" colspan=\"2\">\n";
				echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
				echo "			</tr>\n";
				echo "			<tr>\n";
				echo "				<td align=\"left\" width=\"40px\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\">\n";
				
				echo "<TABLE cellSpacing=1 cellPadding=0 width=\"280\" border=0>\n";
				echo "<TBODY>\n";
				echo "<TR bgcolor=\"#565656\">\n";
				echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"270\" height=\"22\"><FONT color=#ffffff>&nbsp;".$row['id']."</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"270\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"50\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"50\" border=0></TD>\n";
				echo "</TR>\n";
				
				switch ($type)
				{
					case 0:
					{
						global $hostname, $oldhostname, $note, $hostip, $id;
						
						if (substr($status,6,4) == 'joho')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;HOSTNAME</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$hostname."\" name=\"hostname\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,6,4) == 'noho')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;HOSTNAME</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$hostname."\" name=\"hostname\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTE</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$note."\" name=\"note\" size=\"40\">&nbsp;</TD>\n";
						echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
						echo "</TR>\n";
						
						if (substr($status,11,4) == 'joip')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IP</TD>\n";
							echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
							echo "<input type=text value=\"".$hostip."\" name=\"hostip\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,11,4) == 'noip')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IP</TD>\n";
							echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
							echo "<input type=text value=\"".$hostip."\" name=\"hostip\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\" size=\"40\">\n";
						echo "<input type=\"hidden\" value=\"".$oldhostname."\" name=\"oldhostname\" size=\"40\">\n";
						echo "<input type=\"hidden\" name=\"no_change\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"".$PHP_SELF."?module=hosts\"><img src=\"./images/icons/cancel.gif\" border=\"0\">&nbsp;\n";
						echo "</TD>\n";
						echo "</TR>\n";
						
						break;
					}
					case 1:
					{
						global $hostname, $oldhostname, $note, $networkip, $networkmask, $id;
						
						if (substr($status,6,4) == 'joho')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;HOSTNAME</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$hostname."\" name=\"hostname\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,6,4) == 'noho')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;HOSTNAME</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$hostname."\" name=\"hostname\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTE</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$note."\" name=\"note\" size=\"40\">&nbsp;</TD>\n";
						echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
						echo "</TR>\n";
						
						if (substr($status,11,5) == 'jonip')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETWORKIP</TD>\n";
							echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
							echo "<input type=text value=\"".$networkip."\" name=\"networkip\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,11,5) == 'nonip')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETWORKIP</TD>\n";
							echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
							echo "<input type=text value=\"".$networkip."\" name=\"networkip\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						
						if (substr($status,17,7) == 'jonmask')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETMASK</TD>\n";
							echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
							echo "<input type=text value=\"".$networkmask."\" name=\"networkmask\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,17,7) == 'nonmask')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETMASK</TD>\n";
							echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
							echo "<input type=text value=\"".$networkmask."\" name=\"networkmask\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\" size=\"40\">\n";
						echo "<input type=\"hidden\" value=\"".$oldhostname."\" name=\"oldhostname\" size=\"40\">\n";
						echo "<input type=\"hidden\" name=\"no_change\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					echo "<a href=\"".$PHP_SELF."?module=networks\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
						echo "</TD>\n";
						echo "</TR>\n";
						
						break;
					}
					case 2:
					{
						break;
					}
					case 3:
					{
						break;
					}
					default:
					{
						break;
					}
				}
				
				echo "					</tbody>\n";
				echo "					</table>\n";
				echo "				</td>\n";
				echo "			</tr>\n";
				echo "		</table>\n";
				echo "		</form>\n";
				echo "	<br><br><br>\n";
			}
			else
			{
				switch ($type)
				{
					case 0:
					{
						global $hostname, $oldhostname, $note, $hostip, $id, $magic, $lastmagic;
						
						if ($magic == $lastmagic)
						{
							show_objects_networkobjects($type,$section,$section2,$tablename);
						}
						else
						{
							$lastmagic = $magic;
							$field1 = "noho";
							$field2 = "noip";
							
							if ((checkhostname($hostname, $oldhostname, $tablename) == true) and !empty($hostname))
							{
								$field1 = "joho";
							}
							
							if (ip_address_check($hostip, $tablename, "hostip") == true)
							{
								$field2 = "joip";
							}
							
							if (($field1 == 'joho') and ($field2 == 'joip'))
							{
								$result = mysql_query("update $tablename set name='$hostname' where(id='$id')");
								$result = mysql_query("update $tablename set note='$note' where(id='$id')");
								$result = mysql_query("update $tablename set hostip='$hostip' where(id='$id')");
								
								show_objects_networkobjects($type,$section,$section2,$tablename);
							}
							else
							{
								edit_objects_networkobjects($type, $section, $section2, $tablename, $id, "error|".$field1."_".$field2);
							}
						}
						
						break;
					}				
					case 1:
					{
						global $hostname, $oldhostname, $note, $networkip, $networkmask, $id, $magic, $lastmagic;
						
						if ($magic == $lastmagic)
						{
							show_objects_networkobjects($type,$section,$section2,$tablename);
						}
						else
						{
							$lastmagic = $magic;
							$field1 = "noho";
							$field2 = "nonip";
							$field3 = "nonmask";
							
							if ((checkhostname($hostname, $oldhostname, $tablename) == true) and (!empty($hostname)))
							{
								$field1 = "joho";
							}
							
							if (na_address_check($networkip) == true)
							{
								$field2 = "jonip";
							}
							
							if (netmask_check($networkmask) == true)
							{
							    $field3 = "jonmask";
							}
							
							if (($field1 == 'joho') and ($field2 == 'jonip') and ($field3 == 'jonmask'))
							{
								$result = mysql_query("update $tablename set name='$hostname' where(id='$id')");
								$result = mysql_query("update $tablename set note='$note' where(id='$id')");
								$result = mysql_query("update $tablename set networkip='$networkip' where(id='$id')");
								$result = mysql_query("update $tablename set networkmask='$networkmask' where(id='$id')");
								
								show_objects_networkobjects($type,$section,$section2,$tablename);
							}
							else
							{
								edit_objects_networkobjects($type, $section, $section2, $tablename, $id, "error|".$field1."_".$field2."_".$field3);
							}
						}
						
						break;					
					}
					case 2:
					{
						break;						
					}
					case 3:
					{
						break;
					}				
				}
			}
		}

		// ----------------------------------------
		// | Objects - Networkobjects (Add)  |
		// ----------------------------------------
		// | Last Change : 27.11.2001          |
		// ----------------------------------------
		// | Status : Enabled                      |
		// ----------------------------------------
		function add_objects_networkobjects($type, $section, $section2, $tablename, $status)
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
				
				echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=add\" name=\"submitform\">";
				echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
				echo "			<tr>\n";
				echo "				<td height=\"20px\" colspan=\"2\">\n";
				echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
				echo "			</tr>\n";
				echo "			<tr>\n";
				echo "				<td align=\"left\" width=\"40px\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\">\n";
				
				# Add-Type (Hosts, Networks, Ranges) #
				switch ($type)
				{
					# Add Type Selection #
					case 0:
					{
						# Generate Input Form #
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"280\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"270\" height=\"22\"><FONT color=#ffffff>&nbsp;".$id."</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"270\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;HOSTNAME</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$row['name']."\" name=\"hostname\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTE</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$row['note']."\" name=\"note\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IP</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$row['hostip']."\" name=\"hostip\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" name=\"no_submit\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/add.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					echo "<a href=\"".$PHP_SELF."?module=hosts\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 1:
					{
						# Generate Input Form #
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"280\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"270\" height=\"22\"><FONT color=#ffffff>&nbsp;".$id."</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"270\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$row['name']."\" name=\"hostname\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTE</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$row['note']."\" name=\"note\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETWORKIP</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$row['networkip']."\" name=\"networkip\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETMASK</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$row['networkmask']."\" name=\"networkmask\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" name=\"no_submit\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/add.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					echo "<a href=\"".$PHP_SELF."?module=hosts\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 2:
					{
						break;
					}
					case 3:
					{
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
				
				echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=add\" name=\"submitform\">";
				echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
				echo "			<tr>\n";
				echo "				<td height=\"20px\" colspan=\"2\">\n";
				echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
				echo "			</tr>\n";
				echo "			<tr>\n";
				echo "				<td align=\"left\" width=\"40px\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\">\n";
				
				echo "<TABLE cellSpacing=1 cellPadding=0 width=\"280\" border=0>\n";
				echo "<TBODY>\n";
				echo "<TR bgcolor=\"#565656\">\n";
				echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"270\" height=\"22\"><FONT color=#ffffff>&nbsp;".$row['id']."</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"270\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"50\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"50\" border=0></TD>\n";
				echo "</TR>\n";
				
				switch ($type)
				{
					case 0:
					{
						if (substr($status,6,4) == 'joho')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$GLOBALS['hostname']."\" name=\"hostname\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,6,4) == 'noho')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$GLOBALS['hostname']."\" name=\"hostname\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTE</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$GLOBALS['note']."\" name=\"note\" size=\"40\">&nbsp;</TD>\n";
						echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
						echo "</TR>\n";
						
						if (substr($status,11,4) == 'joip')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IP</TD>\n";
							echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
							echo "<input type=text value=\"".$GLOBALS['hostip']."\" name=\"hostip\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,11,4) == 'noip')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IP</TD>\n";
							echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
							echo "<input type=text value=\"".$GLOBALS['hostip']."\" name=\"hostip\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" name=\"no_submit\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/add.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"".$PHP_SELF."?module=hosts\"><img src=\"./images/icons/cancel.gif\" border=\"0\">&nbsp;\n";
						echo "</TD>\n";
						echo "</TR>\n";
						
						break;
					}
					case 1:
					{
						if (substr($status,6,4) == 'joho')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;HOSTNAME</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$GLOBALS['hostname']."\" name=\"hostname\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,6,4) == 'noho')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;HOSTNAME</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$GLOBALS['hostname']."\" name=\"hostname\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTE</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$GLOBALS['note']."\" name=\"note\" size=\"40\">&nbsp;</TD>\n";
						echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
						echo "</TR>\n";
						
						if (substr($status,11,5) == 'jonip')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETWORKIP</TD>\n";
							echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
							echo "<input type=text value=\"".$GLOBALS['networkip']."\" name=\"networkip\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,11,5) == 'nonip')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETWORKIP</TD>\n";
							echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
							echo "<input type=text value=\"".$GLOBALS['networkip']."\" name=\"networkip\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						
						if (substr($status,17,7) == 'jonmask')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETMASK</TD>\n";
							echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
							echo "<input type=text value=\"".$GLOBALS['networkmask']."\" name=\"networkmask\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,17,7) == 'nonmask')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NETMASK</TD>\n";
							echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
							echo "<input type=text value=\"".$GLOBALS['networkmask']."\" name=\"networkmask\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" name=\"no_submit\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/add.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					echo "<a href=\"".$PHP_SELF."?module=networks\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
						echo "</TD>\n";
						echo "</TR>\n";
						
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
						if ($GLOBALS['magic'] == $GLOBALS['lastmagic'])
						{
							show_objects_networkobjects($type,$section,$section2,$tablename);
						}
						else
						{
							$GLOBALS['lastmagic'] = $GLOBALS['magic'];
							$field1 = "noho";
							$field2 = "noip";
							
							if ((checkhostname($GLOBALS['hostname'], "", $tablename) == true) and !empty($GLOBALS['hostname']))
							{
								$field1 = "joho";
							}
							
							if (ip_address_check($GLOBALS['hostip'], $tablename, "hostip") == true)
							{
								$field2 = "joip";
							}
							
							if (($field1 == 'joho') and ($field2 == 'joip'))
							{
								$data = "'','".$GLOBALS['hostname']."','".$GLOBALS['note']."','".$GLOBALS['hostip']."'";
								$fields = "id,name,note,hostip";
								$query = mysql_query("insert into ".$tablename." (".$fields.") values(".$data.")") or die(mysql_error());
								
								show_objects_networkobjects($type,$section,$section2,$tablename);
							}
							else
							{
								add_objects_networkobjects($type, $section, $section2, $tablename, "error|".$field1."_".$field2);
							}
						}
						
						break;
					}
					case 1:
					{
						if ($GLOBALS['magic'] == $GLOBALS['lastmagic'])
						{
							show_objects_networkobjects($type,$section,$section2,$tablename);
						}
						else
						{
							$GLOBALS['lastmagic'] = $GLOBALS['magic'];
							$field1 = "noho";
							$field2 = "nonip";
							$field3 = "nonmask";
						
							if ((checkhostname($GLOBALS['hostname'], "", $tablename) == true) and (!empty($GLOBALS['hostname'])))
							{
								$field1 = "joho";
							}
							
                            if (na_address_check($GLOBALS['networkip']) == true)
							{
								$field2 = "jonip";
							}
							
							if (netmask_check($GLOBALS['networkmask']) == true)
							{
								$field3 = "jonmask";
							}
							
							if (($field1 == 'joho') and ($field2 == 'jonip') and ($field3 == 'jonmask'))
							{
								$data = "'','".$GLOBALS['hostname']."','".$GLOBALS['note']."','".$GLOBALS['networkip']."','".$GLOBALS['networkmask']."'";
								$fields = "id,name,note,networkip,networkmask";
								$query = mysql_query("insert into ".$tablename." (".$fields.") values(".$data.")") or die(mysql_error());
								
								show_objects_networkobjects($type,$section,$section2,$tablename);
							}
							else
							{
								add_objects_networkobjects($type, $section, $section2, $tablename, "error|".$field1."_".$field2."_".$field3);
							}
						}
						
						break;
					}
					case 2:
					{
						break;						
					}
					case 3:
					{
						break;
					}
				}
			}
		}
?>
