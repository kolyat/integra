import logging
import keyring


class UserPassword:
    @staticmethod
    def get_password(username: str, namespace: str = 'integra'):
        return keyring.get_password(namespace, username)

    @staticmethod
    def set_password(username: str, password1: str, password2: str,
                     namespace: str = 'integra'):
        if not username:
            logging.info('UserPassword: No username given')
            return False
        if password1 == password2:
            keyring.set_password(namespace, username, password1)
            logging.info(f'UserPassword: Successfully saved password'
                         f' for {username}')
            return True
        else:
            logging.info('UserPassword: Passwords do not match')
            return False
