#!/bin/sh
#!/bin/python3.7


SERVICE="chaoz.py"
if ps -ef | grep "$SERVICE" | grep -v grep >/dev/null
then
    echo "chaoz.py is running - $(date '+%d/%m/%Y %H:%M:%S')" >> /home/chaozbot/bot/chaoz.log
else
    python3 -u /home/chaozbot/bot/chaoz.py >> chaoz.log & 
    echo "chaoz.py stopped - $(date '+%d/%m/%Y %H:%M:%S')" >> /home/chaozbot/bot/chaoz.log
fi
