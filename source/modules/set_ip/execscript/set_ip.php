#!/usr/bin/php
<?

if ($argc<2)
{
echo "usage: set_ip.php ip_address host_name host_dns\n";
exit(1);
}

if (isset($argv[1]))
  $ip_address = $argv[1];
if (isset($argv[2]))
  $host_name = $argv[2];
else
{
  $host_name = exec("hostname");
}
if (isset($argv[3]))
  $host_dns = $argv[3];
else
{
  $temp_dns = exec("dnsdomainname");
  $host_dns = $host_name.".".$temp_dns;
}

$file_to_edit = array("ipsec.conf","hosts","ukenglish/template.html","german/template.html");
$dir_to_move =  array("/etc","/etc","/etc/dansguardian/languages","/etc/dansguardian/languages");

$i=0;

foreach ($file_to_edit as $filename)
{
  $old_file = file("templates/".$filename);
  $new_file = fopen("templates/".$filename.".new","w+");  

  foreach($old_file as $string)
  {
    if (isset($ip_address))
    {
      $string = str_replace("%ip_address",$ip_address,$string);  
      $string = str_replace("%ip_adress",$ip_address,$string);  
    }
    if (isset($host_dns)) 
      $string = str_replace("%host_dns",$host_dns,$string);
    if (isset($host_name)) 
      $string = str_replace("%host_name",$host_name,$string);
    fputs($new_file,$string);
  }

  fclose($new_file);
  exec("mv templates/".$filename.".new ".$dir_to_move[$i]."/".$filename."\n");
//  echo("mv templates/".$filename.".new ".$dir_to_move[$i]."/".$filename."\n");
  $i++;
}

?>
