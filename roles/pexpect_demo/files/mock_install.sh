#!/bin/bash
PASSWORD=RHUG2020
FILE=/tmp/pexpect_mock_demo
LOGFILE=/tmp/pexpect_mock_demo.$(date '+%Y%m%d').log

# Let's use this script to mock test the following use cases:
#  Checking if the program says it is already installed and having ansible respond changed=false
#  Checking if a program had an error and but exited 0
#  Responding to an expected prompt
#  Hitting a prompt and having a bad response or no response - timeout
#  Checking for success if we can't rely on the exit code

echo "Welcome to the mock interactive installer!"

if test -f "$FILE"; then
    echo "Software already installed at: $FILE"
    exit 0
fi

echo "This is a bash script but let's pretend it's a compiled binary program"
# This is a bad program so we don't hide password input with -s
read -p "Please enter your password: " PASSWORD_CHECK

if [[ $PASSWORD_CHECK == $PASSWORD ]]; then
  echo -e "\nPassword accepted!\n"
else
  # Let's exit 0 here because we're a poorly written program
  #   and we don't use proper exit codes!
  exit 0
fi

echo "Let's pretend we're installing a program..."

# Let's pretend there was a warning prompt
echo "ERROR: splines not properly reticulated..."
while true; do
    read -p "Do you wish to continue anyways (Y/n)?" CHOICE
    case $CHOICE in
        [Yy]*|'' ) echo "Continuing with install..."; break;;
        [Nn]* ) echo -e "\nUser aborted process\nFATAL ERROR!";exit 0;;
        * ) echo "Please answer yes or no.";;
    esac
done

# Create a file in tmp
touch $FILE
echo "We ran the install mock script at: $(date)" >>$LOGFILE
echo "Log file: $LOGFILE"
echo "Created file: $FILE"
echo "Install successful!"
exit 0