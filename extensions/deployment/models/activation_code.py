class ActivationCode:
    _code: str

    USER_CODE_LENGTH: int = 8
    MANAGER_CODE_LENGTH: int = 12
    EXTENSION_LENGTH: int = 2
    TOTAL_CODE_LENGTH = USER_CODE_LENGTH + EXTENSION_LENGTH

    def __init__(self, code: str):
        self._code = code
        if not any((self.is_for_user(), self.is_for_manager())):
            raise TypeError("Given code doesn't match any pattern")

    def __len__(self):
        return len(self._code)

    def __repr__(self):
        return self._code

    @property
    def extension(self):
        start = self.USER_CODE_LENGTH
        if self.is_for_manager():
            start = self.MANAGER_CODE_LENGTH

        return self._code[start : self.TOTAL_CODE_LENGTH]

    @property
    def base(self):
        if self.is_for_user():
            return self._code[: self.USER_CODE_LENGTH]
        elif self.is_for_manager():
            return self._code[: self.MANAGER_CODE_LENGTH]

    def is_for_user(self):
        code_len = len(self)
        return code_len == self.USER_CODE_LENGTH or code_len == self.TOTAL_CODE_LENGTH

    def is_for_manager(self):
        return len(self) == self.MANAGER_CODE_LENGTH
