import keyring


def main():
    print()
    print('======================')
    print('Password setup utility')
    print('======================')
    print()
    print()
    print('Enter username: ', end='')
    username = input()
    if username:
        print('Enter password: ', end='')
        passwd = input()
        print('Repeat password: ', end='')
        passwd2 = input()
        if passwd == passwd2:
            keyring.set_password('system', username, passwd)
            print('\nPassword saved to keyring\n')
        else:
            print('\nPasswords do not match, closing\n')
    else:
        print('\nNo username given, closing\n')
    return


if __name__ == '__main__':
    main()
