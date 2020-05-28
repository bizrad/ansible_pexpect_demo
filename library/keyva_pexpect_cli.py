#!/usr/bin/env python
import os
import sys

DOCUMENTATION = '''
---
module: keyva_pexpect_cli

short_description: This is a custom module using pexpect to run commands in myscript.sh

description:
    - "This module runs commands inside a script in a shell. When run without commands it returns current settings only."

options:
    path:
        description:
            - Path to the script to run
        required: true
    commands:
        description:
            - The commands to run inside myscript in order
        required: false
    options:
        description:
            - options to pass the script
        required: false
    timeout:
        description:
            - Timeout for finding the success string or running the program
        required: false
        default: 300
    password:
        description:
            - Password needed to run myscript
        required: true

author:
    - Brad Johnson, Keyva 
    - https://github.com/keyvatech
    - https://keyvatech.com/ 
'''

EXAMPLES = '''
- name: "Run myscript to set up myprogram"
  keyva_pexpect_cli:
    path: "/path/to/myscript.sh"
    options: "-o myoption"
    password: "{{ myscript_password }}"
    commands:
      - "set minheap 1024m"
      - "set maxheap 5120m"
      - "set port 7000"
      - "set webport 80"
    timeout: 300
'''

RETURN = '''
current_settings: String containing current settings after last command was run and settings saved
    type: str
    returned: On success
logfile: String containing logfile location on the remote host from our script
    type: str
    returned: On success
'''


def main():
    # This is the import required to make this code an Ansible module
    from ansible.module_utils.basic import AnsibleModule
    # This instantiates the module class and provides Ansible with
    # input argument information, it also enforces input types
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(required=True, type='str'),
            commands=dict(required=False, type='list', default=[]),
            options=dict(required=False, type='str', default=""),
            password=dict(required=True, type='str', no_log=True),
            timeout=dict(required=False, type='int', default='300')
        )
    )
    path = module.params['path']
    commands = module.params['commands']
    options = module.params['options']
    password = module.params['password']
    timeout = module.params['timeout']

    try:
        # Importing the modules here allows us to catch them not being installed on remote hosts
        #   and pass back a failure via ansible instead of a stack trace.
        import pexpect
    except ImportError:
        module.fail_json(msg="You must have the pexpect python module installed to use this Ansible module.")

    try:
        # Run our pexpect function
        current_settings, changed, logfile = run_pexpect(path, options, commands, password, timeout)
        # Exit on success and pass back objects to ansible, which are available as registered vars
        module.exit_json(changed=changed, current_settings=current_settings, logfile=logfile)
    # Use python exception handling to keep all our failure handling in our main function
    except pexpect.TIMEOUT as err:
        module.fail_json(msg="pexpect.TIMEOUT: Unexpected timeout waiting for prompt or command: {0}".format(err))
    except pexpect.EOF as err:
        module.fail_json(msg="pexpect.EOF: Unexpected program termination: {0}".format(err))
    except pexpect.exceptions.ExceptionPexpect as err:
        # This catches any pexpect exceptions that are not EOF or TIMEOUT
        # This is the base exception class
        module.fail_json(msg="pexpect.exceptions.{0}: {1}".format(type(err).__name__, err))
    except RuntimeError as err:
        module.fail_json(msg="{0}".format(err))


