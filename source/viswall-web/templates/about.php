<?php
$myinfo=new info();

	echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
	echo "			<tr valign=\"top\">\n";
	echo "				<td align=\"left\" width=\"44px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
	echo "					<img src=\"./images/tpx.gif\" width=\"44px\" height=\"23px\" border=\"0\"></td>\n";
	echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
	echo " 	  				VISWALL | <b>ABOUT</b> &nbsp;</td>\n";
	echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
	echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
	echo "			</tr>\n";
	echo "		</table>\n";
	echo "		<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\">\n";
	echo "			<tr>\n";
	echo "				<td height=\"1px\" colspan=\"2\"><img src=\"./images/tpx.gif\" id=\"blank\" border=\"0\" width=\"1px\" height=\"1px\"></td>\n";
	echo "			</tr>\n";
	echo "			<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td></tr>\n";
	echo "				<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td><td align=\"left\"><b>".$myinfo->g_title."</b></td></tr>\n";
	echo "				<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td><td align=\"left\">&nbsp;</td></tr>\n";
	echo "				<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td><td align=\"left\"><b>Copyright:</b> ".$myinfo->g_copyright."</td></tr>\n";
	echo "				<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td><td align=\"left\">&nbsp;</td></tr>\n";	
	echo "				<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td><td align=\"left\"><b>Release:</b> ".$myinfo->version."</td></tr>\n";
	echo "				<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td><td align=\"left\">&nbsp;</td></tr>\n";	
	echo "				<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td><td align=\"left\"><b>Contact:</b> <br>&nbsp;&nbsp;".$myinfo->g_address[0]."<br>&nbsp;&nbsp;".$myinfo->g_address[1]."<br>&nbsp;&nbsp;".$myinfo->g_address[2]."<br><br>&nbsp;&nbsp;<b>Phone:</b> ".$myinfo->g_phone."<br>&nbsp;&nbsp;<b>E-Mail:</b> <a href=\"mailto:".$myinfo->g_email."\">".$myinfo->g_email."</a><br>&nbsp;&nbsp;<b>WWW:</b> <a href=\"".$myinfo->g_web."\" target=\"_new\">".$myinfo->g_web."</a></td></tr>\n";
	echo "				<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td><td align=\"left\">&nbsp;</td></tr>\n";
	echo "				<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td><td align=\"left\"><b>developer:</b></td></tr>\n";

	foreach ($myinfo->g_developer as $person) {
		echo "				<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td><td align=\"left\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".$person."</td></tr>\n";
	}

	echo "				<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td><td align=\"left\">&nbsp;</td></tr>\n";
	echo "				<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td><td align=\"left\"><b>graphics/design:</b></td></tr>\n";

	foreach ($myinfo->g_designer as $person) {
		echo "				<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td><td align=\"left\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".$person."</td></tr>\n";
	}

	echo "				<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td><td align=\"left\">&nbsp;</td></tr>\n";
	echo "				<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td><td align=\"left\"><b>text/marketing:</b></td></tr>\n";

	foreach ($myinfo->g_texter as $person) {
		echo "				<tr><td align=\"left\" width=\"40px\"><img src=\"./images/tpx.gif\" width=\"40px\" height=\"1px\" border=\"0\"></td><td align=\"left\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".$person."</td></tr>\n";
	}

	echo "			</tr>\n";
	echo "		</table>\n";
	echo "	<br><br><br>\n";

?>
