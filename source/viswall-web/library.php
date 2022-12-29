<?php 
// //////////////////////////////////////////////
// ---> vis|wall Firewall <---    //
// //////////////////////////////////////////////
// Date	: 29.04.2002                          //
// //////////////////////////////////////////////
// ///////////////////////
// Database Connection //
// ///////////////////////
function open_db()
{
    $sql_db = new sql_db;
    mysql_connect($sql_db->sql_db_host, $sql_db->sql_db_username, $sql_db->sql_db_password) or die ("Unable to connect to database. Contact support.");
    mysql_select_db($sql_db->sql_db_name) or die ("Unable to select Database. Contact Support.");
} 
// ///////////////////
// HTML Generation //
// ///////////////////
function generate_html($navigation = 1)
{
    $info = new info;

    echo "<html>\n";
    echo "	<head>\n";
    echo "		<title>vis|wall</title>\n";
    echo "		<link rel=\"stylesheet\" type=\"text/css\" href=\"./styles/viswall.css\">\n";

    if ($_GET['module'] == "nidslog") {
        switch ($_GET['action']) {
            case 'signaturelist':
            case 'detail':
            case 'more': {
                    echo "		<script language=\"JavaScript\" type=\"text/javascript\">\n";
                    echo "			<!--\n";
                    echo "				function popup(filename,name,width,height,scrollbars)\n";
                    echo "				{\n";
                    echo "					if (scrollbars == 'true')\n";
                    echo "					{\n";
                    echo "						window.open(filename,name,\"width=\"+width+\",height=\"+height+\",scrollbars\");\n";
                    echo "					}\n";
                    echo "					else\n";
                    echo "					{\n";
                    echo "						window.open(filename,name,\"width=\"+width+\",height=\"+height);\n";
                    echo "					}\n";
                    echo "				}\n";
                    echo "				function killpopup(filename,name)\n";
                    echo "				{\n";
                    echo "					name.close();\n";
                    echo "				}\n";
                    echo "			// -->\n";
                    echo "		</script>\n";
                    echo "		<script language=\"JavaScript\" type=\"text/javascript\">\n";
                    echo "			<!--\n";
                    echo "				function change_legend(target)\n";
                    echo "				{\n";
                    echo "					LegendeFrame = eval(\"parent.legende\");\n";
                    echo "					LegendeBorderFrame = eval(\"parent.legende_border\");\n";
                    echo "					LegendeFrame.location.href = \"./templates/\"+target;\n";
                    echo "					LegendeBorderFrame.location.href = \"./templates/\"+target;\n";
                    echo "				}\n";
                    echo "			// -->\n";
                    echo "		</script>\n";
                    echo "	</head>\n";
                    echo "	<body bgcolor=\"#E2E3DF\" topmargin=\"0\" leftmargin=\"0\" marginwidth=\"0\" marginheight=\"0\">\n";
                    break;
                } 
            default: {
                    echo "		<script language=\"JavaScript\" type=\"text/javascript\">\n";
                    echo "			<!--\n";
                    echo "				if(window.event + \"\" == \"undefined\") event = null\n";
                    echo "				function HM_f_PopUp(){return false};\n";
                    echo "				function HM_f_PopDown(){return false};\n";
                    echo "				popUp = HM_f_PopUp;\n";
                    echo "				popDown = HM_f_PopDown;\n";
                    echo "				prev1 = new Image (141,108);\n";
                    echo "				prev1.src = \"./images/icons/firewall_icons.jpg\";\n";
                    echo "				HM_PG_MenuWidth = 300;\n";
                    echo "				HM_PG_FontFamily = \"Verdana,Arial,sans-serif\";\n";
                    echo "				HM_PG_FontSize = 7;\n";
                    echo "				HM_PG_FontBold = 0;\n";
                    echo "				HM_PG_FontItalic = 0;\n";
                    echo "				HM_PG_FontColor = \"blue\";\n";
                    echo "				HM_PG_FontColorOver = \"white\";\n";
                    echo "				HM_PG_BGColor = \"#DDDDDD\";\n";
                    echo "				HM_PG_BGColorOver = \"#FFCCCC\";\n";
                    echo "				HM_PG_ItemPadding = 1;\n";
                    echo "				HM_PG_BorderWidth = 1;\n";
                    echo "				HM_PG_BorderColor = \"black\";\n";
                    echo "				HM_PG_BorderStyle = \"solid\";\n";
                    echo "				HM_PG_SeparatorSize = 1;\n";
                    echo "				HM_PG_SeparatorColor = \"#d0ff00\";\n";
                    echo "				HM_PG_ImageSrc = \"./images/menu/DM_more_gray.gif\";\n";
                    echo "				HM_PG_ImageSrcLeft = \"HM_More_black_left.gif\";\n";
                    echo "				HM_PG_ImageSrcOver = \"./images/menu/DM_more_white.gif\";\n";
                    echo "				HM_PG_ImageSrcLeftOver = \"HM_More_white_left.gif\";\n";
                    echo "				HM_PG_ImageSize = 5;\n";
                    echo "				HM_PG_ImageHorizSpace = 0;\n";
                    echo "				HM_PG_ImageVertSpace = 2;\n";
                    echo "				HM_PG_KeepHilite = true;\n";
                    echo "				HM_PG_ClickStart = 0;\n";
                    echo "				HM_PG_ClickKill = false;\n";
                    echo "				HM_PG_ChildOverlap = 20;\n";
                    echo "				HM_PG_ChildOffset = 10;\n";
                    echo "				HM_PG_ChildPerCentOver = null;\n";
                    echo "				HM_PG_TopSecondsVisible = .5;\n";
                    echo "				HM_PG_StatusDisplayBuild = 0;\n";
                    echo "				HM_PG_StatusDisplayLink = 0;\n";
                    echo "				HM_PG_UponDisplay = null;\n";
                    echo "				HM_PG_UponHide = null;\n";
                    echo "				HM_PG_RightToLeft = 0;\n";
                    echo "				HM_PG_CreateTopOnly = 0;\n";
                    echo "				HM_PG_ShowLinkCursor = 1;\n";
                    echo "				HM_PG_NSFontOver = true;\n";
                    echo "			//-->\n";
                    echo "		</script>\n";
                    echo "		<script LANGUAGE=\"JavaScript1.2\" src=\"./scripts/HM_Loader.js\" type=\"text/javascript\"></script>\n";
                    echo "		<script language=\"JavaScript\" type=\"text/javascript\">\n";
                    echo "			<!--\n";
                    echo "				function popup(filename,name,width,height,scrollbars)\n";
                    echo "				{\n";
                    echo "					if (scrollbars == 'true')\n";
                    echo "					{\n";
                    echo "						window.open(filename,name,\"width=\"+width+\",height=\"+height+\",scrollbars\");\n";
                    echo "					}\n";
                    echo "					else\n";
                    echo "					{\n";
                    echo "						window.open(filename,name,\"width=\"+width+\",height=\"+height);\n";
                    echo "					}\n";
                    echo "				}\n";
                    echo "				function killpopup(filename,name)\n";
                    echo "				{\n";
                    echo "					name.close();\n";
                    echo "				}\n";
                    echo "			// -->\n";
                    echo "		</script>\n";
                    echo "		<script language=\"JavaScript\" type=\"text/javascript\">\n";
                    echo "			<!--\n";
                    echo "				function change_legend(target)\n";
                    echo "				{\n";
                    echo "					LegendeFrame = eval(\"parent.legende\");\n";
                    echo "					LegendeBorderFrame = eval(\"parent.legende_border\");\n";
                    echo "					LegendeFrame.location.href = \"./templates/\"+target;\n";
                    echo "					LegendeBorderFrame.location.href = \"./templates/\"+target;\n";
                    echo "				}\n";
                    echo "			// -->\n";
                    echo "		</script>\n";
                    echo "	</head>\n";
                    echo "	<body bgcolor=\"#E2E3DF\" topmargin=\"0\" leftmargin=\"0\" marginwidth=\"0\" marginheight=\"0\">\n";
                    echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
                    echo "			<tr valign=\"middle\">\n";
                    echo "				<td align=\"left\" width=\"32px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                    echo "					<img src=\"./images/tpx.gif\" width=\"32px\" height=\"23px\" border=\"0\"></td>\n";
                    echo "				<td align=\"left\" width=\"95px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                    echo "					<img src=\"./images/tpx.gif\" width=\"92px\" height=\"10px\" border=\"0\"></td>\n";
                    echo "				<td align=\"left\" width=\"95px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                    echo "					<img src=\"./images/tpx.gif\" width=\"92\" height=\"10\" border=\"0\"></td>\n";
                    echo "				<td align=\"left\" width=\"95px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                    echo "					<img src=\"./images/tpx.gif\" width=\"92\" height=\"10\" border=\"0\"></td>\n";
                    echo "				<td align=\"left\" width=\"95px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                    echo "					<img src=\"./images/tpx.gif\" width=\"92\" height=\"10\" border=\"0\"></td>\n";
                    echo "				<td align=\"left\" width=\"95px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                    echo "					<img src=\"./images/tpx.gif\" width=\"92\" height=\"10\" border=\"0\"></td>\n";
                    echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
                    echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
                    echo "			</tr>\n";
                    echo "		</table>\n";
                    break;
                } 
        } 
    } else {
        echo "		<script language=\"JavaScript\" type=\"text/javascript\">\n";
        echo "			<!--\n";
        echo "				if(window.event + \"\" == \"undefined\") event = null\n";
        echo "				function HM_f_PopUp(){return false};\n";
        echo "				function HM_f_PopDown(){return false};\n";
        echo "				popUp = HM_f_PopUp;\n";
        echo "				popDown = HM_f_PopDown;\n";
        echo "				prev1 = new Image (141,108);\n";
        echo "				prev1.src = \"./images/icons/firewall_icons.jpg\";\n";
        echo "				HM_PG_MenuWidth = 300;\n";
        echo "				HM_PG_FontFamily = \"Verdana,Arial,sans-serif\";\n";
        echo "				HM_PG_FontSize = 7;\n";
        echo "				HM_PG_FontBold = 0;\n";
        echo "				HM_PG_FontItalic = 0;\n";
        echo "				HM_PG_FontColor = \"blue\";\n";
        echo "				HM_PG_FontColorOver = \"white\";\n";
        echo "				HM_PG_BGColor = \"#DDDDDD\";\n";
        echo "				HM_PG_BGColorOver = \"#FFCCCC\";\n";
        echo "				HM_PG_ItemPadding = 1;\n";
        echo "				HM_PG_BorderWidth = 1;\n";
        echo "				HM_PG_BorderColor = \"black\";\n";
        echo "				HM_PG_BorderStyle = \"solid\";\n";
        echo "				HM_PG_SeparatorSize = 1;\n";
        echo "				HM_PG_SeparatorColor = \"#d0ff00\";\n";
        echo "				HM_PG_ImageSrc = \"./images/menu/DM_more_gray.gif\";\n";
        echo "				HM_PG_ImageSrcLeft = \"HM_More_black_left.gif\";\n";
        echo "				HM_PG_ImageSrcOver = \"./images/menu/DM_more_white.gif\";\n";
        echo "				HM_PG_ImageSrcLeftOver = \"HM_More_white_left.gif\";\n";
        echo "				HM_PG_ImageSize = 5;\n";
        echo "				HM_PG_ImageHorizSpace = 0;\n";
        echo "				HM_PG_ImageVertSpace = 2;\n";
        echo "				HM_PG_KeepHilite = true;\n";
        echo "				HM_PG_ClickStart = 0;\n";
        echo "				HM_PG_ClickKill = false;\n";
        echo "				HM_PG_ChildOverlap = 20;\n";
        echo "				HM_PG_ChildOffset = 10;\n";
        echo "				HM_PG_ChildPerCentOver = null;\n";
        echo "				HM_PG_TopSecondsVisible = .5;\n";
        echo "				HM_PG_StatusDisplayBuild = 0;\n";
        echo "				HM_PG_StatusDisplayLink = 0;\n";
        echo "				HM_PG_UponDisplay = null;\n";
        echo "				HM_PG_UponHide = null;\n";
        echo "				HM_PG_RightToLeft = 0;\n";
        echo "				HM_PG_CreateTopOnly = 0;\n";
        echo "				HM_PG_ShowLinkCursor = 1;\n";
        echo "				HM_PG_NSFontOver = true;\n";
        echo "			//-->\n";
        echo "		</script>\n";
        echo "		<script LANGUAGE=\"JavaScript1.2\" src=\"./scripts/HM_Loader.js\" type=\"text/javascript\"></script>\n";
        echo "		<script language=\"JavaScript\" type=\"text/javascript\">\n";
        echo "			<!--\n";
        echo "				function popup(filename,name,width,height,scrollbars)\n";
        echo "				{\n";
        echo "					if (scrollbars == 'true')\n";
        echo "					{\n";
        echo "						window.open(filename,name,\"width=\"+width+\",height=\"+height+\",scrollbars\");\n";
        echo "					}\n";
        echo "					else\n";
        echo "					{\n";
        echo "						window.open(filename,name,\"width=\"+width+\",height=\"+height);\n";
        echo "					}\n";
        echo "				}\n";
        echo "				function killpopup(filename,name)\n";
        echo "				{\n";
        echo "					name.close();\n";
        echo "				}\n";
        echo "			// -->\n";
        echo "		</script>\n";
        echo "		<script language=\"JavaScript\" type=\"text/javascript\">\n";
        echo "			<!--\n";
        echo "				function change_legend(target)\n";
        echo "				{\n";
        echo "					LegendeFrame = eval(\"parent.legende\");\n";
        echo "					LegendeBorderFrame = eval(\"parent.legende_border\");\n";
        echo "					LegendeFrame.location.href = \"./templates/\"+target;\n";
        echo "					LegendeBorderFrame.location.href = \"./templates/\"+target;\n";
        echo "				}\n";
        echo "			// -->\n";
        echo "		</script>\n";

        echo "	</head>\n";
        echo "	<body bgcolor=\"#E2E3DF\" topmargin=\"0\" leftmargin=\"0\" marginwidth=\"0\" marginheight=\"0\">\n";
        echo "		<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\" width=\"100%\" height=\"23px\">\n";
        echo "			<tr valign=\"middle\">\n";
        echo "				<td align=\"left\" width=\"32px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
        echo "					<img src=\"./images/tpx.gif\" width=\"32px\" height=\"23px\" border=\"0\"></td>\n";
        echo "				<td align=\"left\" width=\"95px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
        echo "					<img src=\"./images/tpx.gif\" width=\"92px\" height=\"10px\" border=\"0\"></td>\n";
        echo "				<td align=\"left\" width=\"95px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
        echo "					<img src=\"./images/tpx.gif\" width=\"92\" height=\"10\" border=\"0\"></td>\n";
        echo "				<td align=\"left\" width=\"95px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
        echo "					<img src=\"./images/tpx.gif\" width=\"92\" height=\"10\" border=\"0\"></td>\n";
        echo "				<td align=\"left\" width=\"95px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
        echo "					<img src=\"./images/tpx.gif\" width=\"92\" height=\"10\" border=\"0\"></td>\n";
        echo "				<td align=\"left\" width=\"95px\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
        echo "					<img src=\"./images/tpx.gif\" width=\"92\" height=\"10\" border=\"0\"></td>\n";
        echo "				<td align=\"left\" height=\"23px\" bgcolor=\"#E2E3DF\">\n";
        echo "					<img src=\"./images/tpx.gif\" width=\"200px\" height=\"23px\" border=\"0\"></td>\n";
        echo "			</tr>\n";
        echo "		</table>\n";
    } 
} 
// ----------------------------
// | Correct Priorities		  |
// ----------------------------
// | Last Change : 31.01.2002 |
// ----------------------------
// | Status : Enabled		  |
// ----------------------------
function correct_priorities($section, $tablename)
{ 
    // Database Functions #
    $result = mysql_query("select * from " . $tablename . " order by priority");
    $number = mysql_num_rows($result);

    for ($i = 1; $i <= $number; $i++) {
        $row = mysql_fetch_array($result);
        $result_update = mysql_query("update " . $tablename . " set priority='" . ($i * 10) . "' where(id='" . $row['id'] . "')");
    } 
} 
// ----------------------------
// | Generate Magic Key		  |
// ----------------------------
// | Last Change : 27.11.2001 |
// ----------------------------
// | Status : Enabled		  |
// ----------------------------
function generate_magic()
{
    list($usec, $sec) = explode(" ", microtime());
    return md5(((float)$usec + (float)$sec) * 10000);
} 
function checkhostname($hostname, $oldhostname, $tablename)
{
    $result = mysql_query("select * from " . $tablename . " where(name='" . $oldhostname . "')") or die(mysql_error());
    $row = mysql_fetch_array($result);
    $id = $row['id'];
    $validator = true;

    $result = mysql_query("select * from " . $tablename . " order by id");
    $number = mysql_num_rows($result);

    for ($i = 0;$i < $number; $i++) {
        $row = mysql_fetch_array($result);

        if (strtolower($hostname) == strtolower($row['name'])) {
            if (empty($id)) {
                return false;
            } else {
                if ($row['id'] != $id) {
                    return false;
                } else {
                    $validator = true;
                } 
            } 
        } else {
            $validator = true;
        } 
    } 

    return (bool)($validator);
} 

