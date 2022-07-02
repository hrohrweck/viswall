#!/usr/local/bin/php
<?
include "../../interface/config.php";

$pid=$argv[1];
$datum=$argv[2];
$user=$argv[3];
$if=$argv[4];
$tty=$argv[5];
$ttyspeed=$argv[6];
$localip=$argv[7];
$remoteip=$argv[8];
$ipparam=$argv[9];

$mydb=new sql_db ();

$conn=mysql_connect ($mydb->sql_db_host,$mydb->sql_db_username,$mydb->sql_db_password) or die (mysql_error());
mysql_select_db ($mydb->sql_db_name,$conn);

$query="select id from users where username='".trim($user)."'";
echo "SELECT: ".$query."\n";
$result=mysql_query ($query,$conn) or die (mysql_error());

if ($result) {
	if (mysql_num_rows ($result)>0) {
		$row=mysql_fetch_array($result);
		$id=$row["id"];
	}
}

$query="INSERT into pptp_online (id,vpn_ip,vpn_if,connect_time,pid) values (".$id.",'".$remoteip."','".$if."','".$datum."',".$pid.")";
echo "INSERT: ".$query."\n";
$result=mysql_query($query,$conn) or die (mysql_error ());

$query="SELECT oid from pptp_online where id=".$id." and vpn_ip='".$remoteip."' and vpn_if='".$if."' and connect_time='".$datum."' and pid=".$pid;
echo "SELECT: ".$query."\n";
$result=mysql_query($query,$conn) or die (mysql_error());

if ($result) {
	if (mysql_num_rows($result)) {
		$row=mysql_fetch_array ($result);
		$oid=$row["oid"];
	}
}

$fp=fopen ("/tmp/".$if,"w");
if ($fp) {
	fputs ($fp,$oid);
}
fclose ($fp);
?>
