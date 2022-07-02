<?php
		/////////////////////////////////////////////////
		// --> DOMedia <--> 2001/02 <--> vis|wall <--  //
		/////////////////////////////////////////////////
		//											   //
		// MainGroup   : Interface                     //
		//											   //
		// Name			: Module - Squid (General)         //
		// Date			: 18.02.2002							//
		// Comment  	: Squid Functions 					//
		//																//
		///////////////////////////////////////////////////////
		  
		/*
		* +-------------------------------------------+
		* | Edit Squid Entry								|
		* +-------------------------------------------+
		* | Last Change : 25.02.2002       			|
		* +-------------------------------------------+
		* | Status : Enabled                   			|
		* +-------------------------------------------+
		*/
		function edit_squid($section, $section2, $tablename, $sid)
		{
			# Open Database #
			#echo "select * from ".$tablename." where(id='".$sid."')";
			#$result = mysql_query("select * from ".$tablename." where(id='".$sid."')");
			$result = mysql_query("select * from ".$tablename." where id=0");
			$number = mysql_num_rows($result);
			
			# Read and Display Database Entries #
			$row = mysql_fetch_array($result);
			
			# Check if Information is already submitted #
			if (!isset($GLOBALS['rsubmit']))
			{
				echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
				echo "			<tr valign=\"top\">\n";
				echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
				echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo " 	  				".$section2." | <i>proxy_	settings</i> &nbsp;</td>\n";
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
				
				echo "<TABLE cellSpacing=1 cellPadding=0 width=\"480\" border=0>\n";
				echo "<TBODY>\n";
				echo "<TR bgcolor=\"#565656\">\n";
				echo "<TD vAlign=bottom align=left width=\"200\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"200\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=left width=\"250\" height=\"22\"><FONT color=#ffffff>&nbsp;".$id."</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"250\" border=0></TD>\n";
				echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font>\n";
				echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"25\" border=0></TD>\n";
				echo "</TR>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;HTTP PORT</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"http_port\" value=\"".$row['http_port']."\">\n";
				echo "<br>\n</td>\n";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ICP PORT</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"icp_port\" value=\"".$row['icp_port']."\">\n";
				echo "<br>\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;HTCP PORT</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"htcp_port\" value=\"".$row['htcp_port']."\">\n";
				echo "<br>\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\" colspan=\"3\">&nbsp;</TD></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;TCP OUTGOING ADDRESS</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"tcp_outgoing_address\" value=\"".$row['tcp_outgoing_address']."\">\n";
				echo "<br>\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;UDP OUTGOING ADDRESS</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"udp_outgoing_address\" value=\"".$row['udp_outgoing_address']."\">\n";
				echo "<br>\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;UDP INCOMING ADDRESS</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"udp_incoming_address\" value=\"".$row['udp_incoming_address']."\">\n";
				echo "<br>\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\" colspan=\"3\">&nbsp;</TD></tr>\n";
				
				if ($row['cache_mem'] > 1024)
				{
					if ($row['cache_mem'] > 1048576)
					{
						$cmemdiver="1048576";
					}
					else
					{
						$cmemdiver="1024";
					}
				}
				else
				{
					$cmemdiver="1";
				}
				
				$ctest= (int)($row['cache_mem']) / (int)($cmemdiver);
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;CACHE MEMORY</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"cache_mem\" value=\"".$ctest."\">\n";

				echo "<select name=\"cache_mem_divider\">\n";
				echo "<option value=\"1\" ".issel($cmemdiver, "1").">byte</option>\n";
				echo "<option value=\"1024\" ".issel($cmemdiver, "1024").">kbyte</option>\n";
				echo "<option value=\"1048576\" ".issel($cmemdiver, "1048576").">mbyte</option>\n";
				echo "</select></td>\n";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";

				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;CACHE SWAP LOW</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"cache_swap_low\" value=\"".$row['cache_swap_low']."\">&nbsp;&nbsp;%\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;CACHE SWAP HIGH</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"cache_swap_high\" value=\"".$row['cache_swap_high']."\">&nbsp;&nbsp;%\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\" colspan=\"3\">&nbsp;</TD></tr>\n";
				
				if ($row['maximum_object_size'] > 1024)
				{
					if ($row['maximum_object_size'] > 1048576)
					{
						$cmemdiver="1048576";
					}
					else
					{
						$cmemdiver="1024";
					}
				}
					else
				{
					$cmemdiver="1";
				}
				
				$ctest2= (int)($row['maximum_object_size']) / (int)($cmemdiver);
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;MAXIMUM OBJECT SIZE</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"maximum_object_size\" value=\"".$ctest2."\">\n";
				echo "<select name=\"maximum_object_size_divider\">\n";
				echo "<option value=\"1\" ".issel($cmemdiver, "1").">byte</option>\n";
				echo "<option value=\"1024\" ".issel($cmemdiver, "1024").">kbyte</option>\n";
				echo "<option value=\"1048576\" ".issel($cmemdiver, "1048576").">mbyte</option>\n";
				echo "</select></td>\n";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				if ($row['minimum_object_size'] > 1024)
				{
					if ($row['minimum_object_size'] > 1048576)
					{
						$cmemdiver="1048576";
					}
					else
					{
						$cmemdiver="1024";
					}
				}
				else
				{
					$cmemdiver="1";
				}
				
				
				$ctest3= (int)($row['minimum_object_size']) / (int)($cmemdiver);
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;MINIMUM OBJECT SIZE</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"minimum_object_size\" value=\"".$ctest3."\">\n";
				echo "<select name=\"minimum_object_size_divider\">\n";
				echo "<option value=\"1\" ".issel($cmemdiver, "1").">byte</option>\n";
				echo "<option value=\"1024\" ".issel($cmemdiver, "1024").">kbyte</option>\n";
				echo "<option value=\"1048576\" ".issel($cmemdiver, "1048576").">mbyte</option>\n";
				echo "</select></td>\n";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				if ($row['maximum_object_size_in_memory'] > 1024)
				{
					if ($row['maximum_object_size_in_memory'] > 1048576)
					{
						$cmemdiver="1048576";
					}
					else
					{
						$cmemdiver="1024";
					}
				}
				else
				{
					$cmemdiver="1";
				}
				
				$ctest4= (int)($row['maximum_object_size_in_memory']) / (int)($cmemdiver);
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;MAXIMUM OBJECT SIZE (MEM)</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"maximum_object_size_in_memory\" value=\"".$ctest4."\">\n";
				echo "<select name=\"maximum_object_size_in_memory_divider\">\n";
				echo "<option value=\"1\" ".issel($cmemdiver, "1").">byte</option>\n";
				echo "<option value=\"1024\" ".issel($cmemdiver, "1024").">kbyte</option>\n";
				echo "<option value=\"1048576\" ".issel($cmemdiver, "1048576").">mbyte</option>\n";
				echo "</select></td>\n";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\" colspan=\"3\">&nbsp;</TD></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ICP QUERY TIMEOUT</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"icp_query_timeout\" value=\"".$row['icp_query_timeout']."\">&nbsp;&nbsp;msec\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;MAXIMUM ICP QUERY TIMEOUT</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"maximum_icp_query_timeout\" value=\"".$row['maximum_icp_query_timeout']."\">&nbsp;&nbsp;usec\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;MULTICAST ICP QUERY TIMEOUT</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"mcast_icp_query_timeout\" value=\"".$row['mcast_icp_query_timeout']."\">&nbsp;&nbsp;usec\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;DEAD PEER TIMEOUT</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"dead_peer_timeout\" value=\"".$row['dead_peer_timeout']."\">&nbsp;&nbsp;sec\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\" colspan=\"3\">&nbsp;</TD></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IPCACHE SIZE</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"ipcache_size\" value=\"".$row['ipcache_size']."\">&nbsp;&nbsp;no. of entries\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IPCACHE LOW (%)</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"ipcache_low\" value=\"".$row['ipcache_low']."\">&nbsp;&nbsp;%\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;IPCACHE HIGH (%)</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"ipcache_high\" value=\"".$row['ipcache_high']."\">&nbsp;&nbsp;%\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;FGDN CACHE SIZE</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<input type=text name=\"fgdn_cache_size\" value=\"".$row['fgdn_cache_size']."\">&nbsp;&nbsp;no. of entries\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\" colspan=\"3\">&nbsp;</TD></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;CACHE REPLACEMENT POLICY</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<select name=\"cache_replacement_policy\">\n";
				echo "<option value=\"0\" ".issel($row['cache_replacement_policy'],0).">LRU</option>\n";
				echo "<option value=\"1\" ".issel($row['cache_replacement_policy'],1).">HEAP GDSF</option>\n";
				echo "<option value=\"2\" ".issel($row['cache_replacement_policy'],2).">HEAP LFUDA</option>\n";
				echo "<option value=\"3\" ".issel($row['cache_replacement_policy'],3).">HEAP LRU</option>\n";
				echo "</select>\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;MEMORY REPLACEMENT POLICY</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
				echo "&nbsp;&nbsp;<select name=\"memory_replacement_policy\">\n";
				echo "<option value=\"0\" ".issel($row['memory_replacement_policy'],0).">LRU</option>\n";
				echo "<option value=\"1\" ".issel($row['memory_replacement_policy'],1).">HEAP GDSF</option>\n";
				echo "<option value=\"2\" ".issel($row['memory_replacement_policy'],2).">HEAP LFUDA</option>\n";
				echo "<option value=\"3\" ".issel($row['memory_replacement_policy'],3).">HEAP LRU</option>\n";
				echo "</select>\n</td>";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\"><FONT color=#000000>?</font></td></tr>\n";
				
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\" colspan=\"3\">&nbsp;</TD></tr>\n";
				
				# Submit Event Data
				echo "<TR bgColor=\"#d5d5d5\">\n";
				echo "<TD vAlign=right align=center width=\"\" height=\"22\" colspan=\"3\">\n";
				echo "<input type=\"hidden\" value=\"".$sid."\" name=\"hiddenid\">\n";
				echo "<input type=\"hidden\" value=\"".$field."\" name=\"hiddenfield\">\n";
				echo "<input type=\"hidden\" name=\"rsubmit\">";
				echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
				echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
				echo "<a href=\"".$PHP_SELF."?module=squid\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
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
				//check routines
				if(($GLOBALS['http_port']=="") or ($GLOBALS['http_port']=="0") or ($GLOBALS['http_port']>="65535") or (is_numeric($GLOBALS['http_port'])==false))
				{
					$GLOBALS['http_port']="3128";
				}
				if(($GLOBALS['icp_port']=="") or ($GLOBALS['icp_port']=="0") or ($GLOBALS['icp_port']>="65535") or (is_numeric($GLOBALS['icp_port'])==false))
				{
					$GLOBALS['icp_port']="3130";
				}
				if(($GLOBALS['htcp_port']=="") or ($GLOBALS['icp_port']=="0") or ($GLOBALS['icp_port']>="65535") or (is_numeric($GLOBALS['htcp_port'])==false))
				{
					$GLOBALS['htcp_port']="4827";
				}
				if(($GLOBALS['cache_mem']=="") or (is_numeric($GLOBALS['cache_mem'])==false))
				{
					$GLOBALS['cache_mem']="8388608";
				}
				if(($GLOBALS['cache_swap_low']=="") or (is_numeric($GLOBALS['cache_swap_low'])==false))
				{
					$GLOBALS['cache_swap_low']="90";
				}
				if(($GLOBALS['cache_swap_high']=="") or (is_numeric($GLOBALS['cache_swap_high'])==false))
				{
					$GLOBALS['cache_swap_high']="95";
				}
				if(($GLOBALS['maximum_object_size']=="") or (is_numeric($GLOBALS['maximum_object_size'])==false))
				{
					$GLOBALS['maximum_object_size']="4194304";
				}
				if(($GLOBALS['minimum_object_size']=="") or (is_numeric($GLOBALS['minimum_object_size'])==false))
				{
					$GLOBALS['minimum_object_size']="0";
				}
				if(($GLOBALS['maximum_object_size_in_memory']=="") or (is_numeric($GLOBALS['maximum_object_size_in_memory'])==false))
				{
					$GLOBALS['maximum_object_size_in_memory']="8388608";
				}
				if(($GLOBALS['icp_query_timeout']=="") or (is_numeric($GLOBALS['icp_query_timeout'])==false))
				{
					$GLOBALS['icp_query_timeout']="500";
				}
				if(($GLOBALS['maximum_icp_query_timeout']=="") or (is_numeric($GLOBALS['maximum_icp_query_timeout'])==false))
				{
					$GLOBALS['maximum_icp_query_timeout']="2000";
				}
				if(($GLOBALS['mcast_icp_query_timeout']=="") or (is_numeric($GLOBALS['maximum_icp_query_timeout'])==false))
				{
					$GLOBALS['mcast_icp_query_timeout']="2000";
				}
				if(($GLOBALS['dead_peer_timeout']=="") or (is_numeric($GLOBALS['dead_peer_timeout'])==false))
				{
					$GLOBALS['dead_peer_timeout']="10";
				}
				if(($GLOBALS['ipcache_size']=="") or (is_numeric($GLOBALS['ipcache_size'])==false))
				{
					$GLOBALS['ipcache_size']="1024";
				}
				if(($GLOBALS['ipcache_low']=="") or (is_numeric($GLOBALS['ipcache_low'])==false))
				{
					$GLOBALS['ipcache_low']="90";
				}
				if(($GLOBALS['ipcache_high']=="") or (is_numeric($GLOBALS['ipcache_high'])==false))
				{
					$GLOBALS['ipcache_high']="95";
				}
				if(($GLOBALS['fgdn_cache_size']=="") or (is_numeric($GLOBALS['fgdn_cache_size'])==false))
				{
					$GLOBALS['fgdn_cache_size']="1024";
				}
				if($GLOBALS['cache_mem_divider']!=1)
				{
					$GLOBALS['cache_mem']= (int)($GLOBALS['cache_mem']) * (int)($GLOBALS['cache_mem_divider']);
				}
				if($GLOBALS['maximum_object_size_divider']!=1)
				{
					$GLOBALS['maximum_object_size']= (int)($GLOBALS['maximum_object_size']) * (int)($GLOBALS['maximum_object_size_divider']);
				}
				if($GLOBALS['minimum_object_size_divider']!=1)
				{
					$GLOBALS['minimum_object_size']=
					$tet = ((int)($GLOBALS['minimum_object_size']) * (int)($GLOBALS['minimum_object_size_divider']));
				}
				if($GLOBALS['maximum_object_size_in_memory_divider']!=1)
				{
					$GLOBALS['maximum_object_size_in_memory']= (int)($GLOBALS['maximum_object_size_in_memory']) * (int)($GLOBALS['maximum_object_size_in_memory_divider']);
				}
				$query="UPDATE ".$tablename." SET http_port='".$GLOBALS[http_port]."',icp_port='".$GLOBALS['icp_port']."',htcp_port='".$GLOBALS['htcp_port']."',tcp_outgoing_address='".$GLOBALS['tcp_outgoing_address']."',udp_outgoing_address='".$GLOBALS['udp_outgoing_address']."',udp_incoming_address='".$GLOBALS['udp_incoming_address']."',cache_mem='".$GLOBALS['cache_mem']."',cache_swap_low='".$GLOBALS['cache_swap_low']."',cache_swap_high='".$GLOBALS['cache_swap_high']."',maximum_object_size='".$GLOBALS['maximum_object_size']."',minimum_object_size='".$GLOBALS['minimum_object_size']."',maximum_object_size_in_memory='".$GLOBALS['maximum_object_size_in_memory']."',icp_query_timeout='".$GLOBALS['icp_query_timeout']."',maximum_icp_query_timeout='".$GLOBALS['maximum_icp_query_timeout']."',mcast_icp_query_timeout='".$GLOBALS['mcast_icp_query_timeout']."',dead_peer_timeout='".$GLOBALS['dead_peer_timeout']."',ipcache_size='".$GLOBALS['ipcache_size']."',ipcache_low='".$GLOBALS['ipcache_low']."',ipcache_high='".$GLOBALS['ipcache_high']."',fgdn_cache_size='".$GLOBALS['fgdn_cache_size']."',cache_replacement_policy='".$GLOBALS['cache_replacement_policy']."',memory_replacement_policy='".$GLOBALS['memory_replacement_policy']."' WHERE id='".$GLOBALS['hiddenid']."'";
				$result=mysql_query($query) or die(mysql_error());
				show_squid($section, $section2, $tablename);
			}
		}
		
		/*
		* +-------------------------------------------+
		* | Show Squid Entry							|
		* +-------------------------------------------+
		* | Last Change : 22.02.2002       			|
		* +-------------------------------------------+
		* | Status : Enabled                   			|
		* +-------------------------------------------+
		*/
		function show_squid($section, $section2, $tablename)
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
			
			echo "<TABLE cellSpacing=1 cellPadding=0 width=700 border=0>\n";
			echo "<TBODY>\n";
			echo "<TR class=tablehead bgColor=#565656>\n";
			echo "<TD vAlign=bottom align=left width=\"50\" height=\"22\"><FONT color=#ffffff>&nbsp;STATUS</FONT>\n";
			echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"50\" border=0></TD>\n";
			echo "<TD vAlign=bottom align=left width=\"250\" height=\"22\"><FONT color=#ffffff>&nbsp;SERVER</FONT>\n";
			echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"250\" border=0></TD>\n";
			echo "<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;HTTP PORT</FONT>\n";
			echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
			echo "<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;ICP PORT</FONT>\n";
			echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
			echo "<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;HTCP PORT</FONT>\n";
			echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
			echo "<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;ADMINISTRATE</FONT>\n";
			echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
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
				
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\">";
				# Select Correct Status
				# ------------------------
				if ($row['status'] == 1)
				{
					# Output Status == 1
					# ------------------
					echo "								&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=setstatus&sid=".$row['id']."&field=status\"><IMG SRC=\"images/icons/on.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"on\"></a>&nbsp;</td>";
				}
				else
				{
					# Output Status == 0
					# ------------------
					echo "							    &nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=setstatus&sid=".$row['id']."&field=status\"><IMG SRC=\"images/icons/off.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"off\"></a>&nbsp;</td>";
				}	
				echo "</TD>\n";
				
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;vis|wall Squid Proxy Server</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['http_port']."</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['icp_port']."</TD>\n";
				echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;".$row['htcp_port']."</TD>\n";
				echo "<TD vAlign=middle align=center width=\"\" height=\"22\">\n";
				echo "&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=edit&sid=".$row['id']."\"><IMG SRC=\"./images/icons/edit_gr.gif\" WIDTH=\"22\" HEIGHT=\"16\" BORDER=0 ALT=\"edit\"></a></TD>\n";
				echo "</TR>\n";
			}
			
			echo "					<tr bgcolor=\"#565656\">\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
			echo "						<a href=\"".$_SERVER['PHP_SELF']."?module=activate&g_module=".$section."&action=activate&params=execute\"><IMG SRC=\"images/activate.gif\" BORDER=\"0\" ALT=\"activate\"></a></td>";			 
			echo "					</tr>\n";
			echo "					</table>\n";
			echo "					</tbody>\n";
			echo "				</td>\n";
			echo "			</tr>\n";
			echo "		</table>\n";
			echo "	<br><br><br>\n";
		}
		
        // -------------------------------------
		// | Change Proxy Status (Sub,Main) |
		// -------------------------------------
		// | Last Change : 08.03.2002       |
		// -------------------------------------
		// | Status : Enabled                   |
		// -------------------------------------
		function status_proxy($section, $section2, $tablename, $id)
		{
			$result = mysql_query("select status from ".$tablename." where (id='".$id."')") or die(mysql_error());
			
			# Get Current Status of Entry
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
			
			show_squid($section, $section2, $tablename);
		}
		
        // -------------------------------------
        // | check if seleceted (Sub,Main)  |
        // -------------------------------------
        // | Last Change : 21.02.2002       |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------
        function issel($suffix, $compstr){
                    if($suffix==$compstr) {
                        return "selected";
                    }
        }		
?>
