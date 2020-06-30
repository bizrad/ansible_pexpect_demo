RHUG2020_ansible_pexpect
=========
This repo contains a demo code of a custom ansible module in python using pexpect.

This was tested using CentOS 7 and 8 on a vagrant VM.

Note: the **Vagrantfile** is set up for a mac and uses a static IP. **Please edit it as needed before running.**

These playbooks can be launched without any extra_vars.

Running the Example
------------------
```
# Vagrant VM run
$ vagrant up
$ ansible-playbook -v -i "192.168.0.115," -u vagrant ./playbook.yaml

# Localhost run
# (install the pexpect module with pip first)
$ ansible-playbook -v ./localhost.yaml
```
Author Information
------------------

Brad Johnson

Keyva

https://keyvatech.com/

https://github.com/keyvatech
