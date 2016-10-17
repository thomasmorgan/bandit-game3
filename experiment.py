""" The Bandit Game! """

from dallinger.experiments import Experiment
from dallinger.nodes import Agent, Source
from dallinger.models import Info, Network, Vector, Participant
from dallinger.networks import DiscreteGenerational
from dallinger.information import Gene
import random
from json import dumps
import json
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import cast
from sqlalchemy import Integer
from flask import Blueprint, Response
from psiturk.psiturk_config import PsiturkConfig
from dallinger import db
config = PsiturkConfig()


class BanditGame(Experiment):

    def __init__(self, session):
        super(BanditGame, self).__init__(session)

        """ Experiment parameters """
        self.task = "The Bandit Game"
        self.verbose = False
        self.experiment_repeats = 1

        self.generation_size = 5
        self.generations = 5

        self.bonus_payment = 0.6
        self.initial_recruitment_size = self.generation_size
        self.known_classes["Decision"] = Decision

        """ Task parameters """
        self.trials_per_round = 1
        self.rounds = 2

        # how many bandits each node visits
        self.n_trials = 4

        # how many bandits there are
        self.n_bandits = 4

        # how many arms each bandit has
        self.n_options = 10

        # how many times you can pull the arms
        self.n_pulls = 10

        # the payoff from getting it right
        self.payoff = 10

        # how much each unit of memory costs fitness
        self.memory_cost = self.n_trials*self.payoff/self.n_options*0.1
        self.learning_cost = self.n_trials*self.payoff/self.n_options*0.1
        self.pull_cost = self.payoff/self.n_options

        # fitness affecting parameters
        self.f_min = 10
        self.f_scale_factor = 0.01
        self.f_power_factor = 2

        # genetic parameters
        self.allow_memory = True
        self.allow_learning = True
        self.seed_memory = 0
        self.seed_learning = 0

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
        return BanditGenerational(generations=self.generations,
                                  generation_size=self.generation_size,
                                  initial_source=True)

    def create_node(self, participant, network):
        """Create a node for a participant."""
        return BanditAgent(network=network, participant=participant)

    def recruit(self):
        """Recruit participants if necessary."""
        num_approved = len(Participant.query.filter_by(status="approved").all())
        if num_approved % self.generation_size == 0 and num_approved != self.generations*self.generation_size:
            self.log("generation finished, recruiting another")
            self.recruiter().recruit_participants(n=self.generation_size)

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

            # n_trials decision per node
            for node in nodes:
                assert (len([d for d in decisions if d.origin_id == node.id and d.check == "false"])) == self.rounds*self.trials_per_round

            # 0 <= checks <= learning, per round
            for node in nodes:
                my_checks = [d for d in decisions if d.contents == "check" and d.origin_id == node.id]
                learning = int([g for g in genes if g.origin_id == node.id and g.type == "learning_gene"][0].contents)
                for r in range(self.rounds):
                    assert len([c for c in my_checks if json.loads(c.property1).round == r + 1]) <= learning

            # all decisions have an int payoff
            for d in decisions:
                if d.contents == "check":
                    assert json.loads(d.property1).payoff == 0
                else:
                    assert isinstance(int(json.loads(d.property1).payoff), int)

            # all nodes have a fitness
            for node in nodes:
                assert isinstance(node.fitness, float)

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

        max_bonus_payoff = 15*self.trials_per_round*self.rounds

        bonus = round(min(total_payoff/(1.0*max_bonus_payoff), 1.00), 2)
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
        exp = BanditGame(db.session)
        if exp.allow_memory:
            MemoryGene(origin=self, contents=exp.seed_memory)
        else:
            MemoryGene(origin=self, contents=0)

        if exp.allow_learning:
            LearningGene(origin=self, contents=exp.seed_learning)
        else:
            LearningGene(origin=self, contents=0)


