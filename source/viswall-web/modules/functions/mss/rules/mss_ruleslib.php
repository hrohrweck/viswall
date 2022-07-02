<?php
		///////////////////////////////////////////////////////
		// --> DOMedia <--> 2001/02 <--> vis|wall <--  //
		///////////////////////////////////////////////////////
		//																//
		// MainGroup   : Interface                             //
		//																//
		// Name			: Module - MSS                        //
		// Date			: 06.03.2002							//
		// Comment  	: Filename rules 						//
		//																//
		///////////////////////////////////////////////////////
		
		
		// -------------------------------------
		// | Show rules Entry (Sub,Main)    |
		// -------------------------------------
		// | Last Change : 06.03.2002       |
		// -------------------------------------
		// | Status : Enabled                   |
		// -------------------------------------
		function show_rules($section, $section2, $tablename)
		{
			$result = mysql_query("select * from ".$tablename."") or die(mysql_error());
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
			echo "					<table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"672px\" height=\"\">\n";
			echo "						<tr bgcolor=\"#565656\" class=\"tablehead\">\n";
			echo "							<td valign=\"bottom\" align=\"center\" width=\"55\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;ACTION&nbsp;</font>\n";
			echo "								<img src=\"images/border_orange.gif\" width=\"55\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"center\" width=\"210\" height=\"22\">\n";
			echo "   								<font color=\"#ffffff\">&nbsp;EXPRESSION&nbsp;</font>\n";
			echo "   								<img src=\"images/border_orange.gif\" WIDTH=\"210\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"center\" width=\"165\" height=\"22\">\n\n";
			echo "   								<font color=\"#ffffff\">&nbsp;LOG TEXT</font>\n";
			echo "  								<img src=\"images/border_orange.gif\" WIDTH=\"165\" height=\"6\" border=\"0\"></td>\n";
			echo "  							<td valign=\"bottom\" align=\"center\" width=\"165\" height=\"22\">\n";
			echo "  								<font color=\"#ffffff\">&nbsp;USER NOTIFY TEXT</font>\n";
			echo "  								 <img src=\"images/border_orange.gif\" WIDTH=\"165\" height=\"6\" border=\"0\"></td>\n";
            echo "							<td valign=\"bottom\" align=\"center\" width=\"95\" height=\"22\">\n";
			echo "								<font color=\"#ffffff\">&nbsp;ADMINISTRATE&nbsp;</font>\n";
			echo "								<img src=\"images/border_orange.gif\" width=\"95\" height=\"6\" border=\"0\"></td>\n";
			echo " 						</tr>\n";
			
			if($number==0)
			{
				echo "						<tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
				echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;</td>";
				echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">&nbsp;empty</td>";
				echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">&nbsp;</td>";
                echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">&nbsp;</td>";
				echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;";
				echo "							<a href=\"".$PHP_SELF."?module=".$section."&action=addrule\"><IMG SRC=\"images/add_entry_gr.gif\" BORDER=\"0\ ALT=\"add rule\"></a></td>";
			}
			else
			{
                //Main part
                for($i=0;$i<$number;$i++)
                {
                    $row=mysql_fetch_array($result);
                    echo "						<tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
                    echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">";
                    parseaction($section, $row['action'], $row['id']);
                    echo "                            </td>";
                    echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">";
                    parseexpr($section, $row['expr'], $row['id']);
                    echo "                            </td>";
                    echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">";
                    
                   if (strlen($row['logtxt']) > 25)
                   {
                       echo "&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=changelogtxt&id=".$row['id']."\">".substr($row['logtxt'],0,24)." ...</a>";
                   }
                   else
                   {
                       echo "&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=changelogtxt&id=".$row['id']."\">".$row['logtxt']."&nbsp;</a>";
                   }
                   
                    echo "</td>";
                    echo "							<td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">";
                    
                   if (strlen($row['usertext']) > 25)
                   {
                       echo "&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=changeusertext&id=".$row['id']."\">".substr($row['usertext'],0,24)." ...</a>";
                   }
                   else
                   {
                       echo "&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=changeusertext&id=".$row['id']."\">".$row['usertext']."&nbsp;</a>";
                   }                    
                    echo "</td>";
                    echo "							<td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">";
                    echo "							<a href=\"".$PHP_SELF."?module=".$section."&action=addrule\"><IMG SRC=\"./images/neu.gif\" BORDER=\"0\ ALT=\"add rule\"></a>&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=delrule&id=".$row['id']."\"><IMG SRC=\"images/icons/delete.gif\" BORDER=\"0\ ALT=\"delete rule\"></a></td>";
                }
			}
			echo "					<tr bgcolor=\"#565656\">\n";
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
			echo "					</tr>\n";
			echo "					<tr>\n";
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
        
		// ----------------------------
        // | parseaction (Sub)		  |
        // ----------------------------
        // | Last Change : 07.03.2002 |
        // ----------------------------
        // | Status : Enabled		  |
        // ----------------------------
		function parseaction($section, $string, $id)
		{
            if ($string==1)
			{
				echo "								&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=setstatus&id=".$id."&field=status\"><IMG SRC=\"images/icons/pass.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"on\"></a>&nbsp;</td>";
			}
			else
			{
				echo "							    &nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=setstatus&id=".$id."&field=status\"><IMG SRC=\"images/icons/drop.gif\" WIDTH=\"16\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"off\"></a>&nbsp;</td>";
			}
		}
        
        // -------------------------------------
        // | parseexpr (Sub)                    |
        // -------------------------------------
        // | Last Change : 07.03.2002       |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------	
		function parseexpr($section, $string)
		{
            /*if(substr($string, 0, 1)==chr(92))
            {
                $reststr=substr($string, 1);
                $finstr="*".$reststr;
                echo "&nbsp;\"".$finstr."\"&nbsp;";
            }
            else
            {*/
                echo "&nbsp;\"".$string."\"&nbsp;";                
            //}
		}
        
        // -------------------------------------
        // | add rule (Main)                     |
        // -------------------------------------
        // | Last Change : 06.03.2002       |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------		
		function addrule($section, $section2, $tablename, $status)
		{
            if($status!="updatedb")
            {
                echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
                echo "			<tr valign=\"top\">\n";
                echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
                echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                echo " 	  				".$section2." (add rule) &nbsp;</td>\n";
                echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
                echo "			</tr>\n";
                echo "		</table>\n";
                
                echo "		<form method=\"post\" action=\"".$GLOBALS['PHP_SELF']."?module=".$section."&action=addrule\" name=\"submitform\">";
                echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
                echo "			<tr>\n";
                echo "				<td height=\"20px\" colspan=\"2\">\n";
                echo "					<img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
                echo "			</tr>\n";
                echo "			<tr>\n";
                echo "				<td align=\"left\" width=\"40px\">\n";
                echo "					<img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
                echo "				<td align=\"left\">\n";
				
                echo "<TABLE cellSpacing=1 cellPadding=0 width=\"260\" border=0>\n";
                echo "<TBODY>\n";
                echo "<TR bgcolor=\"#565656\">\n";
                echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
                echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
                echo "<TD vAlign=bottom align=left width=\"200\" height=\"22\"><FONT color=#ffffff>&nbsp;</font>\n";
                echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"200\" border=0></TD>\n";
                echo "<TD vAlign=bottom align=left width=\"30\" height=\"22\"><FONT color=#ffffff></font>\n";
                echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"30\" border=0></TD>\n";
                echo "</TR>\n";
                        
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;EXPRESSION</TD>\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=\"text\" name=\"regexp\" size=\"30\" maxlength=\"255\">&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";			
                echo "</TR>\n";
                            
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ACTION</TD>\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=\"radio\" value=\"0\" name=\"aktion\" size=\"30\" checked>DENY&nbsp;<input type=\"radio\" value=\"1\" name=\"aktion\" size=\"30\">ALLOW&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font>\n";			
                echo "</TR>\n";
                            
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;LOG FILE TEXT</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=\"text\" name=\"logtxt\" size=\"20\" maxlength=\"255\">&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";						
                echo "</TR>\n";
                
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;USER NOTIFICATION TEXT</TD>\n";
                echo "<TD vAlign=middle	 align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=\"text\" name=\"usertext\" size=\"30\">&nbsp;</TD>\n";
                echo "<TD vAlign=bottom align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";			
                echo "</TR>\n";
                
                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
                echo "<input type=\"hidden\" name=\"status\" value=\"updatedb\">";
                echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
                echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
                echo "<a href=\"".$GLOBALS['PHP_SELF']."?module=".$section."\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
                echo "</TD>\n";
                echo "<td></td>\n";
                echo "</TR>\n";
                            
                echo "					</tbody>\n";						
                echo "					</table>\n";
                echo "				</td>\n";
                echo "			</tr>\n";
                echo "		</table>\n";
                echo "		</form>\n";
                echo "	<br><br><br>\n";
            }
            else // Update Record
            {
                //place for checkroutines
                
                if(($GLOBALS['regexp'])=="")
                {
                    echo "No expression given!<br>";
                    addrule($section, $section2, $tablename);
                }
                if(substr($GLOBALS['regexp'],0,1)=="*")
                {
                    $reststr=substr($GLOBALS['regexp'],1);
                    $GLOBALS['regexp']=chr(92).chr(92).$reststr;
                }
                if(($GLOBALS['logtxt'])=="")
                {
                    $GLOBALS['logtxt']="-"; 
                }
                if(($GLOBALS['usertext'])=="" or ($GLOBALS['usertext'])==" ")
                {
                    $GLOBALS['usertext']="-"; 
                }
                //chek if we had to create an new entry
                $resultchk=mysql_query("SELECT id FROM ".$tablename." where expr='".$GLOBALS['regexp']."'");
                $rowchk=mysql_fetch_array($resultchk);
                if($rowchk['id']=="")
                {
                    $query="INSERT INTO ".$tablename." (action,expr,logtxt,usertext) VALUES ('".$GLOBALS['aktion']."', '".$GLOBALS['regexp']."', '".$GLOBALS['logtxt']."', '".$GLOBALS['usertext']."')";
                    $result=mysql_query($query) or die(mysql_error());
                }
                else
                {
                    echo "similar rule already present!<br>";
                }
                show_rules($section, $section2, $tablename);
                }
        }
		
        
        // -------------------------------------
        // | del rule (Main)                     |
        // -------------------------------------
        // | Last Change : 07.03.2002       |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------	
        function delrule($section, $section2, $tablename, $id)
		{
            $result=mysql_query("DELETE FROM ".$tablename." WHERE id='".$id."'") or die(mysql_error());
            show_rules($section, $section2, $tablename);
		}
        
        // -------------------------------------
        // | set status (Main)                   |
        // -------------------------------------
        // | Last Change : 07.03.2002       |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------		
		function setstatus($section, $section2, $tablename, $id)
		{
            $result=mysql_query("SELECT action FROM ".$tablename." where id='".$id."'");
            $row=mysql_fetch_array($result);
            
            if($row['action']==0)
            {
                $resultchange=mysql_query("UPDATE ".$tablename." SET action='1' WHERE id='".$id."'") or die(mysql_error());
                show_rules($section, $section2, $tablename);
            }
            else
            {
                $resultchange=mysql_query("UPDATE ".$tablename." SET action='0' WHERE id='".$id."'") or die(mysql_error());
                show_rules($section, $section2, $tablename);
            }
		}
        
        // -------------------------------------
        // | change text (Sub)                 |
        // -------------------------------------
        // | Last Change : 07.03.2002       |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------		
		function changetext($section, $section2, $tablename, $id, $field, $status)
		{
            if($status!="updatedb")
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
                echo "		<form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=change".$field."\" name=\"submitform\">";
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
                echo "								<TD vAlign=bottom align=left width=\"180\" height=\"22\"><FONT color=#ffffff>&nbsp;ID</font>\n";
                echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"180\" border=0></TD>\n";
                echo "								<TD vAlign=bottom align=left width=\"260\" height=\"22\"><FONT color=#ffffff>&nbsp;".$id."</font>\n";
                echo "									<IMG height=6 src=\"./images/border_orange.gif\" width=\"260\" border=0></TD>\n";
                echo "							</TR>\n";
                echo "							<TR bgcolor=\"#d5d5d5\">";
                if($field=="logtext")
                {
                    $field2="LOG FILE TEXT";
                }
                elseif($field=="usertext")
                {
                    $field2="USER NOTIFICATION TEXT";
                }
                echo "								<TD vAlign=middle align=left width=\"80\" height=\"22\">&nbsp;".$field2."\n";
                echo "								</TD>";
                echo "								<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                $result = mysql_query("select ".$field." from ".$tablename." where id='".$id."'");
                $row = mysql_fetch_array($result);
                echo "&nbsp;<input type=\"text\" name=\"option\" value=\"".$row[$field]."\" size=\"40\" maxlength=\"255\">";
                echo "</td>\n";
                echo "<tr bgcolor=\"#d5d5d5\">\n";
                echo "<td align=\"right\" colspan=\"2\">\n";
                echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\">\n";
                echo "<input type=\"hidden\" value=\"".$field."\" name=\"field\">\n";
                echo "<input type=\"hidden\" name=\"status\" value=\"updatedb\">";
                echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
                echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
                echo "<a href=\"".$PHP_SELF."?module=".$section."\"><img src=\"./images/cancel.gif\" border=\"0\"></a>&nbsp;\n";				
                echo "								</td>\n";
                echo "							</tr>\n";
                echo "					</table>\n";
                echo "			</tr>\n";
                echo "		</table>\n";
            }
            elseif($status=="updatedb")
            {
                if(($GLOBALS['option'])=="")
                {
                    $GLOBALS['option']="-";
                }
                $result=mysql_query("UPDATE ".$tablename." SET ".$field."='".$GLOBALS['option']."' WHERE id='".$id."'") or die (mysql_error());
                show_rules($section, $section2, $tablename);
            }
		}
?>