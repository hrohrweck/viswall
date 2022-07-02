<?php
		/////////////////////////////////////////////////
		// --> DOMedia <--> 2001/02 <--> vis|wall <--  //
		/////////////////////////////////////////////////
		//											   //
		// MainGroup    : Interface					   //
		//											   //
		// Name			: Module - QoS				   //
		// Date			: 08.03.2002				   //
		// Comment  	: QoS Functions 			   //
		//											   //
		/////////////////////////////////////////////////
		
		// ----------------------------
		// | Add cbq Entry (Sub,Main) |
		// ----------------------------
		// | Last Change : 08.03.2002 |
		// ----------------------------
		// | Status : Enabled		  |
		// ----------------------------
		function add_cbq($section, $section2, $tablename, $tablename2, $id = 0, $position)
		{
			#$result = mysql_query("select * from ".$tablename." order by priority");
			#$number = mysql_num_rows($result);
			#for ($i=0;$i<=$number-1;$i++) $row = mysql_fetch_array($result);
			
			$result = mysql_query("SELECT * FROM ".$tablename." WHERE(cid='".$id."')");
			$row = mysql_fetch_array($result);

			if ($row['parent'] == 0)
			{
				if ($position == "blank")
				{
					$result_iface = mysql_query("SELECT * FROM io_interfaces");
					$num_iface = mysql_num_rows($result_iface);
					
					$collision = 1;				
					
					for($i=0;$i<$num_iface;$i++)
					{
						$row_iface = mysql_fetch_array($result_iface);
						
						$result_iface_fetch = mysql_query("SELECT * FROM ".$tablename." WHERE(parent='0' and interface='".$row_iface['id']."')");
						$num_iface_fetch = mysql_num_rows($result_iface_fetch);
						
						if($num_iface_fetch == 0)
						{
							$collision = 0;
							$freeinterface = $row_iface['id'];
						}
					}
				}
				elseif ($position == "after")
				{
					$result2 = mysql_query("SELECT * FROM ".$tablename." WHERE(cid='".$id."')");
					$row2 = mysql_fetch_array($result2);
					
					$collision = 0;
					$freeinterface = $row2['interface'];
				}
			}
			else
			{
				$result2 = mysql_query("SELECT * FROM ".$tablename." WHERE(cid='".$row['parent']."')");
				$row2 = mysql_fetch_array($result2);
				
				$collision = 0;
				$freeinterface = $row2['interface'];
			}

			if($collision == 0)
			{
				switch($position)
				{
					case "before":	# Gleiche Subklasse
					{
						$result = mysql_query("SELECT parent FROM $tablename WHERE cid='".$id."'");
						$row = mysql_fetch_array($result);
						print_new($tablename, $tablename2, $section, $section2, $row2['parent'], $freeinterface);
						break;
					}
					case "after": 	# Neue Subklasse
					{
						print_new($tablename, $tablename2, $section, $section2, $id, $freeinterface); 
						break;				
					}
					case 0: 		# Neue Hauptklasse
					{
						print_new($tablename, $tablename2, $section, $section2, 0, $freeinterface);
						break;
					}
				}
			}
			else
			{
				show_cbq($section, $section2, $tablename);
			}
		}
		
		// ----------------------------
		// | Print New line (Sub)	  |
		// ----------------------------
		// | Last Change : 08.03.2002 |
		// ----------------------------
		// | Status : Enabled		  |
		// ----------------------------
		function print_new($tablename, $tablename2, $section, $section2, $parent, $freeinterface)
		{
			$data = "'','newclass','".$parent."','0Mbit','0kbit','0','0','5','".$freeinterface."','0Mbit','0','0','0'";
			$fields = "cid,cname,parent,rate,weight,bounded,isolated,priority,interface,bandwidth,status,cbq_class,service";
			$query = mysql_query("insert into ".$tablename." (".$fields.") values(".$data.")") or die(mysql_error());
			
			# Show Strategies (Default Mode)
			show_cbq($section, $section2, $tablename);
		}
        
        // -------------------------------
		// | Delete CBQ Entry (Sub,Main) |
		// -------------------------------
		// | Last Change : 08.03.2002	 |
		// -------------------------------
		// | Status : Enabled			 |
		// -------------------------------
		function delete_cbq($section, $section2, $tablename, $id, $confirmation, $firstid)
		{
			$result = mysql_query("SELECT cid FROM ".$tablename." WHERE parent='".$id."'");
			$number = mysql_num_rows($result);
			
			if($confirmation == 0)
			{
				if($number >= 1)
				{
					echo "<script language=\"javascript\">\n";
					echo "	check = confirm(\"Should the entry and all subentries really be deleted?\");\n";
					echo "	if(check == true)\n";
					echo "	{\n";
					echo "		window.location.href=\"".$PHP_SELF."?module=cbq&action=delete&id=".$id."&c=1\";\n";
					echo "	}\n";
					echo "	if(check == false)\n";
					echo "	{\n";
					echo "		window.location.href=\"".$PHP_SELF."?module=cbq\";\n";
					echo "	}\n";
					echo "</script>\n";
				}
				else
				{
					$confirmation = 1;
				}
			}
			
			if($confirmation == 1)
			{
				if($number >= 1)
				{
					# Bei rekursivem Eintrag
					chk_dep($id, $tablename, $section, $section2, "delete", $sub, $firstid);
					$result_delete = mysql_query("delete from ".$tablename." where(cid=\"".$id."\")");
				}
				else
				{
					# Bei nur einem Eintrag
					$result_delete = mysql_query("delete from ".$tablename." where(cid=\"".$id."\")");
				}
			}
			
			if ($id == $firstid) show_cbq($section, $section2, $tablename); 
		}
		
		// -----------------------------
		// | Edit CBQ Entry (Sub,Main) |
		// -----------------------------
		// | Last Change : 08.03.2002  |
		// -----------------------------
		// | Status : Enabled		   |
		// -----------------------------
		function edit_cbq($section, $section2, $tablename, $table_net, $table_hosts, $table_iface, $id, $field)
		{
					switch($field)
					{
					case "name":
						if (!isset($GLOBALS['rsubmit']))
						{
							print_edit_html($section, $section2, $tablename, $id, $field);
							break;
						}
						else
						{
							$result_change = mysql_query("UPDATE ".$tablename." SET cname='".$GLOBALS['cname']."' WHERE cid='".$GLOBALS['hiddenid']."'");
							show_cbq($section, $section2,$tablename);
							break;
						}
					case "bandwidth":
						if (!isset($GLOBALS['rsubmit']))
						{
							print_edit_html($section, $section2, $tablename, $id, $field);
							break;
						}
						else
						{
                            if ($GLOBALS['cbandwidth'] == 0)
                            {
                                $result2 = mysql_query("update ".$tablename." set status=0 where (cid='".$GLOBALS['hiddenid']."')") or die(mysql_error());
                            }
                            
                            $result_change = mysql_query("UPDATE ".$tablename." SET $field='".$GLOBALS['cbandwidth'].$GLOBALS['bwidth']."' WHERE cid='".$GLOBALS['hiddenid']."'");
							show_cbq($section, $section2,$tablename);
							break;
						}
					case "rate":
						if (!isset($GLOBALS['rsubmit']))
						{
							print_edit_html($section, $section2, $tablename, $id, $field);
							break;
						}
						else
						{
                            if ($GLOBALS['rate'] == 0)
                            {
                                $result2 = mysql_query("update ".$tablename." set status=0 where (cid='".$GLOBALS['hiddenid']."')") or die(mysql_error());
                            }

							$result_change = mysql_query("UPDATE ".$tablename." SET $field='".$GLOBALS['rate'].$GLOBALS['rateu']."' WHERE cid='".$GLOBALS['hiddenid']."'");
							show_cbq($section, $section2,$tablename);
							break;
						}
					case "weight":
						if (!isset($GLOBALS['rsubmit']))
						{
							print_edit_html($section, $section2, $tablename, $id, $field);
							break;
						}
						else
						{
							$result_change = mysql_query("UPDATE ".$tablename." SET $field='".$GLOBALS['weight'].$GLOBALS['weightu']."' WHERE cid='".$GLOBALS['hiddenid']."'");
							show_cbq($section, $section2,$tablename);
							break;
						}
					case "interface":
						if (!isset($GLOBALS['rsubmit']))
						{
							print_edit_html($section, $section2, $tablename, $id, $field);
							break;
						}
						else
						{
							$result_iface_fetch = mysql_query("SELECT * FROM ".$tablename." WHERE(parent='0' and interface='".get_iinterface($GLOBALS['interface'])."')");
							$num_iface_fetch = mysql_num_rows($result_iface_fetch);
							
							if ($num_iface_fetch == 0)
							{						
								changeint($section, $section2, $tablename, $GLOBALS['hiddenid'], $GLOBALS['interface'],$GLOBALS['hiddenid']);
								show_cbq($section, $section2, $tablename);
								break;
							}
							else
							{
								show_cbq($section, $section2, $tablename);
								break;
							}
						}
					case "priority":
						if (!isset($GLOBALS['rsubmit']))
						{
							print_edit_html($section, $section2, $tablename, $id, $field);
							break;
						}
						else
						{
							$result_change = mysql_query("UPDATE ".$tablename." SET $field='".$GLOBALS['priority']."' WHERE cid='".$GLOBALS['hiddenid']."'");
							show_cbq($section, $section2, $tablename);
							break;
						}
					case "service":
					    if (!isset($GLOBALS['rsubmit']))
					    {
					        print_edit_html($section, $section2, $tablename, $id, $field);
					        break;
					    }
					    else
					    {
					        $result_change = mysql_query("UPDATE ".$tablename." SET $field='".$GLOBALS['service']."' WHERE cid='".$GLOBALS['hiddenid']."'") or die(mysql_error());
					        show_cbq($section, $section2, $tablename);
					        break;
					    }
					}
			//show_cbq($section, $section2, $tablename);
		}
		
		// ----------------------------
		// | print edit HTML (Sub)	  |
		// ----------------------------
		// | Last Change : 08.03.2002 |
		// ----------------------------
		// | Status : Enabled		  |
		// ----------------------------
		function print_edit_html($section, $section2, $tablename, $id, $field)
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
				echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=cbq&action=edit\" name=\"submitform\">";
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
				echo "								<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
				echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
				echo "								<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
				echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
				echo "							</TR>\n";
				echo "							<TR bgcolor=\"#d5d5d5\">";
				echo "								<TD vAlign=middle align=left width=\"80\" height=\"22\">&nbsp;".$field."\n";
				echo "								</TD>";
				echo "								<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				switch ($field)
				{
					case "name":
					{
						$result_cname = mysql_query("select cname from strategies_cbq where cid='".$id."'");
						$row_cname = mysql_fetch_array($result_cname);
						echo "&nbsp;<input type=\"text\" name=\"cname\" value=\"".$row_cname['cname']."\">";
						break;
					}
					case "bandwidth":
					{
						$result_bandw = mysql_query("select bandwidth from strategies_cbq where cid='".$id."'");
						$row_bandw = mysql_fetch_array($result_bandw);
						$prefix = substr($row_bandw['bandwidth'], 0, strlen($row_bandw['bandwidth'])-4);
						$suffix = substr($row_bandw['bandwidth'], -4);
						echo "&nbsp;<input type=\"text\" name=\"cbandwidth\" value=".$prefix." size=\"8\"><SELECT name=bwidth>\n";
						issel($suffix, "kbit");
						echo "kbit</option>\n";
						issel($suffix, "Mbit");
						echo "Mbit</option>\n";
						//issel($suffix, "Gbit");
						//echo "Gbit</option>
                        echo "</SELECT>\n";
						break;
					}
					case "rate":
					{
						$result_rate = mysql_query("SELECT rate from strategies_cbq WHERE cid='".$id."'");
						$row_rate = mysql_fetch_array($result_rate);
						$prefix = substr($row_rate['rate'], 0, strlen($row_rate['rate'])-4);
						$suffix = substr($row_rate['rate'], -4);
						echo "&nbsp;<input type=\"text\" name=\"rate\" value=".$prefix." size=\"8\"><SELECT name=rateu>\n";
						issel($suffix, "kbit");
						echo "kbit</option>\n";
						issel($suffix, "Mbit");
						echo "Mbit</option>\n";
						//issel($suffix, "Gbit");
						//echo "Gbit</option>
                        echo "</SELECT>\n";
						break;
					}
					case "weight":
					{
						$result_weight = mysql_query("SELECT weight from strategies_cbq WHERE cid='".$id."'");
						$row_weight= mysql_fetch_array($result_weight);
						$prefix = substr($row_weight['weight'], 0, strlen($row_weight['weight'])-4);
						$suffix = substr($row_weight['weight'], -4);
						echo "&nbsp;<input type=\"text\" name=\"weight\" value=".$prefix." size=\"8\"><SELECT name=weightu>\n";
						issel($suffix, "kbit");
						echo "kbit</option>\n";
						issel($suffix, "Mbit");
						echo "Mbit</option>\n";
						//issel($suffix, "Gbit");
						//echo "Gbit</option>
                        echo "</SELECT>\n";
						break;
					}
					case "interface":
					{
						$result_int = mysql_query("SELECT id,name FROM io_interfaces");
						$result_local = mysql_query("SELECT interface FROM strategies_cbq WHERE cid='".$id."'");
						
						echo "&nbsp;<SELECT name=interface>\n";
						
						$number = mysql_num_rows($result_int);
						for($i=0;$i<$number;$i++)
						{
							$row_int= mysql_fetch_array($result_int);
							$row_local = mysql_fetch_array($result_local);
							issel($row_int['name'], $row_local['interface']);
							echo $row_int['name']."</option>\n";
						}
						echo "</SELECT>\n";
						break;
					}
					case "priority":
						$result_prio = mysql_query("SELECT priority FROM strategies_cbq WHERE cid='".$id."'");
						$row_prio = mysql_fetch_array($result_prio);
						echo "<SELECT name=priority>\n";
						issel($row_prio['priority'], "1");
						echo "1</option>\n";
						issel($row_prio['priority'], "2");
						echo "2</option>\n";
						issel($row_prio['priority'], "3");
						echo "3</option>\n";
						issel($row_prio['priority'], "4");
						echo "4</option>\n";
						issel($row_prio['priority'], "5");
						echo "5</option>\n";
						issel($row_prio['priority'], "6");
						echo "6</option>\n";
						issel($row_prio['priority'], "7");
						echo "7</option>\n";
						issel($row_prio['priority'], "8");
						echo "8</option>\n";
						echo "</SELECT>\n";
						break;
					case "service":
					{
                        $sql_db_local = new sql_db_local;
                        
						$result_local = mysql_query("SELECT service FROM ".$sql_db_local->sql_db_table_strategies_cbq." WHERE cid='".$id."'");
						$row_local = mysql_fetch_array($result_local);
						
						echo "&nbsp;<SELECT name=service>\n";

						$result_int = mysql_query("SELECT * FROM ".$sql_db_local->sql_db_table_so_services);						
						$number = mysql_num_rows($result_int);
						echo "<option value=\"0\"> ---> Global <--- </option>\n";
						isselval(0, $row_local['service'], 0);
						echo "ANY (n/a)</option>\n";
						echo "<option value=\"0\"> ---> Services <--- </option>\n";
						
						for($i=0;$i<$number;$i++)
						{
							$row_int= mysql_fetch_array($result_int);
							isselval("1".$row_int['id'], $row_local['service'], "1".$row_int['id']);
							echo $row_int['name']."</option>\n";
						}
						
						$result_int = mysql_query("SELECT * FROM ".$sql_db_local->sql_db_table_po_protocols);						
						$number = mysql_num_rows($result_int);
						echo "<option value=\"0\"> ---> Protocols <--- </option>\n";
						
						for($i=0;$i<$number;$i++)
						{
							$row_int= mysql_fetch_array($result_int);
							isselval("2".$row_int['id'], $row_local['service'], "2".$row_int['id']);
							echo $row_int['pr_keyword']."</option>\n";
						}

                        echo "</SELECT>\n";
						
						break;
					}
				}
				echo "</td>\n";
				echo "<tr bgcolor=\"#d5d5d5\">\n";
				echo "<td align=\"right\" colspan=\"2\">\n";
				echo "<input type=\"hidden\" value=\"".$id."\" name=\"hiddenid\">\n";
				echo "<input type=\"hidden\" value=\"".$field."\" name=\"field\">\n";
				echo "<input type=\"hidden\" name=\"rsubmit\">";
				echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
				echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
				echo "<a href=\"".$PHP_SELF."?module=".$section."\"><img src=\"./images/cancel.gif\" border=\"0\"></a>&nbsp;\n";				
				echo "								</td>\n";
				echo "							</tr>\n";
				echo "					</table>\n";
				echo "			</tr>\n";
				echo "		</table>\n";
		}	
		
		// --------------------------------
		// | check if selected (Sub,Main) |
		// --------------------------------
		// | Last Change : 12.02.2002	  |
		// --------------------------------
		// | Status : Enabled			  |
		// --------------------------------
		function issel($suffix, $compstr){
					if($suffix==$compstr) {
						echo "<option selected>";
					} else {
						echo "<option>";
					}
		}
		
		// -----------------------------------------------
		// | check if selected (Sub,Main) with value tag |
		// -----------------------------------------------
		// | Last Change : 12.02.2002	                 |
		// -----------------------------------------------
		// | Status : Enabled			                 |
		// -----------------------------------------------
		function isselval($suffix, $compstr, $value = 0){
					if($suffix==$compstr) {
						echo "<option value=\"".$value."\" selected>";
					} else {
						echo "<option value=\"".$value."\">";
					}
		}
		
		// -----------------------------
		// | Show cbq Entry (Sub,Main) |
		// -----------------------------
		// | Last Change : 08.03.2002  |
		// -----------------------------
		// | Status : Enabled		   |
		// -----------------------------
		function show_cbq($section, $section2, $tablename)
		{
			$result = mysql_query("select * from ".$tablename."");
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
			
			# Generate Table-Header #
			echo "					<table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"672px\" height=\"\">\n";
			echo "						<tr bgcolor=\"#565656\" class=\"tablehead\">\n";
			echo "							<td valign=\"bottom\" align=\"left\" width=\"52\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;STATUS</font>\n";
			echo "								<img src=\"images/border_orange.gif\" width=\"52\" height=\"6\" border=\"0\"></td>\n";
			echo "							<td valign=\"bottom\" align=\"left\" width=\"120\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;CLASS NAME</font>\n";
			echo "								<img src=\"images/border_orange.gif\" WIDTH=\"120\" height=\"6\" border=\"0\"></td>\n";
			echo "							<td valign=\"bottom\" align=\"left\" width=\"76\" height=\"22\">\n\n";
			echo "								<font color=\"#ffffff\">&nbsp;BANDWIDTH</font>\n";
			echo "								<img src=\"images/border_orange.gif\" WIDTH=\"76\" height=\"6\" border=\"0\"></td>\n";
			echo "							<td valign=\"bottom\" align=\"left\" width=\"65\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;RATE</font>\n";
			echo "								<img src=\"images/border_orange.gif\" WIDTH=\"65\" height=\"6\" border=\"0\"></td>\n";
			echo "							<td valign=\"bottom\" align=\"left\" width=\"55\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;WEIGHT</font>\n";
			echo "								<img src=\"images/border_orange.gif\" WIDTH=\"55\" height=\"6\" border=\"0\"></td>\n";
			echo "							<td valign=\"bottom\" align=\"left\" width=\"50\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;IFACE</font>\n";
			echo "								<img src=\"images/border_orange.gif\" WIDTH=\"50\" height=\"6\" border=\"0\"></td>\n";
			echo "							<td valign=\"bottom\" align=\"left\" width=\"37\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;PRIO</font>\n";
			echo "								<img src=\"images/border_orange.gif\" WIDTH=\"37\" height=\"6\" border=\"0\"></td>\n";					
			echo "							<td valign=\"bottom\" align=\"left\" width=\"46\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;BOUND</font>\n";
			echo "								<img src=\"images/border_orange.gif\" WIDTH=\"46\" height=\"6\" border=\"0\"></td>\n";
			echo "							<td valign=\"bottom\" align=\"left\" width=\"62\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;ISO</font>\n";
			echo "								<img src=\"images/border_orange.gif\" WIDTH=\"30\" height=\"6\" border=\"0\"></td>\n";					
			echo "							<td valign=\"bottom\" align=\"left\" width=\"30\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;SERVICE</font>\n";
			echo "								<img src=\"images/border_orange.gif\" WIDTH=\"62\" height=\"6\" border=\"0\"></td>\n";					
			echo "   						<td valign=\"bottom\" align=\"left\" width=\"115\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;FUNCTION</font>\n";
			echo "								<img src=\"images/border_orange.gif\" WIDTH=\"115\" height=\"6\" border=\"0\"></td>\n";
			echo "					</tr>\n";
			
			if($number == 0)
			{
				print_line("noentry", $tablename, 0, $section, $section2);
			}
			else
			{
				$result = mysql_query("select cid from ".$tablename." WHERE parent='0' order by priority");
				$number = mysql_num_rows($result);		
				
				for($i=0;$i<$number;$i++)
				{
					$row = mysql_fetch_array($result);
					print_line($row['cid'], $tablename, 0, $section, $section2, $row['cid']);
				}
			}
			
			print_last_line($section);
		}
		
		// ----------------------------
		// | print line (Sub,Main)	  |
		// ----------------------------
		// | Last Change : 08.03.2002 |
		// ----------------------------
		// | Status : Enabled		  |
		// ----------------------------
		function print_line($id, $tablename, $sub, $section, $section2, $firstid = 0)
		{
			if($id == "noentry")
			{
				echo "						<tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
				echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">-</td>";
				echo "							<td valign=\"middle\" align=\"right\" width=\"\" height=\"20\">-&nbsp;</td>";
				echo "							<td valign=\"middle\" align=\"right\" width=\"\" height=\"20\">-&nbsp;</td>";
				echo "							<td valign=\"middle\" align=\"right\" width=\"\" height=\"20\">-&nbsp;</td>";
				echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">-</td>";
				echo "							<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">&nbsp;-</td>";
				echo "							<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">&nbsp;-</td>";
				echo "							<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">&nbsp;-</td>";
				echo "							<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">&nbsp;-</td>";
				echo "							<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">&nbsp;-</td>";
				echo "							<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">";
				echo "							<a href=\"".$PHP_SELF."?module=".$section."&action=add&position=blank\"><IMG SRC=\"./images/add_entry_gr.gif\" WIDTH=\"50\" HEIGHT=\"16\" BORDER=\"0\ ALT=\"add main\"></a></td>";
			}
			else
			{
				$result = mysql_query("select * from ".$tablename." WHERE cid='".$id."'");
				$number = mysql_num_rows($result);
				$row = mysql_fetch_array($result);
				
				if ($number != 0)
				{
					echo "						<tr bgcolor=\"#bababa\" valign=\"middle\">";
					echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">";
					
					
					if ($row['parent'] == 0)
					{
						if ($row['status'] == 1)
							echo "								&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=setstatus&id=".$row['cid']."&field=status\"><IMG SRC=\"images/icons/on.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"on\"></a>&nbsp;</td>";
						else
							echo "							    &nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=setstatus&id=".$row['cid']."&field=status\"><IMG SRC=\"images/icons/off.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"off\"></a>&nbsp;</td>";
					}
					else
					{
						$result_spec = mysql_query("select status from ".$tablename." WHERE(cid='".$row['parent']."')");
						$row_spec = mysql_fetch_array($result_spec);
						
						if ($row_spec['status'] == 0)
						{
							echo "							   &nbsp<IMG SRC=\"images/icons/off.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"off\">&nbsp;</td>";
						}
						else
						{
							if ($row['status'] == 1)
								echo "								&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=setstatus&id=".$row['cid']."&field=status\"><IMG SRC=\"images/icons/on.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"on\"></a>&nbsp;</td>";
							else
								echo "							    &nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=setstatus&id=".$row['cid']."&field=status\"><IMG SRC=\"images/icons/off.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"off\"></a>&nbsp;</td>";
						}
					}
					
					echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">";
					
					if ($sub != 0)
					{
						echo "								&nbsp;";
						echo "<img src=\"images/tpx.gif\" height=1px width=2px>";
						for($a=0;$a<$sub;$a++)
						{
							echo "<img src=\"images/pfeil_rechts.gif\">&nbsp;";
						}
						
					}
					else
					{
						echo "<img src=\"images/tpx.gif\" height=1px width=1px>";
					}
					
					echo "								<a href=\"".$PHP_SELF."?module=".$section."&action=edit&id=".$row['cid']."&field=name\">".$row['cname']."</a>";
					echo "							</td>";
					echo "							<td valign=\"middle\" align=\"right\" width=\"\" height=\"20\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=edit&id=".$row['cid']."&field=bandwidth\">".$row['bandwidth']."</a>&nbsp;</td>";
					echo "							<td valign=\"middle\" align=\"right\" width=\"\" height=\"20\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=edit&id=".$row['cid']."&field=rate\">".$row['rate']."</a>&nbsp;</td>";
					echo "							<td valign=\"middle\" align=\"right\" width=\"\" height=\"20\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=edit&id=".$row['cid']."&field=weight\">".$row['weight']."</a>&nbsp;</td>";
					
					if ($row['parent'] == 0)					
						echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=edit&id=".$row['cid']."&field=interface\">".get_interface($row['interface'])."</a>&nbsp;</td>";
					else
						echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;".get_interface($row['interface'])."&nbsp;</td>";
					
					echo "							<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\"><a href=\"".$PHP_SELF."?module=".$section."&action=edit&id=".$row['cid']."&field=priority\">&nbsp;".$row['priority']."&nbsp;</a></td>";
					echo "							<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=setstatus&id=".$row['cid']."&field=bounded\">".is_true($row['bounded'])."</a>&nbsp;</td>";
					echo "							<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=setstatus&id=".$row['cid']."&field=isolated\">".is_true($row['isolated'])."</a>&nbsp;</td>";
					// Modified 07.07.2003 - OO
					$temp = catchservice($row['service']);
					echo "                          <td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=edit&id=".$row['cid']."&field=service\">".$temp['name']."&nbsp;</a></td>";
					//
					echo "						<td valign=\"middle\" align=\"middle\" width=\"\" height=\"20\">\n";
					echo "							<a href=\"".$PHP_SELF."?module=".$section."&action=pool&id=".$row['cid']."\"><IMG SRC=\"images/icons/pool.gif\" WIDTH=\"25\" HEIGHT=\"16\" BORDER=\"0\ ALT=\"rule pool\"></a>";
					
					if($row['parent']==0)
						echo "							<a href=\"".$PHP_SELF."?module=".$section."&action=add&position=blank&id=".$row['cid']."\"><IMG SRC=\"images/neu.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\ ALT=\"add main\"></a>";
						
					echo "							<a href=\"".$PHP_SELF."?module=".$section."&action=delete&id=".$row['cid']."&c=0\"><IMG SRC=\"images/icons/delete.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\ ALT=\"delete\"></a>";
					echo "							<a href=\"".$PHP_SELF."?module=".$section."&action=add&position=after&id=".$row['cid']."\"><IMG SRC=\"images/icons/add_after.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"add after\"></a>";
					echo "					</tr>\n";
					
					chk_dep($row['cid'],$tablename, $section, $section2, "query", 0, $firstid, $sub);
				}
			}
		}
		
		// ----------------------------
		// | Print last line (Main)	  |
		// ----------------------------
		// | Last Change : 08.03.2002 |
		// ----------------------------
		// | Status : Enabled		  |
		// ----------------------------
		function print_last_line($section)
		{
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
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"center\" width=\"\" height=\"12\">";
			echo "							<a href=\"".$PHP_SELF."?module=activate&g_module=".$section."&action=activate&params=execute\"><IMG SRC=\"images/activate.gif\" BORDER=\"0\" ALT=\"activate\"></a></td>";	
			echo "					</tr>\n";
			echo "					</table>\n";
			echo "				</td>\n";
			echo "			</tr>\n";
			echo "		</table>\n";
			echo "	<br><br><br>\n";
		}
		
		// --------------------------------
		// | Change CBQ Status (Sub,Main) |
		// --------------------------------
		// | Last Change : 08.03.2002	  |
		// --------------------------------
		// | Status : Enabled			  |
		// --------------------------------
		function status_cbq($section, $section2, $tablename, $id, $field)
		{
			# Changes the status (without prompt) of the selected
			# --------------------------------------------------------------------
			# Status Change for Main Entry
			# ---------------------------------
			$result = mysql_query("select * from ".$tablename." where (cid='".$id."')") or die(mysql_error());
			
			# Get Currente Status of Entry
			# ---------------------------------
			$row = mysql_fetch_array($result);
			# Select Status of Entry
			# -------------------------
			if ($row[$field] == 0)
			{
			    if (($row['bandwidth'] != 0) && ($row['rate'] != 0))
			    {
    				# Set Status of Entry == 1
    				# ---------------------------
    				$result = mysql_query("update ".$tablename." set ".$field."=1 where (cid='".$id."')") or die(mysql_error());
    			}
			}
			else
			{
				# Set Status of Entry == 0
				# ---------------------------
				$result = mysql_query("update ".$tablename." set ".$field."=0 where (cid='".$id."')") or die(mysql_error());
			}
			show_cbq($section, $section2, $tablename);
		}
		
		// ----------------------------
		// | Check Dependencies (Sub) |
		// ----------------------------
		// | Last Change : 06.02.2002 |
		// ----------------------------
		// |Status : Enabled		  |
		// ----------------------------
		function chk_dep($dataset, $tablename, $section, $section2, $action, $interface, $firstid, $sub=0)
		{
			$result = mysql_query("SELECT * FROM ".$tablename." WHERE parent='".$dataset."'");
			$num = mysql_num_rows($result);
			
			$sub++;
			
			for($i=0;$i<$num;$i++)
			{
				$row = mysql_fetch_array($result);
				
				if ($action=="query")
				{
					print_line($row['cid'], $tablename, $sub, $section, $section2, $firstid);
				}
				elseif($action=="delete")
				{
					delete_cbq($section, $section2, $tablename, $row['cid'], 1, $firstid);
				}
				elseif($action=="changeint")
				{
					changeint($section,$section2,$tablename,$row['cid'],$interface,$firstid);
				}
			}
		}
		
		// ----------------------------
		// | Change Interfaces (Sub)  |
		// ----------------------------
		// | Last Change : 08.03.2002 |
		// ----------------------------
		// | Status : Enabled		  |
		// ----------------------------
		function changeint($section, $section2, $tablename, $id, $interface, $firstid)
		{
			$result_int = mysql_query("SELECT * FROM io_interfaces WHERE name='".$interface."'");
			$row_int = mysql_fetch_array($result_int);
			
			if ($id == $firstid)
				$result_change = mysql_query("UPDATE $tablename SET interface='".$row_int['id']."' WHERE cid='".$id."'");
			
			$result_change = mysql_query("UPDATE $tablename SET interface='".$row_int['id']."' WHERE parent='".$id."'");
			
			$GLOBALS['rsubmit']="1";
			chk_dep($id, $tablename, $section, $section2, "changeint", $interface, $id);
			
		}
		
		// ----------------------------
		// | Get Interface (Sub)	  |
		// ----------------------------
		// | Last Change : 08.02.2002 |
		// ----------------------------
		// | Status : Enabled		  |
		// ----------------------------
		function get_interface($iid)
		{
			#convert interface-id in human useable interface-name
			$result = mysql_query("SELECT name FROM io_interfaces WHERE id='".$iid."'");
			$row = mysql_fetch_array($result);
			return $row['name'];
		}
		
		// ----------------------------
		// | Get Interface ID (Sub)	  |
		// ----------------------------
		// | Last Change : 08.02.2002 |
		// ----------------------------
		// | Status : Enabled		  |
		// ----------------------------
		function get_iinterface($iname)
		{
			#convert interface-name in human unuseable interface-id
			$result = mysql_query("SELECT id FROM io_interfaces WHERE name='".$iname."'");
			$row = mysql_fetch_array($result);
			return $row['id'];
		}
		
		// ----------------------------
		// | is_true (Sub)			  |
		// ----------------------------
		// | Last Change : 08.02.2002 |
		// ----------------------------
		// | Status : Enabled		  |
		// ----------------------------
		function is_true($value)
		{
			if($value=="1")
				return "<img src=\"images/icons/on.gif\" border=\"0\">";
			else
				return "<img src=\"images/icons/off.gif\" border=\"0\">";
		}
		
		function catchservice($sid = 0)
		{
            $sql_db_local = new sql_db_local;
		
            if (substr($sid,0,1) == '1')
            {
                $result = mysql_query("select * from ".$sql_db_local->sql_db_table_so_services." order by id");
                $amount = mysql_num_rows($result);

                for($i=0;$i<$amount;$i++)
                {
                    $row = mysql_fetch_array($result);
                    if($row['id'] == substr($sid,1)) return $row;
                }
            }
            elseif (substr($sid,0,1) == '2')
            {
                $result = mysql_query("select * from ".$sql_db_local->sql_db_table_po_protocols." order by id");
                $amount = mysql_num_rows($result);

                for($i=0;$i<$amount;$i++)
                {
                    $row = mysql_fetch_array($result);
                    if($row['id'] == substr($sid,1)) return array("name"=>$row['pr_keyword']);
                }
            }
            
            return array("name"=>"n/a");
		}
		
		// --------------------------------------
		// | CBQ IP/Host/Network Pool Selection |
		// --------------------------------------
		// | Last Change : 07.07.2003           |
		// --------------------------------------
		// | Status : Enabled		            |
		// --------------------------------------
		function pool($section, $section2, $layertable, $id, $hosttable, $networktable, $method)
		{
			$sql_db_local = new sql_db_local;
			
			if ((!isset($method)) or ($method == 'show'))
			{
				$result_H = mysql_query("select * from ".$hosttable." order by id");
				$numbers_H = mysql_num_rows($result_H);
				$result_N = mysql_query("select * from ".$networktable." order by id");
				$numbers_N = mysql_num_rows($result_N);
				
				echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
				echo "			<tr valign=\"top\">\n";
				echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					(".$id.") &nbsp;</td>\n";
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
				echo "<TD vAlign=bottom align=left width=\"175px\" height=\"22\"><FONT color=#ffffff>&nbsp;AVAILABLE RULES</FONT>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"175px\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"175px\" height=\"22\"><FONT color=#ffffff>&nbsp;ADMINISTRATE</FONT>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"175px\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"175px\" height=\"22\"><FONT color=#ffffff>&nbsp;ACTIVE RULES</FONT>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"175px\" border=0></TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"150px\" height=\"\">";
				echo "<form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=pool&id=".$id."&method=add\">";
				echo "<select name=\"c_list[]\" size=\"10\" multiple>";
				echo "<option value=\"empty\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</option>";
				for ($i=1; $i<=$numbers_H; $i++)
				{
					$row_H = mysql_fetch_array($result_H);
					$resultlayer_H = mysql_query("select * from ".$layertable." where tid=\"".$row_H['id']."\" AND toid=\"1\"  and cid=\"".$id."\"");
					$rowlayer_H = mysql_fetch_array($resultlayer_H);
					
					if ($rowlayer_H['tid'] != $row_H['id'])
						echo "<option value=\"".$row_H['id']."\">".$row_H['name']."</option>";
				}
				for ($i=1; $i<=$numbers_N; $i++)
				{
					$row_N = mysql_fetch_array($result_N);
					$resultlayer_N = mysql_query("select * from ".$layertable." where tid=\"".$row_N['id']."\" AND toid=\"2\"  and cid=\"".$id."\"");
					$rowlayer_N = mysql_fetch_array($resultlayer_N);
					
					if ($rowlayer_N['tid'] != $row_N['id'])
						echo "<option value=\"".$row_N['id']."\">".$row_N['name']."</option>";
				}
				echo "</select>";
				echo "</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"\">";
				echo "<input type=\"submit\" name=\"add\" value=\">>\"><input type=\"hidden\" name=\"formid\" value=\"".$id."\">";
				echo "</form>";
				echo "<form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=pool&id=".$id."&method=remove\">";
				echo "<input type=\"submit\" name=\"remove\" value=\"<<\"><input type=\"hidden\" name=\"formid\" value=\"".$id."\">";
				echo "<br><br><a href=\"".$PHP_SELF."?module=cbq\"><img src=\"./images/back.gif\" border=\"0\"></a>\n";
				echo "</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"\">";
				
				$result_H1 = mysql_query("select * from ".$hosttable." order by id");
				$numbers_H1 = mysql_num_rows($result_H1);
				$result_N1 = mysql_query("select * from ".$networktable." order by id");
				$numbers_N1 = mysql_num_rows($result_N1);	
				
				echo "<select name=\"u_list[]\" size=\"10\" multiple>";
				echo "<option value=\"empty\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</option>";
				for ($i=1; $i<=$numbers_H1; $i++)
				{
					$row_H1 = mysql_fetch_array($result_H1);
					$resultlayer_H1 = mysql_query("select * from ".$layertable." where tid=\"".$row_H1['id']."\" AND toid=\"1\"  and cid=\"".$id."\"");
					$rowlayer_H1 = mysql_fetch_array($resultlayer_H1);
					
					if ($rowlayer_H1['tid'] == $row_H1['id'])
						echo "<option value=\"".$rowlayer_H1['tid']."\">".$row_H1['name']."</option>";
				}
				
				for ($i=1; $i<=$numbers_N1; $i++)
				{
					$row_N1 = mysql_fetch_array($result_N1);
					$resultlayer_N1 = mysql_query("select * from ".$layertable." where tid=\"".$row_N1['id']."\" AND toid=\"2\"  and cid=\"".$id."\"");
					$rowlayer_N1 = mysql_fetch_array($resultlayer_N1);
					
					if ($rowlayer_N1['tid'] == $row_N1['id'])
						echo "<option value=\"".$rowlayer_N1['tid']."\">".$row_N1['name']."</option>";
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
					$result = mysql_query("select * from ".$hosttable." order by id");
					$numbers = mysql_num_rows($result);
					
					for ($i=1; $i<=$numbers; $i++)
					{
						$row = mysql_fetch_array($result);
						
						for ($j=0; $j<=sizeof($haystack); $j++)
						{
							if ($row['id'] == $haystack[$j])
								$result2 = mysql_query("insert into ".$layertable." (id,toid,tid,cid) values('','1','".$row['id']."','".$id."')");
						}
					}
					
					$result = mysql_query("select * from ".$networktable." order by id");
					$numbers = mysql_num_rows($result);
					
					for ($i=1; $i<=$numbers; $i++)
					{
						$row = mysql_fetch_array($result);
						
						for ($j=0; $j<=sizeof($haystack); $j++)
						{
							if ($row['id'] == $haystack[$j])
								$result2 = mysql_query("insert into ".$layertable." (id,toid,tid,cid) values('','2','".$row['id']."','".$id."')");
						}
					}
					
					pool("cbq", "STRATEGY | <B>QoS - CBQ</B>", $sql_db_local->sql_db_table_cbq_rules, $GLOBALS['id'], $sql_db_local->sql_db_table_no_hosts, $sql_db_local->sql_db_table_no_networks, "show");
				}
				else
				{
					pool("cbq", "STRATEGY | <B>QoS - CBQ</B>", $sql_db_local->sql_db_table_cbq_rules, $GLOBALS['id'], $sql_db_local->sql_db_table_no_hosts, $sql_db_local->sql_db_table_no_networks, "show");
				}
			}
			elseif (($method == 'remove'))
			{
				$haystack = $GLOBALS['u_list'];
				
				if (!empty($haystack))
				{
					for ($j=0; $j<=sizeof($haystack); $j++)
					{
						$result2 = mysql_query("delete from ".$layertable." where(tid=".$haystack[$j]." and cid=".$GLOBALS['formid'].")");
					}
					
					pool("cbq", "STRATEGY | <B>QoS - CBQ</B>", $sql_db_local->sql_db_table_cbq_rules, $GLOBALS['id'], $sql_db_local->sql_db_table_no_hosts, $sql_db_local->sql_db_table_no_networks, "show");
				}
				else
				{
					pool("cbq", "STRATEGY | <B>QoS - CBQ</B>", $sql_db_local->sql_db_table_cbq_rules, $GLOBALS['id'], $sql_db_local->sql_db_table_no_hosts, $sql_db_local->sql_db_table_no_networks, "show");
				}
			}
			else
			{
				pool("cbq", "STRATEGY | <B>QoS - CBQ</B>", $sql_db_local->sql_db_table_cbq_rules, $GLOBALS['id'], $sql_db_local->sql_db_table_no_hosts, $sql_db_local->sql_db_table_no_networks, "show");
			}
		}
?>
