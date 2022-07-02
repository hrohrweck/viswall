<?php
		if (module_security() == true)
		{
?>
<table cellspacing="0" cellpadding="0" border="0" width="100%" height="23px">
<tr valign="top">
	<td align="left" width="44px" height="23px" bgcolor="#E2E3DF"><img src="./images/tpx.gif" width="44px" height="23px" border="0"></td>
	<td align="left" height="23px" bgcolor="#E2E3DF">STRATEGY | <B>VPN - OpenVPN</B> &nbsp;</td>
	<td align="left" height="23px" bgcolor="#E2E3DF"><img src="./images/tpx.gif" width="200px" height="23px" border="0"></td>
</tr>
</table>
<CENTER>
<iframe src="https://<?=$_SERVER[SERVER_NAME];?>:10000/openvpn" name="openvpn" id="openvpn" width="990" height="450" ALLOWTRANSPARENCY="true" frameborder=0></iframe>
<br><a href="#" onclick="javascript:openvpn.location.href='https://<?=$_SERVER[SERVER_NAME];?>:10000/openvpn';">Back</a>
</CENTER>
<?php
		}
		else
		{
			include($path->path_modules_auth."/authctrl.php");
		}
?>