function checkhostmask($ip, $tablename, $field)
{
    $result = mysql_query("select * from " . $tablename . " where(" . $field . "='" . $ip . "')");
    $row = mysql_fetch_array($result);
    $oid = $row['id'];
    $validator = true;

    $result = mysql_query("select * from " . $tablename . " order by id");
    $number = mysql_num_rows($result);

    for ($i = 0;$i < $number; $i++) {
        $row = mysql_fetch_array($result);

        if (strtolower($ip) == strtolower($row['ip'])) {
            if ((int)($row['id']) != (int)($oid)) {
                $validator = false;
            } 
        } 
    } 

    $ippool = explode(".", $ip);

    if (count($ippool) == 4) {
        if ((isset($ippool[0])) and (isset($ippool[1])) and (isset($ippool[2])) and (isset($ippool[3]))) {
            if (((int)($ippool[0]) >= 0) and ((int)($ippool[1]) >= 0) and ((int)($ippool[2]) >= 0) and ((int)($ippool[3]) >= 0)) {
                if (((int)($ippool[0]) <= 255) and ((int)($ippool[1]) <= 255) and ((int)($ippool[2]) <= 255) and ((int)($ippool[3]) <= 255)) {
                    $validator = true;
                } else {
                    $validator = false;
                } 
            } else {
                $validator = false;
            } 
        } else {
            $validator = false;
        } 
    } else {
        $validator = false;
    } 

    return $validator;
} 

