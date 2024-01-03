class MissingKyes(Exception):
    """Ошибка остуствия ключа."""

    pass


class DocumentationInconsistency():
    """Ошибка несоотвествии документации."""

    pass


class ServerStatusNotOK(Exception):
    """API возвращает код, отличный от 200."""

    pass
