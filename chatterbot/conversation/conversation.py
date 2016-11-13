Conversation(object):

    def __init__(self):
        self.statements = []

    def get_previous_statement(self):
        if not self.statements:
            return None
        return self.statements[-1]

    def add_statement(self, statement):
        """
        Adds a statement to the conversation.
        This statement will be considered the latest statement
        in the conversation.
        """
        previous_statement = self.get_previous_statement()
        if previous_statement:
            statement.add_response(previous_statement)

        self.statements.append(statement)