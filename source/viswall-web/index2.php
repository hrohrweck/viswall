<?php
	# Create Session or ReUse Old one
	session_start();
	session_name("viswall");

	header ("Pragma: no-cache");                                                   // HTTP 1.0
	header ("Cache-Control: no-cache, must-revalidate");                           // HTTP 1.1
?>
<?php
		////////////////////////////////////////////////
		//    ---> itsoft - vis|wall Firewall <---    //
		////////////////////////////////////////////////
		// Date	: 29.04.2002                          //
		////////////////////////////////////////////////
		
		include ("config.php");
		include ("library.php");
		
		open_db();
		$GLOBALS['path'] = new path;
		// <AUTHENTICATION> : <06.03.2002>
		if (module_security() == true)
		{
		    # Workaround forPopUp Issue
				if ($_GET['navigation']==1)
				{
                generate_html($_GLOBALS['navigation']);
				}
				else
				{
								generate_html();
				}
			switch($_GET['module'])
			{
				// <HOSTS> : <31.01.2002>
				case hosts:
					include($path->path_modules_objects."/hosts/hostsctrl.php");
					break;
				// <NETWORKS> : <31.01.2002>
				case networks:
					include($path->path_modules_objects."/networks/networksctrl.php");
					break;
				// <IP-RANGES> : <17.05.2005>
				case ranges:
					include($path->path_modules_objects."/ranges/rangesctrl.php");
					break;
				// <SERVICES> : <31.01.2002>
				case services:
					include($path->path_modules_objects."/services/servicesctrl.php");
					break;
                // <PROTOCOLS> : <24.03.2003>
				case protocols:
					include($path->path_modules_objects."/protocols/protocolsctrl.php");
					break;
				// <INTERFACES> : <31.01.2002>
				case interfaces:
					include($path->path_modules_objects."/interfaces/interfacesctrl.php");
					break;
				// <FILTER> : <31.01.2002>
				case filter:
					include($path->path_modules_functions."/filter/filterctrl.php");
					break;
				// <NAT&PAT> : <31.01.2002>
				case nat:
					include($path->path_modules_functions."/nat/natctrl.php");
					break;
				// <FILTER> : <29.04.2003>
				case routing:
					include($path->path_modules_functions."/routing/routingctrl.php");
					break;
                // <QoS>-<CBQ> : <05.02.2002>
				case cbq:
					include($path->path_modules_functions."/qos/cbq/cbqctrl.php");
					break;
				// <QoS>-<TBF> : <05.02.2002>
				case tbf:
					include($path->path_modules_functions."/qos/tbf/tbfctrl.php");
					break;
				// <SQUID>-<Settings> : <18.02.2002>
				case squid:
					include($path->path_modules_functions."/squid/squidctrl.php");
					break;
				// <Dansguardian>-<Settings> : <06.03.2005>
				case dansguardian:
					include($path->path_modules_functions."/dansguardian/dansguardianctrl.php");
					break;
				// <Frox>-<Settings> : <06.03.2005>
				case frox:
					include($path->path_modules_functions."/frox/froxctrl.php");
					break;
				// <Exim>-<Settings> : <06.03.2005>
				case exim:
					include($path->path_modules_functions."/exim/eximctrl.php");
					break;
				// <Spamassassin>-<Settings> : <06.03.2005>
				case spamassassin:
					include($path->path_modules_functions."/spamassassin/spamassassinctrl.php");
					break;
				// <SYSLOG>-<Settings> : <06.03.2005>
				case syslog:
					include($path->path_modules_functions."/syslog/syslogctrl.php");
					break;
				// <SYSTEMMONITOR>-<Settings> : <06.03.2005>
				case systemmonitor:
					include($path->path_modules_functions."/systemmonitor/systemmonitorctrl.php");
					break;
				// <VPN>-<PPTP> : <18.02.2002>
				case pptp:
					include($path->path_modules_functions."/vpn/pptp/pptpctrl.php");
					break;
				// <VPN>-<IPSEC> : <06.03.2005>
				case ipsec:
					include($path->path_modules_functions."/vpn/ipsec/ipsecctrl.php");
					break;
				// <VPN>-<OpenVPN> : <05.06.2015>
				case openvpn:
					include($path->path_modules_functions."/vpn/openvpn/openvpnctrl.php");
					break;
				case users:
					include($path->path_modules_objects."/users/usersctrl.php");
					break;
				// <MSS>-<SETTINGS> : <27.02.2002>
				case mss:
					include($path->path_modules_functions."/mss/settings/mssctrl.php");
					break;
				// <MSS>-<RULES> : <27.02.2002>
				case mss_rules:
					include($path->path_modules_functions."/mss/rules/mss_rulesctrl.php");
					break;
				// <MSS>-<DOMAINS> : <27.02.2002>
				case mss_domain:
					include($path->path_modules_functions."/mss/domains/mss_domainsctrl.php");
					break;
				// <NIDS>-<SETTINGS> : <27.02.2002>
				case nids:
					include($path->path_modules_functions."/nids/settings/nidsctrl.php");
					break;
				// <NIDS>-<LOG OVERVIEW> : <27.02.2002>
				case nidslog:
					include($path->path_modules_functions."/nids/nidslog/nidslogctrl.php");
					break;
				// <DHCP>-<SETTINGS> : <12.03.2002>
				case dhcp:
					include($path->path_modules_functions."/dhcp/dhcpctrl.php");
					break;				
				// <POPUP CONTROLLER>-<EZ POPUP SYSTEM> : <04.03.2002>
				case popups:
					include($path->path_modules_popups."/popctrl.php");
					break;
				// <CONFIGURATION ACTIVATION> : <04.03.2002>
				case activate:
					activate($g_module,$action,$params);
					break;
				// <ABOUT> : <18.03.2007>
				case aboutvis:
					include($path->path_html."/about.php");
					break;//about-references.php
				// <ABOUT REFERENCES> : <18.03.2007>
				case aboutref:
					include($path->path_html."/about-references.php");
					break;
				// <SPLASH SCREEN> : <07.03.2002>
				default:
					break;
				// <MAILLOG>-<Settings> : <06.03.2005>
				case maillog:
					include($path->path_modules_functions."/maillog/maillogctrl.php");
					break;

			}
		}
		else
		{
			include($GLOBALS['path']->path_modules_auth."/authctrl.php");
		}
?>
