ansible_pexpect_demo
=========
This repo contains example code of custom Ansible modules in python using pexpect. The goal of this code is to provide good examples that cover interacting with both a CLI and an interactive installer. These can hopefully be used as a basis for creating new modules by others.

This was tested using CentOS 7 and 8 on a vagrant VM.

Note: the **Vagrantfile** is set up for a mac and uses a static IP. **Please edit it as needed before running.**

These playbooks can be launched without any extra_vars.

Important Files
------------------
**roles/pexpect_demo/files/mock_cli.sh**  -  This is a simple script that just pretends to be a CLI and echos back to specific inputs.

**library/keyva_pexpect_cli.py**  -  This is the corresponding Ansible module that runs and interacts with the mock_cli.sh script.

**roles/pexpect_demo/files/mock_install.sh**  -  This script is an example of an installer that behaves very poorly. It always exits 0, terminates without a message on a bad password and calls an error, but doesn't quit.

**library/keyva_pexpect_install.py**  -  This custom Ansible module covers how to deal with these difficult situations in code.

**library/keyva_pexpect_minimal_example.py**  -  This module shows the minimum amount of code needed to create a new Anisble module.

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
