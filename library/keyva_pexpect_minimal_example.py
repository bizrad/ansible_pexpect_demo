#!/usr/bin/env python
from ansible.module_utils.basic import AnsibleModule


"""
### IMPORTANT ###
Do NOT use any print statements.
  Can cause an ansible failure due to json output being expected.
Do NOT use any sys.exit statements.
  Use module.fail_json instead.
  Pass the module object or raise and catch in the main function.
"""


# Main minimal ansible module example with one input and one output variable
def main():
    # Example with no incoming arguments
    # module = AnsibleModule()
    # Example with incoming argument named "mysetting"
    module = AnsibleModule(argument_spec=dict(mysetting=dict(required=False, type='str')))
    # Set an example variable to return
    return_value = "mysetting value is: {0}".format(module.params['mysetting'])
    # See the keyva_pexpect_install.py for a better real wold example of failing using excption handling
    foo = "bar"
    if foo != "bar":
        # Cause an ansible failure
        module.fail_json(msg="Error: foo != 'bar'")
    # Exit on success setting ansible changed status and a custom variable named "my_output"
    mychanged = True
    module.exit_json(changed=mychanged, my_output=return_value)


# Minimal pexpect example
# Not used in main, this is just a minimal example of code
def run_pexpect(password):
    import pexpect
    child = pexpect.spawn('/path/to/myscript.sh', encoding='utf-8')
    # NOTE: Always use a timeout with automation, a huge timeout is better than not catching something stuck
    child.timeout = 60
    child.expect(r"Enter password\:")
    child.sendline(password)
    child.expect('Thank you')
    # child.after contains the regex match for the last expect statement
    # If we were to look at it here it would be 'Thank you'
    # Can be very useful when matching a regex and not a string
    child.sendline('exit')
    child.expect(pexpect.EOF)
    # child.before contains the text between the last two expect statements up to the buffer limit
    exit_dialog = child.before.strip()
    return exit_dialog

"""
# How to use python module across multiple Ansible library modules
# See files in module_utils/python_module_example
import python_module_example
foo = python_module_example.test.test_function()
# OR
from python_module_example.test import test_function
foo = test_function()
"""


# Using this is best practice so that you could import this
#   module for testing it's functions without running main.
if __name__ == '__main__':
    main()
