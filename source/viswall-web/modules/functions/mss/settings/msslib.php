<?php
        ///////////////////////////////////////////////////////
        // --> DOMedia <--> 2001/02 <--> vis|wall <--  //
        ///////////////////////////////////////////////////////
        //                                                                //
        // MainGroup   : Interface                             //
        //                                                                //
        // Name            : Module - MSS                        //
        // Date            : 26.02.2002                            //
        // Comment      : MailScanning Functions             //
        //                                                                //
        ///////////////////////////////////////////////////////

        // -------------------------------------
        // | show server Entry (Sub,Main) |
        // -------------------------------------
        // | Last Change : 27.02.2002       |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------
        function show_serverinfo($section, $section2, $tablename, $controltable)
        {
            $result = mysql_query("select * from ".$tablename."") or die(mysql_error());
            $number = mysql_num_rows($result);

            echo "        <table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
            echo "            <tr valign=\"top\">\n";
            echo "                <td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
            echo "                    <img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
            echo "                <td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
            echo "                       ".$section2." (".$number.") &nbsp;</td>\n";
            echo "                <td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
            echo "                    <img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
            echo "            </tr>\n";
            echo "        </table>\n";

            echo "        <table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
            echo "            <tr>\n";
            echo "                <td height=\"20px\" colspan=\"2\">\n";
            echo "                    <img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
            echo "            </tr>\n";
            echo "            <tr>\n";
            echo "                <td align=\"left\" width=\"40px\">\n";
            echo "                    <img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
            echo "                <td align=\"left\">";

            # Generate Table-Header #
            echo "                    <table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"672px\" height=\"\">\n";
            echo "                        <tr bgcolor=\"#565656\" class=\"tablehead\">\n";
            echo "                            <td valign=\"bottom\" align=\"left\" width=\"52\" height=\"22\">\n";
            echo "                                <font color=\"#ffffff\">&nbsp;STATUS</font>\n";
            echo "                                <img src=\"images/border_orange.gif\" width=\"52\" height=\"6\" border=\"0\"></td>\n";
            echo "                              <td valign=\"bottom\" align=\"left\" width=\"180\" height=\"22\">\n";
            echo "                                   <font color=\"#ffffff\">&nbsp;SERVER</font>\n";
            echo "                                   <img src=\"images/border_orange.gif\" WIDTH=\"180\" height=\"6\" border=\"0\"></td>\n";
            echo "                              <td valign=\"bottom\" align=\"left\" width=\"120\" height=\"22\">\n\n";
            echo "                                   <font color=\"#ffffff\">&nbsp;POSTMASTER</font>\n";
            echo "                                  <img src=\"images/border_orange.gif\" WIDTH=\"120\" height=\"6\" border=\"0\"></td>\n";
            echo "                              <td valign=\"bottom\" align=\"left\" width=\"110\" height=\"22\">\n\n";
            echo "                                   <font color=\"#ffffff\">&nbsp;VIRUS SCANNING</font>\n";
            echo "                                  <img src=\"images/border_orange.gif\" WIDTH=\"110\" height=\"6\" border=\"0\"></td>\n";
            echo "                              <td valign=\"bottom\" align=\"left\" width=\"105\" height=\"22\">\n\n";
            echo "                                   <font color=\"#ffffff\">&nbsp;SPAM CHECKING</font>\n";
            echo "                                  <img src=\"images/border_orange.gif\" WIDTH=\"105\" height=\"6\" border=\"0\"></td>\n";
            echo "                              <td valign=\"bottom\" align=\"center\" width=\"60\" height=\"22\">\n";
            echo "                                  <font color=\"#ffffff\">ADMINISTRATE</font>\n";
            echo "                                   <img src=\"images/border_orange.gif\" WIDTH=\"120\" height=\"6\" border=\"0\"></td>\n";
            echo "                         </tr>\n";

            if ($number != 0)
            {
                $result=mysql_query("SELECT * FROM ".$tablename."");
                $result_control=mysql_query("SELECT * FROM ".$controltable."");
                $row_control=mysql_fetch_array($result_control);
                $row=mysql_fetch_array($result);

                echo "                        <tr bgcolor=\"#bababa\" valign=\"middle\">";
                echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">";

                # Select Correct Status
                # ------------------------
                if ($row_control['status'] == 1)
                {
                    # Output Status == 1
                    # ------------------
                    echo "                                &nbsp;<a href=\"".$GLOBALS['PHP_SELF']."?module=".$section."&action=setstatus&id=".$row['id']."&field=status\"><IMG SRC=\"images/icons/on.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"on\"></a>&nbsp;</td>";
                }
                else
                {
                    # Output Status == 0
                    # ------------------
                    echo "                                &nbsp;<a href=\"".$GLOBALS['PHP_SELF']."?module=".$section."&action=setstatus&id=".$row['id']."&field=status\"><IMG SRC=\"images/icons/off.gif\" WIDTH=\"18\" HEIGHT=\"16\" BORDER=\"0\" ALT=\"off\"></a>&nbsp;</td>";
                }


                echo "                            <td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">";
                echo "                                &nbsp;";
                echo                                $row['hostname'];
                echo "                            </td>";
                echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"mailto:".$row['local_postmaster']."\">".$row['local_postmaster']."</a></td>";
                echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$GLOBALS['PHP_SELF']."?module=".$section."&action=setstatus&id=".$row['id']."&field=virus_scanning\">".is_true($row_control['virus_scanning'])."</a></td>";
                echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$GLOBALS['PHP_SELF']."?module=".$section."&action=setstatus&id=".$row['id']."&field=spam_checking\">".is_true($row_control['spam_checking'])."</a></td>";
                echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$GLOBALS['PHP_SELF']."?module=".$section."&action=editserver&id=".$row['id']."\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</td></tr>";
            }
            else
            {
                echo "                        <tr bgcolor=\"#bababa\" valign=\"middle\">";
                echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"><img src=\"images/icons/off.gif\" border=\"0\"></td>";
                echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">";
                echo "                              Server not configured.</td>";
                echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"></td>";
                echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"></td>";
                echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\"></td>";
                echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$GLOBALS['PHP_SELF']."?module=".$section."&action=editserver\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</td></tr>";
            }

            # Generate table footer
            echo "                    <tr bgcolor=\"#565656\">\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                    </tr>\n";
            echo "                    </table>\n";
            echo "                </td>\n";
            echo "            </tr>\n";
            echo "        </table>\n";
            echo "    <br><br>\n";
            show_extinfo($section);
        }

        // -------------------------------------
        // | print edit HTML (Sub)                  |
        // -------------------------------------
        // | Last Change : 01.03.2002           |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------
        function print_edit_html($section, $section2, $tablename, $field)
        {
            switch ($field)
            {
                case "signopt":
                    if($GLOBALS['updatedb']!="updatedb")
                    {
                        $result=mysql_query("SELECT * FROM ".$tablename."");
                        $row=mysql_fetch_array($result);
                        echo "        <table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
                        echo "            <tr valign=\"top\">\n";
                        echo "                <td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                        echo "                    <img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
                        echo "                <td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                        echo "                       ".$section2." (extended options) &nbsp;</td>\n";
                        echo "                <td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                        echo "                    <img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
                        echo "            </tr>\n";
                        echo "        </table>\n";
                        echo "        <form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=editsettings\" name=\"submitform\">";
                        echo "        <table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
                        echo "            <tr>\n";
                        echo "                <td height=\"20px\" colspan=\"2\">\n";
                        echo "                    <img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
                        echo "            </tr>\n";
                        echo "            <tr>\n";
                        echo "                <td align=\"left\" width=\"40px\">\n";
                        echo "                    <img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
                        echo "                <td align=\"left\">\n";
                        // Check if database entries exists
                        $result_db=mysql_query("SELECT * FROM ".$tablename."");
                        $num_db=mysql_num_rows($result_db);
                        if($num_db==0)
                        {
                            $inline_text_signature="This message has been scanned for viruses and\n dangerous content by vis|wall - MailScanner, and is\n believed to be clean.";
                            $inline_html_signature="<BR>--\n<BR>This message has been scanned for viruses and\n<BR>dangerous content by\n<BR>vis|wall - MailScanner\n<BR>and is believed to be clean.\n<BR>--";
                            $inline_text_warning="Warning: This message has had one or more attachments removed.\nWarning: Please read the \"VirusWarning.txt\" attachment(s) for more information.";
                            $inline_html_warning="<P><B><FONT SIZE=\"+1\" COLOR=\"red\">Warning: </FONT>This message has had one or more attachments removed. Please read the \"VirusWarning.txt\" attachment(s) for more information.</B><BR></P>";
                            $query_db="insert into ".$tablename." (inline_text_signature, inline_html_signature, inline_text_warning, inline_html_warning) VALUES ('".$inline_text_signature."', '".$inline_html_signature."', '".$inline_text_warning."', '".$inline_html_warning."')";
                            $result=mysql_query($query_db) or die (mysql_error());
                        }
                        echo "<TABLE cellSpacing=1 cellPadding=0 width=\"260\" border=0>\n";
                        echo "<TBODY>\n";
                        echo "<TR bgcolor=\"#565656\">\n";
                        echo "<TD vAlign=bottom align=left width=\"200\" height=\"22\"><FONT color=#ffffff>&nbsp;OPTION</font>\n";
                        echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"200\" border=0></TD>\n";
                        echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
                        echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
                        echo "<TD vAlign=bottom align=left width=\"210\" height=\"22\"><FONT color=#ffffff>&nbsp;ACTION</font>\n";
                        echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"210\" border=0></TD>\n";
                        echo "<TD vAlign=bottom align=left width=\"30\" height=\"22\"><FONT color=#ffffff></font>\n";
                        echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"30\" border=0></TD>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;SIGN UNSCANNED MESSAGES</TD>\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                        echo "&nbsp;<input type=\"radio\" name=\"sign_unscanned_messages\" value=\"1\" ".chk_if_selected($tablename, sign_unscanned_messages, 1).">YES&nbsp;<input type=\"radio\" name=\"sign_unscanned_messages\" value=\"0\" ".chk_if_selected($tablename, sign_unscanned_messages, 0).">NO</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"\" height=\"22\">&nbsp;<a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=".$section."&action=popup&field=unscanned_header&navigation=0&type=1', 'unscanned_header', '300', '120', 'false')\">> change header text <</a></TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;SIGN CLEAN MESSAGES</TD>\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                        echo "&nbsp;<input type=\"radio\" name=\"sign_clean_messages\" value=\"1\" ".chk_if_selected($tablename, sign_clean_messages, 1).">YES&nbsp;<input type=\"radio\" name=\"sign_clean_messages\" value=\"0\" ".chk_if_selected($tablename, sign_clean_messages, 0).">NO</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"\" height=\"22\">&nbsp;<a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=".$section."&action=popup&field=inline_text_signature&navigation=0&type=0', 'change_inline_sig', '400', '500', 'false')\">> change inline signature <</a>&nbsp;</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;MARK INFECTED MESSAGES</TD>\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                        echo "&nbsp;<input type=\"radio\" name=\"mark_infected_messages\" value=\"1\" ".chk_if_selected($tablename, mark_infected_messages, 1).">YES&nbsp;<input type=\"radio\" name=\"mark_infected_messages\" value=\"0\" ".chk_if_selected($tablename, mark_infected_messages, 0).">NO</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"\" height=\"22\">&nbsp;<a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=".$section."&action=popup&field=inline_text_warning&navigation=0&type=0', 'change_inline_warning', '400', '500', 'false')\">> change inline warning <</a>&nbsp;</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;MAIL HEADER</TD>\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                        echo "&nbsp;<input type=\"text\" name=\"mail_header\" value=\"".$row['mail_header']."\" size=\"20\"></TD>\n";
                        echo "<TD vAlign=middle align=center width=\"\" height=\"22\">&nbsp;<a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=".$section."&action=popup&field=mail_headers&navigation=0&type=1', 'mail_headers', '400', '160', 'false')\">> change mail header messages <</a>&nbsp;</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;MODIFY SUBJECT IN SPAM MAILS</TD>\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                        echo "&nbsp;<input type=\"radio\" name=\"spam_modify_subject\" value=\"1\" ".chk_if_selected($tablename, spam_modify_subject, 1).">YES&nbsp;<input type=\"radio\" name=\"spam_modify_subject\" value=\"0\" ".chk_if_selected($tablename, spam_modify_subject, 0).">NO</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"\" height=\"22\">&nbsp;&nbsp;</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;SPAM SUBJECT</TD>\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                        echo "&nbsp;<input type=\"text\" name=\"spam_subject_text\" value=\"".$row['spam_subject_text']."\" size=\"20\"></TD>\n";
                        echo "<TD vAlign=middle align=center width=\"\" height=\"22\">&nbsp;&nbsp;</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";
                        
                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<td></td>\n";
                        echo "<td></td>\n";
                        echo "<TD vAlign=middle align=center width=\"\" height=\"22\" colspan=\"2\">\n";
                        echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\" size=\"40\">\n";
                        #echo "<input type=\"hidden\" value=\"".$row['name']."\" name=\"oldhostname\" size=\"40\">\n";
                        echo "<input type=\"hidden\" name=\"updatedb\" value=\"updatedb\">";
                        echo "<input type=\"hidden\" name=\"field\" value=\"signopt\">";
                        #echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
                        echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
                        echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
                        echo "<a href=\"".$PHP_SELF."?module=$section\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
                        echo "</TD>\n";
                        echo "<td></td>\n";
                        echo "</TR>\n";

                        echo "                    </tbody>\n";
                        echo "                    </table>\n";
                        echo "                </td>\n";
                        echo "            </tr>\n";
                        echo "        </table>\n";
                        echo "        </form>\n";
                        echo "    <br><br><br>\n";
                    }
                    else // Update Record
                    {
                            //place for checkroutines
                            if($GLOBALS['mail_header']=="")
                            {
                                $GLOBALS['mail_header']="X-MailScanner:";
                            }
                            if(substr($GLOBALS['mail_header'],-1)!=":")
                            {
                                $GLOBALS['mail_header'].=":";
                            }
							if(is_numeric($GLOBALS['spam_modify_subject'])==false)
							{
								$GLOBALS['spam_modify_subject']="1";
							}
                        $query="UPDATE ".$tablename." SET sign_unscanned_messages='".$GLOBALS['sign_unscanned_messages']."', sign_clean_messages='".$GLOBALS['sign_clean_messages']."', mark_infected_messages='".$GLOBALS['mark_infected_messages']."', mail_header='".$GLOBALS['mail_header']."', clean_header='".$GLOBALS['clean_header']."', infected_header='".$GLOBALS['infected_header']."', disinfected_header='".$GLOBALS['disinfected_header']."', spam_modify_subject='".$GLOBALS['spam_modify_subject']."', spam_subject_text='".$GLOBALS['spam_subject_text']."'";
                        $result=mysql_query($query) or die(mysql_error());
                        show_serverinfo($section, $section2, mss_general, control_mss);
                    }
                    break;
                case "notifyopt":
                    if($GLOBALS['updatedb']!="updatedb")
                    {
                        $result=mysql_query("SELECT * FROM ".$tablename."");
                        $row=mysql_fetch_array($result);
                        echo "        <table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
                        echo "            <tr valign=\"top\">\n";
                        echo "                <td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                        echo "                    <img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
                        echo "                <td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                        echo "                       ".$section2." (extended options) &nbsp;</td>\n";
                        echo "                <td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                        echo "                    <img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
                        echo "            </tr>\n";
                        echo "        </table>\n";
                        echo "        <form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=editsettings\" name=\"submitform\">";
                        echo "        <table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
                        echo "            <tr>\n";
                        echo "                <td height=\"20px\" colspan=\"2\">\n";
                        echo "                    <img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
                        echo "            </tr>\n";
                        echo "            <tr>\n";
                        echo "                <td align=\"left\" width=\"40px\">\n";
                        echo "                    <img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
                        echo "                <td align=\"left\">\n";
                        // Check if database entries exists
                        $result_db=mysql_query("SELECT * FROM ".$tablename."");
                        $num_db=mysql_num_rows($result_db);
                        if($num_db==0)
                        {
                            $query_db="insert into ".$tablename." () VALUES ()";
                            $result=mysql_query($query_db) or die (mysql_error());
                        }
                        echo "<TABLE cellSpacing=1 cellPadding=0 width=\"260\" border=0>\n";
                        echo "<TBODY>\n";
                        echo "<TR bgcolor=\"#565656\">\n";
                        echo "<TD vAlign=bottom align=left width=\"250\" height=\"22\"><FONT color=#ffffff>&nbsp;OPTION</font>\n";
                        echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"250\" border=0></TD>\n";
                        echo "<TD vAlign=bottom align=left width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;VALUE</font>\n";
                        echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
                        echo "<TD vAlign=bottom align=left width=\"30\" height=\"22\"><FONT color=#ffffff></font>\n";
                        echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"30\" border=0></TD>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTIFY SENDER</TD>\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                        echo "&nbsp;<input type=\"radio\" name=\"notify_senders\" value=\"1\" ".chk_if_selected($tablename, notify_senders, 1).">YES&nbsp;<input type=\"radio\" name=\"notify_senders\" value=\"0\" ".chk_if_selected($tablename, notify_senders, 0).">NO</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;NOTIFY LOCAL POSTMASTER</TD>\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                        echo "&nbsp;<input type=\"radio\" name=\"notify_local_postmaster\" value=\"1\" ".chk_if_selected($tablename, notify_local_postmaster, 1).">YES&nbsp;<input type=\"radio\" name=\"notify_local_postmaster\" value=\"0\" ".chk_if_selected($tablename, notify_local_postmaster, 0).">NO</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;POSTMASTER GETS FULL HEADER</TD>\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                        echo "&nbsp;<input type=\"radio\" name=\"postmaster_gets_full_header\" value=\"1\" ".chk_if_selected($tablename, postmaster_gets_full_header, 1).">YES&nbsp;<input type=\"radio\" name=\"postmaster_gets_full_header\" value=\"0\" ".chk_if_selected($tablename, postmaster_gets_full_header, 0).">NO</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;DELIVER TO RECIPIENTS</TD>\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                        echo "&nbsp;<input type=\"radio\" name=\"deliver_to_recipients\" value=\"1\" ".chk_if_selected($tablename, deliver_to_recipients, 1).">YES&nbsp;<input type=\"radio\" name=\"deliver_to_recipients\" value=\"0\" ".chk_if_selected($tablename, deliver_to_recipients, 0).">NO</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;DELIVER DISINFECTED FILE</TD>\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                        echo "&nbsp;<input type=\"radio\" name=\"deliver_disinfected_file\" value=\"1\" ".chk_if_selected($tablename, deliver_disinfected_file, 1).">YES&nbsp;<input type=\"radio\" name=\"deliver_disinfected_file\" value=\"0\" ".chk_if_selected($tablename, deliver_disinfected_file, 0).">NO</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;DELIVER FROM LOCAL DOMAINS</TD>\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                        echo "&nbsp;<input type=\"radio\" name=\"deliver_from_local_domains\" value=\"1\" ".chk_if_selected($tablename, deliver_from_local_domains, 1).">YES&nbsp;<input type=\"radio\" name=\"deliver_from_local_domains\" value=\"0\" ".chk_if_selected($tablename, deliver_from_local_domains, 0).">NO</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;DELIVER UNPARSEABLE MS-RICH TEXT</TD>\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                        echo "&nbsp;<input type=\"radio\" name=\"deliver_unparseable_TNEF\" value=\"1\" ".chk_if_selected($tablename, deliver_unparseable_TNEF, 1).">YES&nbsp;<input type=\"radio\" name=\"deliver_unparseable_TNEF\" value=\"0\" ".chk_if_selected($tablename, deliver_unparseable_TNEF, 0).">NO</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<td></td>\n";
                        echo "<TD vAlign=middle align=center width=\"\" height=\"22\" colspan=\"2\">\n";
                        echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\" size=\"40\">\n";
                        #echo "<input type=\"hidden\" value=\"".$row['name']."\" name=\"oldhostname\" size=\"40\">\n";
                        echo "<input type=\"hidden\" name=\"updatedb\" value=\"updatedb\">";
                        echo "<input type=\"hidden\" name=\"field\" value=\"notifyopt\">";
                        #echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
                        echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
                        echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
                        echo "<a href=\"".$PHP_SELF."?module=$section\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
                        echo "</TD>\n";
                        echo "<td></td>\n";
                        echo "</TR>\n";

                        echo "                    </tbody>\n";
                        echo "                    </table>\n";
                        echo "                </td>\n";
                        echo "            </tr>\n";
                        echo "        </table>\n";
                        echo "        </form>\n";
                        echo "    <br><br><br>\n";
                    }
                    else // Update Record
                    {
                        $query="UPDATE ".$tablename." SET notify_senders='".$GLOBALS['notify_senders']."', notify_local_postmaster='".$GLOBALS['notify_local_postmaster']."', postmaster_gets_full_header='".$GLOBALS['postmaster_gets_full_header']."', deliver_from_local_domains='".$GLOBALS['deliver_from_local_domains']."', deliver_unparseable_TNEF='".$GLOBALS['deliver_unparseable_TNEF']."', deliver_to_recipients='".$GLOBALS['deliver_to_recipients']."', deliver_disinfected_file='".$GLOBALS['deliver_disinfected_file']."'";
                        $result=mysql_query($query) or die(mysql_error());
                        show_serverinfo($section, $section2, mss_general, control_mss);
                    }
                    break;
                case "notifymes":
                    if($GLOBALS['updatedb']!="updatedb")
                    {
                        $result=mysql_query("SELECT * FROM ".$tablename."");
                        $row=mysql_fetch_array($result);
                        echo "        <table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
                        echo "            <tr valign=\"top\">\n";
                        echo "                <td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                        echo "                    <img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
                        echo "                <td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                        echo "                       ".$section2." (extended options) &nbsp;</td>\n";
                        echo "                <td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                        echo "                    <img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
                        echo "            </tr>\n";
                        echo "        </table>\n";
                        echo "        <form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=editsettings\" name=\"submitform\">";
                        echo "        <table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
                        echo "            <tr>\n";
                        echo "                <td height=\"20px\" colspan=\"2\">\n";
                        echo "                    <img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
                        echo "            </tr>\n";
                        echo "            <tr>\n";
                        echo "                <td align=\"left\" width=\"40px\">\n";
                        echo "                    <img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
                        echo "                <td align=\"left\">\n";
                        // Check if database entries exists
                        $result_db=mysql_query("SELECT * FROM ".$tablename."");
                        $num_db=mysql_num_rows($result_db);
                        if($num_db==0)
                        {
                            $inline_text_signature="This message has been scanned for viruses and\n dangerous content by vis|wall - MailScanner, and is\n believed to be clean.";
                            $inline_html_signature="<BR>--\n<BR>This message has been scanned for viruses and\n<BR>dangerous content by\n<BR>vis|wall - MailScanner\n<BR>and is believed to be clean.\n<BR>--";
                            $inline_text_warning="Warning: This message has had one or more attachments removed.\nWarning: Please read the \"VirusWarning.txt\" attachment(s) for more information.";
                            $inline_html_warning="<P><B><FONT SIZE=\"+1\" COLOR=\"red\">Warning: </FONT>This message has had one or more attachments removed. Please read the \"VirusWarning.txt\" attachment(s) for more information.</B><BR></P>";
                            $query_db="insert into ".$tablename." (inline_text_signature, inline_html_signature, inline_text_warning, inline_html_warning) VALUES ('".$inline_text_signature."', '".$inline_html_signature."', '".$inline_text_warning."', '".$inline_html_warning."')";
                            $result=mysql_query($query_db) or die (mysql_error());
                        }
                        echo "<TABLE cellSpacing=1 cellPadding=0 width=\"260\" border=0>\n";
                        echo "<TBODY>\n";
                        echo "<TR bgcolor=\"#565656\">\n";
                        echo "<TD vAlign=bottom align=left width=\"350\" height=\"22\"><FONT color=#ffffff>&nbsp;OPTION</font>\n";
                        echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"350\" border=0></TD>\n";
                        echo "<TD vAlign=bottom align=center width=\"100\" height=\"22\"><FONT color=#ffffff>&nbsp;ACTION</font>\n";
                        echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"100\" border=0></TD>\n";
                        echo "<TD vAlign=bottom align=left width=\"30\" height=\"22\"><FONT color=#ffffff></font>\n";
                        echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"30\" border=0></TD>\n";
                        echo "</TR>\n";

                        //$result=mysql_query
                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;INFECTED MAIL STORED MESSAGE</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"\" height=\"22\">\n";
                        echo "&nbsp;<a href=\"".$PHP_SELF."?module=".$section."\"><a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=".$section."&action=popup&field=stored_virus_message&navigation=0&type=0', 'change_inf_mail_msg', '400', '500', 'false')\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;BAD ATTACHMENT STORED MESSAGE</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"\" height=\"22\">\n";
                        echo "&nbsp;<a href=\"".$PHP_SELF."?module=".$section."\"><a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=".$section."&action=popup&field=stored_bad_filename_message&navigation=0&type=0', 'change_stored_bad_filename_message', '400', '500', 'false')\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;INFECTED MAIL DELETED MESSAGE</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"\" height=\"22\">\n";
                        echo "&nbsp;<a href=\"".$PHP_SELF."?module=".$section."\"><a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=".$section."&action=popup&field=deleted_virus_message&navigation=0&type=0', 'change_deleted_virus_message', '400', '500', 'false')\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;BAD ATTACHMENT DELETED MESSAGE</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"\" height=\"22\">\n";
                        echo "&nbsp;<a href=\"".$PHP_SELF."?module=".$section."\"><a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=".$section."&action=popup&field=deleted_bad_filename_message&navigation=0&type=0', 'change_deleted_bad_filename_message', '400', '500', 'false')\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;DISINFECTED MAIL MESSAGE</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"\" height=\"22\">\n";
                        echo "&nbsp;<a href=\"".$PHP_SELF."?module=".$section."\"><a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=".$section."&action=popup&field=disinfected_mail_message&navigation=0&type=0', 'change_disinfected_mail_message', '400', '500', 'false')\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;BAD ATTACHMENT WARNING</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"\" height=\"22\">\n";
                        echo "&nbsp;<a href=\"".$PHP_SELF."?module=".$section."\"><a href=\"javascript:popup('".$GLOBALS['PHP_SELF']."?module=".$section."&action=popup&field=attachment_warning&navigation=0&type=0', 'change_attachment_warning', '400', '500', 'false')\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</TD>\n";
                        echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff><a href=\"javascript:popup\">&nbsp;?&nbsp;</a></font>\n";
                        echo "</TR>\n";

                        echo "<TR bgColor=\"#d5d5d5\">\n";
                        echo "<td></td>\n";
                        echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
                        echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\" size=\"40\">\n";
                        #echo "<input type=\"hidden\" value=\"".$row['name']."\" name=\"oldhostname\" size=\"40\">\n";
                        echo "<input type=\"hidden\" name=\"status\" value=\"updatedb\">";
                        #echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
                        #echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
                        #echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
                        echo "<a href=\"".$PHP_SELF."?module=$section\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;&nbsp;\n";
                        echo "</TD>\n";
                        echo "<td></td>\n";
                        echo "</TR>\n";

                        echo "                    </tbody>\n";
                        echo "                    </table>\n";
                        echo "                </td>\n";
                        echo "            </tr>\n";
                        echo "        </table>\n";
                        echo "        </form>\n";
                        echo "    <br><br><br>\n";
                    }
                    break;
            }
        }

        // -------------------------------------
        // | edit server Entry (Sub,Main)   |
        // -------------------------------------
        // | Last Change : 27.02.2002       |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------
        function edit_server($section, $section2, $tablename, $status, $id)
        {
            $result = mysql_query("SELECT * FROM ".$tablename." WHERE id='".$id."'") or die(mysql_error());
            $row = mysql_fetch_array($result);
            if($status!="updatedb")
            {
                echo "        <table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
                echo "            <tr valign=\"top\">\n";
                echo "                <td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                echo "                    <img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
                echo "                <td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                echo "                       ".$section2." (".$row['hostname'].") &nbsp;</td>\n";
                echo "                <td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                echo "                    <img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
                echo "            </tr>\n";
                echo "        </table>\n";

                echo "        <form method=\"post\" action=\"".$PHP_SELF."?module=".$section."&action=editserver\" name=\"submitform\">";
                echo "        <table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
                echo "            <tr>\n";
                echo "                <td height=\"20px\" colspan=\"2\">\n";
                echo "                    <img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"20px\"></td>\n";
                echo "            </tr>\n";
                echo "            <tr>\n";
                echo "                <td align=\"left\" width=\"40px\">\n";
                echo "                    <img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
                echo "                <td align=\"left\">\n";

                echo "<TABLE cellSpacing=1 cellPadding=0 width=\"260\" border=0>\n";
                echo "<TBODY>\n";
                echo "<TR bgcolor=\"#565656\">\n";
                echo "<TD vAlign=bottom align=left width=\"150\" height=\"22\"><FONT color=#ffffff>&nbsp;SERVER</font>\n";
                echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"150\" border=0></TD>\n";
                echo "<TD vAlign=bottom align=left width=\"210\" height=\"22\"><FONT color=#ffffff>&nbsp;".$row['hostname']."</font>\n";
                echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"210\" border=0></TD>\n";
                echo "<TD vAlign=bottom align=left width=\"30\" height=\"22\"><FONT color=#ffffff></font>\n";
                echo "<IMG height=6 src=\"./images/border_orange.gif\" width=\"30\" border=0></TD>\n";
                echo "</TR>\n";

                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;SERVERNAME</TD>\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=\"text\" value=\"".$row['hostname']."\" name=\"hostname\" size=\"30\" maxsize=\"255\">&nbsp;</TD>\n";
                echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><a href=\"javascript:popup\">&nbsp;?&nbsp;</a>\n";
                echo "</TR>\n";

                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;SCAN BY DOMAIN</TD>\n";
                echo "<TD vAlign=middle     align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=radio value=\"1\" name=\"scanning_by_domain\" ".chk_if_selected($tablename,scanning_by_domain,1).">YES&nbsp;<input type=radio value=\"0\" name=\"scanning_by_domain\" ".chk_if_selected($tablename,scanning_by_domain,0).">NO&nbsp;</TD>\n";
                echo "<TD vAlign=middle align=center width=\"30\" height=\"22\">?</td>\n";
                echo "</TR>\n";

                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;VIRUS SCANNER TIMEOUT</TD>\n";
                echo "<TD vAlign=middle     align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=\"text\" value=\"".$row['virus_scanner_timeout']."\" name=\"virus_scanner_timeout\" size=\"25\" maxsize=\"30\">&nbsp;sek.&nbsp;</TD>\n";
                echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";
                echo "</TR>\n";

                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;RESTART EVERY</TD>\n";
                echo "<TD vAlign=middle     align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=\"text\" value=\"".$row['restart_every']."\" name=\"restart_every\" size=\"25\" maxsize=\"255\">&nbsp;sek.&nbsp;</TD>\n";
                echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";
                echo "</TR>\n";

                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;ACTION</TD>\n";
                echo "<TD vAlign=middle     align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=radio value=\"1\" name=\"action_mss\" ".chk_if_selected($tablename,action,1).">STORE&nbsp;<input type=radio value=\"0\" name=\"action_mss\" ".chk_if_selected($tablename,action,0).">DELETE&nbsp;</TD>\n";
                echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";
                echo "</TR>\n";

                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=left width=\"\" height=\"22\">&nbsp;POSTMASTER</TD>\n";
                echo "<TD vAlign=middle     align=left width=\"\" height=\"22\">\n";
                echo "&nbsp;<input type=\"text\" value=\"".$row['local_postmaster']."\" name=\"postmaster\" size=\"30\">&nbsp;</TD>\n";
                echo "<TD vAlign=middle align=center width=\"30\" height=\"22\"><FONT color=#ffffff>?</font></td>\n";
                echo "</TR>\n";

                echo "<TR bgColor=\"#d5d5d5\">\n";
                echo "<TD vAlign=middle align=right width=\"\" height=\"22\" colspan=\"2\">\n";
                echo "<input type=\"hidden\" value=\"".$id."\" name=\"id\" size=\"40\">\n";
                #echo "<input type=\"hidden\" value=\"".$row['name']."\" name=\"oldhostname\" size=\"40\">\n";
                echo "<input type=\"hidden\" name=\"status\" value=\"updatedb\">";
                #echo "<input type=\"hidden\" name=\"magic\" value=\"".generate_magic()."\">";
                echo "<a href=\"javascript:document.submitform.submit()\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;\n";
                echo "<a href=\"javascript:document.submitform.reset()\"><img src=\"./images/reset.gif\" border=\"0\"></a>&nbsp;\n";
                echo "<a href=\"".$PHP_SELF."?module=$section\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a>&nbsp;\n";
                echo "</TD>\n";
                echo "<td></td>\n";
                echo "</TR>\n";

                echo "                    </tbody>\n";
                echo "                    </table>\n";
                echo "                </td>\n";
                echo "            </tr>\n";
                echo "        </table>\n";
                echo "        </form>\n";
                echo "    <br>\n";
            }
            else // Update Record
            {
                //place for checkroutines

                if(($GLOBALS['restart_every'])=="" OR ($GLOBALS['restart_every'])=="0")
                {
                    $GLOBALS['restart_every']="14400";
                }
                if(($GLOBALS['virus_scanner_timeout'])=="" OR ($GLOBALS['virus_scanner_timeout'])=="0")
                {
                    $GLOBALS['virus_scanner_timeout']="300";
                }
                if($GLOBALS['postmaster']=="")
                {
                    $GLOBALS['postmaster'] = "root@viswall";
                }
                //chek if we had to create an new entry
                $result_chk=mysql_query("SELECT * FROM ".$tablename."");
                $num_chk=mysql_num_rows($result_chk);
                if($num_chk!=0)
                {
                    $query="UPDATE ".$tablename." SET scanning_by_domain='".$GLOBALS['scanning_by_domain']."', virus_scanner_timeout='".$GLOBALS['virus_scanner_timeout']."', restart_every='".$GLOBALS['restart_every']."', hostname='".$GLOBALS['hostname']."', action='".$GLOBALS['action_mss']."', local_postmaster='".$GLOBALS['postmaster']."' WHERE id='".$id."'";
                    $result=mysql_query($query) or die(mysql_error());
                    show_serverinfo($section, $section2, $tablename, "control_mss");
                }
                else
                {
                    $query="INSERT INTO ".$tablename." (scanning_by_domain, virus_scanner_timeout, restart_every, hostname, action, local_postmaster) VALUES ('".$GLOBALS['scanning_by_domain']."', '".$GLOBALS['virus_scanner_timeout']."', '".$GLOBALS['restart_every']."', '".$GLOBALS['hostname']."', '".$GLOBALS['action_mss']."', '".$GLOBALS['postmaster']."')";
                    $result=mysql_query($query) or die(mysql_error());
                    show_serverinfo($section, $section2, $tablename, "control_mss");
                }
            }
        }


        // -------------------------------------
        // | show extended Info (Main)      |
        // -------------------------------------
        // | Last Change : 27.02.2002       |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------
        function show_extinfo($section)
        {
            echo "        <table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
            echo "            <tr>\n";
            echo "                <td align=\"left\" width=\"40px\">\n";
            echo "                    <img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
            echo "                <td align=\"left\">\n";

            # Generate Table-Header #
            echo "                    <table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"672px\" height=\"\">\n";
            echo "                        <tr bgcolor=\"#565656\" class=\"tablehead\">\n";
            echo "                            <td valign=\"bottom\" align=\"left\" width=\"210\" height=\"22\">\n";
            echo "                                <font color=\"#ffffff\">&nbsp;</font>\n";
            echo "                                <img src=\"images/border_orange.gif\" width=\"210\" height=\"6\" border=\"0\"></td>\n";
            echo "                              <td valign=\"bottom\" align=\"center\" width=\"159\" height=\"22\">\n";
            echo "                                   <font color=\"#ffffff\">&nbsp;SIGN OPTIONS</font>\n";
            echo "                                   <img src=\"images/border_orange.gif\" WIDTH=\"159\" height=\"6\" border=\"0\"></td>\n";
            echo "                              <td valign=\"bottom\" align=\"center\" width=\"159\" height=\"22\">\n\n";
            echo "                                   <font color=\"#ffffff\">&nbsp;NOTIFY/DELIVER OPTIONS&nbsp;</font>\n";
            echo "                                  <img src=\"images/border_orange.gif\" WIDTH=\"159\" height=\"6\" border=\"0\"></td>\n";
            echo "                              <td valign=\"bottom\" align=\"center\" width=\"159\" height=\"22\">\n\n";
            echo "                                   <font color=\"#ffffff\">&nbsp;NOTIFY MESSAGES</font>\n";
            echo "                                  <img src=\"images/border_orange.gif\" WIDTH=\"159\" height=\"6\" border=\"0\"></td>\n";
            echo "                         </tr>\n";

            # Generate Table-Data
            echo "                        <tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
            echo "                            <td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">";
            echo "                                &nbsp;extended MailScanner options</td>";
            echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=editsettings&field=signopt\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</td>";
            echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=editsettings&field=notifyopt\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</td>";
            echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=editsettings&field=notifymes\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</td></tr>";

            # Generate table footer
            echo "                    <tr bgcolor=\"#565656\">\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                    </tr>\n";
            echo "                    </table>\n";
            echo "                </td>\n";
            echo "            </tr>\n";
            echo "        </table>\n";
            echo "    <br>\n";
            show_listsinfo($section);
        }

        // -------------------------------------
        // | show lists Info (Main)                  |
        // -------------------------------------
        // | Last Change : 04.03.2002           |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------
        function show_listsinfo($section)
        {
            echo "        <table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
            echo "            <tr>\n";
            echo "                <td align=\"left\" width=\"40px\">\n";
            echo "                    <img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
            echo "                <td align=\"left\">\n";

            # Generate Table-Header #
            echo "                    <table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"672px\" height=\"\">\n";
            echo "                        <tr bgcolor=\"#565656\" class=\"tablehead\">\n";
            echo "                            <td valign=\"bottom\" align=\"left\" width=\"210\" height=\"22\">\n";
            echo "                                <font color=\"#ffffff\">&nbsp;</font>\n";
            echo "                                <img src=\"images/border_orange.gif\" width=\"210\" height=\"6\" border=\"0\"></td>\n";
            echo "                              <td valign=\"bottom\" align=\"center\" width=\"159\" height=\"22\">\n";
            echo "                                   <font color=\"#ffffff\">&nbsp;DOMAINS TO SCAN</font>\n";
            echo "                                   <img src=\"images/border_orange.gif\" WIDTH=\"159\" height=\"6\" border=\"0\"></td>\n";
            echo "                              <td valign=\"bottom\" align=\"center\" width=\"159\" height=\"22\">\n\n";
            echo "                                   <font color=\"#ffffff\">&nbsp;LOCAL DOMAINS&nbsp;</font>\n";
            echo "                                  <img src=\"images/border_orange.gif\" WIDTH=\"159\" height=\"6\" border=\"0\"></td>\n";
            echo "                              <td valign=\"bottom\" align=\"center\" width=\"159\" height=\"22\">\n\n";
            echo "                                   <font color=\"#ffffff\">&nbsp;SPAM WHITELIST</font>\n";
            echo "                                  <img src=\"images/border_orange.gif\" WIDTH=\"159\" height=\"6\" border=\"0\"></td>\n";
            echo "                         </tr>\n";

            # Generate Table-Data
            echo "                        <tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
            echo "                            <td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">";
            echo "                                &nbsp;MailScanner lists</td>";
            echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=editlists&field=domains2scan\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</td>";
            echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=editlists&field=localdomain\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</td>";
            echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=editlists&field=spamwhite\"><img src=\"images/icons/edit_gr.gif\" border=\"0\"></a>&nbsp;</td></tr>";

            # Generate table footer
            echo "                    <tr bgcolor=\"#565656\">\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                    </tr>\n";
            echo "                    <tr>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                    </tr>\n";
            echo "                    <tr>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"center\" width=\"\" height=\"12\">";
            echo "							<a href=\"".$PHP_SELF."?module=activate&g_module=".$section."&action=activate&params=execute\"><IMG SRC=\"images/activate.gif\" BORDER=\"0\" ALT=\"activate\"></a></td>";	
            echo "                    </tr>\n";
            echo "                    </table>\n";
            echo "                </td>\n";
            echo "            </tr>\n";
            echo "        </table>\n";
            //echo "    <br><br><br>\n";
        }

        // -------------------------------------
        // | Change mss Status (Main)     |
        // -------------------------------------
        // | Last Change : 28.02.2002       |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------
        function status_mss($section, $section2, $tablename, $id, $field)
        {
            # Changes the status (without prompt) of the selected
            # --------------------------------------------------------------------
            # Status Change for Main Entry
            # ---------------------------------
            $result_status = mysql_query("select ".$field." from ".$tablename."") or die(mysql_error());
            $row_status = mysql_fetch_array($result_status);
            # Select Status of Entry
            # -------------------------
            if ($row_status[$field] == 0)
            {
                # Set Status of Entry == 1
                # ---------------------------
                $result_status = mysql_query("update ".$tablename." set ".$field."='1'") or die(mysql_error());
            }
            else
            {
                # Set Status of Entry == 0
                # ---------------------------
                $result_status = mysql_query("update ".$tablename." set ".$field."='0'") or die(mysql_error());
            }
            show_serverinfo($section, $section2, "mss_general", "control_mss");
        }

        // --------------------------------------
        // | is_true (Sub)                            |
        // --------------------------------------
        // | Last Change : 27.02.2002        |
        // --------------------------------------
        // |Status : Enabled                        |
        // --------------------------------------
        function is_true($value)
        {
            if($value=="1")
            {
                return "<img src=\"images/icons/on.gif\" border=\"0\">";
            }
            else
            {
                return "<img src=\"images/icons/off.gif\" border=\"0\">";
            }
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
                        echo "<option value=\"".$suffix."\" selected>";
                    } else {
                        echo "<option value=\"".$suffix."\">";
                    }
        }

         // -------------------------------------
        // | chk_if_selected (Sub)           |
        // -------------------------------------
        // | Last Change : 19.02.2002       |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------
        function chk_if_selected($tablename, $column, $compstr)
        {
            $result=mysql_query("SELECT ".$column." FROM ".$tablename."");
            $row=mysql_fetch_array($result);

            if($row[$column]==$compstr)
            {
                return "checked";
            }
        }

        // -------------------------------------
        // | popup enter text (Main)                  |
        // -------------------------------------
        // | Last Change : 04.03.2002           |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------
        function popup_enter_text($field, $tablename)
        {
            echo "        <table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
            echo "          <tr><td align=\"left\"><img src=\"images/tpx.gif\" height=\"10\" border=\"0\"></td></tr>";
            echo "            <tr>\n";
            echo "                <td align=\"left\" width=\"10px\">\n";
            echo "                    <img src=\"./images/tpx.gif\" width=\"10px\" height=\"1px\" border=\"0\"></td>\n";
            echo "                <td align=\"left\">\n";

            # Generate Table-Header #
            echo "                    <table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"\" height=\"\">\n";
            echo "                        <tr bgcolor=\"#565656\" class=\"tablehead\">\n";
            echo "                            <td valign=\"bottom\" align=\"left\" width=\"380\" height=\"22\">\n";
            echo "                                <font color=\"#ffffff\">&nbsp;Enter text:</font>\n";
            echo "                                <img src=\"images/border_orange.gif\" width=\"380\" height=\"6\" border=\"0\"></td>\n";
            echo "                         </tr>\n";
            echo "                           <form name=\"submitform\" action=\"index2.php?module=mss&action=change".$field."\" method=\"post\">";

            # Generate Table-Data
            echo "                        <tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
            echo "                            <td valign=\"top\" align=\"left\" width=\"\" height=\"442\">";

            if(substr($GLOBALS['field'], 0, 6)=="inline")
            {
             if(substr($GLOBALS['field'],-9)=="signature")
             {
                echo "                                <textarea cols=\"44\" rows=\"24\" name=\"text\">";
                $query="SELECT ".$field." FROM ".$tablename."";
                $result=mysql_query($query);
                $row=mysql_fetch_array($result);
                echo $row[$field];
                echo "</textarea><br>";
                echo "<input type=\"hidden\" name=\"type\" value=\"0\">";
             }
             elseif(substr($GLOBALS['field'],-7)=="warning")
             {
                echo "<textarea cols=\"44\" rows=\"24\" name=\"text\">";
                $query="SELECT ".$field." FROM ".$tablename."";
                $result=mysql_query($query);
                $row=mysql_fetch_array($result);
                echo $row[$field];
                echo "</textarea><br>";
                echo "<input type=\"hidden\" name=\"type\" value=\"0\">";
             }
            }
            else
            {
                echo "<textarea cols=\"44\" rows=\"24\" name=\"text\">";
                $query="SELECT ".$field." FROM ".$tablename."";
                $result=mysql_query($query);
                $row=mysql_fetch_array($result);
                echo $row[$field];
                echo "</textarea><br>";
                echo "<input type=\"hidden\" name=\"type\" value=\"0\">";
            }

            /*elseif($GLOBALS['field']=="stored_virus_message") BACKUP
            {
                echo "                                <textarea cols=\"44\" rows=\"24\" name=\"text\">";
                $query="SELECT ".$field." FROM ".$tablename."";
                $result=mysql_query($query);
                $row=mysql_fetch_array($result);
                echo $row[$field];
                echo "                                </textarea><br>";
                echo "                                <input type=\"hidden\" name=\"type\" value=\"0\">";
            }*/
            echo "                                <input type=\"hidden\" name=\"field\" value=\"".$field."\">";
            echo "                                <img src=\"images/tpx.gif\" border=\"0\" height=\"5\" width=\"1\">";
            echo "                                <table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"380\" height=\"\">\n";
            echo "                                       <tr>";
            echo "                                             <td valign=\"top\" align=\"left\" width=\"190\" height=\"\">&nbsp;<a href=\"javascript:document.submitform.submit();window.close()\"><img src=\"images/change.gif\" border=\"0\"></a></td>";
            echo "                                             <td valign=\"top\" align=\"right\" width=\"190\" height=\"\"><a href=\"javascript:window.close()\"><img src=\"images/cancel.gif\" border=\"0\"></a>&nbsp;</td>";
            echo "                                       </tr>";
            echo "                                </table>";
            echo "                        </td></tr>";

            # Generate table footer
            echo "                    <tr bgcolor=\"#565656\">\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                    </tr>\n";
            echo "                    <tr>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                    </tr>\n";
            echo "                    <tr>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                    </tr>\n";
            echo "                    </table>\n";
            echo "                </td>\n";
            echo "            </tr>\n";
            echo "        </table>\n";
            //echo "    <br><br><br>\n";
        }

        // -------------------------------------
        // | popup enter line (Main)            |
        // -------------------------------------
        // | Last Change : 05.03.2002           |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------
        function popup_enter_line($field, $tablename)
        {
            echo "        <table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
            echo "          <tr><td align=\"left\"><img src=\"images/tpx.gif\" height=\"10\" border=\"0\"></td></tr>";
            echo "            <tr>\n";
            echo "                <td align=\"left\" width=\"10px\">\n";
            echo "                    <img src=\"./images/tpx.gif\" width=\"10px\" height=\"1px\" border=\"0\"></td>\n";
            echo "                <td align=\"left\">\n";

            # Generate Table-Header #
            echo "                    <table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"\" height=\"\">\n";
            echo "                        <tr bgcolor=\"#565656\" class=\"tablehead\">\n";
            echo "                            <td valign=\"bottom\" align=\"left\" width=\"280\" height=\"22\">\n";
            echo "                                <font color=\"#ffffff\">&nbsp;Enter text:</font>\n";
            echo "                                <img src=\"images/border_orange.gif\" width=\"100%\" height=\"6\" border=\"0\"></td>\n";
            echo "                         </tr>\n";
            echo "                           <form name=\"submitform\" action=\"".$GLOBALS['PHP_SELF']."?module=mss&action=change".$field."\" onSubmit=\"javascript:window.close();\" method=\"post\">";

            # Generate Table-Data
            echo "                        <tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
            echo "                            <td valign=\"top\" align=\"left\" width=\"\" height=\"60\">";
            echo "                                  <img src=\"images/tpx.gif\" width=\"1\" height=\"10\" border=\"0\"><br>";
            if($field=="unscanned_header")
            {
               $result=mysql_query("SELECT ".$field." FROM ".$tablename."");
               $row=mysql_fetch_array($result);
               echo "                                 &nbsp;<input type=\"text\" value=\"".$row[$field]."\" name=text size=\"43\"><br>";
               echo "                                <input type=\"hidden\" name=\"type\" value=\"0\">";
            }
            elseif($field=="mail_headers")
            {
               $result=mysql_query("SELECT clean_header, infected_header, disinfected_header FROM ".$tablename."");
               $row=mysql_fetch_array($result);
               echo "                         <table border=\"0\" cellspacing=\"0\" cellpadding=\"0\">";
               echo "                                 <tr><td>&nbsp;clean header:&nbsp;</td><td><input type=\"text\" value=\"".$row['clean_header']."\" name=clean_header size=\"40\">&nbsp;</td></tr>";
               echo "                                 <tr><td>&nbsp;infected header:&nbsp;</td><td><input type=\"text\" value=\"".$row['infected_header']."\" name=infected_header size=\"40\">&nbsp;</td></tr>";
               echo "                                 <tr><td>&nbsp;disinfected header:&nbsp;</td><td><input type=\"text\" value=\"".$row['disinfected_header']."\" name=disinfected_header size=\"40\">&nbsp;</td></tr>";
               echo "                         </table>";
               echo "                                <input type=\"hidden\" name=\"type\" value=\"1\">";
            }
            echo "                                <input type=\"hidden\" name=\"field\" value=\"".$field."\">";
            echo "                                <img src=\"images/tpx.gif\" border=\"0\" height=\"5\" width=\"1\">";
            echo "                                <table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"\">\n";
            echo "                                       <tr>";
            echo "                                             <td valign=\"top\" align=\"left\" width=\"50%\" height=\"\">&nbsp;<a href=\"javascript:document.submitform.submit();window.close()\"><img src=\"images/change.gif\" border=\"0\"></a></td>";
            echo "                                             <td valign=\"top\" align=\"right\" width=\"50%\" height=\"\"><a href=\"javascript:window.close()\"><img src=\"images/cancel.gif\" border=\"0\"></a>&nbsp;</td>";
            echo "                                       </tr>";
            echo "                                </table>";
            echo "                        </td></tr>";

            # Generate table footer
            echo "                    <tr bgcolor=\"#565656\">\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                    </tr>\n";
            echo "                    <tr>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                    </tr>\n";
            echo "                    <tr>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                    </tr>\n";
            echo "                    </table>\n";
            echo "                </td>\n";
            echo "            </tr>\n";
            echo "        </table>\n";
            //echo "    <br><br><br>\n";
        }

        // -------------------------------------
        // | change popup text (Sub,Main)     |
        // -------------------------------------
        // | Last Change : 01.03.2002       |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------
        function changepopup_text($field, $tablename, $value, $type, $value2="", $value3="", $field2="", $field3="")
        {
         if($type=="0")
         {
             $query="UPDATE ".$tablename." SET ".$field." = '".$value."'";
             $result=mysql_query($query) or die(mysql_error());
         }
         elseif($type=="1")
         {
             $query="UPDATE ".$tablename." SET ".$field." = '".$value."', ".$field2." = '".$value2."', ".$field3." = '".$value3."'";
             $result=mysql_query($query) or die(mysql_error());
         }
        }


        // -------------------------------------
        // | show domain list (Main)            |
        // -------------------------------------
        // | Last Change : 06.03.2002           |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------
        function show_domain_list($section, $section2, $tablename, $type)
        {
            $result=mysql_query("SELECT * FROM ".$tablename." WHERE type='".$type."'");
            $num=mysql_num_rows($result);

            switch($type)
            {
             case 1:
                   $field="domains2scan";
                   break;
             case 2:
                   $field="local_domains";
                   break;
             case 3:
                   $field="spam_whitelist";
                   break;
            }
            echo "        <table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
            echo "            <tr>\n";
            echo "                <td align=\"left\" width=\"40px\">\n";
            echo "                    <img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
            echo "                <td align=\"left\">\n";
            echo "        <table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
            echo "            <tr valign=\"top\">\n";
            echo "                <td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
            echo "                    <img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
            echo "                <td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
            echo "                       ".$section2." (".$field.") &nbsp;</td>\n";
            echo "                <td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
            echo "                    <img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
            echo "            </tr>\n";
            echo "        </table>\n";
            echo "          <br><br>";
            echo "                    <table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"400px\" height=\"\">\n";
            echo "                        <tr bgcolor=\"#565656\" class=\"tablehead\">\n";
            echo "                              <td valign=\"bottom\" align=\"center\" width=\"250\" height=\"22\">\n";
            echo "                                   <font color=\"#ffffff\">&nbsp;ADRESS/DOMAIN&nbsp;</font>\n";
            echo "                                   <img src=\"images/border_orange.gif\" WIDTH=\"250\" height=\"6\" border=\"0\"></td>\n";
            echo "                              <td valign=\"bottom\" align=\"center\" width=\"150\" height=\"22\">\n\n";
            echo "                                   <font color=\"#ffffff\">&nbsp;ACTION&nbsp;</font>\n";
            echo "                                  <img src=\"images/border_orange.gif\" WIDTH=\"150\" height=\"6\" border=\"0\"></td>\n";
			
			# Generate Table-Data
			if($num==0)
			{
				echo "                        <tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
				echo "							<td>&nbsp;empty</td>";				
				echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=adddomain&type=".$type."\"><img src=\"images/icons/neu.gif\" border=\"0\" alt=\"add domain\"></a>&nbsp;</td>";
			}
			
            for($i=0;$i<$num;$i++)
            {
                    $row=mysql_fetch_array($result);
	                if(is_float(($i/2))==false)
					{
						echo "                        <tr bgcolor=\"#d5d5d5\" valign=\"middle\">";
					}
					else
					{
						echo "                        <tr bgcolor=\"#bababa\" valign=\"middle\">";
					}
                    echo "                            <td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">&nbsp;".$row['name']."</td>";
                    echo "                            <td valign=\"middle\" align=\"center\" width=\"\" height=\"20\">&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=adddomain&type=".$type."\"><img src=\"images/icons/neu.gif\" border=\"0\" alt=\"add domain\"></a>&nbsp;&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=deldomain&field=".$field."&id=".$row['id']."&type=".$type."\"><img src=\"images/icons/delete.gif\" border=\"0\" alt=\"delete domain\"></a></td>";
                    echo "                        </tr>";
            }

            # Generate table footer
            echo "                    <tr bgcolor=\"#565656\">\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                    </tr>\n";
            echo "                    <tr>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                    </tr>\n";
            echo "                    <tr>\n";
            echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
            echo "                        <td valign=\"bottom\" align=\"center\" width=\"\" height=\"12\">";
            echo "                    </tr>\n";
            echo "					<tr>";
			echo "						<td></td>";
			echo "						<td align=\"right\"><a href=\"".$GLOBALS['PHP_SELF']."?module=".$section."\"><img src=\"images/back.gif\" border=\"0\"></a>&nbsp;</td></tr>";
            echo "                    </table>\n";
            echo "                </td>\n";
            echo "            </tr>\n";
            echo "        </table>\n";
        }

		
        // -------------------------------------
        // | add domain list entry (Main)   |
        // -------------------------------------
        // | Last Change : 06.03.2002      |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------
        function add_domain($section, $section2, $tablename, $type, $status)
        {
			if($status!="go")
			{
				switch($type)
				{
					case 1:
						$field="domains2scan";
						break;
					case 2:
						$field="localdomain";
						break;
					case 3:
						$field="spamwhite";
						break;
				}
				echo "        <table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
				echo "            <tr>\n";
				echo "                <td align=\"left\" width=\"40px\">\n";
				echo "                    <img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td>\n";
				echo "                <td align=\"left\">\n";
				echo "        <table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
				echo "            <tr valign=\"top\">\n";
				echo "                <td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "                    <img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
				echo "                <td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "                       ".$section2." (".$field.") &nbsp;</td>\n";
				echo "                <td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
				echo "                    <img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
				echo "            </tr>\n";
				echo "        </table>\n";
				echo "          <br><br>";
				echo "                    <table cellspacing=\"1\" cellpadding=\"0\" border=\"0\" width=\"400px\" height=\"\">\n";
				echo "                        <tr bgcolor=\"#565656\" class=\"tablehead\">\n";
				echo "                              <td valign=\"bottom\" align=\"center\" width=\"150\" height=\"22\">\n\n";
				echo "                                   <font color=\"#ffffff\">&nbsp;&nbsp;</font>\n";
				echo "                                  <img src=\"images/border_orange.gif\" WIDTH=\"150\" height=\"6\" border=\"0\"></td>\n";
				echo "                              <td valign=\"bottom\" align=\"left\" width=\"250\" height=\"22\">\n";
				echo "                                   <font color=\"#ffffff\">&nbsp;ADRESS/DOMAIN&nbsp;</font>\n";
				echo "                                   <img src=\"images/border_orange.gif\" WIDTH=\"250\" height=\"6\" border=\"0\"></td>\n";
				
				# Generate Table-Data
				echo "						<form name=\"submitform\" action=\"".$GLOBALS['PHP_SELF']."?module=".$section."&action=adddomain&type=".$type."&status=go\" method=\"post\">\n";	        
				echo "                        <tr bgcolor=\"#d5d5d5\" valign=\"middle\">\n";
				echo "                            <td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">&nbsp;enter name:</td>\n";
				echo "                            <td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">&nbsp;<input type=\"text\" size=\"38\" name=\"domain\">&nbsp;</td>\n";
				echo "                        </tr>\n";
				echo "                        <tr bgcolor=\"#d5d5d5\" valign=\"middle\">\n";
				echo "                            <td valign=\"middle\" align=\"left\" width=\"\" height=\"20\">&nbsp;</td>\n";
				echo "                            <td valign=\"middle\" align=\"right\" width=\"\" height=\"20\">&nbsp;<a href=\"javascript:document.submitform.submit();window.close()\"><img src=\"images/change.gif\" border=\"0\"></a>&nbsp;<a href=\"".$PHP_SELF."?module=".$section."&action=editlists&field=".$field."\"><img src=\"images/cancel.gif\" border=\"0\"></a>&nbsp;</td>\n";			
				echo "                        </tr></form>\n";
				# Generate table footer
				echo "                    <tr bgcolor=\"#565656\">\n";
				echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "                    </tr>\n";
				echo "                    <tr>\n";
				echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "                    </tr>\n";
				echo "                    <tr>\n";
				echo "                        <td valign=\"bottom\" align=\"left\" width=\"\" height=\"12\">&nbsp;</td>\n";
				echo "                        <td valign=\"bottom\" align=\"center\" width=\"\" height=\"12\">";
				echo "                    </tr>\n";
				echo "                    </table>\n";
				echo "                </td>\n";
				echo "            </tr>\n";
				echo "        </table>\n";
			}
			elseif($status=="go")
			{
				$result=mysql_query("INSERT INTO ".$tablename." (name, type) VALUES ('".$GLOBALS['domain']."', '".$type."')") or die(mysql_error());
				show_domain_list($section, $section2, $tablename, $type);
				
			}
		}
		
        // -------------------------------------
        // | del domain list entry (Main)   |
        // -------------------------------------
        // | Last Change : 06.03.2002      |
        // -------------------------------------
        // | Status : Enabled                   |
        // -------------------------------------
        function del_domain($section, $section2, $tablename, $id, $type)
        {
			$result=mysql_query("DELETE FROM ".$tablename." WHERE id='".$id."'") or die(mysql_error());
			show_domain_list($section, $section2, $tablename, $type);
		}
?>