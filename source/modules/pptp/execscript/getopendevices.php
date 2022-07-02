#!/usr/local/bin/php
<?
include_once "../../interface/config.php";

$mydb=new sql_db();

$conn=mysql_connect ($mydb->sql_db_host,$mydb->sql_db_username,$mydb->sql_db_password) or die (mysql_error());
mysql_select_db ($mydb->sql_db_name,$conn);

$query="select * from pptp_online where disconnect_time='0000-00-00 00:00:00'";
$result=mysql_query ($query,$conn) or die (mysql_error());

if ($result) {
        if (mysql_num_rows ($result)>0) {
                while ($row=mysql_fetch_array($result)) {
                        system ("./getdat ".$row["vpn_if"]);

                        $fp=fopen ("/tmp/".$row["vpn_if"]."-traffic.dat","r");

						$in=-1;
						$out=-1;
						
                        if ($fp) {
							while(!feof ($fp)){
                                $line=fgets($fp);
								if (!(strpos($line,$row["vpn_if"]) === false) && (strpos($line,"VPN-".$row["vpn_if"]) === false)) {
									if ($in==-1) {
										$paramcount=0;
										$foundstring=0;
										
									    for ($a=0;$a<strlen($line);$a++) {
											if (substr($line,$a,1) != " ") {
											    if ($foundstring) {
													$foundstring++;											        
											    } else {
													$foundstring=1;
													$paramcount++;
												}
											} else {
												if (($paramcount==2) && ($foundstring)) {
												    $in=substr($line,$a-$foundstring,$foundstring);
													echo "in: ".$in."\n";
													echo "line: ".$line."\n";
												}
												
												$foundstring=0;
											}
										}
									} else {
										$paramcount=0;
										$foundstring=0;
										
									    for ($a=0;$a<strlen($line);$a++) {
											if (substr($line,$a,1) != " ") {
											    if ($foundstring) {
													$foundstring++;											        
											    } else {
													$foundstring=1;
													$paramcount++;
												}
											} else {
												if (($paramcount==2) && ($foundstring)) {
												    $out=substr($line,$a-$foundstring,$foundstring);
													echo "out: ".$out."\n";
													echo "line: ".$line."\n";
												}
												
												$foundstring=0;
											}
										}									
									}
								}
							} // while
                        }

					$traffic_in=$row["traffic_in"]+$in;
					$traffic_out=$row["traffic_out"]+$out;
					
					$query="UPDATE pptp_online set traffic_in=".$traffic_in." WHERE oid=".$row["oid"];
					//echo $query."\n";
					mysql_query($query,$conn) or die (mysql_error());
					
					$query="UPDATE pptp_online set traffic_out=".$traffic_out." WHERE oid=".$row["oid"];
					//echo $query."\n";
					mysql_query($query,$conn) or die (mysql_error());
                }
        }
}
?>
