from functools import wraps


def handle(*node_classes):
    assert node_classes

    @wraps(handle)
    def inner(func):
        func.handles_classes = node_classes
        return func

    return inner


class EvaluatorMeta(type):
    def __init__(cls, name, bases, dct):
        for value in dct.values():
            if hasattr(value, 'handles_classes'):
                for handled_class in value.handles_classes:
                    cls.handler_map[handled_class] = value


class Evaluator(metaclass=EvaluatorMeta):
    handler_map = {}

    def evaluate(self, node):
        if hasattr(node, 'get_sub_nodes'):
            sub_args = [
                self.evaluate(sub_node)
                for sub_node in node.get_sub_nodes()
            ]
        else:
            sub_args = []

        node_type = type(node)
        if node_type in self.handler_map:
            return self.handler_map[node_type](self, node, *sub_args)
        return self.adopt(node, *sub_args)

    def adopt(self, node, *sub_args):
        raise NotImplementedError(
            f'Failed to evaluate node of type {type(node)}'
        )
