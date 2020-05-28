#!/usr/bin/env python
import os
import tempfile

DOCUMENTATION = '''
---
module: keyva_pexpect_install

short_description: This is a custom module using pexpect to run commands in mock.sh

description:
    - "This module runs commands inside a script in a shell. When run without commands it returns current settings only."

options:
    path:
        description:
            - Path to the script to run
        required: true
    password:
        description:
            - Password needed to run demo script
        required: true
    timeout:
        description:
            - Timeout for running the script
        required: false
        default: 300
    mock_failure:
        description:
            - Run a failure test scenario
        choices: ['password', 'timeout', 'error_abort', 'die_early']
        required: false
    
author:
    - Brad Johnson, Keyva 
    - https://github.com/keyvatech
    - https://keyvatech.com/ 
'''

EXAMPLES = '''
- name: "Run our custom pexpect module"
  keyva_pexpect_install:
    path: "mock.sh"
    password: "{{ pexpect_demo_password }}"
    timeout: 60
'''

RETURN = '''
output: String containing output from script
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
            password=dict(required=True, type='str', no_log=True),
            timeout=dict(required=False, type='int', default='60'),
            mock_failure=dict(required=False, type='str', default=None,
                              choices=['password', 'timeout', 'error_abort', 'die_early'])
        )
    )
    path = module.params['path']
    password = module.params['password']
    timeout = module.params['timeout']
    mock_failure = module.params['mock_failure']

    try:
        # Importing the modules here allows us to catch them not being installed on remote hosts
        #   and pass back a failure via ansible instead of a stack trace.
        import pexpect
    except ImportError:
        module.fail_json(msg="You must have the pexpect python module installed to use this Ansible module.")

    try:
        # Run our pexpect function
        script_output, install_logfile, changed, child_exitstatus, errors_found = run_pexpect(path, password, timeout, mock_failure)

        # Exit on success and pass back objects to ansible, which are available as registered vars
        module.exit_json(changed=changed, script_output=script_output,
                         logfile=install_logfile, return_code=child_exitstatus, errors_found=errors_found)

    # Use python exception handling to keep all our failure handling in our main function
    except pexpect.TIMEOUT as err:
        module.fail_json(msg="pexpect.TIMEOUT: Unexpected timeout waiting for prompt or command: {0}".format(err))

    except pexpect.EOF as err:
        module.fail_json(msg="pexpect.EOF: Unexpected program termination: {0}".format(err))

    except pexpect.exceptions.ExceptionPexpect as err:
        # This catches any pexpect exceptions that are not EOF or TIMEOUT
        # This is the base exception class
        module.fail_json(msg="pexpect.exceptions.{0}: {1}".format(type(err).__name__, err))

    # We use this to exit on failure instead of a sys.exit call.
    except RuntimeError as err:
        module.fail_json(msg="{0}".format(err))


def run_pexpect(script_path, password, timeout=60, mock_failure=None):
    """
    mock_failure can cause intentional failure when set to: 'password', 'timeout', 'error_abort', or 'die_early'
    This variable is for demo purposes only, please remove it if you want to reuse this code.
    """
    import pexpect
    if not os.path.exists(script_path):
        raise RuntimeError("Error: the script '{0}' does not exist!".format(script_path))

    # Set some default variables
    changed = True
    program_failed = False
    install_logfile = None

    # Set some variables for error catch and handling
    errors_found = []
    if mock_failure == 'error_abort':
        fail_on_errors = True
    else:
        fail_on_errors = False

    # Test die early scenario and cause the password prompt expect to raise pexpect.EOF
    if mock_failure == 'die_early':
        script_path = '/bin/bash -c "exit 0"'

    # Create a temp log file and start our program
    #   it is automatically deleted after the block exits
    with tempfile.NamedTemporaryFile() as tmp_output:
        # Use a try block here so we can always run the close finally statement
        try:
            # Start our program
            # Note that calling a simple script does not need the encoding option
            # A bash shell would need encoding='utf-8'
            child = pexpect.spawn(script_path)
            child.logfile = tmp_output

            # If you have a program with TONS of output use these options to deal with it.
            # child = pexpect.spawn(script_path, maxread=100000000, searchwindowsize=2000)

            # make sure we don't wait long for a password prompt
            child.timeout = 10
            # Look for password prompt
            i = child.expect([r"Please enter your password", r'(?i)software already installed.+?$'])
            if i == 1:
                changed = False
                child.close()
                return child.after.strip(), None, changed, child.exitstatus, errors_found
            # Send password
            if mock_failure == 'password':
                child.sendline()
            else:
                child.sendline(password)
            try:
                child.timeout = 2
                child.expect(pexpect.EOF)
            except pexpect.TIMEOUT:
                pass
            else:
                raise RuntimeError("This program is really bad and doesn't even tell us about bad passwords...")
            # Set the timeout to run the main program
            # NOTE: Always use a timeout with automation, a huge timeout is better than not catching something stuck
            child.timeout = timeout
            while True:
                # Note that using the pseudo tty causes \r\n line endings even on linux
                i = child.expect([r'ERROR:.+?\r\n',
                                  r'(?i)do you wish to continue',
                                  r'(?i)log file:.+?\r\n',
                                  r'FATAL ERROR',
                                  pexpect.EOF])
                if i == 0:
                    errors_found.append(child.after.strip())
                elif i == 1:
                    if mock_failure == 'timeout':
                        child.expect(r'bad expect this will cause a pexpect.TIMEOUT')
                    if fail_on_errors and errors_found:
                        child.sendline('n')
                    else:
                        child.sendline('y')
                elif i == 2:
                    install_logfile = child.after.split()[-1]
                elif i == 3:
                    program_failed = True
                elif i == 4:
                    # The program exited with an EOF
                    break

            # Now let's take our temporary log file and turn it into a variable
            tmp_output.flush()
            tmp_output.seek(0)
            script_output = tmp_output.read()
        finally:
            # Always hang up on the process and close the pty
            child.close()
        if program_failed:
            raise RuntimeError("The program failed to run properly.\nOutput:\n{0}".format(script_output))

    return script_output, install_logfile, changed, child.exitstatus, errors_found


if __name__ == '__main__':
    main()