class MemoryGene(Gene):
    """ A gene that controls the time span of your memory """

    __mapper_args__ = {"polymorphic_identity": "memory_gene"}

    def _mutated_contents(self):
        exp = BanditGame(db.session)
        if exp.allow_memory:
            if random.random() < 0.5:
                return max([int(self.contents) + random.sample([-1, 1], 1)[0], 0])
            else:
                return self.contents
        else:
            return 0


class LearningGene(Gene):
    """ A gene that controls your learning capacity """

    __mapper_args__ = {"polymorphic_identity": "learning_gene"}

    def _mutated_contents(self):
        exp = BanditGame(db.session)
        if exp.allow_learning:
            if random.random() < 0.5:
                return max([int(self.contents) + random.sample([-1, 1], 1)[0], 0])
            else:
                return self.contents
        else:
            return 1


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

    def update(self, infos):
        for info in infos:
            if isinstance(info, Gene):
                self.mutate(info_in=info)

    def calculate_fitness(self):
        exp = BanditGame(db.session)

        my_decisions = Pull.query.filter_by(origin_id=self.id, check="false").all()
        my_checks = Pull.query.filter_by(origin_id=self.id, check="true").all()
        bandits = Bandit.query.filter_by(network_id=self.network_id).all()

        payoff = exp.payoff
        memory = int(self.infos(type=MemoryGene)[0].contents)
        learning = int(self.infos(type=LearningGene)[0].contents)

        correct_decisions = [d for d in my_decisions if [b for b in bandits if b.bandit_id == d.bandit_id][0].good_arm == int(d.contents)]

        fitness = exp.f_min + len(correct_decisions)*payoff - memory*exp.memory_cost - learning*exp.learning_cost - len(my_checks)*exp.pull_cost

        fitness = max([fitness, 0.001])
        fitness = ((1.0*fitness)*exp.f_scale_factor)**exp.f_power_factor
        self.fitness = fitness

    def _what(self):
        return Gene


extra_routes = Blueprint(
    'extra_routes', __name__,
    template_folder='templates',
    static_folder='static')


@extra_routes.route("/node/<int:node_id>/calculate_fitness", methods=["GET"])
def calculate_fitness(node_id):

    exp = BanditGame(db.session)
    node = BanditAgent.query.get(node_id)
    if node is None:
        exp.log("Error: /node/{}/calculate_fitness, node {} does not exist".format(node_id))
        page = exp.error_page(error_type="/node/calculate_fitness, node does not exist")
        js = dumps({"status": "error", "html": page})
        return Response(js, status=400, mimetype='application/json')

    node.calculate_fitness()
    exp.save()

    data = {"status": "success"}
    return Response(dumps(data), status=200, mimetype='application/json')


@extra_routes.route("/num_trials", methods=["GET"])
def get_num_trials():
    exp = BanditGame(db.session)
    data = {"status": "success",
            "experiment_repeats": exp.experiment_repeats,
            "practice_repeats": exp.practice_repeats,
            "n_trials": exp.n_trials}
    return Response(dumps(data), status=200, mimetype='application/json')


@extra_routes.route("/num_bandits", methods=["GET"])
def get_num_bandits():
    exp = BanditGame(db.session)
    data = {"status": "success", "num_bandits": exp.n_bandits}
    return Response(dumps(data), status=200, mimetype='application/json')


@extra_routes.route("/num_arms/<int:network_id>/<int:bandit_id>", methods=["GET"])
def get_num_arms(network_id, bandit_id):
    bandit = Bandit.query.filter_by(network_id=network_id, bandit_id=bandit_id).one()
    data = {"status": "success", "num_arms": bandit.num_arms}
    return Response(dumps(data), status=200, mimetype='application/json')


@extra_routes.route("/good_arm/<int:network_id>/<int:bandit_id>", methods=["GET"])
def good_arm(network_id, bandit_id):
    bandit = Bandit.query.filter_by(network_id=network_id, bandit_id=bandit_id).one()
    data = {"status": "success", "good_arm": bandit.good_arm}
    return Response(dumps(data), status=200, mimetype='application/json')
