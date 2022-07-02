#!/usr/local/bin/php
<?
include "../../interface/config.php";

$if=$argv[1];
$tty=$argv[2];
$ttyspeed=$argv[3];
$localip=$argv[4];
$remoteip=$argv[5];
$ipparam=$argv[6];

include "./getopendevices.php";

$fp=fopen ("/tmp/".$if,"r");

if ($fp) {
	$oid=fgets($fp);
}

fclose ($fp);

$mydb=new sql_db();

$conn=mysql_connect ($mydb->sql_db_host,$mydb->sql_db_username,$mydb->sql_db_password) or die (mysql_error());
mysql_select_db ($mydb->sql_db_name,$conn);

$query="select * from pptp_online where oid=".$oid;
$result=mysql_query ($query,$conn) or die (mysql_error());

if ($result) {
	if (mysql_num_rows ($result)>0) {
		$row=mysql_fetch_array($result);
	}
}

$datum=date ("Y-m-d H:i:s");
$query="UPDATE pptp_online set disconnect_time='".$datum."' WHERE oid=".$oid;
$result=mysql_query($query,$conn) or die (mysql_error());
?>
