<html>
<head>

</head>
<body>
   <p><b>Suchtext eingeben</b> ...</p>
   <form name="suchform" action="result.php" method="post">
    <fieldset>
     <legend> Felder mit * sind erforderlich </legend>
     <label for="suchtext">Suchtext * </label>
      <input id="suchtext" type="text" name="Suchtext" size="60" /><br />
     <label for="datum">Datum &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</label>
      <input id="datum" type="text" name="Datum" size="30" /> (Format: 2013-04-08)<br />
     <label for="zeitraum">Zeitraum</label>
      <select id="zeitraum" name="Zeitraum" style="margin-left:10px; ">
      <option value="/var/log/exim4/mainlog*">Alles</option>
      <option value="/var/log/exim4/mainlog">Heute</option>
      <option value="/var/log/exim4/mainlog.1">Gestern</option>
      <option value="/var/log/exim4/mainlog.2">Vorgestern</option>
      <option value="/var/log/exim4/mainlog.3">vor 3 Tagen</option>
      <option value="/var/log/exim4/mainlog.4">vor 4 Tagen</option>
      <option value="/var/log/exim4/mainlog.5">vor 5 Tagen</option>
      <option value="/var/log/exim4/mainlog.6">vor 6 Tagen</option>
      <option value="/var/log/exim4/mainlog.7">vor 7 Tagen</option>
      <option value="/var/log/exim4/mainlog.8">vor 8 Tagen</option>
      <option value="/var/log/exim4/mainlog.9">vor 9 Tagen</option>
      <option value="/var/log/exim4/mainlog.10">vor 10 Tagen</option>
      <option value="/var/log/exim4/mainlog.11">vor 11 Tagen</option>
      <option value="/var/log/exim4/mainlog.12">vor 12 Tagen</option>
      <option value="/var/log/exim4/mainlog.13"> vor 13 Tagen</option>
      </select>
      <br />
<!--
<br>
      <input id="zeitraum" type="radio" name="Zeitraum" value="/var/log/exim4/mainlog*" checked style="margin-left:70px; " /> Alles <br />
      <input id="zeitraum" type="radio" name="Zeitraum" value="/var/log/exim4/mainlog" style="margin-left:70px; " /> Heute <br />
      <input id="zeitraum" type="radio" name="Zeitraum" value="/var/log/exim4/mainlog.1" style="margin-left:70px; " /> Gestern<br />
      <input id="zeitraum" type="radio" name="Zeitraum" value="/var/log/exim4/mainlog.2" style="margin-left:70px; " /> Vorgestern<br />
      <input id="zeitraum" type="radio" name="Zeitraum" value="/var/log/exim4/mainlog.3" style="margin-left:70px; " /> vor 3 Tagen<br />
      <input id="zeitraum" type="radio" name="Zeitraum" value="/var/log/exim4/mainlog.4" style="margin-left:70px; " /> vor 4 Tage<br />
      <input id="zeitraum" type="radio" name="Zeitraum" value="/var/log/exim4/mainlog.5" style="margin-left:70px; " /> vor 5 Tagen<br />
      <input id="zeitraum" type="radio" name="Zeitraum" value="/var/log/exim4/mainlog.6" style="margin-left:70px; " /> vor 6 Tagen<br />
      <input id="zeitraum" type="radio" name="Zeitraum" value="/var/log/exim4/mainlog.7" style="margin-left:70px; " /> vor 7 Tagen<br />
      <input id="zeitraum" type="radio" name="Zeitraum" value="/var/log/exim4/mainlog.8" style="margin-left:70px; " /> vor 8 Tagen<br />
      <input id="zeitraum" type="radio" name="Zeitraum" value="/var/log/exim4/mainlog.9" style="margin-left:70px; " /> vor 9 Tagen<br />
      <input id="zeitraum" type="radio" name="Zeitraum" value="/var/log/exim4/mainlog.10" style="margin-left:70px; " /> vor 10 Tagen<br />
      <input id="zeitraum" type="radio" name="Zeitraum" value="/var/log/exim4/mainlog.11" style="margin-left:70px; " /> vor 11 Tagen<br />
      <input id="zeitraum" type="radio" name="Zeitraum" value="/var/log/exim4/mainlog.12" style="margin-left:70px; " /> vor 12 Tagen<br />
      <input id="zeitraum" type="radio" name="Zeitraum" value="/var/log/exim4/mainlog.13" style="margin-left:70px; " /> vor 13 Tagen<br />
-->
     <label for="Senden"> </label>
      <input id="Senden" type="submit" name="senden" value="Senden" />
    </fieldset>
   </form>
</body>
