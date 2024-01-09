class MissingKyes(Exception):
    """Ошибка остуствия ключа."""

    pass


class ServerStatusNotOK(Exception):
    """API возвращает код, отличный от 200."""

    pass
