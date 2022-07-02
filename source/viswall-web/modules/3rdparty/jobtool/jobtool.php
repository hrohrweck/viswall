<?php
	header ("Pragma: no-cache");							// HTTP 1.0
	header ("Cache-Control: no-cache, must-revalidate");	// HTTP 1.1
?>
<?php
		////////////////////////////////////////////////
		// ---> PHP TECHWEB - Firewall INTerface <--- //
		////////////////////////////////////////////////
        //											  //
		// Date			: 18.03.2002				  //
		// Comment	: Commandline File				  //
		//											  //
		////////////////////////////////////////////////
		include("config/config.php");
		include("config/global.php");
		
		processdatabase($process_db);
		
		function processdatabase($dbpool)
		{
			$filename = "./output/iptables.tmp";
			$filename2 = "./output/iptables.gen";
			$filename3 = "./config/iptables.def";
			
			if (file_exists($filename))
			{
				unlink($filename);
				unlink($filename2);
			}
			
			for($i=1; $i<=count($dbpool); $i++)
			{
				processtable($dbpool["db".$i]);
			}
			
			$file = fopen($filename3,"r");
			$process_file = fread($file, filesize($filename3));
			fclose($file);
			
			$file2 = fopen($filename,"r");
			$process_file2 = fread($file2, filesize($filename));
			fclose($file2);
			
			if (file_exists($filename2)) $file = fopen($filename2,"a+");
			else $file = fopen($filename2,"w+");
			fwrite($file, $process_file);
			fwrite($file, $process_file2);
			fclose($file);
			
			chmod($filename2,777);
		}
		
		function processtable($process_table)
		{
			$result = mysql_query("select * from ".$process_table." order by priority");
			$number = mysql_num_rows($result);
			
			for($i=0; $i<$number; $i++)
			{
				processentry(mysql_fetch_array($result));
			}				
		}
		
		function processentry($process_entry)
		{
			echo "Processing Entry #".$process_entry['id']." ...\n<br>";
			generateentry(gatherentry($process_entry));
		}
		
		function gatherentry($gather)
		{
			global $process_table_source, $process_table_destination, $process_table_service;
			
			$returnfunc = array("source"=>"0","destination"=>"0","method"=>"0","chain"=>"0","protocol"=>"0","portstart"=>"0","portend"=>"0","portspread"=>"0");
			
			switch (substr($gather['stype'],0,1))
			{
				# Any #
				case 0:
				{
					$returnfunc['source'] = "0.0.0.0/0";
					break;
				}					
				# Hosts #
				case 1:
				{
					$result = mysql_query("select * from ".$process_table_source["tb".substr($gather['stype'],0,1)]." where (id=".substr($gather['stype'],1).")");
					$row = mysql_fetch_array($result);
					$returnfunc['source'] = $row['hostip'];
					break;
				}
				# Networks #
				case 2:
				{
					$result = mysql_query("select * from ".$process_table_source["tb".substr($gather['stype'],0,1)]." where (id=".substr($gather['stype'],1).")");
					$row = mysql_fetch_array($result);
					$returnfunc['source'] = $row['networkip']."/".maskresolver($row);
					break;
				}
			}
			switch (substr($gather['dtype'],0,1))
			{
				# Any #
				case 0:
				{
					$returnfunc['destination'] = "0.0.0.0/0";
					break;
				}
				# Hosts #
				case 1:
				{
					$result = mysql_query("select * from ".$process_table_source["tb".substr($gather['dtype'],0,1)]." where (id=".substr($gather['dtype'],1).")");
					$row = mysql_fetch_array($result);
					$returnfunc['destination'] = $row['hostip'];
					break;
				}
				# Networks #
				case 2:
				{
					$result = mysql_query("select * from ".$process_table_source["tb".substr($gather['dtype'],0,1)]." where (id=".substr($gather['dtype'],1).")");
					$row = mysql_fetch_array($result);
					$returnfunc['destination'] = $row['networkip']."/".maskresolver($row);
					break;
				}
			}
			switch ($gather['baction'])
			{
				# Drop #
				case 0:
				{
					$returnfunc['method'] = "DROP";
					break;
				}					
				# Drop + Log #
				case 1:
				{
					$returnfunc['method'] = "DROP:LOG";
					break;
				}					
				# Accept #
				case 2:
				{
					$returnfunc['method'] = "ACCEPT";
					break;
				}					
				# Accept + Log #
				case 3:
				{
					$returnfunc['method'] = "ACCEPT:LOG";
					break;
				}					
			}
			
			# Chain : Forward #
			$returnfunc['chain'] = 1;
			
			switch (substr($gather['atype'],0,1))
			{
				# Any #
				case 0:
				{
					$returnfunc['protocol'] = 0;
					$returnfunc['portstart'] = 0;
					$returnfunc['portend'] = 0;
					break;
				}
				# Default - Protocol List #
				case 1:
				{
					$result = mysql_query("select * from ".$process_table_service["tb".substr($gather['atype'],0,1)]." where (id=".(substr($gather['atype'],1)).")");
					$row = mysql_fetch_array($result);
					$returnfunc['protocol'] = $row['protocoll'];
					$returnfunc['portstart'] = $row['portstart'];
					$returnfunc['portend'] = $row['portend'];
					$returnfunc['portspread'] = (int)($row['portend']) - (int)($row['portstart']);
					break;
				}
			}
			
			return $returnfunc;
		}
		
		function maskresolver($maskarray)
		{
			$maskpool = explode(".",$maskarray['networkmask']);
			$returnflag = "";
			
			for ($i=0; $i<count($maskpool); $i++)
			{
				switch ($maskpool[$i])
				{
					case 255: case 254: case 252: case 248: case 240: case 224: case 192: case 128: case 0:
						$returnflag = $returnflag."0";
						break;
					default:
						$returnflag = $returnflag."1";
						break;
				}
			}
			
			if (($maskpool[0] >= $maskpool[1]) and ($maskpool[1] >= $maskpool[2]) and ($maskpool[2] >= $maskpool[3]))
				$returnflag = $returnflag."0";
			else
				$returnflag = $returnflag."1";
			
			if (intval($returnflag) == 0)
				return sprintf("%s.%s.%s.%s",$maskpool[0],$maskpool[1],$maskpool[2],$maskpool[3]);
		}
		
		function flipstring($inputstring)
		{
			$outputstring = "";
			
			for($i=strlen($inputstring); $i>=0; $i--)
			{
				$outputstring = $outputstring.substr($inputstring,$i,1);
			}
			
			return $outputstring;
		}			
		
		function mask2bin($inputarray)
		{
			return (sprintf("%08s%08s%08s%08s",decbin($inputarray[0]),decbin($inputarray[1]),decbin($inputarray[2]),decbin($inputarray[3])));
		}			
		
		function array2str($inputarray)
		{
			$outputstring = "";
			
			for ($i=0; $i<count($inputarray); $i++)
			{
				$outputstring = $outputstring.$inputarray[$i];
			}
			
			return $outputstring;			
		}			
		
		function bin_count($binarystring)
		{
			return strlen(substr($binarystring,strcspn($binarystring,"1")));
		}			
		
		function bin_invert($binarystring)
		{
			$outputstring = "";
			
			for ($i=0; $i<strlen($binarystring); $i++)
			{
				if (substr($binarystring,$i,1) == '0')
					$outputstring = $outputstring."1";
				elseif (substr($binarystring,$i,1) == '1')
					$outputstring = $outputstring."0";
				else
					return "0";
			}
			
			return $outputstring;
		}			
		
		function processdefault()
		{
			return $process_file;
		}
		
		function generateentry($entry)
		{
			$filename = "./output/iptables.tmp";
			
			if (file_exists($filename)) $file = fopen($filename,"a+");
			else $file = fopen($filename,"w+");
			
			if (substr($entry['method'],0,4) == "DROP")
			{
				if (($entry['portstart'] == 0) and ($entry['portend'] == 0))
				{
					if ($entry['protocol'] == 0)
					{
						fwrite($file, "iptables -A FORWARD -j DROP -p TCP -s ".$entry['source']." -d ".$entry['destination']."\n");
					}
					elseif ($entry['protocol'] == 1)
					{
						fwrite($file, "iptables -A FORWARD -j DROP -p UDP -s ".$entry['source']." -d ".$entry['destination']."\n");
					}
					elseif ($entry['protocol'] == 2)
					{
						fwrite($file, "iptables -A FORWARD -j DROP -p TCP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j DROP -p UDP -s ".$entry['source']." -d ".$entry['destination']."\n");
					}
					elseif ($entry['protocol'] == 3)
					{
						fwrite($file, "iptables -A FORWARD -j DROP -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
					}
					elseif ($entry['protocol'] == 4)
					{
						fwrite($file, "iptables -A FORWARD -j DROP -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j DROP -p TCP -s ".$entry['source']." -d ".$entry['destination']."\n");
					}
					elseif ($entry['protocol'] == 5)
					{
						fwrite($file, "iptables -A FORWARD -j DROP -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j DROP -p UDP -s ".$entry['source']." -d ".$entry['destination']."\n");
					}
					elseif ($entry['protocol'] == 6)
					{
						fwrite($file, "iptables -A FORWARD -j DROP -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j DROP -p UDP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j DROP -p TCP -s ".$entry['source']." -d ".$entry['destination']."\n");
					}
					
					if (substr($entry['method'],5,3) == "LOG")
					{
						if ($entry['protocol'] == 0)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p TCP -s ".$entry['source']." -d ".$entry['destination']."\n");
						}
						elseif ($entry['protocol'] == 1)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p UDP -s ".$entry['source']." -d ".$entry['destination']."\n");
						}
						elseif ($entry['protocol'] == 2)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p TCP -s ".$entry['source']." -d ".$entry['destination']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p UDP -s ".$entry['source']." -d ".$entry['destination']."\n");
						}
						elseif ($entry['protocol'] == 3)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
						}
						elseif ($entry['protocol'] == 4)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p TCP -s ".$entry['source']." -d ".$entry['destination']."\n");
						}
						elseif ($entry['protocol'] == 5)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p UDP -s ".$entry['source']." -d ".$entry['destination']."\n");
						}
						elseif ($entry['protocol'] == 6)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p UDP -s ".$entry['source']." -d ".$entry['destination']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p TCP -s ".$entry['source']." -d ".$entry['destination']."\n");
						}
					}
				}
				else
				{
					if ($entry['protocol'] == 0)
					{
						fwrite($file, "iptables -A FORWARD -j DROP -p TCP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
					}
					elseif ($entry['protocol'] == 1)
					{
						fwrite($file, "iptables -A FORWARD -j DROP -p UDP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
					}
					elseif ($entry['protocol'] == 2)
					{
						fwrite($file, "iptables -A FORWARD -j DROP -p TCP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						fwrite($file, "iptables -A FORWARD -j DROP -p UDP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
					}
					elseif ($entry['protocol'] == 3)
					{
						fwrite($file, "iptables -A FORWARD -j DROP -p ICMP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
					}
					elseif ($entry['protocol'] == 4)
					{
						fwrite($file, "iptables -A FORWARD -j DROP -p ICMP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						fwrite($file, "iptables -A FORWARD -j DROP -p TCP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
					}
					elseif ($entry['protocol'] == 5)
					{
						fwrite($file, "iptables -A FORWARD -j DROP -p ICMP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						fwrite($file, "iptables -A FORWARD -j DROP -p UDP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
					}
					elseif ($entry['protocol'] == 6)
					{
						fwrite($file, "iptables -A FORWARD -j DROP -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j DROP -p UDP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						fwrite($file, "iptables -A FORWARD -j DROP -p TCP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
					}
					
					if (substr($entry['method'],5,3) == "LOG")
					{
						if ($entry['protocol'] == 0)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p TCP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						}
						elseif ($entry['protocol'] == 1)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p UDP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						}
						elseif ($entry['protocol'] == 2)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p TCP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p UDP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						}
						elseif ($entry['protocol'] == 3)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p ICMP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						}
						elseif ($entry['protocol'] == 4)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p ICMP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p TCP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						}
						elseif ($entry['protocol'] == 5)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p ICMP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p UDP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						}
						elseif ($entry['protocol'] == 6)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p UDP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p TCP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						}
					}
				}
			}
			elseif (substr($entry['method'],0,6) == "ACCEPT")
			{
				if (($entry['portstart'] == 0) and ($entry['portend'] == 0))
				{
					if ($entry['protocol'] == 0)
					{
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p TCP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -s ".$entry['destination']." -d ".$entry['source']." -m state --state ESTABLISHED,RELATED\n");
					}
					elseif ($entry['protocol'] == 1)
					{
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p UDP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -s ".$entry['destination']." -d ".$entry['source']." -m state --state ESTABLISHED,RELATED\n");
					}
					elseif ($entry['protocol'] == 2)
					{
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p TCP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p UDP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -s ".$entry['destination']." -d ".$entry['source']." -m state --state ESTABLISHED,RELATED\n");
					}
					elseif ($entry['protocol'] == 3)
					{
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -s ".$entry['destination']." -d ".$entry['source']." -m state --state ESTABLISHED,RELATED\n");
					}
					elseif ($entry['protocol'] == 4)
					{
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p TCP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -s ".$entry['destination']." -d ".$entry['source']." -m state --state ESTABLISHED,RELATED\n");
					}
					elseif ($entry['protocol'] == 5)
					{
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p UDP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -s ".$entry['destination']." -d ".$entry['source']." -m state --state ESTABLISHED,RELATED\n");
					}
					elseif ($entry['protocol'] == 6)
					{
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p UDP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p TCP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -s ".$entry['destination']." -d ".$entry['source']." -m state --state ESTABLISHED,RELATED\n");
					}
					
					if (substr($entry['method'],7,3) == "LOG")
					{
						if ($entry['protocol'] == 0)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p TCP -s ".$entry['source']." -d ".$entry['destination']."\n");
						}
						elseif ($entry['protocol'] == 1)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p UDP -s ".$entry['source']." -d ".$entry['destination']."\n");
						}
						elseif ($entry['protocol'] == 2)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p TCP -s ".$entry['source']." -d ".$entry['destination']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p UDP -s ".$entry['source']." -d ".$entry['destination']."\n");
						}
						elseif ($entry['protocol'] == 3)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
						}
						elseif ($entry['protocol'] == 4)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p TCP -s ".$entry['source']." -d ".$entry['destination']."\n");
						}
						elseif ($entry['protocol'] == 5)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p UDP -s ".$entry['source']." -d ".$entry['destination']."\n");
						}
						elseif ($entry['protocol'] == 6)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p UDP -s ".$entry['source']." -d ".$entry['destination']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p TCP -s ".$entry['source']." -d ".$entry['destination']."\n");
						}
					}
				}
				else
				{
					if ($entry['protocol'] == 0)
					{
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p TCP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -s ".$entry['destination']." -d ".$entry['source']." -m state --state ESTABLISHED,RELATED\n");
					}
					elseif ($entry['protocol'] == 1)
					{
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p UDP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -s ".$entry['destination']." -d ".$entry['source']." -m state --state ESTABLISHED,RELATED\n");
					}
					elseif ($entry['protocol'] == 2)
					{
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p TCP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p UDP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -s ".$entry['destination']." -d ".$entry['source']." -m state --state ESTABLISHED,RELATED\n");
					}
					elseif ($entry['protocol'] == 3)
					{
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p ICMP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -s ".$entry['destination']." -d ".$entry['source']." -m state --state ESTABLISHED,RELATED\n");
					}
					elseif ($entry['protocol'] == 4)
					{
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p ICMP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p TCP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -s ".$entry['destination']." -d ".$entry['source']." -m state --state ESTABLISHED,RELATED\n");
					}
					elseif ($entry['protocol'] == 5)
					{
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p ICMP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p UDP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -s ".$entry['destination']." -d ".$entry['source']." -m state --state ESTABLISHED,RELATED\n");
					}
					elseif ($entry['protocol'] == 6)
					{
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p UDP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -p TCP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						fwrite($file, "iptables -A FORWARD -j ACCEPT -s ".$entry['destination']." -d ".$entry['source']." -m state --state ESTABLISHED,RELATED\n");
					}
					
					if (substr($entry['method'],7,3) == "LOG")
					{
						if ($entry['protocol'] == 0)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p TCP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						}
						elseif ($entry['protocol'] == 1)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p UDP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						}
						elseif ($entry['protocol'] == 2)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p TCP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p UDP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						}
						elseif ($entry['protocol'] == 3)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p ICMP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						}
						elseif ($entry['protocol'] == 4)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p ICMP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p TCP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						}
						elseif ($entry['protocol'] == 5)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p ICMP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p UDP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						}
						elseif ($entry['protocol'] == 6)
						{
							fwrite($file, "iptables -A FORWARD -j LOG -p ICMP -s ".$entry['source']." -d ".$entry['destination']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p TCP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
							fwrite($file, "iptables -A FORWARD -j LOG -p UDP -s ".$entry['source']." -d ".$entry['destination']." --destination-port ".$entry['portstart'].":".$entry['portend']."\n");
						}
					}
				}
			}					
			
			fclose($file);
		}			
?>