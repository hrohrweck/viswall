<html>
<head>

</head>
<body>
<?php
   echo("	<p><b>Ergebnis der Suche</b> ... ");
   echo(" [".$_POST['Suchtext']."] - [".$_POST['Datum']."]</p>\n");
   if ($_POST['Datum']) {
      $output = shell_exec('grep "'.$_POST['Datum'].'" '.$_POST['Zeitraum'].' | /viswall/exim/bin/exigrep '.$_POST['Suchtext'].' | sed -f /viswall/interface/modules/functions/maillog/.sedfile');
   } else {
      $output = shell_exec('/viswall/exim/bin/exigrep "'.$_POST['Suchtext'].'" '.$_POST['Zeitraum'].' | sed -f /viswall/interface/modules/functions/maillog/.sedfile');
   }
   echo "<pre>$output</pre>";
?>

</body>
