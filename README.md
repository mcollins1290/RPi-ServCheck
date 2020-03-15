# RPi-ServCheck - Python systemd Monitoring script

RPi-ServCheck is a Python program that does two things:

1) Reads in a list of Services defined in a settings.ini file, loops through each service to obtain it's systemd status.
2) Checks for ANY systemd unit in failed status.

Any issues are then sent as an email to a email address defined in the settings.ini file.

Included with this Python program is a number of BASH launcher scripts so that the program can be run from CRON.
The following BASH launcher scripts are available:

-> hourly-launcher.sh   = When run hourly from CRON, an email is only sent if there is an issue.
-> midnight-launcher.sh = When run at midnight from CRON, an email is always sent even if all Services are OK.
-> reboot-launcher.sh   = When run after system startup, an email is always sent even if all Services are OK.

The following are example CRON entries to run the aforementioned BASH launcher scripts:

# RPi-ServCheck scripts
0 0 * * * /root/Git/RPi-ServCheck/midnight-launcher.sh
0 * * * * /root/Git/RPi-ServCheck/hourly-launcher.sh
@reboot /root/Git/RPi-ServCheck/reboot-launcher.sh
