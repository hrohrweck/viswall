<?php
		/////////////////////////////////////////////////
		// --> itsoft Software GmbH --> vis|wall <--  //
		/////////////////////////////////////////////////
		//											   //
		// MainGroup   : Interface					   //
		//											   //
		// Name			: Module - Users		       //
		// Date			: 07.03.2002				   //
		// Comment  	: Object Users				   //
		//											   //
		/////////////////////////////////////////////////
		
		// ------------------------------------
		// | Objects - Users (Show)			  |
		// ------------------------------------
		// | Last Change : 07.03.2002		  |
		// ------------------------------------
		// | Status : Enabled				  |
		// ------------------------------------
		function show_users($section, $section2, $tablename)
		{
			$result = mysql_query("select * from ".$tablename." order by id");
			$number = mysql_num_rows($result);
			
			echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
			echo "			<tr valign=\"top\">\n";
			echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
			echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
			echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
			echo "					".$section2." (".$number.") &nbsp;</td>\n";
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
			
			// Generate Table-Header
			echo "<TABLE cellSpacing=1 cellPadding=0 width=650 border=0>\n";
			echo "<TBODY>\n";
			echo "<TR class=tablehead bgColor=#565656>\n";
			echo "<TD vAlign=bottom align=left width=\"50\" height=\"22\"><FONT color=#ffffff>&nbsp;STATUS</FONT>\n";
			echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"50\" border=0></TD>\n";
			echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;USERNAME</FONT>\n";
			echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
			echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;PASSWORD</FONT>\n";
			echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
			echo "<TD vAlign=bottom align=left width=\"200\" height=\"22\"><FONT color=#ffffff>&nbsp;NOTE</FONT>\n";
			echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"200\" border=0></TD>\n";
			echo "<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;ADMINISTRATE</FONT>\n";
			echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
			echo "</TR>\n";
			
			// Read and Display Database Entries
			for ($i=0; $i < $number; $i++)
			{
				$row = mysql_fetch_array($result);
				
				if (is_float(($i/2)) == false)
					echo "						<tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
				else
					echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
				
				if ($row['isroot'] == 0)
					echo "<TD vAlign=middle align=center width=\"\" height=\"22\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=setroot&root=1&sid=".$row['id']."\"><img src=\"./images/root_off.gif\" border=\"0\"></a></td>\n";
				else
					echo "<TD vAlign=middle align=center width=\"\" height=\"22\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=setroot&root=0&sid=".$row['id']."\"><img src=\"./images/root_on.gif\" border=\"0\"></a></td>\n";
				
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['username']."</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;************</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['note']."</TD>\n";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\">\n";
				echo "&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=edit&sid=".$row['id']."\"><IMG SRC=\"./images/icons/edit_gr.gif\" WIDTH=\"22\" HEIGHT=\"16\" BORDER=0 ALT=\"edit\"></a>\n";
				
				if ($row['issticky'] == 0)
					echo "<a href=\"".$PHP_SELF."?module=".$section."&action=delete&sid=".$row['id']."&sd_override=no\"><IMG SRC=\"./images/icons/delete.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=0 ALT=\"delete\"></a>&nbsp;</TD>\n";
				else
					echo "&nbsp;</td>\n";
				
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
		}
		
		// ------------------------------------
		// | Objects - Users (Edit)           |
		// ------------------------------------
		// | Last Change : 07.03.2002         |
		// ------------------------------------
		// | Status : Enabled                 |
		// ------------------------------------
		function edit_users($section, $section2, $tablename, $id, $status, $remote_module = 0)
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
				echo "					".$section2." (".$row['id'].") &nbsp;</td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
				echo "			</tr>\n";
				echo "		</table>\n";
				
				echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=edit&sid=".$id."&remote_module=".$remote_module."\" name=\"submitform\">";
				echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
				echo "			<tr>\n";
				echo "				<td height=\"20px\" colspan=\"2\">\n";
				echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
				echo "			</tr>\n";
				echo "			<tr>\n";
				echo "				<td align=\"left\" width=\"40px\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\">\n";
				
				echo "<TABLE cellSpacing=1 cellPadding=0 width=\"375\" border=0>\n";
				echo "<TBODY>\n";
				echo "<TR bgcolor=\"#565656\">\n";
				echo "<TD vAlign=bottom align=left width=\"175\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"175\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"200\" height=\"22\"><FONT color=#ffffff>&nbsp;".$id."</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"200\" border=0></TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;OLD PASSWORD</TD>\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
				echo "<input type=\"password\" value=\"\" name=\"users_edit_oldpassword\" size=\"29\">&nbsp;</TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;</TD>\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\">&nbsp;</TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;USERNAME</TD>\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
				echo "<input type=\"text\" value=\"".$row['username']."\" name=\"users_edit_username\" size=\"29\">&nbsp;</TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NEW PASSWORD</TD>\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
				echo "<input type=\"password\" value=\"\" name=\"users_edit_password\" size=\"29\">&nbsp;</TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;RE-ENTER NEW PASSWORD</TD>\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
				echo "<input type=\"password\" value=\"\" name=\"users_edit_password_again\" size=\"29\">&nbsp;</TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;</TD>\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\">&nbsp;</TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTE</TD>\n";
				echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
				echo "<input type=\"text\" value=\"".$row['note']."\" name=\"users_edit_note\" size=\"29\">&nbsp;</TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
				echo "<input type=\"hidden\" value=\"".$row['username']."\" name=\"users_edit_old_username\">\n";
				echo "<input type=\"hidden\" value=\"".$row['password']."\" name=\"users_edit_old_password\">\n";
				echo "<input type=\"hidden\" name=\"users_change\">";
				echo "<input type=\"hidden\" name=\"users_edit_magic\" value=\"".generate_magic()."\">";
				echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
				echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
				
				if ($remote_module == "pptp")
				{
					echo "<a href=\"".$PHP_SELF."?module=pptp\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
				}
				elseif ($remote_module == 0)
				{
					echo "<a href=\"".$PHP_SELF."?module=users\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
				}
				
				echo "</TD>\n";
				echo "</TR>\n";
				
				echo "					</tbody>\n";
				echo "					</table>\n";
				echo "				</td>\n";
				echo "			</tr>\n";
				echo "		</table>\n";
				echo "		</form>\n";
				echo "	<br><br><br>\n";
				echo "</form>";
			}
			elseif ($status == 'error')
			{
				echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
				echo "			<tr valign=\"top\">\n";
				echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo " 	  				".$section2." | (".$id.") &nbsp;</td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
				echo "			</tr>\n";
				echo "		</table>\n";
				
				echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=edit&sid=".$id."&remote_module=".$remote_module."\" name=\"submitform\">";
				echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
				echo "			<tr>\n";
				echo "				<td height=\"20px\" colspan=\"2\">\n";
				echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
				echo "			</tr>\n";
				echo "			<tr>\n";
				echo "				<td align=\"left\" width=\"40px\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\">\n";
				
				echo "<TABLE cellSpacing=1 cellPadding=0 width=\"425\" border=0>\n";
				echo "<TBODY>\n";
				echo "<TR bgcolor=\"#565656\">\n";
				echo "<TD vAlign=bottom align=left width=\"175\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"175\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"200\" height=\"22\"><FONT color=#ffffff>&nbsp;".$id."</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"200\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"50\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"50\" border=0></TD>\n";
				echo "</TR>\n";
				
				if ($GLOBALS['users_error0'])
				{
					echo "<TR bgColor=\"#d5d5d5\">\n";
					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;OLD PASSWORD</TD>\n";
					echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
					echo "<input type=\"password\" value=\"".$GLOBALS['users_edit_oldpassword']."\" name=\"users_edit_oldpassword\" size=\"29\">&nbsp;</TD>\n";
					echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
					echo "</TR>\n";
				}
				else
				{
					echo "<TR bgColor=\"#d5d5d5\">\n";
					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;OLD PASSWORD</TD>\n";
					echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
					echo "<input type=\"password\" value=\"".$GLOBALS['users_edit_oldpassword']."\" name=\"users_edit_oldpassword\" size=\"29\" readonly>&nbsp;</TD>\n";
					echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
					echo "</TR>\n";
				}
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;</TD>\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\">&nbsp;</TD>\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\">&nbsp;</TD>\n";
				echo "</TR>\n";				
				
				if ($GLOBALS['users_error1'])
				{
					echo "<TR bgColor=\"#d5d5d5\">\n";
					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;USERNAME</TD>\n";
					echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
					echo "<input type=\"text\" value=\"".$GLOBALS['users_edit_username']."\" name=\"users_edit_username\" size=\"29\">&nbsp;</TD>\n";
					echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
					echo "</TR>\n";
				}
				else
				{
					echo "<TR bgColor=\"#d5d5d5\">\n";
					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;USERNAME</TD>\n";
					echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
					echo "<input type=\"text\" value=\"".$GLOBALS['users_edit_username']."\" name=\"users_edit_username\" size=\"29\" readonly>&nbsp;</TD>\n";
					echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
					echo "</TR>\n";
				}
				
				if ($GLOBALS['users_error2'])
				{
					echo "<TR bgColor=\"#d5d5d5\">\n";
					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NEW PASSWORD</TD>\n";
					echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
					echo "<input type=\"password\" value=\"".$GLOBALS['users_edit_password']."\" name=\"users_edit_password\" size=\"29\">&nbsp;</TD>\n";
					echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
					echo "</TR>\n";
				}
				else
				{
					echo "<TR bgColor=\"#d5d5d5\">\n";
					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NEW PASSWORD</TD>\n";
					echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
					echo "<input type=\"password\" value=\"".$GLOBALS['users_edit_password']."\" name=\"users_edit_password\" size=\"29\">&nbsp;</TD>\n";
					echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
					echo "</TR>\n";
				}
				
				if ($GLOBALS['users_error3'])
				{
					echo "<TR bgColor=\"#d5d5d5\">\n";
					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;E-ENTER NEW PASSWORD</TD>\n";
					echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
					echo "<input type=\"password\" value=\"".$GLOBALS['users_edit_password_again']."\" name=\"users_edit_password_again\" size=\"29\">&nbsp;</TD>\n";
					echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
					echo "</TR>\n";
				}
				else
				{
					echo "<TR bgColor=\"#d5d5d5\">\n";
					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;E-ENTER NEW PASSWORD</TD>\n";
					echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
					echo "<input type=\"password\" value=\"".$GLOBALS['users_edit_password']."\" name=\"users_edit_password_again\" size=\"29\">&nbsp;</TD>\n";
					echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
					echo "</TR>\n";
				}
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;</TD>\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\">&nbsp;</TD>\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\">&nbsp;</TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTE</TD>\n";
				echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
				echo "<input type=\"text\" value=\"".$GLOBALS['users_edit_note']."\" name=\"users_edit_note\" size=\"29\" readonly>&nbsp;</TD>\n";
				echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"3\">\n";
				echo "<input type=\"hidden\" value=\"".$row['username']."\" name=\"users_edit_old_username\">\n";
				echo "<input type=\"hidden\" value=\"".$row['password']."\" name=\"users_edit_old_password\">\n";
				echo "<input type=\"hidden\" name=\"users_change\">";
				echo "<input type=\"hidden\" name=\"users_edit_magic\" value=\"".generate_magic()."\">";
				echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
				echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
				
				if ($remote_module == "pptp")
				{
					echo "<a href=\"".$PHP_SELF."?module=pptp\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
				}
				elseif ($remote_module == 0)
				{
					echo "<a href=\"".$PHP_SELF."?module=users\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
				}
				
				echo "</TD>\n";
				echo "</TR>\n";
				
				echo "					</tbody>\n";
				echo "					</table>\n";
				echo "				</td>\n";
				echo "			</tr>\n";
				echo "		</table>\n";
				echo "		</form>\n";
				echo "	<br><br><br>\n";
				echo "</form>";
			}
			else
			{
				if ($GLOBALS['users_edit_magic'] == $GLOBALS['users_edit_lastmagic'])
				{
					show_users($section,$section2,$tablename);
				}
				else
				{
					$GLOBALS['users_edit_lastmagic'] = $GLOBALS['users_edit_magic'];
					$GLOBALS['users_error0'] = 0;
					$GLOBALS['users_error1'] = 0;
					$GLOBALS['users_error2'] = 0;
					$GLOBALS['users_error3'] = 0;
					
					$result = mysql_query("select * from ".$tablename." where(id='".$id."')");
					$row = mysql_fetch_array($result);
					
					if (($GLOBALS['users_edit_oldpassword'] != $row['password']) or (empty($GLOBALS['users_edit_oldpassword']) == true))
					{
						$GLOBALS['users_error0'] = 1;
					}
					
					if (empty($GLOBALS['users_edit_username']) == true)
					{
						$GLOBALS['users_error1'] = 1;	
					}
					else
					{
						if ($GLOBALS['users_edit_old_username'] != $GLOBALS['users_edit_username'])
						{
							$result2 = mysql_query("select * from ".$tablename);
							$number = mysql_num_rows($result2);
							
							for ($i=0;$i<=$number-1;$i++)
							{
								$row2 = mysql_fetch_array($result2);
								
								if ($row2['username'] == $GLOBALS['users_edit_username'])
								{
									$GLOBALS['users_error1'] = 1;
								}
							}
						}
					}
					
					if ($GLOBALS['users_edit_password'] != $GLOBALS['users_edit_password_again'])
					{
						$GLOBALS['users_error2'] = 1;
						$GLOBALS['users_error3'] = 1;
					}
					
					if (($GLOBALS['users_error0'] == 0) and ($GLOBALS['users_error1'] == 0) and ($GLOBALS['users_error2'] == 0) and ($GLOBALS['users_error3'] == 0))
					{
						if ((empty($GLOBALS['users_edit_password']) == false) and (empty($GLOBALS['users_edit_password_again']) == false))
						{
							$result = mysql_query("update ".$tablename." set password='".$GLOBALS['users_edit_password_again']."' where(id='".$id."')");
							$result = mysql_query("update ".$tablename." set note='".$GLOBALS['users_edit_note']."' where(id='".$id."')");
							$result = mysql_query("update ".$tablename." set username='".$GLOBALS['users_edit_username']."' where(id='".$id."')");
							$result = mysql_query("update ".$tablename." set magic='".generate_magic()."' where(id='".$id."')");
						}
						else
						{
							$result = mysql_query("update ".$tablename." set username='".$GLOBALS['users_edit_username']."' where(id='".$id."')");
							$result = mysql_query("update ".$tablename." set note='".$GLOBALS['users_edit_note']."' where(id='".$id."')");
							$result = mysql_query("update ".$tablename." set magic='".generate_magic()."' where(id='".$id."')");
						}
						
						if ($remote_module == "pptp")
						{
							$path = new path;
						    include($path->path_modules_functions."/vpn/pptp/pptplib.php");							
							
							show_serverinfo("pptp", "STRATEGY | <B>VPN - PPTP</B>", "pptp_options");
						}
						elseif ($remote_module == 0)
						{
							show_users($section,$section2,$tablename);
						}
					}
					else
					{
						edit_users($section, $section2, $tablename, $id, "error", $remote_module);
					}
				}
			}
		}
		
		// ----------------------------
		// | Objects - Users (Add)    |
		// ----------------------------
		// | Last Change : 07.03.2002 |
		// ----------------------------
		// | Status : Enabled         |
		// ----------------------------
		function add_users($section, $section2, $tablename, $status)
		{
			# Add Objects #
			if (!isset($status))
			{
				echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
				echo "			<tr valign=\"top\">\n";
				echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					".$section2." | <i>ADD ENTRY</i> &nbsp;</td>\n";
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
				
				echo "<TABLE cellSpacing=1 cellPadding=0 width=\"350\" border=0>\n";
				echo "<TBODY>\n";
				echo "<TR bgcolor=\"#565656\">\n";
				echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"200\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"200\" border=0></TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;USERNAME</TD>\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
				echo "<input type=\"text\" value=\"\" name=\"users_username\" size=\"29\">&nbsp;</TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PASSWORD</TD>\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
				echo "<input type=\"password\" value=\"\" name=\"users_password\" size=\"29\">&nbsp;</TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PASSWORD (AGAIN)</TD>\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
				echo "<input type=\"password\" value=\"\" name=\"users_password_again\" size=\"29\">&nbsp;</TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTE</TD>\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
				echo "<input type=\"text\" value=\"\" name=\"users_note\" size=\"29\">&nbsp;</TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
				echo "<input type=\"hidden\" name=\"users_submit\">";
				echo "<input type=\"hidden\" name=\"users_magic\" value=\"".generate_magic()."\">";
				echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/add.gif\" border=\"0\"></a>&nbsp;\n";
				echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
				echo "<a href=\"".$PHP_SELF."?module=users\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
				echo "</TD>\n";
				echo "</TR>\n";
				
				echo "					</tbody>\n";
				echo "					</table>\n";
				echo "				</td>\n";
				echo "			</tr>\n";
				echo "		</table>\n";
				echo "		</form>\n";
				echo "	<br><br><br>\n";
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
				
				echo "<TABLE cellSpacing=1 cellPadding=0 width=\"400\" border=0>\n";
				echo "<TBODY>\n";
				echo "<TR bgcolor=\"#565656\">\n";
				echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"200\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"200\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"50\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"50\" border=0></TD>\n";
				echo "</TR>\n";
				
				if ($GLOBALS['users_error0'] != 0)
				{
					echo "<TR bgColor=\"#d5d5d5\">\n";
					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;USERNAME</TD>\n";
					echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
					echo "<input type=\"text\" value=\"".$GLOBALS['users_username']."\" name=\"users_username\" size=\"29\">&nbsp;</TD>\n";
					echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
					echo "</TR>\n";
				}
				else
				{
					echo "<TR bgColor=\"#d5d5d5\">\n";
					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;USERNAME</TD>\n";
					echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
					echo "<input type=\"text\" value=\"".$GLOBALS['users_username']."\" name=\"users_username\" size=\"29\">&nbsp;</TD>\n";
					echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
					echo "</TR>\n";
				}
				
				if ($GLOBALS['users_error1'] != 0)
				{
					echo "<TR bgColor=\"#d5d5d5\">\n";
					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PASSWORD</TD>\n";
					echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
					echo "<input type=\"password\" value=\"".$GLOBALS['users_password']."\" name=\"users_password\" size=\"29\">&nbsp;</TD>\n";
					echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
					echo "</TR>\n";
				}
				else
				{
					echo "<TR bgColor=\"#d5d5d5\">\n";
					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PASSWORD</TD>\n";
					echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
					echo "<input type=\"password\" value=\"".$GLOBALS['users_password']."\" name=\"users_password\" size=\"29\">&nbsp;</TD>\n";
					echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
					echo "</TR>\n";
				}
				
				if ($GLOBALS['users_error2'] != 0)
				{
					echo "<TR bgColor=\"#d5d5d5\">\n";
					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PASSWORD (AGAIN)</TD>\n";
					echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
					echo "<input type=\"password\" value=\"".$GLOBALS['users_password_again']."\" name=\"users_password_again\" size=\"29\">&nbsp;</TD>\n";
					echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
					echo "</TR>\n";
				}
				else
				{
					echo "<TR bgColor=\"#d5d5d5\">\n";
					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PASSWORD (AGAIN)</TD>\n";
					echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
					echo "<input type=\"password\" value=\"".$GLOBALS['users_password_again']."\" name=\"users_password_again\" size=\"29\">&nbsp;</TD>\n";
					echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
					echo "</TR>\n";
				}
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTE</TD>\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
				echo "<input type=\"text\" value=\"".$GLOBALS['users_note']."\" name=\"users_note\" size=\"29\">&nbsp;</TD>\n";
				echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
				echo "<input type=\"hidden\" name=\"users_submit\">";
				echo "<input type=\"hidden\" name=\"users_magic\" value=\"".generate_magic()."\">";
				echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/add.gif\" border=\"0\"></a>&nbsp;\n";
				echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
				echo "<a href=\"".$PHP_SELF."?module=users\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
				echo "</TD>\n";
				echo "</TR>\n";
			}
			else
			{
				if ($GLOBALS['users_magic'] == $GLOBALS['users_lastmagic'])
				{
					show_users($section,$section2,$tablename);
				}
				else
				{
					$GLOBALS['users_lastmagic'] = $GLOBALS['users_magic'];
					$GLOBALS['users_error0'] = 0;
					$GLOBALS['users_error1'] = 0;
					$GLOBALS['users_error2'] = 0;
					
					if (empty($GLOBALS['users_username']) == true)
					{
						$GLOBALS['users_error0'] = 1;
					}
					else
					{
						$result = mysql_query("select * from ".$tablename);
						$number = mysql_num_rows($result);
						
						for ($i=0;$i<=$number-1;$i++)
						{
							$row = mysql_fetch_array($result);
							
							if ($row['username'] == $GLOBALS['users_username'])
								$GLOBALS['users_error0'] = 1;
						}
					}
					
					if (empty($GLOBALS['users_password']) == true)
						$GLOBALS['users_error1'] = 1;
					
					if (empty($GLOBALS['users_password_again']) == true)
						$GLOBALS['users_error2'] = 1;
					
					if (isset($GLOBALS['users_password']) and isset($GLOBALS['users_password_again']))
					{
						if ($GLOBALS['users_password'] != $GLOBALS['users_password_again'])
						{
							$GLOBALS['users_error2'] = 1;
						}
					}
					
					if (($GLOBALS['users_error0'] != 0) or ($GLOBALS['users_error1'] != 0) or ($GLOBALS['users_error2'] != 0))
					{
						add_users($section, $section2, $tablename, "error");
					}
					else
					{
						$data = "'','".$GLOBALS['users_username']."','".$GLOBALS['users_note']."','0','0','".$GLOBALS['users_password']."',''";
						$fields = "id,username,note,isroot,issticky,password,magic";
						$query = mysql_query("insert into ".$tablename." (".$fields.") values(".$data.")");
						
						show_users($section,$section2,$tablename);
					}
				}
			}
		}
?>
