import pexpect
import sys
import os
import time

password = "s)E7H5Z{BD(+ö(^"
host = "37.27.252.179"
pub_key_path = os.path.expanduser("~/.ssh/hetzner_key.pub")

def try_copy_id(user):
    print(f"\n--- Attempting with user: {user} ---")
    cmd = f"ssh-copy-id -i {pub_key_path} -o StrictHostKeyChecking=no {user}@{host}"
    child = pexpect.spawn(cmd, encoding='utf-8')
    
    # Enable logging to see what's happening
    # child.logfile = sys.stdout 

    try:
        i = child.expect(['password:', 'Password:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
        if i == 0 or i == 1:
            print("Password prompt detected. Sending password...")
            child.sendline(password)
            j = child.expect(['Number of key\(s\) added:', 'Permission denied', 'Time out', pexpect.EOF], timeout=10)
            if j == 0:
                print(f"SUCCESS: Key added for user {user}!")
                return True
            elif j == 1:
                print(f"FAILED: Permission denied for {user}.")
            else:
                print(f"FAILED: Unknown response or timeout. Output:\n{child.before}")
        else:
            print(f"FAILED: No password prompt (maybe key already there or connection blocked). Output:\n{child.before}")
    except Exception as e:
        print(f"Error during execution: {e}")
    
    child.close()
    return False

if __name__ == "__main__":
    if try_copy_id("root"):
        sys.exit(0)
    
    if try_copy_id("adminuser"):
        sys.exit(0)
        
    print("\nALL ATTEMPTS FAILED.")
