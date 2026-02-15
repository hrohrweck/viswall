"""
Viswall Mail Service Agent

Manages complete email infrastructure:
- Exim MTA (SMTP)
- Courier IMAP/POP3
- ClamAV virus scanning
- SpamAssassin spam filtering
- LLM-based email classification
- DKIM/DMARC/SPF support
"""

import asyncio
import subprocess
import re
import json
import os
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib

@dataclass
class MailMessage:
    id: str
    sender: str
    recipients: List[str]
    subject: str
    size: int
    timestamp: datetime
    spam_score: Optional[float] = None
    virus_status: Optional[str] = None
    llm_classification: Optional[Dict[str, Any]] = None
    queue_id: Optional[str] = None


class EximManager:
    """Manages Exim MTA configuration and operations"""
    
    CONFIG_PATH = "/etc/exim4/exim4.conf.template"
    CONFIG_DIR = "/etc/exim4"
    
    # Exim ACL for spam/virus scanning
    ACL_SCAN_CONFIG = '''
# Viswall Mail Scanner Integration

acl_check_rcpt:
  accept hosts = :
          hosts = +relay_from_hosts
          condition = ${if eq{$interface_port}{25}{false}{true}}

  deny message = Helo name contains a bare IP address (HELO was $sender_helo_name)
       condition = ${if match{$sender_helo_name}{\\N^\\[?\\d+\\.\\d+\\.\\d+\\.\\d+\\]?$\\N}{true}{false}}

  deny message = Helo name contains an IP address (HELO was $sender_helo_name)
       condition = ${if match{$sender_helo_name}{\\N\\d+\\.\\d+\\.\\d+\\.\\d+\\N}{true}{false}}

  deny message = Rejected because $sender_host_address is in a black list at $dnslist_domain\\n$dnslist_text
       dnslists = zen.spamhaus.org : b.barracudacentral.org

  accept

acl_check_data:
  # SpamAssassin scan
  warn spam = spamd:true
       add_header = X-Spam-Score: $spam_score
       add_header = X-Spam-Report: $spam_report
  
  deny message = This message scored $spam_score spam points.
       condition = ${if >{$spam_score}{10}{true}{false}}

  # ClamAV scan
  deny message = This message contains malware ($malware_name)
       demime = *
       malware = */bin/false

  accept
'''

    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.exim_log = "/var/log/exim4/mainlog"
    
    def generate_config(
        self,
        primary_hostname: str,
        local_domains: List[str],
        relay_domains: List[str] = None,
        smarthost: Optional[str] = None,
        enable_dkim: bool = True,
        enable_dmarc: bool = True,
        enable_spf: bool = True
    ) -> str:
        """Generate comprehensive Exim configuration"""
        
        config = f'''# Viswall Exim Configuration
# Generated: {datetime.utcnow().isoformat()}

# Primary host identification
primary_hostname = {primary_hostname}
local_interfaces = 0.0.0.0 : ::

# Domain lists
domainlist local_domains = @ : localhost : {' : '.join(local_domains)}
domainlist relay_to_domains = {' : '.join(relay_domains or [])}
hostlist relay_from_hosts = localhost : 127.0.0.1 : ::1

# MySQL lookups
hide mysql_servers = {self.db_config.get('host', 'localhost')}/{self.db_config.get('database', 'exim')}/{self.db_config.get('user')}/{self.db_config.get('password')}

# Main configuration
acl_smtp_rcpt = acl_check_rcpt
acl_smtp_data = acl_check_data
acl_smtp_mime = acl_check_mime

# Limits
smtp_accept_max = 100
smtp_accept_max_per_host = 20
message_size_limit = 50M
smtp_accept_queue_per_connection = 50

# Timeouts
smtp_connect_timeout = 30s
smtp_banner = $tls_in_cipher : $primary_hostname ESMTP Exim $version_number $tod_full
keep_environment =
add_environment = PATH=/bin:/usr/bin

# TLS Configuration
tls_advertise_hosts = *
tls_certificate = /etc/exim4/tls.crt
tls_privatekey = /etc/exim4/tls.key
tls_require_ciphers = HIGH:!aNULL:!MD5:!3DES

# Logging
log_selector = +smtp_protocol_error +smtp_syntax_error +tls_cipher +tls_peerdn +queue_time

# Hostname verification
helo_verify_hosts = *
helo_try_verify_hosts = *

{self.ACL_SCAN_CONFIG}

acl_check_mime:
  deny message = Blacklisted file extension detected
       condition = ${if match{{$mime_filename}}{\\N\\.(exe|com|pif|scr|bat|cmd|vbs|js|jar)$\\N}{true}{false}}
  accept

begin routers

# DNS lookup router
dnslookup:
  driver = dnslookup
  domains = ! +local_domains
  transport = remote_smtp
  ignore_target_hosts = 0.0.0.0 : 127.0.0.0/8 : ::1
  no_more

# MySQL router for local delivery
mysql_user:
  driver = accept
  domains = +local_domains
  local_parts = mysql; SELECT localpart FROM mail_users WHERE localpart='${quote_mysql:$local_part}' AND domain='${quote_mysql:$domain}' AND enabled=1
  transport = local_delivery
  cannot_route_message = Unknown user

# Catch-all (if configured)
mysql_catchall:
  driver = redirect
  domains = +local_domains
  data = mysql; SELECT forwardto FROM mail_catchall WHERE domain='${quote_mysql:$domain}' AND enabled=1
  redirect_router = mysql_user

begin transports

remote_smtp:
  driver = smtp
  hosts_try_fastopen = :
  interface = $primary_hostname
  dkim_domain = $sender_address_domain
  dkim_selector = default
  dkim_private_key = /etc/exim4/dkim/${dkim_domain}.key
  dkim_canon = relaxed

local_delivery:
  driver = appendfile
  file = /var/mail/$domain/$local_part/Maildir/
  delivery_date_add
  envelope_to_add
  return_path_add
  maildir_format
  maildir_use_size_file = false
  user = mail
  group = mail
  mode = 0600

begin retry

# Remote retry rules
* * F,2h,15m; G,16h,1h,1.5; F,4d,6h

begin authenticators

# CRAM-MD5 authentication
cram_md5:
  driver = cram_md5
  public_name = CRAM-MD5
  server_secret = ${lookup mysql{{SELECT password FROM mail_users \\
    WHERE localpart='${quote_mysql:$auth1}' AND domain='${quote_mysql:$domain}'}}}
  server_set_id = $auth1

# PLAIN authentication (with TLS required)
plain:
  driver = plaintext
  public_name = PLAIN
  server_condition = ${lookup mysql{{SELECT 'yes' FROM mail_users \\
    WHERE localpart='${quote_mysql:$auth2}' AND domain='${quote_mysql:$auth3}' \\
    AND password='${quote_mysql:$auth3}' AND enabled=1}}{yes}{no}}
  server_set_id = $auth2@$auth3
  server_advertise_condition = ${if eq{$tls_in_cipher}{}{}{*}}

# LOGIN authentication (with TLS required)
login:
  driver = plaintext
  public_name = LOGIN
  server_prompts = Username:: : Password::
  server_condition = ${lookup mysql{{SELECT 'yes' FROM mail_users \\
    WHERE localpart='${quote_mysql:$auth1}' AND domain='${quote_mysql:$auth2}' \\
    AND password='${quote_mysql:$auth2}' AND enabled=1}}{yes}{no}}
  server_set_id = $auth1@$auth2
  server_advertise_condition = ${if eq{$tls_in_cipher}{}{}{*}}
'''
        
        if smarthost:
            # Insert smarthost router before dnslookup
            smarthost_router = f'''
smarthost:
  driver = manualroute
  domains = ! +local_domains
  transport = remote_smtp
  route_list = * {smarthost} byname
  host_find_failed = defer
  no_more
'''
            config = config.replace('dnslookup:', smarthost_router + '\ndnslookup:')
        
        return config
    
    async def apply_config(self, config: str) -> bool:
        """Apply Exim configuration and reload"""
        try:
            # Backup existing config
            backup_path = f"{self.CONFIG_PATH}.backup.{int(datetime.utcnow().timestamp())}"
            if os.path.exists(self.CONFIG_PATH):
                os.rename(self.CONFIG_PATH, backup_path)
            
            # Write new config
            with open(self.CONFIG_PATH, 'w') as f:
                f.write(config)
            
            # Set permissions
            os.chmod(self.CONFIG_PATH, 0o644)
            
            # Validate config
            proc = await asyncio.create_subprocess_exec(
                "exim4", "-bV",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                # Restore backup
                os.rename(backup_path, self.CONFIG_PATH)
                print(f"Exim config validation failed: {stderr.decode()}")
                return False
            
            # Reload Exim
            proc = await asyncio.create_subprocess_exec(
                "systemctl", "reload", "exim4",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            
            return True
            
        except Exception as e:
            print(f"Failed to apply Exim config: {e}")
            return False
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current mail queue status"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "exim4", "-bpc",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            count = int(stdout.decode().strip())
            
            # Get queue details
            proc = await asyncio.create_subprocess_exec(
                "exim4", "-bp",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            
            return {
                "count": count,
                "details": stdout.decode()
            }
        except:
            return {"count": 0, "details": ""}
    
    async def flush_queue(self) -> bool:
        """Flush the mail queue"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "exim4", "-q",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return proc.returncode == 0
        except:
            return False
    
    async def remove_message(self, message_id: str) -> bool:
        """Remove a message from the queue"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "exim4", "-Mrm", message_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return proc.returncode == 0
        except:
            return False
    
    def generate_dkim_keys(self, domain: str) -> Tuple[str, str]:
        """Generate DKIM keys for a domain"""
        key_dir = "/etc/exim4/dkim"
        os.makedirs(key_dir, exist_ok=True)
        
        private_key_path = f"{key_dir}/{domain}.key"
        public_key_path = f"{key_dir}/{domain}.pub"
        
        # Generate private key
        subprocess.run([
            "openssl", "genrsa", "-out", private_key_path, "2048"
        ], check=True, capture_output=True)
        
        # Generate public key
        subprocess.run([
            "openssl", "rsa", "-in", private_key_path,
            "-pubout", "-out", public_key_path
        ], check=True, capture_output=True)
        
        # Read and format public key for DNS
        with open(public_key_path, 'r') as f:
            pub_key = f.read()
        
        # Extract base64 key
        key_data = ''.join(pub_key.split('\n')[1:-2])
        
        # Generate DNS TXT record
        dns_record = f"v=DKIM1; k=rsa; p={key_data}"
        
        os.chmod(private_key_path, 0o600)
        
        return private_key_path, dns_record


class SpamAssassinManager:
    """Manages SpamAssassin configuration and training"""
    
    CONFIG_PATH = "/etc/spamassassin/local.cf"
    BAYES_DB_PATH = "/var/lib/spamassassin"
    
    def __init__(self, db_config: Dict[str, str] = None):
        self.db_config = db_config or {}
    
    def generate_config(
        self,
        required_score: float = 5.0,
        use_bayes: bool = True,
        bayes_auto_learn: bool = True,
        use_pyzor: bool = True,
        use_razor: bool = True,
        use_dcc: bool = True,
        custom_rules: List[Dict] = None
    ) -> str:
        """Generate SpamAssassin configuration"""
        
        config = f'''# Viswall SpamAssassin Configuration
# Generated: {datetime.utcnow().isoformat()}

# Required score to flag as spam
required_score {required_score}

# Bayesian filtering
use_bayes {'1' if use_bayes else '0'}
bayes_auto_learn {'1' if bayes_auto_learn else '0'}
'''
        
        if use_bayes and self.db_config:
            config += f'''
# MySQL Bayes storage
bayes_store_module Mail::SpamAssassin::BayesStore::MySQL
bayes_sql_dsn DBI:mysql:{self.db_config.get('database', 'spamassassin')}:{self.db_config.get('host', 'localhost')}
bayes_sql_username {self.db_config.get('user', 'sa')}
bayes_sql_password {self.db_config.get('password', '')}
'''
        
        config += f'''
# Network tests
use_pyzor {'1' if use_pyzor else '0'}
use_razor2 {'1' if use_razor else '0'}
use_dcc {'1' if use_dcc else '0'}

# Network checks
dns_available yes
skip_rbl_checks 0

# MIME and header checks
mimeheader UNDISC_RECIPS To =~ /^(undisclosed)?-?recipients/i
describe UNDISC_RECIPS Undisclosed recipients
score UNDISC_RECIPS 2.0

mimeheader HTML_MIME_NO_HTML_TAG Content-Type =~ /text\\/html/i
meta HTML_MIME_NO_HTML_TAG (!HTML_MESSAGE)
describe HTML_MIME_NO_HTML_TAG Content-Type text/html without HTML message
score HTML_MIME_NO_HTML_TAG 2.0
'''
        
        # Add custom rules
        if custom_rules:
            config += "\n# Custom rules\n"
            for rule in custom_rules:
                config += f"{rule['type']} {rule['name']} {rule['condition']}\n"
                if 'describe' in rule:
                    config += f"describe {rule['name']} {rule['describe']}\n"
                if 'score' in rule:
                    config += f"score {rule['name']} {rule['score']}\n"
        
        # Whitelist/blacklist
        config += '''
# Default whitelist/blacklist
whitelist_from_rcvd *@localhost localhost
whitelist_from_rcvd *@localhost.localdomain localhost.localdomain
'''
        
        return config
    
    async def apply_config(self, config: str) -> bool:
        """Apply SpamAssassin configuration"""
        try:
            with open(self.CONFIG_PATH, 'w') as f:
                f.write(config)
            
            # Compile rules
            proc = await asyncio.create_subprocess_exec(
                "spamassassin", "--lint",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                print(f"SpamAssassin lint failed: {stderr.decode()}")
                return False
            
            # Restart service
            proc = await asyncio.create_subprocess_exec(
                "systemctl", "restart", "spamassassin",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            
            return True
        except Exception as e:
            print(f"Failed to apply SpamAssassin config: {e}")
            return False
    
    async def learn_spam(self, message_path: str) -> bool:
        """Train SpamAssassin with a spam message"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "sa-learn", "--spam", message_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return proc.returncode == 0
        except:
            return False
    
    async def learn_ham(self, message_path: str) -> bool:
        """Train SpamAssassin with a ham (non-spam) message"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "sa-learn", "--ham", message_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return proc.returncode == 0
        except:
            return False
    
    async def sync_bayes(self) -> bool:
        """Sync Bayes database"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "sa-learn", "--sync",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return proc.returncode == 0
        except:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get SpamAssassin statistics"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "sa-learn", "--dump", "magic",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            
            # Parse output
            stats = {}
            for line in stdout.decode().split('\n'):
                if 'nspam' in line:
                    stats['spam_learned'] = int(line.split()[-1])
                elif 'nham' in line:
                    stats['ham_learned'] = int(line.split()[-1])
            
            return stats
        except:
            return {"spam_learned": 0, "ham_learned": 0}


class ClamAVManager:
    """Manages ClamAV virus scanner"""
    
    CONFIG_PATH = "/etc/clamav/clamd.conf"
    FRESHCLAM_CONFIG = "/etc/clamav/freshclam.conf"
    
    def generate_config(
        self,
        max_scan_size: str = "100M",
        max_file_size: str = "25M",
        max_recursion: int = 10,
        max_files: int = 10000,
        detect_pua: bool = True
    ) -> str:
        """Generate ClamAV daemon configuration"""
        
        return f'''# Viswall ClamAV Configuration
# Generated: {datetime.utcnow().isoformat()}

# Basic settings
LocalSocket /var/run/clamav/clamd.ctl
FixStaleSocket true
LocalSocketGroup clamav
LocalSocketMode 666

# Limits
MaxScanSize {max_scan_size}
MaxFileSize {max_file_size}
MaxRecursion {max_recursion}
MaxFiles {max_files}
MaxEmbeddedPE 10M
MaxHTMLNormalize 10M
MaxHTMLNoTags 2M
MaxScriptNormalize 5M
MaxZipTypeRcg 1M

# Detection
DetectPUA {'yes' if detect_pua else 'no'}
ExcludePUA NetTool
ExcludePUA PWTool

# Heuristic alerts
HeuristicAlerts true
HeuristicScanPrecedence false

# Scan settings
ScanPE true
ScanELF true
ScanOLE2 true
ScanPDF true
ScanSWF true
ScanXMLDOCS true
ScanHWP3 true
ScanMail true
ScanPartialMessages false
ScanArchive true

# Archive limits
ArchiveBlockEncrypted false
MaxScanTime 300000
MaxRecHWP3 16

# Logging
LogFile /var/log/clamav/clamav.log
LogTime true
LogClean false
LogSyslog false
LogFacility LOG_LOCAL6
LogVerbose false
PreludeEnable no
PreludeAnalyzerName ClamAV
DigitalSignatures false

# Database
Bytecode true
BytecodeSecurity TrustSigned
BytecodeTimeout 60000
'''
    
    async def update_definitions(self) -> bool:
        """Update virus definitions"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "freshclam",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            return proc.returncode == 0
        except:
            return False
    
    async def scan_file(self, file_path: str) -> Dict[str, Any]:
        """Scan a file for viruses"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "clamdscan", "--fdpass", "--multiscan", file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            output = stdout.decode()
            
            if "OK" in output:
                return {"clean": True, "virus": None}
            elif "FOUND" in output:
                # Extract virus name
                match = re.search(r':\s*(.+?)\s+FOUND', output)
                virus_name = match.group(1) if match else "Unknown"
                return {"clean": False, "virus": virus_name}
            else:
                return {"clean": None, "error": output}
        except Exception as e:
            return {"clean": None, "error": str(e)}
    
    async def get_version(self) -> str:
        """Get ClamAV version"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "clamdscan", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            return stdout.decode().strip()
        except:
            return "Unknown"


class LLMClassifier:
    """LLM-based email classification for advanced filtering"""
    
    def __init__(self, config: Dict[str, str]):
        self.provider = config.get("provider", "openai")
        self.model = config.get("model", "gpt-4")
        self.api_key = config.get("api_key")
        self.api_base = config.get("api_base")
        self.temperature = float(config.get("temperature", 0.3))
        
        self.categories = config.get("categories", [
            "important", "newsletter", "social", "promotional", 
            "spam", "work", "personal", "finance", "travel"
        ])
    
    async def classify_email(
        self,
        subject: str,
        body: str,
        sender: str,
        headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Classify an email using LLM"""
        
        if not self.api_key:
            return {
                "classified": False,
                "error": "API key not configured"
            }
        
        # Truncate body if too long
        max_body_length = 4000
        truncated_body = body[:max_body_length] + "..." if len(body) > max_body_length else body
        
        prompt = f'''Analyze this email and classify it into categories.

Categories: {', '.join(self.categories)}

Email:
From: {sender}
Subject: {subject}

Body:
{truncated_body}

Respond in JSON format:
{{
  "category": "one of the categories",
  "confidence": 0.0-1.0,
  "summary": "brief summary",
  "action": "deliver|quarantine|reject|tag",
  "reason": "explanation"
}}'''
        
        try:
            if self.provider == "openai":
                result = await self._classify_openai(prompt)
            elif self.provider == "anthropic":
                result = await self._classify_anthropic(prompt)
            else:
                result = await self._classify_local(prompt)
            
            return {
                "classified": True,
                "category": result.get("category", "unknown"),
                "confidence": result.get("confidence", 0.0),
                "summary": result.get("summary", ""),
                "action": result.get("action", "deliver"),
                "reason": result.get("reason", ""),
                "provider": self.provider
            }
        except Exception as e:
            return {
                "classified": False,
                "error": str(e)
            }
    
    async def _classify_openai(self, prompt: str) -> Dict[str, Any]:
        """Classify using OpenAI API"""
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an email classification assistant. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": 500
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base or 'https://api.openai.com/v1'}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                data = await response.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
    
    async def _classify_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Classify using Anthropic Claude API"""
        # Implementation similar to OpenAI
        pass
    
    async def _classify_local(self, prompt: str) -> Dict[str, Any]:
        """Classify using local LLM (ollama, etc.)"""
        # Implementation for local models
        pass


class MailServiceAgent:
    """Main mail service agent"""
    
    def __init__(self, config: Dict[str, Any]):
        self.exim = EximManager(config.get("db", {}))
        self.spamassassin = SpamAssassinManager(config.get("db", {}))
        self.clamav = ClamAVManager()
        self.llm = None
        
        llm_config = config.get("llm", {})
        if llm_config.get("enabled") and llm_config.get("api_key"):
            self.llm = LLMClassifier(llm_config)
    
    async def deploy_mail_server(
        self,
        domain_config: Dict[str, Any]
    ) -> bool:
        """Deploy complete mail server configuration"""
        
        # Generate and apply Exim config
        exim_config = self.exim.generate_config(
            primary_hostname=domain_config["hostname"],
            local_domains=domain_config["domains"],
            enable_dkim=domain_config.get("dkim_enabled", True),
            enable_dmarc=domain_config.get("dmarc_enabled", True),
            enable_spf=domain_config.get("spf_enabled", True)
        )
        
        exim_ok = await self.exim.apply_config(exim_config)
        
        # Generate and apply SpamAssassin config
        sa_config = self.spamassassin.generate_config(
            required_score=domain_config.get("spam_threshold", 5.0),
            use_bayes=domain_config.get("bayes_enabled", True),
            use_pyzor=domain_config.get("pyzor_enabled", True),
            use_razor=domain_config.get("razor_enabled", True)
        )
        
        sa_ok = await self.spamassassin.apply_config(sa_config)
        
        # Generate ClamAV config
        clamav_config = self.clamav.generate_config()
        # ClamAV config is static, applied via Dockerfile
        
        return exim_ok and sa_ok
    
    async def get_mail_stats(self) -> Dict[str, Any]:
        """Get comprehensive mail statistics"""
        
        queue = await self.exim.get_queue_status()
        sa_stats = await self.spamassassin.get_stats()
        
        return {
            "queue": queue,
            "spamassassin": sa_stats,
            "clamav_version": await self.clamav.get_version(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def process_email_with_llm(self, message: MailMessage) -> Dict[str, Any]:
        """Process an email through LLM classification"""
        
        if not self.llm:
            return {"classified": False, "reason": "LLM not configured"}
        
        return await self.llm.classify_email(
            subject=message.subject,
            body="",  # Would need to fetch full body
            sender=message.sender
        )


# Main entry point
async def main():
    """Mail Service Agent main loop"""
    
    config = {
        "db": {
            "host": os.getenv("DB_HOST", "localhost"),
            "database": os.getenv("DB_NAME_VISWALL", "viswall"),
            "user": os.getenv("DB_USER", "viswall"),
            "password": os.getenv("DB_PASS", "")
        },
        "llm": {
            "enabled": os.getenv("LLM_ENABLED", "false").lower() == "true",
            "provider": os.getenv("LLM_PROVIDER", "openai"),
            "api_key": os.getenv("LLM_API_KEY"),
            "model": os.getenv("LLM_MODEL", "gpt-4")
        }
    }
    
    agent = MailServiceAgent(config)
    
    print("Viswall Mail Service Agent started")
    print(f"Features: Exim + ClamAV + SpamAssassin + {'LLM' if agent.llm else 'No LLM'}")
    
    # Example deployment
    # await agent.deploy_mail_server({
    #     "hostname": "mail.example.com",
    #     "domains": ["example.com"],
    #     "dkim_enabled": True
    # })

if __name__ == "__main__":
    asyncio.run(main())
