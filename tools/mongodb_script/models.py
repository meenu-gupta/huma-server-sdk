from typing import Optional


class Row:
    def __init__(self, row_array):
        self.user_id = row_array[0]
        self.fenland_id = row_array[2]


class FileData(list):
    user_ids_list = None

    @property
    def user_ids(self):
        if not self.user_ids_list:
            self.user_ids_list = [row.user_id for row in self]
        return self.user_ids_list

    def get_fenland_id(self, user_id: str):
        filtered_rows = filter(lambda x: x.user_id == user_id, self)
        user_row: Optional[Row] = next(filtered_rows, None)
        return user_row.fenland_id if user_row else None
