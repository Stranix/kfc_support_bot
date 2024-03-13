class BreakShiftError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class TaskAssignedError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DocumentsNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class NotAvailableToAssignError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class NoSelectedEngineerError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class TaskNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
