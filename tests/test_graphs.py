from chatterbot.trainers import ListTrainer
from chatterbot.conversation import Statement
from chatterbot.graphs import StatementGraph
from .base_case import ChatBotTestCase


class GraphTestCase(ChatBotTestCase):

    def setUp(self):
        super(GraphTestCase, self).setUp()
        self.chatbot.set_trainer(ListTrainer)
        self.chatbot.train([
            'Hi, how are you?',
            'I am good, how about you?',
            'I am also good.'
        ])
        self.graph = StatementGraph(self.chatbot.storage)

    def test_get_child_nodes(self):
        nodes = self.graph.get_child_nodes(Statement('Hi, how are you?'))

        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].text, 'I am good, how about you?')

    def test_get_parent_nodes(self):
        nodes = self.graph.get_parent_nodes(Statement('I am also good.'))

        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].text, 'I am good, how about you?')

    def test_search_children_for_best_match_exact(self):
        conversations = [
            [
                Statement('Hi, how are you?'),
                Statement('I am good, how about you?'),
                Statement('I am also good.')
            ],
            [
                Statement('Hi, how are you?'),
                Statement('I am great!'),
                Statement('That is good to hear.')
            ]
        ]

        for conversation in conversations:
            self.chatbot.train(statement.text for statement in conversation)

        search_node = Statement('I am great!')
        root_nodes = self.graph.get_parent_nodes(search_node)

        value, best_match = self.graph.search_children_for_best_match(search_node, root_nodes)

        self.assertEqual(best_match, search_node)
        self.assertEqual(value, 100)

    def test_find_closest_matching_sequence(self):

        conversation = [
            Statement('Hi, how are you?'),
            Statement('I am good, how about you?'),
            Statement('I am also good.')
        ]
        start_statement = conversation[0]

        self.chatbot.train(statement.text for statement in conversation)

        total_max_value, sequence = self.graph.find_closest_matching_sequence(
            start_statement,
            conversation
        )

        self.assertEqual(len(sequence), 3)
        self.assertEqual(conversation[0], sequence[0])
        self.assertEqual(conversation[1], sequence[1])
        self.assertEqual(conversation[2], sequence[2])
        self.assertEqual(total_max_value, 104)

    def test_list_close_matches_for_statements(self):
        statements = [
            Statement('Close'),
            Statement('Close.'),
            Statement('Close..'),
            Statement('Hello'),
            Statement('Hello!'),
            Statement('Hello!!!')
        ]

        for statement in statements:
            self.graph.storage.update(statement)

        results = self.graph.list_close_matches_for_statements([
            Statement('Close'),
            Statement('Hello')
        ], max_results=2)

        self.assertEqual(len(results), 4)
        self.assertIn('Close', results[1])
        self.assertIn('Close.', results[0])
        self.assertIn('Hello', results[3])
        self.assertIn('Hello!', results[2])


class SubtreeMatchingTestCase(ChatBotTestCase):

    def setUp(self):
        super(SubtreeMatchingTestCase, self).setUp()
        self.chatbot.set_trainer(ListTrainer)
        self.graph = StatementGraph(self.chatbot.storage)

    def test_exact_match(self):
        sequence = [
            Statement('Hi, how are you?'),
            Statement('I am good, how about you?'),
            Statement('I am also good.')
        ]
        self.chatbot.train(statement.text for statement in sequence)

        found = self.graph.find_closest_matching_sequence_in_tree(sequence)

        self.assertEqual(len(found), len(sequence))
        self.assertEqual(found[0], sequence[0])
        self.assertEqual(found[1], sequence[1])
        self.assertEqual(found[2], sequence[2])

    def test_close_match(self):
        sequence = [
            Statement('Are you a robot?'),
            Statement('No, I am not a robot.'),
            Statement('Darn, I like robots.')
        ]
        close_sequence = [
            Statement('Are thou a robot?'),
            Statement('I am not a robot.'),
            Statement('Okay, I like robots.')
        ]
        self.chatbot.train(statement.text for statement in sequence)

        found = self.graph.find_closest_matching_sequence_in_tree(close_sequence)

        print('found:', found)

        self.assertEqual(len(found), len(sequence))
        self.assertEqual(found[0], sequence[0])
        self.assertEqual(found[1], sequence[1])
        self.assertEqual(found[2], sequence[2])

    def test_partial_sequence_match(self):
        sequence = [
            Statement('Look at this cat!'),
            Statement('Wow, that is a cool cat.'),
            Statement('I know, right?')
        ]
        close_sequence = [
            Statement('Look at this cat!'),
            Statement('Where is it?')
        ]
        self.chatbot.train(statement.text for statement in sequence)

        found = self.graph.find_closest_matching_sequence_in_tree(close_sequence)

        print('found:', found)

        self.assertEqual(len(found), len(sequence))
        self.assertEqual(found[0], sequence[0])
        self.assertEqual(found[1], sequence[1])
        self.assertEqual(found[2], sequence[2])

    def test_partial_tree_match(self):
        sequence = [
            Statement('Look at this cat!'),
            Statement('Where is it?')
        ]
        close_sequence = [
            Statement('Look at this cat!'),
            Statement('Wow, that is a cool cat.'),
            Statement('I know, right?')
        ]
        self.chatbot.train(statement.text for statement in sequence)

        found = self.graph.find_closest_matching_sequence_in_tree(close_sequence)

        print('found:', found)

        self.assertEqual(len(found), len(sequence))
        self.assertEqual(found[0], sequence[0])
        self.assertEqual(found[1], sequence[1])


class SequenceMatchingTestCase(ChatBotTestCase):

    def test_get_all_ordered_subsets(self):
        from chatterbot.graphs import get_all_ordered_subsets

        subsets = list(get_all_ordered_subsets([1, 2, 3]))

        self.assertEqual(len(subsets), 6)
        self.assertIn([1], subsets)
        self.assertIn([2], subsets)
        self.assertIn([3], subsets)
        self.assertIn([1, 2], subsets)
        self.assertIn([2, 3], subsets)
        self.assertIn([1, 2, 3], subsets)

    def test_get_max_comparison(self):
        from chatterbot.graphs import get_max_comparison
        options = [
            Statement('I like to watch the boats on the river.'),
            Statement('Why are there boats on the river?'),
            Statement('I like to sail my boat on the river.')
        ]

        statement = Statement('I like to watch the boats.')
        confidence, result = get_max_comparison(statement, options)

        self.assertEqual(result, options[0])