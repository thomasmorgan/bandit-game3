""" The Bandit Game! """

from dallinger.experiments import Experiment
from dallinger.nodes import Agent, Source
from dallinger.models import Info, Network, Vector, Participant
from dallinger.networks import DiscreteGenerational
from dallinger.information import Gene
import random
import json
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import cast
from sqlalchemy import Integer
from psiturk.psiturk_config import PsiturkConfig
from dallinger import config as dalcon
from operator import attrgetter
config = dalcon.experiment_configuration
cfg = PsiturkConfig()


class BanditGame(Experiment):

    def __init__(self, session):
        super(BanditGame, self).__init__(session)
        self.task = "The Bandit Game"
        self.verbose = False
        self.experiment_repeats = 1

        self.initial_recruitment_size = config.generation_size
        self.known_classes["Decision"] = Decision

        self.trials_per_round = config.trials_per_round
        self.rounds = config.rounds

        if not self.networks():
            self.setup()
        self.save()

    def setup(self):
        super(BanditGame, self).setup()
        for net in self.networks():
            source = GeneticSource(network=net)
            source.create_genes()

    def create_network(self):
        """Return a new network."""
        return BanditGenerational(generations=config.generations,
                                  generation_size=config.generation_size,
                                  initial_source=True)

    def create_node(self, participant, network):
        """Create a node for a participant."""
        return BanditAgent(network=network, participant=participant)

    def recruit(self):
        """Recruit participants if necessary."""
        num_approved = len(Participant.query.filter_by(status="approved").all())
        if num_approved % config.generation_size == 0 and num_approved != config.generations*config.generation_size:
            self.log("generation finished, recruiting another")
            self.recruiter().recruit_participants(n=config.generation_size)

    def submission_successful(self, participant):
        """Calculate fitness of nodes if all nodes finished."""
        num_approved = len(Participant.query.filter_by(status="approved").all())
        if num_approved % config.generation_size == 0:
            current_generation = participant.nodes()[0].generation
            nodes = BanditAgent.query.filter_by(generation=current_generation, failed=False).all()
            for n in nodes:
                n.calculate_payoff()
            for n in nodes:
                n.calculate_fitness()

    def data_check(self, participant):

        # get the necessary data
        networks = Network.query.all()
        nodes = BanditAgent.query.filter_by(participant_id=participant.id).all()
        node_ids = [n.id for n in nodes]
        genes = Gene.query.filter(Gene.origin_id.in_(node_ids)).all()
        incoming_vectors = Vector.query.filter(Vector.destination_id.in_(node_ids)).all()
        outgoing_vectors = Vector.query.filter(Vector.origin_id.in_(node_ids)).all()
        decisions = Decision.query.filter(Decision.origin_id.in_(node_ids)).all()

        try:
            # 1 node per network
            for net in networks:
                assert len([n for n in nodes if n.network_id == net.id]) == 1

            # 1 learning and memory gene per node
            for node in nodes:
                assert len([g for g in genes if g.origin_id == node.id]) == 2
                assert len([g for g in genes if g.origin_id == node.id and g.type == "memory_gene"]) == 1
                assert len([g for g in genes if g.origin_id == node.id and g.type == "learning_gene"]) == 1

            # 1 vector (incoming) per node
            for node in nodes:
                assert len([v for v in outgoing_vectors if v.origin_id == node.id]) == 0
                assert len([v for v in incoming_vectors if v.destination_id == node.id]) == 1

            # correct numbers of decisions per node
            for node in nodes:
                assert (len([d for d in decisions if d.origin_id == node.id])) == config.rounds*config.trials_per_round

            # 0 <= checks <= learning, per round
            for node in nodes:
                my_checks = [d for d in decisions if d.contents == "check" and d.origin_id == node.id]
                learning = int([g for g in genes if g.origin_id == node.id and g.type == "learning_gene"][0].contents)
                for r in range(config.rounds):
                    assert len([c for c in my_checks if json.loads(c.property1)['round'] == r + 1]) <= learning

            # all decisions have an int payoff
            for d in decisions:
                if d.contents == "check":
                    assert json.loads(d.property1)['payoff'] == 0
                else:
                    assert isinstance(int(json.loads(d.property1)['payoff']), int)

            self.log("Data check passed")
            return True
        except:
            import traceback
            traceback.print_exc()
            return False

    def bonus(self, participant):

        # query all nodes, bandits, pulls and Genes
        nodes = BanditAgent.query.filter_by(participant_id=participant.id).all()
        node_ids = [n.id for n in nodes]
        decisions = Decision.query.filter(Decision.origin_id.in_(node_ids)).all()
        total_payoff = sum([json.loads(d.property1)['payoff'] for d in decisions])

        max_bonus_payoff = 10*config.trials_per_round*config.rounds
        min_bonus_payoff = 4*config.trials_per_round*config.rounds

        bonus = round(
            max(
                min(
                    (total_payoff-min_bonus_payoff)/(1.0*(max_bonus_payoff-min_bonus_payoff)),
                    1.00
                ),
                0.00
            ),
            2
        )
        return bonus