def run_pexpect(script_path, options, commands, password, timeout=300):
    import pexpect
    changed = True
    if not os.path.exists(script_path):
        raise RuntimeError("Error: the script '{0}' does not exist!".format(script_path))

    # This is what we set the prompt to so we can recognize bash prompts
    prompt = r'\[PEXPECT\]\$'
    # Here's another example of a prompt for RHEL if you didn't want to set it
    # prompt = r'\[{0}\@.+?\]\$'.format(getpass.getuser())

    # Note that the bash shell outputs in utf-8 in RHEL/CentOS 8, unlike a simple script
    # Using encoding will automatically encode/decode as needed
    if sys.version_info.major == "2":
        child = pexpect.spawn('/bin/bash')
    else:
        child = pexpect.spawn('/bin/bash', encoding='utf-8')
    try:
        # Set our prompt so we recognize it
        child.sendline(r"PS1=[PEXPECT]\$")
        # Look for initial bash prompt
        child.expect(prompt)
        # Start our program
        child.sendline("{0} {1}".format(script_path, options))
        # look for our scripts logfile prompt
        # Example text seen in output: 'Logfile: /path/to/mylog.log'
        child.expect(r'Logfile\:.+?/.+?\.log')
        # Note that child.after contains the text of the matching regex
        logfile = child.after.split()[1]
        # Look for password prompt
        i = child.expect([r"Enter password\:", '>'])
        if i == 0:
            # Send password
            child.sendline(password)
        # Increase timeout for longer running interactions after quick initial ones
        # NOTE: Always use a timeout with automation, a huge timeout is better than not catching something stuck
        child.timeout = timeout
        try:
            # Look for program internal prompt or new config dialog
            i = child.expect([r'Initialize New Config\?', '>'])
            # pexpect will return the index of the regex it found first
            if i == 0:
                # Answer 'y' to initialize new config prompt
                child.sendline('y')
                child.expect('>')
            # If any commands were passed in loop over them and run them one by one.
            for command in commands:
                child.sendline(command)
                i = child.expect([r'ERROR.+?does not exist', r'ERROR.+?$', '>'])
                if i == 0:
                    # Attempt to intelligently add items that may have multiple instances and are missing
                    # e.g. "socket.2" may need "add socket" run before it.
                    # Try to allow the user just to use the set command and run add as needed
                    try:
                        new_item = child.after.split('"')[1].split('.')[0]
                    except IndexError:
                        raise RuntimeError("ERROR: unable to automatically add new item in myscript,"
                                           " file a bug\n  {0}".format(child.after))
                    child.sendline('add {0}'.format(new_item))
                    i = child.expect([r'ERROR.+?$', '>'])
                    if i == 0:
                        raise RuntimeError("ERROR: unable to automatically add new item in myscript,"
                                           " file a bug\n  {0}".format(child.after.strip()))
                    # Retry the failed original command after the add
                    child.sendline(command)
                    i = child.expect([r'ERROR.+?$', '>'])
                    if i == 0:
                        raise RuntimeError("ERROR: unable to automatically add new item in myscript,"
                                           " file a bug\n  {0}".format(child.after.strip()))
                elif i == 1:
                    raise RuntimeError("ERROR: unspecified error running a myscript command\n"
                                       "  {0}".format(child.after.strip()))
            # Set timeout shorter for final commands
            child.timeout = 15
            # If we processed any commands run the save function last
            if commands:
                child.sendline('save')
                # Using true loops with expect statements allow us to process multiple items in a block until
                #    some kind of done or exit condition is met where we then call a break.
                while True:
                    i = child.expect([r'No changes made', r'ERROR.+?$', '>'])
                    if i == 0:
                        changed = False
                    elif i == 1:
                        raise RuntimeError("ERROR: unexpected error saving configuration\n"
                                           "  {0}".format(child.after.strip()))
                    elif i == 2:
                        break
            # Always print out the config data from out script and return it to the user
            child.sendline('print config')
            # Expect our command echo from pexpect
            child.expect('print config')
            child.expect('>')
            # Note that child.before contains the output between the last two expects, up to the character limit
            current_settings = child.before.strip()
            # Run the 'exit' command that is inside myscript
            child.sendline('exit')
            # Look for a linux prompt to see if we quit
            child.expect(prompt)
        except pexpect.TIMEOUT:
            raise RuntimeError("ERROR: timed out waiting for a prompt in myscript")
        # Get shell/bash return code of myscript
        child.sendline("echo $?")
        child.expect(prompt)
        # process the output into a variable and remove any whitespace
        exit_status = child.before.split('\r\n')[1].strip()
        if exit_status != "0":
            raise RuntimeError("ERROR: The command returned a non-zero exit code! '{0}'".format(exit_status))
        # Exit bash shell
        child.sendline('exit 0')
        # run exit as many times as needed to exit the shell or subshells
        # This might be useful if you ran a script that put you into a new shell where you then ran some other scripts
        while True:
            i = child.expect([prompt, pexpect.EOF])
            if i == 0:
                child.sendline('exit 0')
            elif i == 1:
                break
    finally:
        # Always try to close the pexpect process
        child.close()
    return current_settings, changed, logfile


if __name__ == '__main__':
    main()
