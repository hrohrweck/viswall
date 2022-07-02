<?php
		////////////////////////////////////////////////
		// --> DOMedia <--> 2001/02 <--> vis|wall <-- //
		////////////////////////////////////////////////
		//											  //
		// MainGroup   : Interface                    //
		//											  //
		// Name			: Module - NIDS Logging       //
		// Date			: 08.03.2002				  //
		// Comment  	: Network Intrusion Detection //
		//											  //
		////////////////////////////////////////////////
        
		// -------------------------------------
		// | Open NIDS Logging DB			   |
		// -------------------------------------
		// | Last Change : 28.02.2002          |
		// -------------------------------------
		// | Status : Enabled                  |
		// -------------------------------------
		function open_db_nids()
		{
			$sql_db_nids = new sql_db_nids;
            mysql_connect($sql_db_nids->sql_db_host, $sql_db_nids->sql_db_username, $sql_db_nids->sql_db_password) or die ("Kann keine Verbindung zur Datenbank herstellen");
            mysql_select_db($sql_db_nids->sql_db_name) or die ("Die Datenbank wurde nicht gefunden");
		}
		
		function more()
		{
			$result = mysql_query("SELECT * FROM signature WHERE(sig_sid='".$GLOBALS['mid']."')");
			$num = mysql_numrows($result);
			$row=mysql_fetch_array($result);
			
			echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"10px\">\n";
			echo "			<tr>\n";
			echo "				<td height=\"10px\">\n";
			echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"10px\"></td>\n";
			echo "			</tr>\n";
			echo "		</table>\n";
			
			echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
			echo "			<tr>\n";
			echo "				<td align=\"left\" width=\"5px\">\n";
			echo "					<img src=\"./images/tpx.gif\" width=\"5px\" height=\"1px\" border=\"0\"></td>\n";
			echo "				<td align=\"left\">\n";
			echo "					<TABLE cellSpacing=0 cellPadding=0 width=\"480\" border=0>\n";
			echo "						<TBODY>\n";
			echo "							<TR bgcolor=\"#565656\">\n";
			echo "								<TD vAlign=bottom align=left width=\"480\">";
			echo "									<TABLE cellspacing=\"0\" cellpadding=\"0\" border=\"0\" height=\"22\">\n";
			echo "										<TR>";
			echo "											<TD vAlign=middle align=left width=\"450\">";
			echo "												<FONT color=#ffffff>&nbsp;SIGNATURE DETAILS</font></td>";
			echo "											<TD vAlign=bottom align=right width=\"30\">";
				if ($row[3] == 1)
					echo "										<img src=\"./images/prio_rot.gif\">&nbsp;</td>\n";
				elseif ($row[3] == 2)
					echo "										<img src=\"./images/prio_gelb.gif\">&nbsp;</td>\n";
				elseif ($row[3] == 3)
					echo "										<img src=\"./images/prio_grun.gif\">&nbsp;</td>\n";
				elseif ($row[3] == 5)
					echo "										<img src=\"./images/prio_grau_off.gif\">&nbsp;</td>\n";
				else
					echo "										<img src=\"./images/prio_grau_on.gif\">&nbsp;</td>\n";
			echo "										</tr>";
			echo "									</table>\n";
			echo "								</td>\n";
			echo "							</tr>\n";
			echo "							<TR bgcolor=\"#565656\">\n";
			echo "								<TD height=\"6\">";
			echo "									<IMG height=\"6\" src=\"./images/border_orange.gif\" width=\"480\" border=0></TD>\n";
			echo "							</TR>\n";
			echo "							<TR bgColor=\"#d5d5d5\">\n";
			echo "								<table border=\"0\" cellpadding=\"5\" cellspacing=\"0\" border=\"0\" width=\"480px\">\n";
			echo "									<tr bgColor=\"#d5d5d5\" rowspan=\"2\">";
			echo "										<TD vAlign=middle align=left width=\"\" height=\"30\">".$row['sig_name']."&nbsp;</TD>\n";
			echo "									</tr>\n";
			echo "								</table>\n";
			echo "							</tr>\n";
			echo "						</tbody>\n";
			echo "					</table>\n";
			
			echo "				</td>\n";
			echo "			</tr>\n";
			echo "		</table>\n";
		}
		
		function detail()
		{
			$result = mysql_query("SELECT * FROM signature WHERE(sig_id='".$GLOBALS['mid']."')");
			$num = mysql_numrows($result);
			$row=mysql_fetch_array($result);
			
			echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"10px\">\n";
			echo "			<tr>\n";
			echo "				<td height=\"10px\">\n";
			echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"10px\"></td>\n";
			echo "			</tr>\n";
			echo "		</table>\n";
			
			echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
			echo "			<tr>\n";
			echo "				<td align=\"left\" width=\"5px\">\n";
			echo "					<img src=\"./images/tpx.gif\" width=\"5px\" height=\"1px\" border=\"0\"></td>\n";
			echo "				<td align=\"left\">\n";
			echo "					<TABLE cellSpacing=0 cellPadding=0 width=\"480\" border=0>\n";
			echo "						<TBODY>\n";
			echo "							<TR bgcolor=\"#565656\">\n";
			echo "								<TD vAlign=bottom align=left width=\"480\">";
			echo "									<TABLE cellspacing=\"0\" cellpadding=\"0\" border=\"0\" height=\"22\">\n";
			echo "										<TR>";
			echo "											<TD vAlign=middle align=left width=\"450\">";
			echo "												<FONT color=#ffffff>&nbsp;SIGNATURE DETAILS</font></td>";
			echo "											<TD vAlign=bottom align=right width=\"30\">";
				if ($row[3] == 1)
					echo "										<img src=\"./images/prio_rot.gif\">&nbsp;</td>\n";
				elseif ($row[3] == 2)
					echo "										<img src=\"./images/prio_gelb.gif\">&nbsp;</td>\n";
				elseif ($row[3] == 3)
					echo "										<img src=\"./images/prio_grun.gif\">&nbsp;</td>\n";
				elseif ($row[3] == 5)
					echo "										<img src=\"./images/prio_grau_off.gif\">&nbsp;</td>\n";
				else
					echo "										<img src=\"./images/prio_grau_on.gif\">&nbsp;</td>\n";
			echo "										</tr>";
			echo "									</table>\n";
			echo "								</td>\n";
			echo "							</tr>\n";
			echo "							<TR bgcolor=\"#565656\">\n";
			echo "								<TD height=\"6\">";
			echo "									<IMG height=\"6\" src=\"./images/border_orange.gif\" width=\"480\" border=0></TD>\n";
			echo "							</TR>\n";
			echo "							<TR bgColor=\"#d5d5d5\">\n";
			echo "								<table border=\"0\" cellpadding=\"5\" cellspacing=\"0\" border=\"0\" width=\"480px\">\n";
			echo "									<tr bgColor=\"#d5d5d5\" rowspan=\"2\">";
			echo "										<TD vAlign=middle align=left width=\"\" height=\"30\">".$row['sig_name']."&nbsp;</TD>\n";
			echo "									</tr>\n";
			echo "								</table>\n";
			echo "							</tr>\n";
			echo "						</tbody>\n";
			echo "					</table>\n";
			
			echo "				</td>\n";
			echo "			</tr>\n";
			echo "		</table>\n";
		}
		
		// -------------------------------------
		// | Popup : Signature List            |
		// -------------------------------------
		// | Last Change : 08.03.2002          |
		// -------------------------------------
		// | Status : Enabled                  |
		// -------------------------------------
		function signaturelist()
		{
			$result = mysql_query("SELECT * FROM signature ORDER BY sig_priority DESC");
			$num = mysql_numrows($result);
			
			echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
			echo "			<tr>\n";
			echo "				<td height=\"5px\" colspan=\"2\">\n";
			echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"5px\"></td>\n";
			echo "			</tr>\n";
			echo "			<tr valign=\"top\">\n";
			echo "				<td align=\"left\" width=\"5px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
			echo "					<img src=\"./images/tpx.gif\" width=\"5px\" height=\"23px\" border=\"0\"></td>\n";
			echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
			echo " 	  				LOG | <b>SIGNATURE-LIST</b> &nbsp;(".$num.")</td>\n";
			echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
			echo "					<img src=\"./images/tpx.gif\" width=\"100px\" height=\"23px\" border=\"0\"></td>\n";
			echo "			</tr>\n";
			echo "		</table>\n";
			
			echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
			echo "			<tr>\n";
			echo "				<td align=\"left\" width=\"5px\">\n";
			echo "					<img src=\"./images/tpx.gif\" width=\"5px\" height=\"1px\" border=\"0\"></td>\n";
			echo "				<td align=\"left\">\n";
			
			echo "					<TABLE cellSpacing=1 cellPadding=0 width=\"480\" border=0>\n";
			echo "						<TBODY>\n";
			echo "							<TR bgcolor=\"#565656\">\n";
			echo "								<TD vAlign=bottom align=left width=\"50\" height=\"22\"><FONT color=#ffffff>&nbsp;SIG. ID</font>\n";
			echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"50\" border=0></TD>\n";
			echo "								<TD vAlign=bottom align=left width=\"400\" height=\"22\"><FONT color=#ffffff>&nbsp;SIGNATURE NAME</font>\n";
			echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"400\" border=0></TD>\n";
			echo "								<TD vAlign=bottom align=left width=\"40\" height=\"22\"><FONT color=#ffffff>&nbsp;PRIO</font>\n";
			echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"40\" border=0></TD>\n";			
			echo "							</TR>\n";
			
			for ($i=0;$i<=$num-1;$i++)
			{
				$row = mysql_fetch_array($result);
				
				echo "							<TR bgColor=\"#d5d5d5\">\n";				
				echo "								<TD vAlign=middle align=right width=\"\" height=\"22\">$row[0]&nbsp;</TD>\n";
				
				if (strlen($row[1]) > 50)
					$output = substr($row[1],0,50)." ... [<a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=nidslog&action=more&navigation=0&mid=$row[5]','more','505','50','true')\"><font color=\"blue\">more</font>]&nbsp;&nbsp;";
				else
					$output = $row[1];
				
				echo "								<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;$output</td>\n";
				echo "								<TD vAlign=middle align=center width=\"\" height=\"22\">\n";
				
				if ($row[3] == 1)
					echo "									<img src=\"./images/prio_rot.gif\"></td>\n";
				elseif ($row[3] == 2)
					echo "									<img src=\"./images/prio_gelb.gif\"></td>\n";
				elseif ($row[3] == 3)
					echo "									<img src=\"./images/prio_grun.gif\"></td>\n";
				elseif ($row[3] == 5)
					echo "									<img src=\"./images/prio_grau_off.gif\"></td>\n";
				else
					echo "									<img src=\"./images/prio_grau_on.gif\"></td>\n";
				
			}
			
			echo "						</tbody>\n";
			echo "					</table>\n";
			
			echo "				</td>\n";
			echo "			</tr>\n";
			echo "		</table>\n";
		}
		
		/*
		* +-------------------------------------------+
		* | Show Network Intrusion Detection Entry	  |
		* +-------------------------------------------+
		* | Last Change : 27.05.2002       			  |
		* +-------------------------------------------+
		* | Status : Enabled                   		  |
		* +-------------------------------------------+
		*/
		function show_nidslog($section, $section2, $section3)
		{
			switch($section3)
			{
				case 'SUMMARY':
				{
					$result = mysql_query("SELECT COUNT(event.cid), MIN(event.timestamp), MAX(event.timestamp) FROM event");
					$result2 = mysql_query("SELECT DISTINCT signature FROM event");
					$result3 = mysql_query("SELECT ip_src FROM iphdr GROUP BY ip_src");
					$result4 = mysql_query("SELECT ip_dst FROM iphdr GROUP BY ip_dst");
					
					if ($result != 0 and mysql_num_rows($result) != 0)
						$row = mysql_fetch_row($result);
					else
						$row = array("-","-","-");
					
					if($result2 != 0 and mysql_num_rows($result2) != 0)
						$tot_sig = mysql_num_rows($result2);
					else
						$tot_sig = 0;
					
					if($result3 != 0 and mysql_num_rows($result3) != 0)
						$tot_dip = mysql_num_rows($result3);
					else
						$tot_dip = 0;
					
					if($result4 != 0 and mysql_num_rows($result4) != 0)
						$tot_sip = mysql_num_rows($result4);
					else
						$tot_sip = 0;
					
					mysql_free_result($result);
					mysql_free_result($result2);
					mysql_free_result($result3);
					mysql_free_result($result4);
					
					echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
					echo "			<tr valign=\"top\">\n";
					echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
					echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
					echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
					echo " 	  				".$section2." &nbsp;(".$section3.")</td>\n";
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
					
					echo "					<TABLE cellSpacing=1 cellPadding=0 width=\"360\" border=0>\n";
					echo "						<TBODY>\n";
					echo "							<TR bgcolor=\"#565656\">\n";
					echo "								<TD vAlign=bottom align=left width=\"200\" height=\"22\"><FONT color=#ffffff>&nbsp;SUMMARY</font>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"200\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"160\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"160\" border=0></TD>\n";
					echo "							</TR>\n";
					
					echo "							<TR bgColor=\"#d5d5d5\">\n";
					echo "								<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;TOTAL LOGGED EVENTS</TD>\n";
					echo "								<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;$row[0]</td>\n";
					echo "							</tr>\n";
					
					echo "							<TR bgColor=\"#d5d5d5\">\n";
					echo "								<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;STARTED LOGGING @</TD>\n";
					echo "								<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;$row[1]</td>\n";
					echo "							</tr>\n";
					
					echo "							<TR bgColor=\"#d5d5d5\">\n";
					echo "								<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;LATEST LOGGING @</TD>\n";
					echo "								<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;$row[2]</td>\n";
					echo "							</tr>\n";
					
					echo "							<TR bgColor=\"#d5d5d5\">\n";
					echo "								<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;TOTAL SIGNATURES</TD>\n";
					echo "								<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;$tot_sig [<a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=nidslog&action=signaturelist&navigation=0','signaturelist','525','400','true')\"><font color=\"blue\">LIST</font></a>]</td>\n";
					echo "							</tr>\n";
					
					echo "							<TR bgColor=\"#d5d5d5\">\n";
					echo "								<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;OBSERVED DESTINATION IPs</TD>\n";
					echo "								<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;$tot_dip</td>\n";
					echo "							</tr>\n";
					
					echo "							<TR bgColor=\"#d5d5d5\">\n";
					echo "								<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;OBSERVED SOURCE IPs</TD>\n";
					echo "								<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;$tot_sip</td>\n";
					echo "							</tr>\n";
					
					$result5 = mysql_query("SELECT interface, hostname FROM sensor");
					for ($i=1;$i<=mysql_num_rows($result5);$i++)
					{
						$row5 = mysql_fetch_array($result5);
						
						echo "						<TR bgColor=\"#d5d5d5\">\n";
						echo "							<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;OBSERVED INTERFACE #$i</TD>\n";
						echo "							<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row5['interface'].": ".$row5['hostname']."</td>\n";
						echo "						</tr>\n";
					}
					
					echo "						</tbody>\n";
					echo "					</table>\n";
					
					echo "				</td>\n";
					echo "			</tr>\n";
					echo "		</table>\n";
					
					break;
				}
				case 'TCP PROBE':
				{
					echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
					echo "			<tr valign=\"top\">\n";
					echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
					echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
					echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
					echo " 	  				".$section2." &nbsp;(".$section3.")</td>\n";
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
					
					echo "					<TABLE cellSpacing=1 cellPadding=0 width=575 border=0>\n";
					echo "						<TBODY>\n";
					echo "							<TR class=tablehead bgColor=#565656>\n";
					echo "								<TD vAlign=bottom align=left width=\"50\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"50\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"40\" height=\"22\"><FONT color=#ffffff>&nbsp;IFACE</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"40\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"130\" height=\"22\"><FONT color=#ffffff>&nbsp;TIMESTAMP</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"130\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"110\" height=\"22\"><FONT color=#ffffff>&nbsp;SOURCE IP</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"110\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"110\" height=\"22\"><FONT color=#ffffff>&nbsp;DESTINATION IP</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"110\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"55\" height=\"22\"><FONT color=#ffffff>&nbsp;S. PORT</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"55\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"55\" height=\"22\"><FONT color=#ffffff>&nbsp;D. PORT</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"55\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=center width=\"95\" height=\"22\"><FONT color=#ffffff>SIGNATURE</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"95\" border=0></TD>\n";
					echo "							</TR>\n";
					
					$result = mysql_query("SELECT event.sid, event.signature, event.timestamp, iphdr.ip_src, iphdr.ip_dst, tcphdr.tcp_sport, tcphdr.tcp_dport, event.cid FROM event, iphdr, tcphdr WHERE iphdr.sid = event.sid AND iphdr.cid = event.cid AND tcphdr.sid = event.sid AND tcphdr.cid = event.cid ORDER BY event.timestamp DESC LIMIT 10");
					if (mysql_num_rows($result) != 0)
					{
						for ($i = 0; $i < mysql_num_rows($result); $i++)
						{
							$row = mysql_fetch_row($result);
							echo "					<TR bgColor=#d5d5d5>\n";
							echo "						<TD valign=middle align=left height=\"22\">&nbsp;$row[7]</td>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;#$row[0]</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$row[2]</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;".long2ip((double)$row[3])."</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;".long2ip((double)$row[4])."</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$row[5]</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$row[6]</TD>\n";
							echo "						<TD vAlign=middle align=right height=\"22\">$row[1] [<a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=nidslog&action=detail&navigation=0&mid=$row[1]','detail','505','50','true')\"><font color=\"blue\">detail</font>]&nbsp;&nbsp;</TD>\n";
							echo "					</TR>\n";
						}
					}
					else
					{
						echo "					<TR bgColor=#d5d5d5>\n";
						echo "						<TD vAlign=middle align=left height=\"22\" colspan=\"8\">Nothing there!</TD>\n";
						echo "					</TR>\n";
					}
					mysql_free_result($result);
					
					echo "						</tbody>\n";
					echo "					</table>\n";
					echo "				</td>\n";
					echo "			</tr>\n";
					echo "		</table>\n";
					
					break;
				}
				case 'UDP PROBE':
				{
					echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
					echo "			<tr valign=\"top\">\n";
					echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
					echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
					echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
					echo " 	  				".$section2." &nbsp;(".$section3.")</td>\n";
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
					
					echo "					<TABLE cellSpacing=1 cellPadding=0 width=575 border=0>\n";
					echo "						<TBODY>\n";
					echo "							<TR class=tablehead bgColor=#565656>\n";
					echo "								<TD vAlign=bottom align=left width=\"50\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"50\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"40\" height=\"22\"><FONT color=#ffffff>&nbsp;IFACE</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"40\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"130\" height=\"22\"><FONT color=#ffffff>&nbsp;TIMESTAMP</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"130\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"110\" height=\"22\"><FONT color=#ffffff>&nbsp;SOURCE IP</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"110\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"110\" height=\"22\"><FONT color=#ffffff>&nbsp;DESTINATION IP</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"110\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"55\" height=\"22\"><FONT color=#ffffff>&nbsp;S. PORT</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"55\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"55\" height=\"22\"><FONT color=#ffffff>&nbsp;D. PORT</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"55\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=center width=\"95\" height=\"22\"><FONT color=#ffffff>SIGNATURE</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"95\" border=0></TD>\n";
					echo "							</TR>\n";
					
					$result = mysql_query("SELECT event.sid, event.signature, event.timestamp, iphdr.ip_src, iphdr.ip_dst, udphdr.udp_sport, udphdr.udp_dport, event.cid FROM event, iphdr, udphdr WHERE iphdr.sid = event.sid AND iphdr.cid = event.cid AND udphdr.sid = iphdr.sid AND udphdr.cid = iphdr.cid ORDER BY event.timestamp DESC LIMIT 10");
					if (mysql_num_rows($result) != 0)
					{
						for ($i = 0; $i < mysql_num_rows($result); $i++ )
						{
							$row = mysql_fetch_row($result);
							echo "					<TR bgColor=#d5d5d5>\n";
							echo "						<TD valign=middle align=left height=\"22\">&nbsp;$row[7]</td>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;#$row[0]</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$row[2]</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;".long2ip((double)$row[3])."</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;".long2ip((double)$row[4])."</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$row[5]</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$row[6]</TD>\n";
							echo "						<TD vAlign=middle align=right height=\"22\">$row[1] [<a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=nidslog&action=detail&navigation=0&mid=$row[1]','detail','505','50','true')\"><font color=\"blue\">detail</font>]&nbsp;&nbsp;</TD>\n";
							echo "					</TR>\n";
						}
					}
					else
					{
						echo "					<TR bgColor=#d5d5d5>\n";
						echo "						<TD vAlign=middle align=left height=\"22\" colspan=\"8\">Nothing there!</TD>\n";
						echo "					</TR>\n";
					}
					mysql_free_result($result);
					
					break;
				}
				case 'ICMP PROBE':
				{
					echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
					echo "			<tr valign=\"top\">\n";
					echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
					echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
					echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
					echo " 	  				".$section2." &nbsp;(".$section3.")</td>\n";
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
					
					echo "					<TABLE cellSpacing=1 cellPadding=0 width=575 border=0>\n";
					echo "						<TBODY>\n";
					echo "							<TR class=tablehead bgColor=#565656>\n";
					echo "								<TD vAlign=bottom align=left width=\"50\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"50\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"40\" height=\"22\"><FONT color=#ffffff>&nbsp;IFACE</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"40\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"130\" height=\"22\"><FONT color=#ffffff>&nbsp;TIMESTAMP</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"130\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"110\" height=\"22\"><FONT color=#ffffff>&nbsp;SOURCE IP</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"110\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"110\" height=\"22\"><FONT color=#ffffff>&nbsp;DESTINATION IP</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"110\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"55\" height=\"22\"><FONT color=#ffffff>&nbsp;TYPE</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"55\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"55\" height=\"22\"><FONT color=#ffffff>&nbsp;CODE</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"55\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=center width=\"95\" height=\"22\"><FONT color=#ffffff>SIGNATURE</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"95\" border=0></TD>\n";
					echo "							</TR>\n";
					
					
					$result = mysql_query("SELECT event.sid, event.signature, event.timestamp, iphdr.ip_src, iphdr.ip_dst, icmphdr.icmp_type, icmphdr.icmp_code, event.cid FROM event, iphdr, icmphdr WHERE iphdr.sid = event.sid AND iphdr.cid = event.cid AND icmphdr.sid = iphdr.sid AND icmphdr.cid = iphdr.cid ORDER BY event.timestamp DESC LIMIT 10");
					if (mysql_num_rows($result) != 0)
					{
						for ($i = 0; $i < mysql_num_rows($result); $i++ )
						{
							$row = mysql_fetch_row($result);
							echo "					<TR bgColor=#d5d5d5>\n";
							echo "						<TD valign=middle align=left height=\"22\">&nbsp;$row[7]</td>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;#$row[0]</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$row[2]</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;".long2ip((double)$row[3])."</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;".long2ip((double)$row[4])."</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$row[5]</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$row[6]</TD>\n";
							echo "						<TD vAlign=middle align=right height=\"22\">$row[1] [<a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=nidslog&action=detail&navigation=0&mid=$row[1]','detail','505','50','true')\"><font color=\"blue\">detail</font>]&nbsp;&nbsp;</TD>\n";
							echo "					</TR>\n";
						}
					}
					else
					{
						echo "					<TR bgColor=#d5d5d5>\n";
						echo "						<TD vAlign=middle align=left height=\"22\" colspan=\"8\">Nothing there!</TD>\n";
						echo "					</TR>\n";
					}
					mysql_free_result($result);
					
					break;
				}
				case 'ATTACK STATISTIC':
				{
					echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
					echo "			<tr valign=\"top\">\n";
					echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
					echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
					echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
					echo " 	  				".$section2." &nbsp;(".$section3.")</td>\n";
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
					
					echo "					<TABLE cellSpacing=1 cellPadding=0 width=680 border=0>\n";
					echo "						<TBODY>\n";
					echo "							<TR class=tablehead bgColor=#565656>\n";
					echo "								<TD vAlign=bottom align=left width=\"55\" height=\"22\"><FONT color=#ffffff>&nbsp;AMOUNT</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"55\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"75\" height=\"22\"><FONT color=#ffffff>&nbsp;SIGNATURE</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"75\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"400\" height=\"22\"><FONT color=#ffffff>&nbsp;TYPE OF ATTACK</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"400\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;LATEST TIMESTAMP</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
					echo "							</TR>\n";
					
					$result = mysql_query("SELECT event.signature, COUNT(event.cid) as tot_id ,MAX(event.timestamp), signature.sig_name, signature.sig_class_id, signature.sig_priority, signature.sig_rev, signature.sig_sid FROM event, signature WHERE signature.sig_id = event.signature GROUP BY event.signature ORDER BY tot_id DESC LIMIT 30");
					if ($result != 0)
					{
						for ($i = 0; $i < mysql_num_rows($result); $i++ )
						{
							$row = mysql_fetch_row($result);
							echo "					<TR bgColor=#d5d5d5>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$row[1]</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$row[0]</TD>\n";
							
							if (strlen($row[3]) > 50)
								$output = substr($row[3],0,50)." ... [<a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=nidslog&action=more&navigation=0&mid=$row[7]','more','505','50','true')\"><font color=\"blue\">more</font>]";
							else
								$output = $row[3];
							
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$output</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$row[2]</TD>\n";
							echo "					</TR>\n";
						}
					}
					else
					{
						echo "					<TR bgColor=#d5d5d5>\n";
						echo "						<TD vAlign=middle align=left width=\"200\" height=\"22\" colspan=\"5\">Nothing there!</TD>\n";
						echo "					</TR>\n";
					}
					mysql_free_result($result);
					
					break;
				}
				case 'SUSPICIOUS IPs':
				{
					echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
					echo "			<tr valign=\"top\">\n";
					echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
					echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
					echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
					echo " 	  				".$section2." &nbsp;(".$section3.")</td>\n";
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
					
					echo "					<TABLE cellSpacing=1 cellPadding=0 width=700 border=0>\n";
					echo "						<TBODY>\n";
					echo "							<TR class=tablehead bgColor=#565656>\n";
					echo "								<TD vAlign=bottom align=left width=\"55\" height=\"22\"><FONT color=#ffffff>&nbsp;AMOUNT</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"55\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"110\" height=\"22\"><FONT color=#ffffff>&nbsp;SOURCE IP</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"110\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"110\" height=\"22\"><FONT color=#ffffff>&nbsp;DESTINATION IP</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"110\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"75\" height=\"22\"><FONT color=#ffffff>&nbsp;SIGNATURE</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"75\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"80\" height=\"22\"><FONT color=#ffffff>&nbsp;FREQUENCY</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"80\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"135\" height=\"22\"><FONT color=#ffffff>&nbsp;FIRST TIMESTAMP</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"135\" border=0></TD>\n";
					echo "								<TD vAlign=bottom align=left width=\"135\" height=\"22\"><FONT color=#ffffff>&nbsp;LATEST TIMESTAMP</FONT>\n";
					echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"135\" border=0></TD>\n";
					echo "							</TR>\n";
					
					//$result = mysql_query("SELECT iphdr.ip_src, iphdr.ip_dst, COUNT(iphdr.cid) as total, event.signature, MAX(event.timestamp), MIN(event.timestamp), UNIX_TIMESTAMP(MAX(event.timestamp)) - UNIX_TIMESTAMP(MIN(event.timestamp)) FROM iphdr,event WHERE event.sid = iphdr.sid AND event.cid = iphdr.cid GROUP BY iphdr.ip_src,event.signature ORDER BY total DESC LIMIT 30");
					$result = mysql_query("SELECT iphdr.ip_src, iphdr.ip_dst, COUNT(iphdr.cid) as total, event.signature, MAX(event.timestamp), MIN(event.timestamp), UNIX_TIMESTAMP(MAX(event.timestamp)) - UNIX_TIMESTAMP(MIN(event.timestamp)) FROM iphdr,event WHERE event.sid = iphdr.sid AND event.cid = iphdr.cid GROUP BY iphdr.ip_src,event.signature ORDER BY total DESC LIMIT 30");
					if ($result !=0 )
					{
						for ($i = 0; $i < mysql_num_rows($result); $i++ )
						{
							$row = mysql_fetch_row($result);
							echo "					<TR bgColor=#d5d5d5>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$row[2]</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;".long2ip((double)($row[0]))."</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;".long2ip((double)($row[1]))."</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$row[3] [<a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=nidslog&action=detail&navigation=0&mid=$row[3]','detail','505','50','true')\"><font color=\"blue\">detail</font>]</TD>\n";
							
							if (strlen(round((($row[3] / $row[6])),4)) < 6)
							{
								if (round((($row[3] / $row[6])),4) == 0)
									$var = "0.0000";
								else
									$var = round((($row[3] / $row[6])),4).substr("000000",strlen(round((($row[3] / $row[6])),4))-1,6-strlen(round((($row[3] / $row[6])),4)));
							}
							else
							{
								$var = round((($row[3] / $row[6])),4);
							}
							
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;".$var." attps</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$row[5]</TD>\n";
							echo "						<TD vAlign=middle align=left height=\"22\">&nbsp;$row[4]</TD>\n";
							echo "					</TR>\n";
						}
					}
					else
					{
						echo "					<TR bgColor=#d5d5d5>\n";
						echo "						<TD vAlign=middle align=left width=\"200\" height=\"22\" colspan=\"5\">Nothing there!</TD>\n";
						echo "					</TR>\n";
					}
					mysql_free_result($result);
					
					break;
				}
			}
			/*
			
			

			
			echo "						</tbody>\n";
			echo "					</table>\n";
			
			echo "					<br><br><br>";
			
			echo "					<TABLE cellSpacing=1 cellPadding=0 width=650 border=0>\n";
			echo "						<TBODY>\n";
			echo "							<TR class=tablehead bgColor=#565656>\n";
			echo "								<TD vAlign=bottom align=left width=\"200\" height=\"22\"><FONT color=#ffffff>&nbsp;REPORTS</FONT>\n";
			echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"200\" border=0></TD>\n";
			echo "								<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;STARTED @</FONT>\n";
			echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
			echo "								<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;SOURCE IP</FONT>\n";
			echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
			echo "								<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;LAST RECORDED TIMESTAMP</FONT>\n";
			echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
			echo "								<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;SIGNATURE</FONT>\n";
			echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
			echo "								<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;FREQUENCY</FONT>\n";
			echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
			echo "							</TR>\n";
			
			//$result = mysql_query("SELECT event.signature,MIN(event.timestamp),MAX(event.timestamp),iphdr.ip_src,COUNT(iphdr.cid) as total, UNIX_TIMESTAMP(MAX(event.timestamp))-UNIX_TIMESTAMP(MIN(event.timestamp)) FROM event,iphdr WHERE iphdr.ip_dst = $c00lip AND event.sid = iphdr.sid AND event.cid=iphdr.cid GROUP BY iphdr.ip_src,event.signature ORDER BY total DESC LIMIT 30");
			//$result = mysql_query("SELECT event.signature,MIN(event.timestamp),MAX(event.timestamp),iphdr.ip_src,COUNT(iphdr.cid) as total, UNIX_TIMESTAMP(MAX(event.timestamp))-UNIX_TIMESTAMP(MIN(event.timestamp)) FROM event,iphdr WHERE event.sid = iphdr.sid AND event.cid=iphdr.cid GROUP BY iphdr.ip_src,event.signature ORDER BY total DESC LIMIT 30");
			$result = mysql_query("SELECT signature.sig_name,MIN(event.timestamp),MAX(event.timestamp),iphdr.ip_src,COUNT(iphdr.cid) as total, UNIX_TIMESTAMP(MAX(event.timestamp))-UNIX_TIMESTAMP(MIN(event.timestamp)) FROM event,iphdr,signature WHERE event.sid = iphdr.sid AND event.cid=iphdr.cid AND event.signature=signature.sig_id GROUP BY iphdr.ip_src,event.signature ORDER BY total DESC LIMIT 30");
			if ($result != 0)
			{
				for ($i = 0; $i < mysql_num_rows($result); $i++ )
				{
					$row = mysql_fetch_row($result);
					//$freq = $row[1] / $row[2];
					echo "					<TR bgColor=#d5d5d5>\n";
					echo "						<TD vAlign=middle align=left width=\"200\" height=\"22\">&nbsp;$row[4]</TD>\n";
					echo "						<TD vAlign=middle align=left width=\"150\" height=\"22\">&nbsp;$row[1]</TD>\n";
					echo "						<TD vAlign=middle align=left width=\"100\" height=\"22\">&nbsp;".long2ip($row[3])."</TD>\n";
					echo "						<TD vAlign=middle align=left width=\"100\" height=\"22\">&nbsp;$row[2]</TD>\n";
					echo "						<TD vAlign=middle align=left width=\"100\" height=\"22\">&nbsp;$row[0]</TD>\n";
					echo "						<TD vAlign=middle align=left width=\"100\" height=\"22\">&nbsp;$freq</TD>\n";
					echo "					</TR>\n";
				}
			}
			else
			{
				echo "					<TR bgColor=#d5d5d5>\n";
				echo "						<TD vAlign=middle align=left width=\"200\" height=\"22\" colspan=\"6\">Nothing there!</TD>\n";
				echo "					</TR>\n";
			}
			mysql_free_result($result);
			*/

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
			
			show_tbf($section, $section2, $tablename);
		}
		
?>