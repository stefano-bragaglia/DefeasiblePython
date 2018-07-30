from collections import namedtuple
from typing import List, Optional, Set

from defeasible.domain.definitions import RuleType

OrderedLiteral = namedtuple('OrderedLiteral', 'position literal')
Trace = Set[OrderedLiteral]
Derivation = List['Literal']


class NotGroundLiteralException(Exception):
    pass


class Memory:
    def __init__(self, program: 'Program'):
        from defeasible.domain.definitions import RuleType

        self._facts = set()
        self._stricts = dict()
        self._defeasibles = dict()
        for rule in program.get_ground_program().rules:
            if rule.is_fact():
                self._facts.add(rule)
            self._defeasibles.setdefault(rule.head, set()).add(rule)
            if rule.type == RuleType.STRICT:
                self._stricts.setdefault(rule.head, set()).add(rule)

    def derive(self, literal: 'Literal', type: RuleType = RuleType.DEFEASIBLE) -> Optional[List[Derivation]]:
        if not literal.is_ground():
            raise NotGroundLiteralException("Ground literal expected, but '%s' found" % literal)

        if not self._facts:
            return None

        if literal not in (self._defeasibles if type is RuleType.DEFEASIBLE else self._stricts):
            return None

        results = []
        for rule in (self._defeasibles if type is RuleType.DEFEASIBLE else self._stricts)[literal]:
            complete = True
            derivations = [[]]
            for body in rule.body:
                partials = self.derive(body)
                if partials is None:
                    complete = False
                    break

                temporary = []
                for derivation in derivations:
                    for partial in partials:
                        current = [*derivation]
                        for value in partial:
                            if value not in current:
                                current.append(value)
                        if current and current not in temporary:
                            temporary.append(current)
                derivations = temporary

            if complete:
                for derivation in derivations:
                    if rule.head not in derivation:
                        derivation.append(rule.head)
                    results.append(derivation)

        return results


if __name__ == '__main__':
    from defeasible.domain.rendering import Renderer
    from defeasible.domain.definitions import Program

    p = Program.parse("""
        bird(X) <- chicken(X).
        bird(X) <- penguin(X).
        ~flies(X) <- penguin(X).
        chicken(tina).
        penguin(tweety).
        scared(tina).
        flies(X) -< bird(X).
        flies(X) -< chicken(X), scared(X).
        nests_in_trees(X) -< flies(X).
        ~flies(X) -< chicken(X).
    """)
    m = Memory(p)
    p = p.get_ground_program()
    print(Renderer.render(p))
    print()

    for literal in sorted(p.as_literals()):
        print(Renderer.render(literal))
        derivations = m.derive(literal)
        if derivations is None:
            print('\t', 'impossible')
        elif not derivations:
            print('\t', 'empty')
        else:
            for derivation in derivations:
                print('\t', ', '.join(Renderer.render(lit) for lit in derivation))
        print()

    # p = p.get_ground_program()
    # for literal in sorted(p.as_literals()):
    #     print(Renderer.render(literal))
    #     arguments = p.get_arguments(literal)
    #     if not arguments:
    #         print('\t', '-')
    #     else:
    #         for argument in sorted(arguments):
    #             print('\t', Renderer.render(argument))

    # p = p.get_ground_program()
    # arguments = {arg for lit in p.as_literals() for arg in p.get_arguments(lit)}
    # for arg in arguments:
    #     print(Renderer.render(arg))
    #     for other in arguments:
    #         if other != arg and other.is_substructure(arg):
    #             print('\t', Renderer.render(other))
    #     print()