class BanditGenerational(DiscreteGenerational):

    __mapper_args__ = {"polymorphic_identity": "bandit_generational"}

    def add_node(self, node):
        super(BanditGenerational, self).add_node(node=node)
        node.receive()


class GeneticSource(Source):
    """ A source that initializes the genes of the first generation """

    __mapper_args__ = {"polymorphic_identity": "genetic_source"}

    def _what(self):
        return Gene

    def create_genes(self):
        if config.allow_memory:
            MemoryGene(origin=self, contents=config.seed_memory)
        else:
            MemoryGene(origin=self, contents=0)

        if config.allow_learning:
            LearningGene(origin=self, contents=config.seed_learning)
        else:
            LearningGene(origin=self, contents=0)


class MemoryGene(Gene):
    """ A gene that controls the time span of your memory """

    __mapper_args__ = {"polymorphic_identity": "memory_gene"}

    def _mutated_contents(self):
        if config.allow_memory:
            if random.random() < 0.5:
                return max([int(self.contents) + random.sample([-1, 1], 1)[0], 1])
            else:
                return self.contents
        else:
            return 0


class LearningGene(Gene):
    """ A gene that controls your learning capacity """

    __mapper_args__ = {"polymorphic_identity": "learning_gene"}

    def _mutated_contents(self):
        if config.allow_learning:
            if random.random() < 0.5:
                return max([int(self.contents) + random.sample([-1, 1], 1)[0], 1])
            else:
                return self.contents
        else:
            return 0


class Decision(Info):
    """ An info representing a decision made by a participant. """

    __mapper_args__ = {"polymorphic_identity": "decision"}


class BanditAgent(Agent):

    __mapper_args__ = {"polymorphic_identity": "bandit_agent"}

    @hybrid_property
    def generation(self):
        return int(self.property2)

    @generation.setter
    def generation(self, generation):
        self.property2 = repr(generation)

    @generation.expression
    def generation(self):
        return cast(self.property2, Integer)

    @hybrid_property
    def payoff(self):
        return int(self.property3)

    @payoff.setter
    def payoff(self, payoff):
        self.property3 = repr(payoff)

    @payoff.expression
    def payoff(self):
        return cast(self.property3, Integer)

    def update(self, infos):
        for info in infos:
            if isinstance(info, Gene):
                self.mutate(info_in=info)

    def calculate_payoff(self):
        decisions = self.infos(type=Decision)
        self.payoff = sum([json.loads(d.property1)['payoff'] for d in decisions])

    def calculate_fitness(self):
        learning = int(self.infos(type=LearningGene)[0].contents)
        memory = int(self.infos(type=MemoryGene)[0].contents)
        score = max(self.payoff - learning*config.learning_cost - memory*config.memory_cost, 0)
        self.fitness = pow(score, 2)

    def _what(self):
        return Gene
