#!/bin/bash
PASSWORD=RHUG2020
LOGFILE=/tmp/pexpect_mock_cli.$(date '+%Y%m%d').log

# Let's use this script to mock test accessing an interactive CLI

echo "Welcome to the mock CLI!"
echo "Logfile: $LOGFILE"

read -s -p "Enter password: " PASSWORD_CHECK

if [[ $PASSWORD_CHECK == $PASSWORD ]]; then
  echo -e "\nPassword accepted!\n"
else
  exit 1
fi

while true; do
    IFS=' ' read -p "> " -a TEST
    case "${TEST[@]}" in
        set*)
            echo "${TEST[1]} set to ${TEST[2]}"
        ;;
        print\ config)
            echo -e "\nFake Config:\nminheap: 1024m\nmaxheap: 5120m\nport: 7000\nwebport: 80"
        ;;
        save)
            if [[ $1 == "mock_no_changes" ]]; then
                echo "No changes made."
            else
                echo "Settings saved!"
            fi
        ;;
        exit)
            echo "Exiting fake cli"; break
        ;;
    esac
done

exit 0