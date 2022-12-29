<?php
		///////////////////////////////////////////////////////
		//                 --> vis|wall <--                  //
		///////////////////////////////////////////////////////
		//						     //
		// MainGroup   : Interface                           //
		//						     //
		// Name			: Module - Services          //
		// Date			: 27.03.2003		     //
		// Comment  	: Object Interfaces		     //
		//						     //
		///////////////////////////////////////////////////////
        
		// --------------------------------------
		// | Edit Service Entries                |
		// --------------------------------------
		// | Last Change : 27.11.2001        |
		// --------------------------------------
		// | Status : Enabled                    |
		// --------------------------------------
		function edit_objects_services($type, $section, $section2, $tablename, $id, $status)
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
				
				echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=edit&sid=".$id."\" name=\"submitform\">";
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
				switch ($type)
				{
					// Edit Type Selection
					case 0:
					{
						# Services (Edit)
						
                                                echo "<TABLE cellSpacing=1 cellPadding=0 width=\"360\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD&nbsp;</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"210\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE&nbsp;</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"210\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME OF SERVICE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" value=\"".$row['name']."\" name=\"name\" size=\"30\" maxlength=\"30\">&nbsp;</TD>\n";
						echo "</TR>\n";
						if ($row['so_type']==1) { // Just if record is an user-defined record
        						echo "<TR bgColor=\"#d5d5d5\">\n";
                					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ENABLE TCP</TD>\n";
                					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                					echo "<input type=\"checkbox\" name=\"tcp\" ".convert_checkbox_value($row['TCP'],2).">&nbsp;</TD>\n";
                					echo "</TR>\n";
                						
                					echo "<TR bgColor=\"#d5d5d5\">\n";
                					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ENABLE UDP</TD>\n";
                					echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                					echo "<input type=\"checkbox\" name=\"udp\" ".convert_checkbox_value($row['UDP'],2).">&nbsp;</TD>\n";
                					echo "</TR>\n";
        						
        						if (empty($_POST['portend']))
        						{
        						          $portend = $row['portstart'];
        						}
        						else
        						{
        						          $portend = $row['portend'];
        						}
        						echo "<TR bgColor=\"#d5d5d5\">\n";
        						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PORTSTART</TD>\n";
        						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
        						echo "<input type=\"text\" value=\"".$row['portstart']."\" name=\"portstart\" size=\"6\" maxlength=\"5\">&nbsp;</TD>\n";
        						echo "</TR>\n";
        						
        						echo "<TR bgColor=\"#d5d5d5\">\n";
        						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PORTEND</TD>\n";
        						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
        						echo "<input type=\"text\" value=\"".$row['portend']."\" name=\"portend\" size=\"6\" maxlength=\"5\">&nbsp;</TD>\n";
        						echo "</TR>\n";
						}
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
//						echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\" size=\"40\">\n";
						echo "<input type=\"hidden\" name=\"so_change\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$PHP_SELF."?module=services\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
				
				echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=edit&sid=".$_GET['sid']."\" name=\"submitform\">";
				echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
				echo "			<tr>\n";
				echo "				<td height=\"20px\" colspan=\"2\">\n";
				echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
				echo "			</tr>\n";
				echo "			<tr>\n";
				echo "				<td align=\"left\" width=\"40px\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\">\n";
				
				echo "<TABLE cellSpacing=1 cellPadding=0 width=\"360\" border=0>\n";
				echo "<TBODY>\n";
				echo "<TR bgcolor=\"#565656\">\n";
				echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"210\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"210\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"50\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"50\" border=0></TD>\n";
				echo "</TR>\n";
				
				switch ($type)
				{
					case 0:
					{
                                                if (substr($status,6,2) == 'OK') // Name OK
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME OF SERVICE</TD>\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['name']."\" name=\"name\" size=\"30\" maxlength=\"30\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,6,2) == 'ER') // Name Error
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME OF SERVICE</TD>\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['name']."\" name=\"name\" size=\"30\" maxlength=\"30\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						if ($row['so_type']==1) { // just if type is user
                                                        if (substr($status,9,2) == 'OK') // Protocol OK
        						{
                						echo "<TR bgColor=\"#d5d5d5\">\n";
                						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ENABLE TCP</TD>\n";
                						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                						echo "<input type=\"checkbox\" name=\"tcp\" ".convert_checkbox_value($_POST['tcp'],1).">&nbsp;</TD>\n";
        							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
                						echo "</TR>\n";
                						
                						echo "<TR bgColor=\"#d5d5d5\">\n";
                						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ENABLE UDP</TD>\n";
                						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                						echo "<input type=\"checkbox\" name=\"udp\" ".convert_checkbox_value($_POST['udp'],1).">&nbsp;</TD>\n";
        							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
                						echo "</TR>\n";
                                                        }
                                                        elseif (substr($status,9,2) == 'ER') // Protocol Error
                                                        {
                                                                echo "<TR bgColor=\"#d5d5d5\">\n";
                						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ENABLE TCP</TD>\n";
                						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                						echo "<input type=\"checkbox\" name=\"tcp\" ".convert_checkbox_value($_POST['tcp'],1).">&nbsp;</TD>\n";
        							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
                						echo "</TR>\n";
                						
                						echo "<TR bgColor=\"#d5d5d5\">\n";
                						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ENABLE UDP</TD>\n";
                						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                						echo "<input type=\"checkbox\" name=\"udp\" ".convert_checkbox_value($_POST['udp'],1).">&nbsp;</TD>\n";
        							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";        						
                						echo "</TR>\n";
                					}
                                                        if (substr($status,12,2) == 'OK') // Portstart OK
        						{
        						        // so if there is no endport but the Startport is OK, there is only one port!
        						        if (empty($_POST['portend']))
        						        {
        						                  $portend = $_POST['portstart'];
        						        }
        							else
        						        {
        						                  $portend = $_POST['portend'];
        						        }
        							echo "<TR bgColor=\"#d5d5d5\">\n";
        							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PORTSTART</TD>\n";
        							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
        							echo "<input type=\"text\" value=\"".$_POST['portstart']."\" name=\"portstart\" size=\"6\" maxlength=\"5\">&nbsp;</TD>\n";
        							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
        							echo "</TR>\n";
        						}
        						elseif (substr($status,12,2) == 'ER') // Portstart Error
        						{
                                                                // if $startport is errorous
        						        $endport = $_POST['endport'];
        							echo "<TR bgColor=\"#d5d5d5\">\n";
        							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PORTSTART</TD>\n";
        							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
        							echo "<input type=\"text\" value=\"".$_POST['portstart']."\" name=\"portstart\" size=\"6\" maxlength=\"5\">&nbsp;</TD>\n";
        							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
        							echo "</TR>\n";
        						}
        						if (substr($status,15,2) == 'OK') // Portend OK
        						{
        							echo "<TR bgColor=\"#d5d5d5\">\n";
        							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PORTEND</TD>\n";
        							echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
        							echo "<input type=text value=\"".$portend."\" name=\"portend\" size=\"6\" maxlength=\"5\">&nbsp;</TD>\n";
        							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
        							echo "</TR>\n";
        						}
        						elseif (substr($status,15,2) == 'ER') // Portend Error
        						{
        							echo "<TR bgColor=\"#d5d5d5\">\n";
        							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PORTEND</TD>\n";
        							echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
        							echo "<input type=text value=\"".$portend."\" name=\"portend\" size=\"6\" maxlength=\"5\">&nbsp;</TD>\n";
        							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
        							echo "</TR>\n";
        						}
        					}	
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						//echo "<input type=\"hidden\" value=\"".$_GET['sid']."\" name=\"id\" size=\"40\">\n";
						echo "<input type=\"hidden\" name=\"so_change\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$PHP_SELF."?module=services\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
						if ($GLOBALS['magic'] == $GLOBALS['lastmagic'])
						{
							show_objects_services($type, $section, $section2, $tablename);
						}
						else
						{
                                                        $GLOBALS['lastmagic'] = $GLOBALS['magic'];
        						$field_NAME = "ER";
        						if (!empty($_POST['name'])) $field_NAME = "OK";

                                                        if ($row['so_type']==0) {//case type SYSTEM
                                                                if ($field_NAME=="OK") {
                                                                        $result = mysql_query("update ".$tablename." set name='".$_POST['name']."' where(id='".$_GET['sid']."')");
              								show_objects_services($type, $section, $section2, $tablename);
        							}
        							else
        							{
        								edit_objects_services($type, $section, $section2, $tablename, $_GET['sid'], "error|".$field1."_".$field2."_".$field3);
        							}
                                                        } else {
        							$field_PROTOCOL = "ER";
        							$field_PS = "ER";
        							$field_PE = "ER";

        							if (!(empty($_POST['tcp'])) or !(empty($_POST['udp']))) $field_PROTOCOL = "OK";

                                                                // Trim Port Values to an Integer Value

                                                                $portstart = (int) $_POST['portstart'];
                                                                $portend = (int) $_POST['portend'];

                                                                if (valid_port($portstart, $portend)=="OK"){
                                                                        $field_PS = "OK";
                                                                        $field_PE = "OK";
                                                                } elseif(valid_port($portstart, $portend)=="ER_PE") {
                                                                        $field_PS = "OK"; // if only the End Port is invalid
                                                                }
        					                // if $portend is empty, it seems the user want a single port services
                                                                if (empty($portend)) {
                                                                        $portend = $portstart;
                                                                }
        							// Convert Checkbox Value to 1 (on) or 0 (off)
                                                                $tcp = convert_checkbox_value($_POST['tcp'],0); // Convert Checked to 1
        							$udp = convert_checkbox_value($_POST['udp'],0);
                                                                // finaly check if entry does not already exist
                                                                if (!check_duplicates($tablename, $portstart, $portend, $tcp, $udp, $_GET['sid'])) {
                                                                        $field_PS = "ER";
                                                                        $field_PE = "ER";
                                                                }

                                                                if (($field_NAME == 'OK') and ($field_PROTOCOL == 'OK') and ($field_PS == 'OK') and ($field_PE == 'OK'))
        							{
        								$result = mysql_query("update ".$tablename." set name='".$_POST['name']."' where(id='".$_GET['sid']."')");
        								$result = mysql_query("update ".$tablename." set TCP='".$tcp."' where(id='".$_GET['sid']."')");
        								$result = mysql_query("update ".$tablename." set UDP='".$udp."' where(id='".$_GET['sid']."')");
        								$result = mysql_query("update ".$tablename." set portstart='".$portstart."' where(id='".$_GET['sid']."')");
        								$result = mysql_query("update ".$tablename." set portend='".$portend."' where(id='".$_GET['sid']."')");
        								
        								show_objects_services($type, $section, $section2, $tablename);
        							}
        							else
        							{
        								edit_objects_services($type, $section, $section2, $tablename, $_GET['sid'], "error|".$field_NAME."_".$field_PROTOCOL."_".$field_PS."_".$field_PE);
        							}
        						}
						}
						break;
					}
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
		function add_objects_services($type, $section, $section2, $tablename, $status)
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
				
				# Add-Type (Services) #
				switch ($type)
				{
					# Add Type Selection #
					case 0:
					{
						echo "<TABLE cellSpacing=1 cellPadding=0 width=\"360\" border=0>\n";
						echo "<TBODY>\n";
						echo "<TR bgcolor=\"#565656\">\n";
						echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD&nbsp;</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
						echo "<TD vAlign=bottom align=left width=\"210\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE&nbsp;</font>\n";
						echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"210\" border=0></TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME OF SERVICE</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" name=\"name\" size=\"30\" maxlength=\"30\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ENABLE TCP</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<input type=\"checkbox\" name=\"tcp\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ENABLE UDP</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<input type=\"checkbox\" name=\"udp\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PORTSTART</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
						echo "<input type=\"text\" name=\"portstart\" size=\"6\" maxlength=\"5\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PORTEND</TD>\n";
						echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
						echo "<input type=text name=\"portend\" size=\"6\" maxlength=\"5\">&nbsp;</TD>\n";
						echo "</TR>\n";
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						echo "<input type=\"hidden\" name=\"so_submit\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/add.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$PHP_SELF."?module=services\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
				echo " 	  				".$section2." | <i>".$row['name']."</i> (".$row['id'].") &nbsp;</td>\n";
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
				
				echo "<TABLE cellSpacing=1 cellPadding=0 width=\"360\" border=0>\n";
				echo "<TBODY>\n";
				echo "<TR bgcolor=\"#565656\">\n";
				echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;FIELD&nbsp;</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"210\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE&nbsp;</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"210\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"50\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"50\" border=0></TD>\n";
				echo "</TR>\n";
				
				switch ($type)
				{
					case 0:
					{
                                                if (substr($status,6,2) == 'OK') // Name OK
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME OF SERVICE</TD>\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['name']."\" name=\"name\" size=\"30\" maxlength=\"30\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,6,2) == 'ER') // Name Error
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NAME OF SERVICE</TD>\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['name']."\" name=\"name\" size=\"30\" maxlength=\"30\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						if (substr($status,9,2) == 'OK') // Protocol OK
						{
        						echo "<TR bgColor=\"#d5d5d5\">\n";
        						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ENABLE TCP</TD>\n";
        						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
        						echo "<input type=\"checkbox\" name=\"tcp\" ".convert_checkbox_value($_POST['tcp'],1).">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
        						echo "</TR>\n";
        						
        						echo "<TR bgColor=\"#d5d5d5\">\n";
        						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ENABLE UDP</TD>\n";
        						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
        						echo "<input type=\"checkbox\" name=\"udp\" ".convert_checkbox_value($_POST['udp'],1).">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
        						echo "</TR>\n";
                                                }
                                                elseif (substr($status,9,2) == 'ER') // Protocol Error
                                                {
                                                        echo "<TR bgColor=\"#d5d5d5\">\n";
        						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ENABLE TCP</TD>\n";
        						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
        						echo "<input type=\"checkbox\" name=\"tcp\" ".convert_checkbox_value($_POST['tcp'],1).">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
        						echo "</TR>\n";
        						
        						echo "<TR bgColor=\"#d5d5d5\">\n";
        						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ENABLE UDP</TD>\n";
        						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
        						echo "<input type=\"checkbox\" name=\"udp\" ".convert_checkbox_value($_POST['udp'],1).">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";        						
        						echo "</TR>\n";
        					}
                                                if (substr($status,12,2) == 'OK') // Portstart OK
						{
						        // so if there is no endport but the Startport is OK, there is only one port!
						        if (empty($_POST['portend']))
						        {
						                  $portend = $_POST['portstart'];
						        }
							else
						        {
						                  $portend = $_POST['portend'];
						        }
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PORTSTART</TD>\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['portstart']."\" name=\"portstart\" size=\"6\" maxlength=\"5\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,12,2) == 'ER') // Portstart Error
						{
                                                        // if $startport is errorous
						        $endport = $_POST['endport'];
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PORTSTART</TD>\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
							echo "<input type=\"text\" value=\"".$_POST['portstart']."\" name=\"portstart\" size=\"6\" maxlength=\"5\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						if (substr($status,15,2) == 'OK') // Portend OK
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PORTEND</TD>\n";
							echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
							echo "<input type=text value=\"".$portend."\" name=\"portend\" size=\"6\" maxlength=\"5\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/ok.gif\"></td>\n";
							echo "</TR>\n";
						}
						elseif (substr($status,15,2) == 'ER') // Portend Error
						{
							echo "<TR bgColor=\"#d5d5d5\">\n";
							echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;PORTEND</TD>\n";
							echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
							echo "<input type=text value=\"".$portend."\" name=\"portend\" size=\"6\" maxlength=\"5\">&nbsp;</TD>\n";
							echo "<td valign=middle align=center width=\"\" height=\"22\"><img src=\"./images/error.gif\"></td>\n";
							echo "</TR>\n";
						}
						
						echo "<TR bgColor=\"#d5d5d5\">\n";
						echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
						//echo "<input type=\"hidden\" value=\"".$GLOBALS['id']."\" name=\"id\" size=\"40\">\n";
						echo "<input type=\"hidden\" name=\"so_submit\">";
						echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
						echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/add.gif\" border=\"0\"></a>&nbsp;\n";
						echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
    					        echo "<a href=\"".$PHP_SELF."?module=services&action=list\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
						if ($GLOBALS['magic'] == $GLOBALS['lastmagic'])
						{
							show_objects_services($type, $section, $section2, $tablename);
						}
						else
						{
                                                        $GLOBALS['lastmagic'] = $GLOBALS['magic'];
							$field_NAME = "ER";
							$field_PROTOCOL = "ER";
							$field_PS = "ER";
							$field_PE = "ER";
							
							if (!empty($_POST['name'])) $field_NAME = "OK";
							if (!(empty($_POST['tcp'])) or !(empty($_POST['udp']))) $field_PROTOCOL = "OK";

                                                        // Trim Port Values to an Integer Value
                                                        
                                                        $portstart = (int) $_POST['portstart'];
                                                        $portend = (int) $_POST['portend'];

                                                        if (valid_port($portstart, $portend)=="OK"){
                                                                $field_PS = "OK";
                                                                $field_PE = "OK";
                                                        } elseif(valid_port($portstart, $portend)=="ER_PE") {
                                                                $field_PS = "OK"; // if only the End Port is invalid
                                                        }
					                // if $portend is empty, it seems the user want a single port services
                                                        if (empty($portend)) {
                                                                $portend = $portstart;
                                                        }
							// Convert Checkbox Value to 1 (on) or 0 (off)
                                                        $tcp = convert_checkbox_value($_POST['tcp'],0); // Convert Checked to 1
							$udp = convert_checkbox_value($_POST['udp'],0);
                                                        // finaly check if entry does not already exist
                                                        if (!check_duplicates($tablename, $portstart, $portend, $tcp, $udp, "")) {
                                                                $field_PS = "ER";
                                                                $field_PE = "ER";
                                                        }

							if (($field_NAME == 'OK') and ($field_PROTOCOL == 'OK') and ($field_PS == 'OK') and ($field_PE == 'OK'))
							{
							
                                                                $data = "'','".$_POST['name']."','".$tcp."','".$udp."','".$portstart."','".$portend."','1'";
								$fields = "id,name,tcp,udp,portstart,portend,so_type";
								$query = mysql_query("insert into ".$tablename." (".$fields.") values(".$data.")") or die(mysql_error());
								
								show_objects_services($type, $section, $section2, $tablename);
							}
							else
							{
								add_objects_services($type, $section, $section2, $tablename, "error|".$field_NAME."_".$field_PROTOCOL."_".$field_PS."_".$field_PE);
							}
						}
						break;
					}
				}
			}
		}
		// -------------------------------------
		// | Default Style - Show Services  |
		// -------------------------------------
		// | Last Change : 27.11.2001       |
		// -------------------------------------
		// | Status : Enabled                   |
		// -------------------------------------
		function show_objects_services($type, $section, $section2, $tablename)
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
					echo "<TABLE cellSpacing=1 cellPadding=0 width=562 border=0>\n";
					echo "<TBODY>\n";
					echo "<TR class=tablehead bgColor=#565656>\n";
					echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;NAME</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"138\" height=\"22\"><FONT color=#ffffff>&nbsp;ENABLED PROTOCOLS</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"138\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"90\" height=\"22\"><FONT color=#ffffff>&nbsp;PORT START</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"90\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"90\" height=\"22\"><FONT color=#ffffff>&nbsp;PORT END</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"90\" border=0></TD>\n";
					echo "<TD vAlign=bottom align=left width=\"94\" height=\"22\"><FONT color=#ffffff>&nbsp;ADMINISTRATE</FONT>\n";
					echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"94\" border=0></TD>\n";
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
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".quickview($row['id'],$tablename)."</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['portstart']."</TD>\n";
						echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['portend']."</TD>\n";
						echo "<TD vAlign=middle align=middle width=\"\" height=\"22\">\n";
						echo "&nbsp;<a href=\"".$PHP_SELF."?module=services&action=edit&sid=".$row['id']."\"><IMG SRC=\"./images/icons/edit_gr.gif\" WIDTH=\"22\" HEIGHT=\"16\" BORDER=0 ALT=\"edit\"></a>\n";
						if ($row['so_type']==1)
                        {
					       echo "</a>&nbsp;&nbsp;<a href=\"".$PHP_SELF."?module=services&action=delete&sid=".$row['id']."&sd_override=no\"><IMG SRC=\"./images/icons/delete.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=0 ALT=\"delete\"></a>&nbsp;</TD>\n";
					    }
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
					echo "						<TD vAlign=bottom align=middle height=20>&nbsp;<a href=\"".$PHP_SELF."?module=services&action=add\"><IMG SRC=\"./images/add_entry_gr.gif\" WIDTH=\"50\" HEIGHT=\"16\" BORDER=0 ALT=\"add entry\"></a>&nbsp;</TD>\n";
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
		}			
		// -----------------------------------
		// | Protocol Quick View Funtion  |
		// -----------------------------------
		// | Last Change : 15.11.2001    |
		// -----------------------------------
		// | Status : Enabled                 |
		// -----------------------------------
		function quickview($id, $tablename)
		{
			$result = mysql_query("select TCP,UDP from ".$tablename." where(id='".$id."')");
			$row = mysql_fetch_array($result);
			if (($row['TCP']==1) and ($row['UDP']==0))
			{
			        $output = "TCP";
			}
			elseif (($row['TCP']==0) and ($row['UDP']==1))
			{
			        $output = "UDP";
			}
			elseif (($row['TCP']==1) and ($row['UDP']==1))
			{
				$output = "TCP, UDP";
			}
			else
			{
				$output = "error: no protocol";
			}
					
			return $output;
		}
		// --------------------------------
		// | Protocol Status Analyzer   |
		// --------------------------------
		// | Last Change : 30.11.2001 |
		// --------------------------------
		// | Status : Enabled             |
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
		// | convert Checkbox Value        |
		// --------------------------------
		// | Last Change : 27.03.2003      |
		// --------------------------------
		// | Status : Enabled              |
		// --------------------------------
		function convert_checkbox_value($checkboxvalue, $direction) {
                        switch ($direction)
                        {
                                case 0:
                                       if ($checkboxvalue=="on") {
                		                   return 1;
                	               } else {
                        	                   return 0;
                        	       }
                        	       break;
                        	case 1:
                        	       if ($checkboxvalue=="on") {
                        	               return "checked";
                                       } else {
                                               return;
                                       }
                                       break;
                        	case 2:
                        	       if ($checkboxvalue==1) {
                        	               return "checked";
                                       } else {
                                               return;
                                       }
                                       break;
                                default:
                        	       errorcode(7,0);
                        	       break;
                	}
                }
                // --------------------------------
		// | Check Start & End Ports       |
		// --------------------------------
		// | Last Change : 27.03.2003      |
		// --------------------------------
		// | Status : Enabled              |
		// --------------------------------
                function valid_port($portstart, $portend) {
                        if (empty($portstart)) {
                                return "ER_PS";
                        } 
                        if (!is_numeric($portstart)) {
                                return "ER_PS";
                        }
                        if (!($portstart>= 1) and !($portstart<= 65535)) {
                                return "ER_PS";
                        }
                        if (empty($portend)) {
                                $portend = $portstart;
                        }
                        if (!is_numeric($portend)) {
                                return "ER_PE";
                        }
                        if (!($portend>= $portstart) and !($portend<= 65535)) {
                                return "ER_PE";
                        }
                        return "OK";
                }
                
                // --------------------------------
		// | Check for duplicate Ports     |
		// --------------------------------
		// | Last Change : 28.03.2003      |
		// --------------------------------
		// | Status : Enabled              |
		// --------------------------------
                function check_duplicates($tablename, $portstart, $portend, $tcp, $udp, $skipid) {
                        $result = mysql_query("SELECT id FROM ".$tablename." WHERE portstart=".$portstart." and portend=".$portend." and TCP=".$tcp." and UDP=".$udp);
                        $number = mysql_num_rows($result);
                        $row = mysql_fetch_array($result);
                        if ($number==0) {
                                mysql_free_result($result);
                                return true;
                        } else {
                                if ($row['id']!=$skipid) { //Skip if record = current record
                                        errorcode(3,0);
                                        mysql_free_result($result);
                                        return;
                                } else {
                                        return true;
                                }
                        }
                        
                }
?>
