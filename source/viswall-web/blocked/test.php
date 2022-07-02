
<?php

$all = $_GET['DENIEDURL'];
echo $all;

for ($i=1;$all[$i]!=':' || $all[$i+1]!=':' || $all[$i+2]!='I' || $all[$i+3]!='P';$i++)
{
	$url .= $all[$i];
}

$i = $i +3;

for (;$all[$i]!=':' || $all[$i+1]!=':' || $all[$i+2]!='U' || $all[$i+3]!='S'|| $all[$i+4]!='E'|| 
$all[$i+5]!='R';$i++)
{
        $ip .= $all[$i];
}

echo "URL: ".$url."\n";
echo "USER".$user."\n";

function get_between($all,$first,$last)
{
  
}

?>