function errorcode($errorcode, $subsection = 0)
{
    switch ($errorcode) {
        // Operation successfull
        case 0: {
                echo "<center><i><b>Success: Entry successfully added/changed !</b></i>";
                echo "<br><a href=\"" . $PHP_SELF . "?mainsection=t_objects&section=t_objects_item&subsection=" . $subsection . "\">Zurueck</a></center>";
                echo "</td></tr></table>\n";
                break;
            } 
            // Hostname Error
        case 1: {
                echo "<center><i><b>Error: Invalid or empty Hostname</b></i>";
                echo "<br><a href=\"javascript:history.back(1)\">Back</a></center>";
                echo "</td></tr></table>\n";
                break;
            } 
            // Address Error
        case 2: {
                echo "<center><i><b>Error: Invalid or incomplete Address !</b></i>";
                echo "<br><a href=\"javascript:history.back(1)\">Back</a></center>";
                echo "</td></tr></table>\n";
                break;
            } 
            // Duplicated Entry
        case 3: {
                echo "<center><i><b>Error: Duplicated Entry found !</b></i>";
                echo "<br><a href=\"javascript:history.back(1)\">Back</a></center>";
                echo "</td></tr></table>\n";
                break;
            } 
            // Field Error
        case 4: {
                echo "<center><i><b>Error: Not all fields were filled !</b></i>";
                echo "<br><a href=\"javascript:history.back(1)\">Back</a></center>";
                echo "</td></tr></table>\n";
                break;
            } 
            // Command Error
        case 5: {
                echo "<center><i><b>Error: No valid command !</b></i>";
                echo "<br><a href=\"javascript:history.back(1)\">Back</a></center>";
                echo "</td></tr></table>\n";
                break;
            } 
            // Entry added
        case 6: {
                echo "<center><i><b>Success: Entry successfully deleted !</b></i>";
                echo "<br><a href=\"javascript:history.back(1)\">Back</a></center>";
                echo "</td></tr></table>\n";
                break;
            } 
            // Unhandled Call
        case 7: {
                echo "<center><i><b>Error: Unhandled Call !</b></i>";
                echo "<br><a href=\"javascript:history.back(1)\">Back</a></center>";
                echo "</td></tr></table>\n";
                break;
            } 
            // Global MySQL Error
        case 8: {
                echo "<center><i><b>Error: Global MySQL Exception (" . $subsection . ")</b></i>";
                echo "<br><a href=\"javascript:history.back(1)\">Back</a></center>";
                echo "</td></tr></table>\n";
                break;
            } 
    } 
} 
// ----------------------------
// | Secure Delete			  |
// ----------------------------
// | Last Change : 26.03.2003 |
// ----------------------------
// | Status : Enabled		  |
// ----------------------------
function secure_delete($section, $tablename, $id, $sd_override)
{
    $secure = new dbvars; 
    // check for Section #
    if ($section == "hosts") {
        // check for Override Setting #
        if (($sd_override == "no") or (!isset($sd_override))) {
            $result_pptp = mysql_query("select * from " . $secure->sql_db_table_pptp_layers . " where ip_adress = '" . $id . "'");
            $amount_pptp = mysql_num_rows($result_pptp);
            $result_filter = mysql_query("select * from " . $secure->sql_db_table_strategies_filter . " where((stype = 1 || dtype = 1) && (did = " . $id . " || sid = " . $id . "))");
            $amount_filter = mysql_num_rows($result_filter);
            $result_nat = mysql_query("select * from " . $secure->sql_db_table_strategies_nat . " where((stype = 1 || dtype = 1) && (did = " . $id . " || sid = " . $id . " || toid = " . $id . "))");
            $amount_nat = mysql_num_rows($result_nat);
            $result_routing = mysql_query("select * from " . $secure->sql_db_table_strategies_routing . " where(type = 1 && (did = " . $id . " || gateway = " . $id . "))");
            $amount_routing = mysql_num_rows($result_routing);
            $result_cbq = mysql_query("select * from " . $secure->sql_db_table_cbq_rules . " where(toid = 1 && (tid = " . $id . "))");
            $amount_cbq = mysql_num_rows($result_cbq);
            $amount = intval($amount_pptp) + intval($amount_filter) + intval($amount_nat) + intval($amount_routing) + intval($amount_cbq);

            if ($amount == 0) {
                $result_delete = mysql_query("delete from " . $secure->sql_db_table_no_hosts . " where(id=" . $id . ")");
                show_objects_networkobjects(0, "hosts", "OBJECTS | <B>HOSTS</B>", $secure->sql_db_table_no_hosts);
            } else {
                echo "<br><br><center><i><b>Warning: Host is in use </b></i><br>\n";
                echo "(if you proceed all entries, containing this host will also be deleted)\n<br>";

                echo "<br><a href=\"" . $PHP_SELF . "?module=" . $section . "&action=delete&sid=" . $id . "&sd_override=yes\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;<a href=\"" . $PHP_SELF . "?module=" . $section . "&action=list\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a></center>";
                echo "</td></tr></table>\n";
            } 
        } elseif ($sd_override == "yes") {
            $result_pptp = mysql_query("delete from " . $secure->sql_db_table_pptp_layers . " where ip_adress = '" . $id . "'") or die(mysql_error());
            $result_filter = mysql_query("delete from " . $secure->sql_db_table_strategies_filter . " where((stype = 1 || dtype = 1) && (did = " . $id . " || sid = " . $id . "))") or die(mysql_error());
            $result_nat = mysql_query("delete from " . $secure->sql_db_table_strategies_nat . " where((stype = 1 || dtype = 1) && (did = " . $id . " || sid = " . $id . " || toid = " . $id . "))") or die(mysql_error());
            $result_routing = mysql_query("delete from " . $secure->sql_db_table_strategies_routing . " where(type = 1 && (did = " . $id . " || gateway = " . $id . "))") or die(mysql_error());
            $result_hosts = mysql_query("delete from " . $secure->sql_db_table_no_hosts . " where(id = " . $id . ")") or die(mysql_error());
            $result_cbq = mysql_query("delete from " . $secure->sql_db_table_cbq_rules . " where(toid = 1 && (tid = " . $id . "))");

            show_objects_networkobjects(0, "hosts", "OBJECTS | <B>HOSTS</B>", $secure->sql_db_table_no_hosts);
        } else {
            // if override is cancel or in another state, cancel process and go back to show event #
            show_objects_networkobjects(0, "hosts", "OBJECTS | <B>HOSTS</B>", $secure->sql_db_table_no_hosts);
        } 
    } elseif ($section == "users") {
        mysql_query("delete from users where id=" . $id);
        show_users("users", "OBJECTS | <B>USERS</B>", "users");
    } elseif ($section == "networks") {
        // check for Override Setting #
        if (($sd_override == "no") or (!isset($sd_override))) {
            $result_filter = mysql_query("select * from " . $secure->sql_db_table_strategies_filter . " where((stype = 2 || dtype = 2) && (did = " . $id . " || sid = " . $id . "))");
            $amount_filter = mysql_num_rows($result_filter);
            $result_nat = mysql_query("select * from " . $secure->sql_db_table_strategies_nat . " where((stype = 2 || dtype = 2) && (did = " . $id . " || sid = " . $id . "))");
            $amount_nat = mysql_num_rows($result_nat);
            $result_routing = mysql_query("select * from " . $secure->sql_db_table_strategies_routing . " where(type = 2 && (did = " . $id . "))");
            $amount_routing = mysql_num_rows($result_routing);
            $result_cbq = mysql_query("select * from " . $secure->sql_db_table_cbq_rules . " where(toid = 2 && (tid = " . $id . "))");
            $amount_cbq = mysql_num_rows($result_cbq);
            $amount = intval($amount_filter) + intval($amount_nat) + intval($amount_routing);

            if ($amount == 0) {
                $result_delete = mysql_query("delete from " . $secure->sql_db_table_no_networks . " where(id=" . $id . ")");
                show_objects_networkobjects(1, "networks", "OBJECTS | <B>NETWORKS</B>", $secure->sql_db_table_no_networks);
            } else {
                echo "<br><br><center><i><b>Warning: Network is in use </b></i><br>\n";
                echo "(if you proceed all entries, containing this host will also be deleted)\n<br>";

                echo "<br><a href=\"" . $PHP_SELF . "?module=" . $section . "&action=delete&sid=" . $id . "&sd_override=yes\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;<a href=\"" . $PHP_SELF . "?module=" . $section . "&action=list\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a></center>";
                echo "</td></tr></table>\n";
            } 
        } elseif ($sd_override == "yes") {
            $result_filter = mysql_query("delete from " . $secure->sql_db_table_strategies_filter . " where((stype = 2 || dtype = 2) && (did = " . $id . " || sid = " . $id . "))") or die(mysql_error());
            $result_nat = mysql_query("delete from " . $secure->sql_db_table_strategies_nat . " where((stype = 2 || dtype = 2) && (did = " . $id . " || sid = " . $id . "))") or die(mysql_error());
            $result_routing = mysql_query("delete from " . $secure->sql_db_table_strategies_routing . " where(type = 2 && did = " . $id . ")") or die(mysql_error());
            $result_hosts = mysql_query("delete from " . $secure->sql_db_table_no_networks . " where(id = " . $id . ")") or die(mysql_error());
            $result_cbq = mysql_query("delete from " . $secure->sql_db_table_cbq_rules . " where(toid = 2 && (tid = " . $id . "))");

            show_objects_networkobjects(1, "networks", "OBJECTS | <B>NETWORKS</B>", $secure->sql_db_table_no_networks);
        } else {
            // if override is cancel or in another state, cancel process and go back to show event #
            show_objects_networkobjects(1, "networks", "OBJECTS | <B>NETWORKS</B>", $secure->sql_db_table_no_networks);
        } 
    } elseif ($section == "interfaces") {
        // check for Override Setting #
        if (($sd_override == "no") or (!isset($sd_override))) {
            $result_filter = mysql_query("select * from " . $secure->sql_db_table_strategies_filter . " where(siface = " . $id . " || diface = " . $id . ")");
            $amount_filter = mysql_num_rows($result_filter);
            $result_cbq = mysql_query("select * from " . $secure->sql_db_table_strategies_cbq . " where(interface = " . $id . ")");
            $amount_cbq = mysql_num_rows($result_cbq);
            $result_nat = mysql_query("select * from " . $secure->sql_db_table_strategies_nat . " where(iiface = " . $id . " || oiface = " . $id . ")");
            $amount_nat = mysql_num_rows($result_nat);
            $result_routing = mysql_query("select * from " . $secure->sql_db_table_strategies_routing . " where(iid = " . $id . ")");
            $amount_routing = mysql_num_rows($result_routing);
            $result_tbf = mysql_query("select * from " . $secure->sql_db_table_strategies_tbf . " where(iid = " . $id . ")");
            $amount_tbf = mysql_num_rows($result_tbf);

            $amount = intval($amount_filter) + intval($amount_cbq) + intval($amount_nat) + intval($amount_routing) + intval($amount_tbf);

            if ($amount == 0) {
                $result_delete = mysql_query("delete from " . $secure->sql_db_table_io_interfaces . " where(id=" . $id . ")");
                show_objects_interfaces(0, "interfaces", "OBJECTS | <B>INTERFACES</B>", $secure->sql_db_table_io_interfaces);
            } else {
                echo "<br><br><center><i><b>Warning: Interface is in use </b></i><br>\n";
                echo "(if you proceed all entries, containing this host will also be deleted)\n<br>";

                echo "<br><a href=\"" . $PHP_SELF . "?module=" . $section . "&action=delete&sid=" . $id . "&sd_override=yes\"><img src=\"./images/change.gif\" border=\"0\"></a>&nbsp;<a href=\"" . $PHP_SELF . "?module=" . $section . "&action=list\"><img src=\"./images/icons/cancel.gif\" border=\"0\"></a></center>";
                echo "</td></tr></table>\n";
            } 
        } elseif ($sd_override == "yes") {
            $result_filter = mysql_query("delete from " . $secure->sql_db_table_strategies_filter . " where(siface = " . $id . " || diface = " . $id . ")");
            $result_cbq = mysql_query("delete from " . $secure->sql_db_table_strategies_cbq . " where(interface = " . $id . ")");
            $result_nat = mysql_query("delete from " . $secure->sql_db_table_strategies_nat . " where(iiface = " . $id . " || oiface = " . $id . ")");
            $result_routing = mysql_query("delete from " . $secure->sql_db_table_strategies_routing . " where(iid = " . $id . ")");
            $result_tbf = mysql_query("delete from " . $secure->sql_db_table_strategies_tbf . " where(iid = " . $id . ")");
            $result_interface = mysql_query("delete from " . $secure->sql_db_table_io_interfaces . " where(id = " . $id . ")");

            show_objects_interfaces(0, "interfaces", "OBJECTS | <B>INTERFACES</B>", $secure->sql_db_table_io_interfaces);
        } else {
            // if override is cancel or in another state, cancel process and go back to show event #
            show_objects_interfaces(0, "interfaces", "OBJECTS | <B>INTERFACES</B>", $secure->sql_db_table_io_interfaces);
        } 
    } 
} 
// -------------------------------
// | Correct Priorities (Remote) |
// -------------------------------
// | Last Change : 14.11.2001	 |
// -------------------------------
// | Status : Enabled			 |
// -------------------------------
function correct_priorities_remote()
{
    $correct = new dbvars; 
    // Database Functions #
    $result = mysql_query("select * from " . $correct->sql_db_table_strategies_filter . " order by priority");
    $number = mysql_num_rows($result);

    for ($i = 1; $i <= $number; $i++) {
        $row = mysql_fetch_array($result);
        $result_update = mysql_query("update " . $correct->sql_db_table_strategies_filter . " set priority='" . ($i * 10) . "' where(id='" . $row['id'] . "')");
    } 
} 
// -------------------------------
// | Check Security in Module	 |
// -------------------------------
// | Last Change : 07.03.2002	 |
// -------------------------------
// | Status : Enabled			 |
// -------------------------------
function module_security()
{
    if (isset($_SESSION['database']) == 0) return false;
    if (isset($_SESSION['username']) == 0) return false;
    if (isset($_SESSION['session_magic']) == 0) return false;

    $query = mysql_query("select * from " . $_SESSION['database'] . " where (username='" . $_SESSION['username'] . "' and magic='" . $_SESSION['session_magic'] . "')");
    $row = mysql_fetch_array($query);

    if (!empty($row)) {
        // Valid User Found
        return true;
    } else {
        // No Valid User Found
        return false;
    } 
} 
// -------------------------------
// |Convert IPv4 to 32bit binary |
// -------------------------------
// | Last Change : 15.04.2003	 |
// -------------------------------
// | Status : Enabled		 |
// -------------------------------
function ip2bin($ip)
{
    $dec_ip = explode(".", $ip);
    foreach ($dec_ip as $rr) {
        $bin_ip[] = sprintf("%08d", decbin($rr));
    } 
    return join("", $bin_ip);
} 
// ---------------------------------
// | netmask check (Sub,Main)      |
// ---------------------------------
// | Last Change : 15.04.2003	   |
// ---------------------------------
// | Status : Enabled		   |
// ---------------------------------
function netmask_check($netmask)
{ 
    // check for invalid mask
    $netmask_long = ip2long($netmask); //Convert IP Address to long value
    $netmask_reverse = long2ip($netmask_long); //if it could be re-converted the IP seems to be Ok.
    if ($netmask != $netmask_reverse)
        return false;
    if ($netmask == "0.0.0.0") {
        return false; //netmask 0.0.0.0 isn't it
    } 
    // Convert to binary
    $netmask_bin = ip2bin($netmask);
    if (substr_count($netmask_bin, "01") == 0) { // if 01 is found the mask is invalid
        return true;
    } else {
        return false;
    } 
} 
// ---------------------------------
// | IP Address check (Sub,Main)   |
// ---------------------------------
// | Last Change : 14.04.2003	   |
// ---------------------------------
// | Status : Enabled		   |
// ---------------------------------
function ip_address_check($ip)
{
    if (!is_string($ip)) {
        return false;
    } 
    if ((substr($ip, (strrpos($ip, ".") + 1)) == 0) or (substr($ip, (strrpos($ip, ".") + 1)) == 255)) {
        return false; // user tries to assign Net- or broadcast Address
    } 
    $ip_long = ip2long($ip); //Convert IP Address to long value
    $ip_reverse = long2ip($ip_long); //if it could be re-converted the IP seems to be Ok.
    if ($ip == $ip_reverse) {
        return true;
    } else {
        return false;
    } 
} 
// ---------------------------------
// | Network Address Address check (Sub,Main)   |
// ---------------------------------
// | Last Change : 17.06.2005	   |
// ---------------------------------
// | Status : Enabled		   |
// ---------------------------------
function na_address_check($ip)
{
    if (!is_string($ip)) {
        return false;
    } 
    $ip_long = ip2long($ip); //Convert IP Address to long value
    $ip_reverse = long2ip($ip_long); //if it could be re-converted the IP seems to be Ok.
    if ($ip == $ip_reverse) {
        return true;
    } else {
        return false;
    } 
} 
// -------------------------------------------
// | Language Themability (Description)       |
// -------------------------------------------
// | Last Change : 28.04.2003                 |
// -------------------------------------------
// | Status : Disabled			              |
// -------------------------------------------
function getDesc($idDescription)
{
    $info = new info();
    $result = mysql_query("select sDescription from viswall_description where(idLanguage = '" . $info->g_language . "' and idDescription = '" . $idDescription . "')");
    $row = mysql_fetch_array($result);

    return $row['sDescription'];
} 
// -------------------------------
// | Activate Changings			 |
// -------------------------------
// | Last Change : 08.03.2002	 |
// -------------------------------
// | Status : Enabled			 |
// -------------------------------
function activate($module, $action, $params)
{
    $execfilter = "/viswall/execscripts/filter/mysql2bash.pl";
    $execnat = "/viswall/execscripts/nat/mysql2bash.pl";
    $global = "/viswall/execscripts/pptpd/mysql2bash.pl";
    $execcbq = "/viswall/execscripts/tc/mysql2bash.pl";
    $exectbf = "/viswall/execscripts/tc/mysql2bash.pl";
    $execmss = "/viswall/execscripts/mailscanner/mysql2bash.pl";
    $execmss_rules = "/viswall/execscripts/mailscanner/mysql2bash.pl";
    $execinterfaces = "/viswall/execscripts/objects/interfaces/mysql2bash.pl";
    $execpptp = "/viswall/execscripts/pptpd/mysql2bash.pl";
    $execsquid = "/viswall/execscripts/squid/mysql2bash.pl";
    $execset_ip = "/viswall/execscripts/set_ip/set_ip.php"; 
    // f.e.:
    // $action = "xcopy"
    // $params = "a:\*.* c:\"
    // orig, 3. 6. 2015
    $MSGKEY = 10001;
    //$MSGKEY = 650001;

    $msg_id = msg_get_queue ($MSGKEY, 0666);

    switch ($module) {
        case squid: { // added Squid Support by Enzi 26.1.2005
                echo "squid executed";
                if (!msg_send ($msg_id, 1, $execsquid, false, true, $msg_err))
                    echo "Msg not sent because $msg_err\n";
                break;
            } 
        case filter: {
                if (!msg_send ($msg_id, 1, $execfilter, false, true, $msg_err))
                    echo "Msg not sent because $msg_err\n";
                break;
            } 
        case nat: {
                if (!msg_send ($msg_id, 1, $execnat, false, true, $msg_err))
                    echo "Msg not sent because $msg_err\n";
                break;
            } 
        case pptp: {
                if (!msg_send ($msg_id, 1, $execpptp, false, true, $msg_err))
                    echo "Msg not sent because $msg_err\n";
                break;
            } 
        case cbq: {
                if (!msg_send ($msg_id, 1, $execcbq, false, true, $msg_err))
                    echo "Msg not sent because $msg_err\n";
                break;
            } 
        case tbf: {
                if (!msg_send ($msg_id, 1, $exectbf, false, true, $msg_err))
                    echo "Msg not sent because $msg_err\n";
                break;
            } 
        case mss: {
                if (!msg_send ($msg_id, 1, $execmss, false, true, $msg_err))
                    echo "Msg not sent because $msg_err\n";
                break;
            } 
        case mss_rules: {
                if (!msg_send ($msg_id, 1, $execmss_rules, false, true, $msg_err))
                    echo "Msg not sent because $msg_err\n";
                break;
            } 
        case interfaces: {
                if (!msg_send ($msg_id, 1, $execinterfaces, false, true, $msg_err))
                    echo "Msg not sent because $msg_err\n";
                if (!msg_send ($msg_id, 1, $execset_ip, false, true, $msg_err))
                    echo "Msg not sent because $msg_err\n";

                break;
            } 
        default: {
                if (!msg_send ($msg_id, 1, $module, false, true, $msg_err))
                    echo "Msg not sent because $msg_err\n";
                break;
            } 
    } 

    /*switch($module)
			{
				// <HOSTS> : <31.01.2002>
				case hosts:
				{
					break;
				}
				// <NETWORKS> : <31.01.2002>
				case networks:
				{
					break;
				}
				// <SERVICES> : <31.01.2002>
				case services:
				{
					break;
				}
				// <INTERFACES> : <31.01.2002>
				case interfaces:
				{
					break;
				}
				// <FILTER> : <31.01.2002>
				case filter:
				{
					// Code to execute
						exec("perl /daten/webs/test/viswall/execscripts/filter/mysql2bash.pl > /dev/null");
					// Return to spawn point, when done
						$path = new path;

						include($path->path_modules_functions."/filter/filterconfig.php");

						$sql_db_local = new sql_db_local;

						include($path->path_modules_functions."/filter/filterlib.php");
						show_strategies(0, "filter", "STRATEGY | <B>FIREWALL</B>", $sql_db_local->sql_db_table_strategies_filter);
					
					break;
				}
				// <NAT&PAT> : <31.01.2002>
				case nat:
				{
					// Code to execute
					
					// Return to spawn point, when done
					    $path = new path;

						include($path->path_modules_functions."/nat/natconfig.php");

						$sql_db_local = new sql_db_local;

						include($path->path_modules_functions."/nat/natlib.php");
						show_nat(0, "nat", "STRATEGY | <B>N.A.T.</B>", $sql_db_local->sql_db_table_strategies_nat);
					
					break;
				}
				// <QoS>-<CBQ> : <05.02.2002>
				case cbq:
				{
					// Code to execute
					
					// Return to spawn point, when done
						$path = new path;
						include($path->path_modules_functions."/qos/cbq/cbqconfig.php");
						$sql_db_local = new sql_db_local;
						include($path->path_modules_functions."/qos/cbq/cbqlib.php");
						show_cbq("cbq", "STRATEGY | <B>QoS - CBQ</B>", $sql_db_local->sql_db_table_strategies_cbq);
					
					break;
				}
				// <QoS>-<TBF> : <05.02.2002>
				{
					// Code to execute
					
					// Return to spawn point, when done
						$path = new path;
						include($path->path_modules_functions."/qos/tbf/tbfconfig.php");
						$sql_db_local = new sql_db_local;
						include($path->path_modules_functions."/qos/tbf/tbflib.php");
						show_tbf("tbf", "STRATEGY | <B>QoS - TBF</B>", $sql_db_local->sql_db_table_strategies_tbf);
					
					break;
				}
				// <SQUID>-<Settings> : <18.02.2002>
				case squid:
				{
					// Code to execute
					
					// Return to spawn point, when done
						$path = new path;
						include($path->path_modules_functions."/squid/squidconfig.php");
						$sql_db_local = new sql_db_local;
						include($path->path_modules_functions."/squid/squidlib.php");
						show_squid("squid", "STRATEGY | <B>PROXY</B>", $sql_db_local->sql_db_table_strategies_squid);
					
					break;
				}
				// <VPN>-<PPTP> : <18.02.2002>
				case pptp:
				{
					// Code to execute
					
					// Return to spawn point, when done
						$path = new path;
						include($path->path_modules_functions."/vpn/pptp/pptpconfig.php");
						$sql_db_local = new sql_db_local;
						include($path->path_modules_functions."/vpn/pptp/pptplib.php");
						show_serverinfo("pptp", "STRATEGY | <B>VPN - PPTP</B>", $sql_db_local->sql_db_table_pptp_options);
					
					break;
				}
				case users:
				{
					break;
				}
				// <MSS>-<SETTINGS> : <27.02.2002>
				case mss:
				{
					// Code to execute
					
					// Return to spawn point, when done
						$path = new path;
						include($path->path_modules_functions."/mss/settings/mssconfig.php");
						$sql_db_local = new sql_db_local;
						include($path->path_modules_functions."/mss/settings/msslib.php");
						show_serverinfo("mss", "STRATEGY | <B>MailScanner - Settings</B>", $sql_db_local->sql_db_table_mss_general, $sql_db_local->sql_db_table_control_mss);
					
					break;
				}
				// <MSS>-<RULES> : <27.02.2002>
				case mss_rules:
				{
					// Code to execute
					
					// Return to spawn point, when done
						$path = new path;
						include($path->path_modules_functions."/mss/rules/mss_rulesconfig.php");
						$sql_db_local = new sql_db_local;
						include($path->path_modules_functions."/mss/rules/mss_ruleslib.php");
						show_rules("mss_rules", "STRATEGY | <B>MailScanner - Filename rules</B>", $sql_db_local->sql_db_table_mss_filename_rules);
					
					break;
				}
				// <MSS>-<DOMAINS> : <27.02.2002>
				case mss_domain:
				{
					break;
				}
				// <NIDS>-<SETTINGS> : <27.02.2002>
				case nids:
				{
					break;
				}
				// <SPLASH SCREEN> : <07.03.2002>
				default:
				{
					break;
				}
			}*/
} 
// ---------------------------------
// | Gateway <-> IP/Subnet Compare |
// ---------------------------------
// | Last Change : 28.05.2002	   |
// ---------------------------------
// | Status : Disabled			   |
// ---------------------------------
function gateipcompare()
{ 
    // Do not Tresspass ... they will eat you !!!
    $gipcomp = new dbvars;

    $result_gateway = mysql_query("select * from " . $gipcomp->sql_db_table_io_gateway);
    $result_interfaces = mysql_query("select * from " . $gipcomp->sql_db_table_io_interfaces);

    $data_gateway = mysql_fetch_array($result_gateway);
    $array_gateway = split("\.", $data_gateway['adress']);

    for($i = 0; $i < intval(mysql_num_rows($result_interfaces)); $i++) {
        $data_interfaces = mysql_fetch_array($result_interfaces); 
        // Compare Interface Data with Gateway Entry
        $array_subnet = split("\.", $data_interfaces['netmask']);
        $array_ip = split("\.", $data_interfaces['ip']);
        $hosts = array((256 - intval($array_subnet[0])), (256 - intval($array_subnet[1])), (256 - intval($array_subnet[2])), (256 - intval($array_subnet[3])));
        $curpos = 0;

        for($j = 0; $j < count($hosts); $j++) {
            if ($hosts[$j] == 1)
                $curpos = $curpos + 1;
        } 

        $error = 0;

        for($k = 0; $k < $curpos; $k++) {
            if ($array_ip[$k] != $array_gateway[$k])
                $error = 1;
        } 

        if ($error == 0) {
            if ($curpos < count($hosts)) {
                for ($l = 1; $l <= (count($hosts) - $curpos); $l++) {
                    if (($array_gateway[count($hosts) - $l] > 0) && ($array_gateway[count($hosts) - $l] < 255) && ($array_gateway[count($hosts) - $l] <= $hosts[count($hosts) - $l])) {
                        $error = 0;
                    } else {
                        $error = 1;
                    } 
                } 
            } 
        } 

        if ($error == 1) {
            echo "Interface $i: gateway not accessible<br>";
        } else {
            echo "Interface $i: gateway is accessible<br>";
        } 
    } 
    // $result_pptp = mysql_query("select * from ".$secure->sql_db_table_pptp_layers." where ip_adress = '".$id."'");
    // $amount_pptp = mysql_num_rows($result_pptp);
    // $result_filter = mysql_query("select * from ".$secure->sql_db_table_strategies_filter." where((stype = 1 || dtype = 1) && (did = ".$id." || sid = ".$id."))");
    // $amount_filter = mysql_num_rows($result_filter);
    // $result_nat = mysql_query("select * from ".$secure->sql_db_table_strategies_nat." where((stype = 1 || dtype = 1) && (did = ".$id." || sid = ".$id." || toid = ".$id."))");
    // $amount_nat = mysql_num_rows($result_nat);
    // $result_routing = mysql_query("select * from ".$secure->sql_db_table_strategies_routing." where(type = 1 && (did = ".$id." || gateway = ".$id."))");
    // $amount_routing = mysql_num_rows($result_routing);
    // $result_cbq = mysql_query("select * from ".$secure->sql_db_table_cbq_rules." where(toid = 1 && (tid = ".$id."))");
    // $amount_cbq = mysql_num_rows($result_cbq);
    // $amount = intval($amount_pptp) + intval($amount_filter) + intval($amount_nat) + intval($amount_routing) + intval($amount_cbq);
    // $gipcomp->sql_db_table_io_interfaces
    // echo "huhu";
} 

function checktype($data, $type)
{
    switch ($type) {
        case 'integer':
            return is_int($data);
            break;
        case 'boolean':
            return is_bool($data);
            break;
        case 'float':
            return is_float($data);
            break;
        case 'numeric':
            return is_numeric($data);
            break;
        case 'string':
            return is_string($data);
            break;
        case 'array':
            return is_array($data);
            break;
        case 'object':
            return is_object($data);
            break;
    } 
} 

?>
