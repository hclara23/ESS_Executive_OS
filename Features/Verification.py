import secrets

import Features.Database as db
from getpass import getpass, getuser
from Features.Face.Mouth import speak


def set_pass():
    speak("Enter your new password below:")
    new_pass = getpass("Enter new pass: ")
    try:
        db.Updatepassword(getuser(), new_pass)
        speak("New password has been changed successfully.")
    except Exception as e:
        print(f"[Verification] Failed to update password: {e}")
        speak("There was a problem updating your password.")


def set_user():
    print("--- If you don't know your user name type \"whoami\" in command prompt.--- ")
    speak("Enter new user name below")
    new_user = input("Enter user name: ")
    try:
        db.Addnewuser(new_user)
        speak("New user added successfully.")
    except Exception as e:
        print(f"[Verification] Failed to add user: {e}")
        speak("There was a problem adding the new user.")


def verify_user(isnewpass=0, setnewuser=False):
    try:
        info = db.Infodetails(getuser())
    except Exception as e:
        print(f"[Verification] Database error during login: {e}")
        speak("Authentication failed due to a database error.")
        return False

    known_users = info[0]
    u_pwd = info[1]
    isadmin = info[2]

    if getuser() != known_users:
        speak("User Authentication Failed!\nPlease login through a verified account or contact your admin to get verified.")
        return False

    if setnewuser and not isadmin:
        return False

    speak("User Authentication Successful!")
    for i in range(3):
        if isnewpass == 0:
            speak("Please type your password below:")
        else:
            speak("Enter your current password below:")
        p_pwd = getpass(prompt="Enter password: ")

        if secrets.compare_digest(p_pwd, u_pwd):
            return True

        if i == 2:
            speak("Maximum attempts exceeded.\nPlease contact admin and try again later.")
            return False

        speak(f"Wrong password!\n[Attempts Left: {3 - (i + 1)}]\nTry again.")

    return False
