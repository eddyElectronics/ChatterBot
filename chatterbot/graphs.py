class StatementGraph(object):
    """
    This object is a wrapper around chatterbot's storage backend
    that makes it more convenient to traverse known statements as
    a tree-like data structure.
    """

    def __init__(self, storage):
        self.storage = storage

    def get_child_nodes(self, statement):
        return self.storage.filter(in_response_to__contains=statement.text)

    def get_parent_nodes(self, statement):
        return self.storage.find(statement.text).in_response_to

    def search_children_for_best_match(self, search_node, root_nodes, max_depth=2):
        """
        Search for a best match down to a maximum depth.
        """
        nodes = set(root_nodes)

        # Get all nodes down to the maximum depth
        while max_depth >= 0:
            max_depth -= 1
            for node in nodes.copy():
                children = self.get_child_nodes(node)
                nodes.update(children)

        return get_max_comparison(search_node, nodes)

    def list_close_matches_for_statements(self, statements, max_results=10):
        """
        Takes a list of statements and returns a dictionary where each key is
        the index of the statement in the list, and each value is a list of tuples.
        The first element of each tuple is the closeness that the statement matched,
        and the second value of the tuple is the statement that matched.
        The tuples in the list represent the top selection of most closely matching
        statements.
        """
        close_entries = []
        entries = {}

        for known_statement in self.storage.filter():
            for index, statement in enumerate(statements):

                if index not in entries:
                    entries[index] = []

                closeness = statement.compare_to(known_statement)
                entries[index].append((closeness, known_statement, ))

                if len(entries[index]) > max_results:

                    # Sort the list by the closeness value
                    entries[index].sort(key=lambda tup: tup[0])

                    # Remove the least-close vlaue from the list
                    entries[index].pop(0)

        # Add the top set of close entries to the list of candidates
        for index in range(0, len(entries)):
            close_entries += entries[index]

        return close_entries

    def find_closest_matching_sequence(self, start_statement, conversation):
        """
        Takes a conversation (a list of statements). Returns a sum of the best matching
        closest statement comparasons within an alloted search distance from each consecutive
        response.
        """
        total_max_value = 0
        sequence = [start_statement]

        for statement in conversation:
            child_nodes = self.get_child_nodes(sequence[-1])
            if child_nodes:
                max_value, max_node = self.search_children_for_best_match(statement, child_nodes)
                current_node = max_node
                total_max_value += max_value
                sequence.append(max_node)

        return total_max_value, sequence

    def find_closest_matching_sequence_in_tree(self, conversation, max_depth=100, max_search_distance=1):
        """
        Method to find the closest match to a sequence of strings in
        a tree-like data structure.

        Find the closest match to a sequence S1 l1 S2 l2 S3 l3 ... Sn where each
        Sx is an element in the list S at an index of x and where l is some number
        of S-like elements between 0 and max. Allow the case that some Sx may not
        exist.
        """
        # First, create a list of possible close matches for each statement in the conversation
        # These are candiate root nodes for the closest matching sequence
        matching_data = self.list_close_matches_for_statements(conversation)

        total_max_value = -1
        max_sequence = []

        for match_value, match_statement in matching_data:

            # Check for a close match to next elements in the conversation
            value, sequence = self.find_closest_matching_sequence(match_statement, conversation)

            # Create a sum of the closeness of each of the adjacent element's closeness
            match_sum = match_value + value

            if match_sum > total_max_value:
                total_max_value = match_sum
                max_sequence = sequence

        return max_sequence


def get_all_ordered_subsets(items):
    """
    Return a list of all ordered subsets of the input list.
    """
    from itertools import combinations
    for i, j in combinations(range(len(items) + 1), 2):
        yield items[i:j]


def get_max_comparison(match_statement, statements):
    """
    Given a statement and a list of statements, return the statement from
    the list that most closely matches the given statement.
    """
    max_value = -1
    max_statement = None

    for statement in statements:
        value = match_statement.compare_to(statement)

        if value > max_value:
            max_value = value
            max_statement = statement

    return max_value, max_statement
