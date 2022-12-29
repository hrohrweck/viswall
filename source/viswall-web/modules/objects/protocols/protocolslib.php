<?php
		///////////////////////////////////////////////////////
		//                 --> vis|wall <--                  //
		///////////////////////////////////////////////////////
		//						     //
		// MainGroup   : Interface                           //
		//						     //
		// Name			: Module - Protocols         //
		// Date			: 24.03.2002		     //
		// Comment  	: Object Interfaces		     //
		//						     //
		///////////////////////////////////////////////////////
        
		// --------------------------------------
		// | Edit Protocols Entries                |
		// --------------------------------------
		// | Last Change : 25.03.2003            |
		// --------------------------------------
		// | Status : Enabled                    |
		// --------------------------------------
		function edit_objects_protocols($type, $section, $section2, $tablename, $id, $status)
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
				echo " 	  				".$section2." | <i>".$row['pr_keyword']."</i> (".$row['pr_decimal'].") &nbsp;</td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
				echo "			</tr>\n";
				echo "		</table>\n";
				
				echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=edit&pid=".$_GET['pid']."\" name=\"submitform\">";
				echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
				echo "			<tr>\n";
				echo "				<td height=\"20px\" colspan=\"2\">\n";
				echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
				echo "			</tr>\n";
				echo "			<tr>\n";
				echo "				<td align=\"left\" width=\"40px\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\">\n";
				
				# Edit-Type (List, Range, Group)
				switch ($row['pr_type'])
				{
					// Edit Type System
					case 0:
					{
						# Protocols (Edit)
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"285\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"85\" height=\"22\"><FONT color=#ffffff>&nbsp;NAME</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"85\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"270\" height=\"22\"><FONT color=#ffffff>&nbsp;".$row['pr_keyword']."</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"270\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$row['pr_keyword']."\" name=\"keyword\" size=\"40\" maxlength=\"30\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
                                                echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;DESCRIPTION</TD>\n";
						echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
						echo "<input type=text value=\"".$row['pr_description']."\" name=\"description\" size=\"40\" maxlength=\"512\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						//echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\"\n";
						echo "<input type=\"hidden\" name=\"po_change\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$PHP_SELF."?module=protocols\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					// Edit Type User
					case 1:
                                        {
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"425\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"155\" height=\"22\"><FONT color=#ffffff>&nbsp;NAME</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"155\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"270\" height=\"22\"><FONT color=#ffffff>&nbsp;".$row['pr_keyword']."</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"270\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$row['pr_keyword']."\" name=\"keyword\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IANA PROTOCOL NUMBER</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$row['pr_decimal']."\" name=\"decimal\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;DESCRIPTION</TD>\n";
						echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
						echo "<input type=text value=\"".$row['pr_description']."\" name=\"description\" size=\"40\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						//echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\" size=\"40\">\n";
						echo "<input type=\"hidden\" name=\"po_change\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$PHP_SELF."?module=protocols\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
                                input_error($section, $section2, $status, $id, $row['pr_type']);
			}
			else
			{
				switch ($row['pr_type'])
				{
					case 0: // Case System
					{
						if ($GLOBALS['magic'] == $GLOBALS['lastmagic'])
						{
							show_objects_protocols($type, $section, $section2, $tablename);
						}
						else
						{
							$GLOBALS['lastmagic'] = $GLOBALS['magic'];
							
							$field_K = "ER"; // Status Flag for keyword
							$field_N = "OK"; // Status Flag for Protocol Number --> Type System: No need to set Protocol number
							$field_D = "OK"; // Description is optional
							
							if (!empty($_POST['keyword'])) $field_K = "OK";
							
							if (($field_K == 'OK') and ($field_D == 'OK') and ($field_N == 'OK'))
							{
								$result = mysql_query("update ".$tablename." set pr_keyword='".$_POST['keyword']."' where(id='".$_GET['pid']."')") or die (mysql_error());
								$result = mysql_query("update ".$tablename." set pr_description='".$_POST['description']."' where(id='".$_GET['pid']."')") or die (mysql_error());

								show_objects_protocols($type, $section, $section2, $tablename);
							}
							else
							{
								edit_objects_protocols($type, $section, $section2, $tablename, $_GET['pid'], "error|".$field_K."_".$field_N."_".$field_D);
							}
						}
						break;
					}
					case 1: //Case User
					{
						if ($GLOBALS['magic'] == $GLOBALS['lastmagic'])
						{
							show_objects_protocols(0, $section, $section2, $tablename);
						}
						else
						{
							$GLOBALS['lastmagic'] = $GLOBALS['magic'];
							
							$field_K = "ER"; // Status Flag for keyword
							$field_N = "ER"; // Status Flag for Protocol Number
							$field_D = "OK"; // Description is optional
							
							if (!empty($_POST['keyword'])) $field_K = "OK";
							if ((!empty($_POST['decimal'])) and (is_numeric($_POST['decimal'])))
                                                        {
                                                                if (check_duplicate_pr($tablename, $_POST['decimal'],$_GET['pid'])==0)
                                                                {
                                                                        $field_N = "OK"; // Protocol Number is not empty, numeric and does not already exist
                                                                } else {
                                                                        errorcode(3,0);
                                                                }
                                                        }
							if (($field_K == 'OK') and ($field_D == 'OK') and ($field_N == 'OK'))
							{
								$result = mysql_query("update ".$tablename." set pr_keyword='".$_POST['keyword']."' where(id='".$_GET['pid']."')") or die (mysql_error());
								$result = mysql_query("update ".$tablename." set pr_decimal='".$_POST['decimal']."' where(id='".$_GET['pid']."')") or die (mysql_error());
                                                                $result = mysql_query("update ".$tablename." set pr_description='".$_POST['description']."' where(id='".$_GET['pid']."')") or die (mysql_error());
								show_objects_protocols(0, $section, $section2, $tablename);
							}
							else
							{
								edit_objects_protocols($type, $section, $section2, $tablename, $_GET['pid'], "error|".$field_K."_".$field_N."_".$field_D);
							}
						}
						break;
					}
					default:
                                           errorcode(7,0);
					   break;
				}
			}
		}
		// -----------------------------------
		// | Default Style - Add Services  |
		// -----------------------------------
		// | Last Change : 27.11.2001     |
		// -----------------------------------
		// | Status : Enabled                 |
		// -----------------------------------
		function add_objects_protocols($type, $section, $section2, $tablename, $status)
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
				
				echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=add&type=".$type."\" name=\"submitform\">";
				echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
				echo "			<tr>\n";
				echo "				<td height=\"20px\" colspan=\"2\">\n";
				echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
				echo "			</tr>\n";
				echo "			<tr>\n";
				echo "				<td align=\"left\" width=\"40px\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\">\n";
				
				# Add-Type (User-defined Protocol) #
				switch ($type)
				{
					# Add Type Selection #
					case 0:
					{
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"425\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"155\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"155\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"270\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"270\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" name=\"keyword\" size=\"40\" maxlength=\"30\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IANA PROTOCOL NUMBER</TD>\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" name=\"decimal\" size=\"40\" maxlength=\"5\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;DESCRIPTION</TD>\n";
						echo "<TD vAlign=middle	 align=right width=\"\" height=\"22\">\n";
						echo "<input type=text name=\"description\" size=\"40\" maxlength=\"512\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\">\n";
						echo "<input type=\"hidden\" name=\"po_submit\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/add.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$PHP_SELF."?module=protocols\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
				echo "<TABLE cellSpacing=1 cellPadding=0 width=\"425\" border=0>\n";
				echo "<TBODY>\n";
				echo "<TR bgcolor=\"#565656\">\n";
				echo "<TD vAlign=bottom align=left width=\"155\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"155\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"270\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"270\" border=0></TD>\n";
				echo "</TR>\n";

                                        if (substr($status,6,2) == 'OK') // valid Name
					{
						        echo "<TR bgColor=\"#d5d5d5\">\n";
						        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
						        echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						        echo "<input type=\"text\" value=\"".$_POST['keyword']."\" name=\"keyword\" size=\"40\">&nbsp;</TD>\n";
						        echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
						        echo "</TR>\n";
					}
					elseif (substr($status,6,2) == 'ER') // invalid Name
					{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['keyword']."\" name=\"keyword\" size=\"40\" maxlength=\"30\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
					}
					if (substr($status,9,2) == 'OK') // valid Protocol Number
					{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IANA PROTOCOL NUMBER&nbsp;</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['decimal']."\" name=\"decimal\" size=\"40\" maxlength=\"5\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
					}
					elseif (substr($status,9,2) == 'ER') // Invalid Protocol Number
					{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IANA PROTOCOL NUMBER&nbsp;</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['decimal']."\" name=\"decimal\" size=\"40\" maxlength=\"5\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
					}
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;DESCRIPTION</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['description']."\" name=\"description\" size=\"40\" maxlength=\"512\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
					
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						//echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\" size=\"40\">\n";
						echo "<input type=\"hidden\" name=\"po_submit\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/add.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$PHP_SELF."?module=protocols\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
			else
			{
				switch ($type)
				{
					case 0:
					{
						if ($GLOBALS['magic'] == $GLOBALS['lastmagic'])
						{
							show_objects_protocols($type, $section, $section2, $tablename);
						}
						else
						{
							$GLOBALS['lastmagic'] = $GLOBALS['magic'];
							$field_K = "ER";
							$field_N = "ER";
							$field_D = "OK"; // Description is optional
							
							if (!empty($_POST['keyword'])) $field_K = "OK";
							if ((!empty($_POST['decimal'])) and (is_numeric($_POST['decimal'])))
                                                        {
                                                                if (check_duplicate_pr($tablename, $_POST['decimal'],"")==0)
                                                                {
                                                                        $field_N = "OK"; // Protocol Number is not empty, numeric and does not already exist
                                                                }
                                                        }
							if (($field_K == 'OK') and ($field_N == 'OK') and ($field_D == 'OK'))
							{
								$data = "'','".$_POST['keyword']."','".$_POST['decimal']."','".$_POST['description']."',1";
								$fields = "id,pr_keyword,pr_decimal,pr_description,pr_type";
								$query = mysql_query("insert into ".$tablename." (".$fields.") values(".$data.")") or die(mysql_error());
								
								show_objects_protocols(0, $section, $section2, $tablename);
							}
							else
							{
								add_objects_protocols($type, $section, $section2, $tablename, "error|".$field_K."_".$field_N."_".$field_D);
							}
						}
						break;
					}
					default:
					{
					   errorcode(7,0);
					   break;
					}
				}
			}
		}
		// -------------------------------------
		// | Default Style - Show Services      |
		// -------------------------------------
		// | Last Change : 25.03.2003           |
		// -------------------------------------
		// | Status : Enabled                   |
		// -------------------------------------
		function show_objects_protocols($type, $section, $section2, $tablename)
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
			
			switch ($type)
			{
				case 0:
				{
					// Generate Table-Header
					echo "<TABLE cellSpacing=1 cellPadding=0 width=553 border=0>\n";
					echo "<TBODY>\n";
					echo "<TR class=tablehead bgColor=#565656>\n";
					echo "<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;NAME</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"55\" height=\"22\"><FONT color=#ffffff>&nbsp;NUMBER</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"55\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"318\" height=\"22\"><FONT color=#ffffff>&nbsp;PROTOCOL DESCRIPTION</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"318\" border=0></TD>\n";
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
						
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['pr_keyword']."</TD>\n";
						echo "<TD vAlign=middle align=middle width=\"\" height=\"22\">&nbsp;".$row['pr_decimal']."</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['pr_description']."</TD>\n";
						echo "<TD vAlign=middle align=middle width=\"\" height=\"22\">\n";
						$type = convert_type($row['pr_type']);
						echo "&nbsp;<a href=\"".$PHP_SELF."?module=protocols&action=edit&pid=".$row['id']."\"><IMG SRC=\"./images/icons/edit_gr.gif\" WIDTH=\"22\" HEIGHT=\"16\" BORDER=0 ALT=\"edit\"></a>\n";
						if ($row['pr_type']==1)
                        {
                            echo "</a>&nbsp;&nbsp;<a href=\"".$PHP_SELF."?module=protocols&action=delete&pid=".$row['id']."&sd_override=no\"><IMG SRC=\"./images/icons/delete.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=0 ALT=\"delete\"></a>&nbsp;</TD>\n";
                        }
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
					echo "						<TD vAlign=bottom align=middle height=20>&nbsp;<a href=\"".$PHP_SELF."?module=protocols&action=add\"><IMG SRC=\"./images/add_entry_gr.gif\" WIDTH=\"50\" HEIGHT=\"16\" BORDER=0 ALT=\"add entry\"></a>&nbsp;</TD>\n";
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
		      mysql_free_result($result);
        }			

		// --------------------------------
		// | Protocol Status Analyzer   |
		// --------------------------------
		// | Last Change : 30.11.2001 |
		// --------------------------------
		// | Status : Disabled             |
		// --------------------------------				
		function protalizer($section, $section2, $hometable, $id, $protocoltable, $method)
		{
			$sql_db_local = new sql_db_local;
			
			if ((!isset($method)) or ($method == 'show'))
			{
				$result = mysql_query("select * from ".$protocoltable." order by pr_decimal");
				$numbers = mysql_num_rows($result);
				
				echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
	            echo "			<tr valign=\"top\">\n";
	            echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
	            echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo " 	  				".$section2." (".$numbers.") &nbsp;</td>\n";
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
				
				echo "<TABLE cellSpacing=1 cellPadding=0 width=525 border=0>\n";
				echo "<TBODY>\n";
				echo "<TR class=tablehead bgColor=#565656>\n";
				echo "<TD vAlign=bottom align=left width=\"175px\" height=\"22\"><FONT color=#ffffff>&nbsp;AVAILABLE PROTOCOLS</FONT>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"175px\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"175px\" height=\"22\"><FONT color=#ffffff>&nbsp;ADMINISTRATE</FONT>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"175px\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"175px\" height=\"22\"><FONT color=#ffffff>&nbsp;ACTIVE PROTOCOLS</FONT>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"175px\" border=0></TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"150px\" height=\"\">";
				echo "<form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=show&sid=".$id."&method=add\">";
				echo "<select name=\"c_list[]\" size=\"10\" multiple>";
				echo "<option value=\"empty\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</option>";
				for ($i=1; $i<=$numbers; $i++)
				{
					$row = mysql_fetch_array($result);
					$resulthome = mysql_query("select * from ".$hometable." where(sid=\"".$id."\" and pid=\"".$row['pr_decimal']."\")");
					$rowhome = mysql_fetch_array($resulthome);
					
					if (($rowhome['sid'] == $id) and ($rowhome['pid'] == $row['pr_decimal']))
					{
						//
					}
					else
					{
						echo "<option value=\"".$row['pr_decimal']."\">".$row['pr_keyword']."</option>";
					}
				}
				
				echo "</select>";
				echo "</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"\">";
				echo "<input type=\"submit\" name=\"add\" value=\">>\"><input type=\"hidden\" name=\"formid\" value=\"".$id."\">";
				echo "</form>";
				echo "<form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=show&sid=".$id."&method=remove\">";
				echo "<input type=\"submit\" name=\"remove\" value=\"<<\"><input type=\"hidden\" name=\"formid\" value=\"".$id."\">";
				echo "<br><br><a href=\"".$PHP_SELF."?module=services\"><img src=\"./images/back.gif\" border=\"0\"></a>\n";
				echo "</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"\">";
				
				$result = mysql_query("select * from ".$protocoltable." order by pr_decimal");
				$numbers = mysql_num_rows($result);
				
				
				echo "<select name=\"u_list[]\" size=\"10\" multiple>";
				echo "<option value=\"empty\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</option>";
				for ($i=1; $i<=$numbers; $i++)
				{
					$row = mysql_fetch_array($result);
					$resulthome = mysql_query("select * from ".$hometable." where(sid=\"".$id."\" and pid=\"".$row['pr_decimal']."\")");
					$rowhome = mysql_fetch_array($resulthome);
					
					if (($rowhome['sid'] == $id) and ($rowhome['pid'] == $row['pr_decimal']))
					{
						echo "<option value=\"".$row['pr_decimal']."\">".$row['pr_keyword']."</option>";
					}
					else
					{
						//
					}
				}
				
				echo "</select>";
				echo "</td></tr>";
				echo "					</tbody>\n";
				echo "					</table>\n";
				echo "				</td>\n";
				echo "			</tr>\n";
				echo "		</table>\n";
				echo "		</form>\n";
				echo "	<br><br><br>\n";
			}
			elseif (($method == 'add'))
			{
				$haystack = $GLOBALS['c_list'];
				
				if (!empty($haystack))
				{
					$result = mysql_query("select * from ".$protocoltable." order by pr_decimal");
					$numbers = mysql_num_rows($result);
					
					for ($i=1; $i<=$numbers; $i++)
					{
						$row = mysql_fetch_array($result);
						
						for ($j=0; $j<=sizeof($haystack); $j++)
						{
							if ($row['pr_decimal'] == $haystack[$j])
							{
								$result2 = mysql_query("insert into ".$hometable." (id,pid,sid) values('','".$row['pr_decimal']."','".$GLOBALS['formid']."')");
							}
						}
					}
					
					protalizer("services", "OBJECTS | <B>SERVICES</B>", $sql_db_local->sql_db_table_po_layers, $GLOBALS['formid'], $sql_db_local->sql_db_table_po_protocols, "show");
				}
				else
				{
					protalizer("services", "OBJECTS | <B>SERVICES</B>", $sql_db_local->sql_db_table_po_layers, $GLOBALS['formid'], $sql_db_local->sql_db_table_po_protocols, "show");
				}
			}
			elseif (($method == 'remove'))
			{
				$haystack = $GLOBALS['u_list'];
				
				if (!empty($haystack))
				{
					for ($j=0; $j<=sizeof($haystack); $j++)
					{
						$result2 = mysql_query("delete from ".$hometable." where(pid=".$haystack[$j]." and sid=".$GLOBALS['formid'].")");
					}
					
					protalizer("services", "OBJECTS | <B>SERVICES</B>", $sql_db_local->sql_db_table_po_layers, $GLOBALS['formid'], $sql_db_local->sql_db_table_po_protocols, "show");
				}
				else
				{
					protalizer("services", "OBJECTS | <B>SERVICES</B>", $sql_db_local->sql_db_table_po_layers, $GLOBALS['formid'], $sql_db_local->sql_db_table_po_protocols, "show");
				}
			}
			else
			{
				protalizer("services", "OBJECTS | <B>SERVICES</B>", $sql_db_local->sql_db_table_po_layers, $GLOBALS['formid'], $sql_db_local->sql_db_table_po_protocols, "show");
			}
		}
		// --------------------------------
		// | Input Error                   |
		// --------------------------------
		// | Last Change : 26.03.2003      |
		// --------------------------------
		// | Status : Enabled              |
		// --------------------------------	
                function input_error($section, $section2, $status, $id, $type)
                {
				echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
				echo "			<tr valign=\"top\">\n";
				echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo " 	  				".$section2." | <i>".$_POST['keyword']."</i> (".$id.") &nbsp;</td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
				echo "			</tr>\n";
				echo "		</table>\n";
				
				echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=edit&type=".$type."\" name=\"submitform\">";
				echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
				echo "			<tr>\n";
				echo "				<td height=\"20px\" colspan=\"2\">\n";
				echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
				echo "			</tr>\n";
				echo "			<tr>\n";
				echo "				<td align=\"left\" width=\"40px\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\">\n";
				
	
				switch ($type)
				{
					case 0: // Case System
					{
					        echo "<TABLE cellSpacing=1 cellPadding=0 width=\"285\" border=0>\n";
				                echo "<TBODY>\n";
				                echo "<TR bgcolor=\"#565656\">\n";
				                echo "<TD vAlign=bottom align=left width=\"85\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD</font>\n";
				                echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"85\" border=0></TD>\n";
				                echo "<TD vAlign=bottom align=left width=\"270\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
				                echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"270\" border=0></TD>\n";
				                echo "<TD vAlign=bottom align=left width=\"50\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
				                echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"50\" border=0></TD>\n";
				                echo "</TR>\n";
						if (substr($status,6,2) == 'OK')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['keyword']."\" name=\"name\" size=\"40\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,6,2) == 'ER')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['keyword']."\" name=\"keyword\" size=\"40\" maxlength=\"30\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
                                                // Skipping Protocol Number (system type does not require it)
						if (substr($status,12,2) == 'OK')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;DESCRIPTION</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['description']."\" name=\"description\" size=\"40\" maxlength=\"512\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,12,2) == 'ER')
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;DESCRIPTION</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['description']."\" name=\"description\" size=\"40\" maxlength=\"512\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\">\n";
						echo "<input type=\"hidden\" name=\"po_change\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$PHP_SELF."?module=protocols\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
					case 1: // case user
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"425\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"155\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"155\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"270\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"270\" border=0></TD>\n";
						echo "</TR>\n";
                                                if (substr($status,6,2) == 'OK') // valid Name
						{
						        echo "<TR bgColor=\"#d5d5d5\">\n";
						        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
						        echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
						        echo "<input type=\"text\" value=\"".$_POST['keyword']."\" name=\"keyword\" size=\"40\">&nbsp;</TD>\n";
						        echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
						        echo "</TR>\n";
						}
						elseif (substr($status,6,2) == 'ER') // invalid Name
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['keyword']."\" name=\"keyword\" size=\"40\" maxlength=\"30\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						if (substr($status,9,2) == 'OK') // valid Protocol Number
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IANA PROTOCOL NUMBER&nbsp;</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['decimal']."\" name=\"decimal\" size=\"40\" maxlength=\"5\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,9,2) == 'ER') // Invalid Protocol Number
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IANA PROTOCOL NUMBER&nbsp;</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['decimal']."\" name=\"decimal\" size=\"40\" maxlength=\"5\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;DESCRIPTION</TD>\n";
							echo "<TD vAlign=middle align=right width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['description']."\" name=\"description\" size=\"40\" maxlength=\"512\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
												
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\" size=\"40\">\n";
						echo "<input type=\"hidden\" name=\"po_change\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$PHP_SELF."?module=protocols\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
		      return;
                }

		// --------------------------------
		// | Check for duplicate IANA Nrs. |
		// --------------------------------
		// | Last Change : 26.03.2003      |
		// --------------------------------
		// | Status : Enabled              |
		// --------------------------------
		function check_duplicate_pr($tablename, $protnr, $id)
		{
		        $result = mysql_query("select id from ".$tablename." where pr_decimal='".$protnr."'") or die (mysql_error());
		        $number = mysql_num_rows($result);
		        $row = mysql_fetch_array($result);
		        if ($row['id']==$id) $number = 0; // Accept if current record seems to get updated
		        mysql_free_result($result);
                        return $number;
		}
		
                // --------------------------------
		// | convert types system=0 user=1 |
		// --------------------------------
		// | Last Change : 26.03.2003      |
		// --------------------------------
		// | Status : Enabled              |
		// --------------------------------
		function convert_type($type)
		{
		        if ($type=="system")
                        {
                                return 0;
                        }
                        elseif ($type=="user")
                        {
                                return 1;
                        }
                        else
                        {
                                return "error!";
                        }
		        
		}
?>
