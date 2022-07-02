#!/bin/bash
echo ====================================================================== >> /var/spool/mail/du.txt
echo `date` >> /var/spool/mail/du.txt
du -k -s /var/spool/mail >> /var/spool/mail/du.txt
find /var/spool/mail/ -type f -mtime +14 | xargs rm
echo ---------------------------------------------------------------------- >> /var/spool/mail/du.txt
du -k -s /var/spool/mail >> /var/spool/mail/du.txt

