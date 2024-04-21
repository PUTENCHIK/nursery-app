from fastapi import HTTPException


class UserException:
    @staticmethod
    def http(code: int, detail: str):
        return HTTPException(status_code=code, detail=detail)

    @staticmethod
    def user_exists(login: str):
        return UserException.http(
            code=404,
            detail=f"User with login '{login}' is already exists."
        )

    @staticmethod
    def wrong_admin_token(token: str):
        return UserException.http(
            code=404,
            detail=f"Entered wrong admin-token '{token}'."
        )

    @staticmethod
    def wrong_password(login: str):
        return UserException.http(
            code=404,
            detail=f"Entered wrong password for login '{login}'."
        )

    @staticmethod
    def no_user(login: str):
        return UserException.http(
            code=404,
            detail=f"No user with login '{login}'."
        )
