import json

from Python.utils.constant import (
    DEVICE_LABEL_D,
    MATCH_EXCEPT_DEVICES_L,
    PHYSICAL_CHANNEL_L,
    STATE_VERB_D,
    THETA_DIRECT_F,
    THETA_IMPLICIT_F,
    VALUE_DIFFERENT_DEVICES_L,
    VALUE_NORMALIZE_D,
    VALUE_WHATEVER_DEVICES_L,
)
from Python.utils.enum import (
    ChainEnum,
    ConnEnum,
    MethodTypeEnum,
    TcaEnum,
    ThreatTypeEnum,
)


class InputClass:
    """
    Inputs include name, type, title and section
    """

    def __init__(self, name_s: str, type_s: str, device_s: str):
        """
        Initialize name, type, title, section from the raw input


        Args:
            name_s (str): the name of the input

        """
        self.name: str = name_s
        self.type: str = type_s
        self.device: str = device_s


class MethodCallClass:
    """
    The detail of a Method Call node, include receiver, method, and arguments
    """

    def __init__(
        self,
        text_s: str,
        device_s: str,
        receiver_s: str,
        name_s: str,
        arguments_l: list,
        type_u: MethodTypeEnum,
    ):
        """
        Initialize the method call class


        Args:
            text_s (str):
            receiver_s (str):
            name_s (str):
            arguments_l (list):


        """
        self.text: str = text_s
        self.device: str = device_s
        self.receiver: str = receiver_s
        self.name: str = name_s
        self.arguments: list = arguments_l
        self.type: MethodTypeEnum = type_u


class ConnectionClass:
    """
    Docstring for ConnectionClass.
    """

    def __init__(
        self, next_tca_u, prev_tca_u, latter_rule_u, prior_rule_u, conn_m, chain_m
    ):
        """
        : to be defined.
        prev -> next
        prior -> latter

        next <- prev
        latter <- prior


        Args:
            action_u ():
            trigger_or_condition_u ():
            conn_type_s (str):


        """
        self.next = next_tca_u
        self.prev = prev_tca_u
        self.latter = latter_rule_u
        self.prior = prior_rule_u
        self.conn = conn_m
        self.chain = chain_m
        self.update_chain_connects()

    def update_chain_connects(self):
        self.next.chain_connects.add((self.prev, self.conn, self.chain))

    def __repr__(self):
        return f"({self.next.device}, {self.prev.device}, {self.latter.appname}, {self.prior.appname}, {str(self.conn)}, {str(self.chain)}"

    def __str__(self):
        return repr(self)

    def __unicode__(self):
        return repr(self)


class TcaClass:
    """
    Docstring for TriggerConditionActionClass.
    """

    def __init__(
        self,
        device_s: str,
        attribute_s: str,
        operator_s: str,
        value_s: str,
        arguments_l: list,
        type_u: TcaEnum,
        appname_s: str,
    ):
        """
        : to be defined.
        """

        # self.varname = ""
        self.device = device_s
        self.attribute = attribute_s
        self.operator = operator_s
        self.value = value_s
        self.arguments = ", ".join(arguments_l)
        self.type = type_u
        self.execution = {}
        self.inference = {}
        self.appname = appname_s
        self.threat = self.get_threat_type()
        self.rule_connects = set()
        self.chain_connects = set()

    def get_threat_type(self):
        if self.device not in DEVICE_LABEL_D:
            return None
        return DEVICE_LABEL_D[self.device]

    # def matches(self, other_u) -> bool:
    #     device_b: bool = (self.device == other_u.device) and (
    #         self.device not in MATCH_EXCEPT_DEVICES_L
    #     )
    #     value_b: bool = True
    #     if (
    #         (self.value in STATE_VERB_D)
    #         and (other_u.value in STATE_VERB_D)
    #         and (self.value != other_u.value)
    #     ):
    #         value_b = False
    #     return device_b and value_b

    # def influences(self, other_u) -> bool:
    #     if (other_u.device, self.device) not in PHYSICAL_CHANNEL_L:
    #         return False

    #     if (other_u.value, self.operator) == ("on", "<"):
    #         return False

    #     if (other_u.value, self.value) == ("on", "inactive"):
    #         return False

    #     if (other_u.value, self.operator) == ("off", ">"):
    #         return False

    #     if (other_u.value, self.value) == ("off", "active"):
    #         return False

    def matches(self, other_u) -> bool:
        normalized_values_l = ["on", "off"]
        device_b: bool = (self.device == other_u.device) and (
            self.device not in MATCH_EXCEPT_DEVICES_L
        )
        value_b: bool = True
        other_value_s = VALUE_NORMALIZE_D.get(other_u.value, other_u.value)
        value_s = VALUE_NORMALIZE_D.get(self.value, self.value)
        if (
            (other_value_s in normalized_values_l)
            and (value_s in normalized_values_l)
            and (other_value_s != value_s)
        ):
            value_b = False
        return device_b and value_b

    def influences(self, other_u) -> bool:
        normalized_values_l = ["on", "off"]
        if (other_u.device, self.device) not in PHYSICAL_CHANNEL_L:
            return False

        other_value_s = VALUE_NORMALIZE_D.get(other_u.value, other_u.value)
        value_s = VALUE_NORMALIZE_D.get(self.operator, "")
        if self.device in ["water", "presence", "motion"]:
            value_s = VALUE_NORMALIZE_D.get(self.value, self.value)
        if (other_value_s not in normalized_values_l) or (
            value_s not in normalized_values_l
        ):
            return True
        if (other_u.device, self.device) in VALUE_WHATEVER_DEVICES_L:
            return True
        if (other_u.device, self.device) in VALUE_DIFFERENT_DEVICES_L:
            return other_value_s != value_s
        return other_value_s == value_s

    def get_connection(self, other):
        """self -> other"""
        conn_m = None

        if self.matches(other):
            conn_m = ConnEnum.MATCH
        elif self.influences(other):
            conn_m = ConnEnum.INFLUENCE

        return conn_m

    def set_execution(self, action_tca_u, probability_f: float):
        self.execution[action_tca_u] = self.get_execution(action_tca_u) + probability_f

    def get_execution(self, action_tca_u):
        return self.execution.get(action_tca_u, 0)

    def set_inference(self, sink_tca_u, action_tca_u, probability_f: float):

        self.inference[sink_tca_u] = (
            self.get_inference(sink_tca_u)
            + self.get_execution(action_tca_u) * probability_f
        )

    def get_inference(self, sink_tca_u):
        return self.inference.get(sink_tca_u, 0)

    def get_repr(self):
        repr_s = f"{self.device}"
        if self.operator != "==":
            repr_s += f"{self.operator}"
        else:
            repr_s += f"."
        if self.value != "":
            repr_s += f"{self.value}"
        return repr_s

    def __repr__(self):
        repr_s = f"{self.device}.{self.value}({self.arguments})"
        if self.operator != "==":
            repr_s = f"{self.device}{self.operator}{self.value}({self.arguments})"
        # repr_s += self.convert_dict(self.execution)
        repr_s += self.convert_dict(self.inference)
        repr_s += str(self.type.value)
        return repr_s

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        if self.appname != other.appname:
            return False
        if (self.type in [TcaEnum.SINK_MSG, TcaEnum.SINK_HTTP, TcaEnum.SINK_API]) and (
            other.type in [TcaEnum.SINK_MSG, TcaEnum.SINK_HTTP, TcaEnum.SINK_API]
        ):
            return True
        if self.type != other.type:
            return False
        return hash(self) == hash(other)

    def __lt__(self, other):
        if self.appname != other.appname:
            return self.appname < other.appname

        if (self.type in [TcaEnum.SINK_MSG, TcaEnum.SINK_HTTP, TcaEnum.SINK_API]) and (
            other.type in [TcaEnum.SINK_MSG, TcaEnum.SINK_HTTP, TcaEnum.SINK_API]
        ):
            return len(self.value + self.arguments) < len(other.value + other.arguments)

        if self.type != other.type:
            return self.type < other.type

        return (
            self.device + self.attribute + self.operator + self.value + self.arguments
        ) < (
            other.device
            + other.attribute
            + other.operator
            + other.value
            + other.arguments
        )

    def __le__(self, other) -> bool:
        return self < other or self == other

    def __hash__(self):
        hash_obj = hash(
            (
                self.device,
                self.attribute,
                self.operator,
                self.value,
                self.type,
                self.arguments,
                self.appname,
            )
        )
        # if self.type in [TcaEnum.SINK_MSG, TcaEnum.SINK_HTTP, TcaEnum.SINK_API]:
        #     hash_obj = hash((self.device,))
        return hash_obj

    def convert_dict(self, prob_d: dict):
        prod_dict_d = {}
        for action_u, prob_f in prob_d.items():
            repr_s = f"{action_u.device}.{action_u.value}({action_u.arguments})"
            if action_u.operator != "==":
                repr_s = f"{action_u.device}{action_u.operator}{action_u.value}({action_u.arguments})"
            prod_dict_d[repr_s] = prob_f
        return json.dumps(prod_dict_d)


class RuleClass:
    """
    Docstring for RuleClass.
    """

    def __init__(
        self,
        trigger_u,
        conditions_l,
        action_u: TcaClass,
        appname_s: str,
    ):
        """
        : to be defined.


        Args:
            trigger_u (TriggerClass):
            conditions_l (list[ConditionClass]):
            action_u (ActionClass):


        """
        self.trigger = trigger_u
        self.conditions = sorted(conditions_l)
        self.action = action_u
        self.execution = {}
        self.inference = {}
        self.appname = appname_s
        self.update_rule_connect()

    def update_rule_connect(self):
        if len(self.conditions) > 0:
            self.action.rule_connects.add(self.conditions[0])
            cond_len_i: int = len(self.conditions)
            for i_i in range(cond_len_i - 1):
                self.conditions[i_i].rule_connects.add(self.conditions[i_i + 1])
            self.conditions[cond_len_i - 1].rule_connects.add(self.trigger)
        else:
            self.action.rule_connects.add(self.trigger)

    def set_execution(self, action_tca_u, probability_f: float):
        self.trigger.set_execution(action_tca_u, probability_f)
        for condition_u in self.conditions:
            condition_u.set_execution(action_tca_u, probability_f)
        self.action.set_execution(action_tca_u, probability_f)

    def get_execution(self, action_u):
        execution_d: dict = {}
        execution_d[self.trigger.get_repr()] = execution_d.get(
            self.trigger.get_repr(), 0
        ) + self.trigger.get_execution(action_u)
        for condition_u in self.conditions:
            execution_d[condition_u.get_repr()] = execution_d.get(
                condition_u.get_repr(), 0
            ) + condition_u.get_execution(action_u)
        execution_d[self.action.get_repr()] = execution_d.get(
            self.action.get_repr(), 0
        ) + self.action.get_execution(action_u)
        return execution_d

    def __repr__(self):
        trigger_s = "Trigger: " + repr(self.trigger)
        conditions_l = [repr(condition_u) for condition_u in self.conditions]
        conditions_s = "[]"
        if len(conditions_l) > 0:
            conditions_s = "[Conditions: " + ", ".join(conditions_l) + "]"
        action_s = "Action: " + repr(self.action)

        return f"{self.appname} ## {trigger_s} -> {conditions_s} -> {action_s}"

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        return (
            self.trigger == other.trigger
            and self.conditions == other.conditions
            and self.action == other.action
        )

    def __lt__(self, other):
        if self.action == other.action:
            if self.trigger < other.trigger:
                return True
            elif self.trigger == other.trigger:
                return self.conditions < other.conditions
            elif self.trigger > other.trigger:
                return False
        return self.action < other.action

    def __le__(self, other) -> bool:
        return self < other or self == other

    def __hash__(self):
        hash_l = []
        hash_l.append(hash(self.trigger))
        for condition_u in self.conditions:
            hash_l.append(hash(condition_u))
        hash_l.append(hash(self.action))
        return hash(tuple(hash_l))


class RuleMergeClass:
    def __init__(self, action_u: TcaClass, rules_l) -> None:
        self.action = action_u
        self.rules = sorted(rules_l)
        self.conditions = self.get_conditions()
        self.triggers = self.get_triggers()
        self.connections = {}
        self.appname = action_u.appname

    def get_conditions(self):
        conditions_e = set()
        for rule_u in self.rules:
            for condition_u in rule_u.conditions:
                conditions_e.add(condition_u)
        return sorted(conditions_e)

    def get_triggers(self):
        triggers_e = set()
        for rule_u in self.rules:
            triggers_e.add(rule_u.trigger)
        return sorted(triggers_e)

    def activates(self, other_u):
        """
        other_u -> self

        Trigger another Trigger-Condition-Action class

        Args:
            other_tca_u (RuleClass):

        Returns:


        """
        connections_l: list = []

        chain_m = ChainEnum.ACTIVATE
        action_u: TcaClass = other_u.action
        for trigger_u in self.triggers:
            conn_m = trigger_u.get_connection(action_u)
            if conn_m is not None:
                conn_u = ConnectionClass(
                    trigger_u, action_u, self, other_u, conn_m, chain_m
                )
                connections_l.append(conn_u)
        return connections_l

    def enables(self, other_u):
        """
        Enable another Trigger-Condition-Action class

        Args:
            other_tca_u (TcaClass):

        Returns:


        """
        connections_l: list = []

        chain_m = ChainEnum.ENABLE
        action_u: TcaClass = other_u.action
        for condition_u in self.conditions:
            conn_m = condition_u.get_connection(action_u)
            if conn_m is not None:
                conn_u = ConnectionClass(
                    condition_u, action_u, self, other_u, conn_m, chain_m
                )
                connections_l.append(conn_u)
        return connections_l

    def update_connections(self, other_u):
        """other_u -> self"""

        if other_u.appname == self.appname:
            return

        connections_l: list = []

        activates_l: list = self.activates(other_u)
        enables_l: list = self.enables(other_u)

        connections_l.extend(activates_l)
        connections_l.extend(enables_l)

        if len(connections_l) > 0:
            self.connections[other_u] = connections_l

    def clear_connections(self):
        self.connections = {}
        for trigger_u in self.triggers:
            trigger_u.inference = {}
            trigger_u.chain_connects = set()

        for condition_u in self.conditions:
            condition_u.inference = {}
            condition_u.chain_connects = set()
        self.action.inference = {}
        self.action.chain_connects = set()

    def set_execution(self, action_tca_u, probability_f: float):
        for rule_u in self.rules:
            rule_u.set_execution(action_tca_u, probability_f)

    def set_inference(self, sink_tca_u, probability_f: float):
        for trigger_u in self.triggers:
            trigger_u.set_inference(sink_tca_u, self.action, probability_f)
        for condition_u in self.conditions:
            condition_u.set_inference(sink_tca_u, self.action, probability_f)
        self.action.set_inference(sink_tca_u, self.action, probability_f)

    def __repr__(self):
        retval_s = ""
        for rule_u in self.rules:
            retval_s += repr(rule_u) + "\n"
        return retval_s

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        return self.rules == other.rules

    def __lt__(self, other):
        return self.rules < other.rules

    def __le__(self, other) -> bool:
        return self < other or self == other

    def __hash__(self):
        hash_l = []
        for rule_u in self.rules:
            hash_l.append(hash(rule_u))
        return hash(tuple(hash_l))


class ChainClass:
    def __init__(self, rule_merge_ul) -> None:
        self.rules = rule_merge_ul
        self.appnames = self.get_appnames()
        self.sink = self.rules[0].action
        self.length = len(self.rules)
        self.triggers, self.conditions, self.actions = [[], []], [[], []], [[], []]
        for i_i in range(2):
            self.triggers[i_i], self.conditions[i_i], self.actions[i_i] = self.get_tcas(
                i_i
            )

    def get_appnames(self):
        return [rule_u.appname for rule_u in self.rules]

    def get_tcas(self, index=0):
        triggers_e, conditions_e, actions_e = set(), set(), set()
        for i_i in range(index, self.length):
            rule_merge_u = self.rules[i_i]
            triggers_e.update(rule_merge_u.triggers)
            conditions_e.update(rule_merge_u.conditions)
            actions_e.add(rule_merge_u.action)
        return sorted(triggers_e), sorted(conditions_e), sorted(actions_e)

    def get_risky_count(self, index_i=0):
        risky_direct_i, risky_implicit_i = 0, 0
        devinfer_d: dict = {}
        for tca_l in [self.triggers, self.conditions, self.actions]:
        # for tca_l in [self.triggers, self.conditions]:
            for tca_u in tca_l[index_i]:
                if tca_u.threat is None:
                    continue
                device_s = tca_u.device
                if device_s not in DEVICE_LABEL_D:
                    continue
                # devinfer_d[device_s] = max(
                #     devinfer_d.get(device_s, 0), tca_u.get_inference(self.sink)
                # )
                devinfer_d[device_s] = devinfer_d.get(
                    device_s, 0
                ) + tca_u.get_inference(self.sink)

                if devinfer_d[device_s] >= THETA_DIRECT_F:
                    risky_direct_i = 1
                elif (
                    devinfer_d[device_s] > THETA_IMPLICIT_F
                    and devinfer_d[device_s] < THETA_DIRECT_F
                ):
                    risky_implicit_i = 1
        risky_both_i = risky_direct_i + risky_implicit_i
        return risky_direct_i, risky_implicit_i, risky_both_i

    def set_inference(self, sink_tca_u: TcaClass, probability_f: float):

        self.rules[0].set_inference(sink_tca_u, probability_f)
        for i_i in range(self.length - 1):
            latter_u, prior_u = self.rules[i_i], self.rules[i_i + 1]
            connections_l: list = latter_u.connections[prior_u]
            len_conns_i: int = len(connections_l)
            probability_f *= 1 / len_conns_i

            for conn_u in connections_l:
                trigger_condition_u: TcaClass = conn_u.next
                action_u: TcaClass = conn_u.prev
                coefficient_f = trigger_condition_u.execution[latter_u.action]

                prior_u.set_inference(sink_tca_u, coefficient_f * probability_f)

    def __repr__(self):
        retval_s = ""
        for rule_u in self.rules:
            retval_s += repr(rule_u) + "\n"
        return retval_s

    def __str__(self):
        return repr(self)

    def __len__(self):
        return self.length


class ChainListClass:
    def __init__(
        self,
        chains_ul,
    ) -> None:
        self.chains = chains_ul
        self.sink = chains_ul[0].sink
        self.number = len(chains_ul)
        self.update_inference()

        self.triggers, self.conditions, self.actions = [[], []], [[], []], [[], []]
        (
            self.count,
            self.count_risky_direct,
            self.count_risky_implicit,
            self.count_risky_both,
            self.avg_len,
            self.max_len,
        ) = (
            [0, 0],
            [0, 0],
            [0, 0],
            [0, 0],
            [0, 0],
            [0, 0],
        )
        self.single_inference = [{}, {}]
        self.direct_exposure, self.implicit_inference = [{}, {}], [{}, {}]
        self.multiple_candidates = [{}, {}]

        for i_i in range(2):
            self.triggers[i_i], self.conditions[i_i], self.actions[i_i] = self.get_tcas(
                i_i
            )
            (
                self.count[i_i],
                self.count_risky_direct[i_i],
                self.count_risky_implicit[i_i],
                self.count_risky_both[i_i],
                self.avg_len[i_i],
                self.max_len[i_i],
            ) = self.get_count_and_length(i_i)
            self.single_inference[i_i] = self.get_single_inference(i_i)
            (
                self.direct_exposure[i_i],
                self.implicit_inference[i_i],
                self.multiple_candidates[i_i],
            ) = self.split_single_inference(i_i)

    def update_inference(self):
        probability_f = 1 / len(self.chains)
        for chain_u in self.chains:
            chain_u.set_inference(self.sink, probability_f)

    def get_tcas(self, index_i=0):

        triggers_e, conditions_e, actions_e = set(), set(), set()
        for chain_u in self.chains:
            triggers_e.update(chain_u.triggers[index_i])
            conditions_e.update(chain_u.conditions[index_i])
            actions_e.update(chain_u.actions[index_i])

        return sorted(triggers_e), sorted(conditions_e), sorted(actions_e)

    def get_single_inference(self, index_i=0):
        devinfer_d: dict = {}
        for tca_l in [self.triggers, self.conditions, self.actions]:
        # for tca_l in [self.triggers, self.conditions]:
            for tca_u in tca_l[index_i]:
                if tca_u.threat is None:
                    continue
                state_s = tca_u.get_repr()
                device_s = tca_u.device
                if device_s not in DEVICE_LABEL_D:
                    continue
                if state_s not in devinfer_d:
                    devinfer_d[state_s] = SingleInferClass(state_s, device_s, self)
                devinfer_d[state_s].update_inference(tca_u)
        return devinfer_d

    def get_count_and_length(self, index_i=0):
        count_i, count_risky_direct_i, count_risky_implicit_i, count_risky_both_i = (
            0,
            0,
            0,
            0,
        )
        max_len_i, avg_len_i = 0, 0

        for chain_u in self.chains:
            len_each_i = chain_u.length
            if len_each_i > index_i:
                count_i += 1
                tmp_dirct_i, tmp_implicit_i, tmp_both_i = chain_u.get_risky_count(
                    index_i
                )
                count_risky_direct_i += tmp_dirct_i
                count_risky_implicit_i += tmp_implicit_i
                count_risky_both_i += tmp_both_i
                avg_len_i += len_each_i
                max_len_i = max(max_len_i, len_each_i)
        if count_i > 0:
            avg_len_i /= count_i
        return (
            count_i,
            count_risky_direct_i,
            count_risky_implicit_i,
            count_risky_both_i,
            avg_len_i,
            max_len_i,
        )

    def split_single_inference(
        self,
        index_i: int,
    ):
        direct_exposure_d, implicit_inference_d, multiple_candidates_d = {}, {}, {}
        for state_s, single_infer_u in self.single_inference[index_i].items():
            if single_infer_u.threat is None:
                multiple_candidates_d[state_s] = single_infer_u
            elif single_infer_u.threat == ThreatTypeEnum.DIRECT:
                direct_exposure_d[state_s] = single_infer_u
            elif single_infer_u.threat == ThreatTypeEnum.IMPLICIT:
                implicit_inference_d[state_s] = single_infer_u
        return direct_exposure_d, implicit_inference_d, multiple_candidates_d


class SingleInferClass:
    def __init__(
        self,
        state_s: str,
        device_s: str,
        chainlist_u: ChainListClass,
    ) -> None:
        self.state = state_s
        self.device = device_s
        self.chainlist = chainlist_u
        self.inference = 0
        self.threat = None
        self.privacy = []
        self.tcalist = []
        self.appnames = set()

    def update_inference(self, tca_u: TcaClass):
        prob_f: float = tca_u.get_inference(self.chainlist.sink)
        self.inference += prob_f
        # self.inference = max(prob_f, self.inference)
        self.tcalist.append(tca_u)
        self.appnames.add(tca_u.appname)
        self.update_threat_privacy()

    def update_threat_privacy(self):
        if self.device not in DEVICE_LABEL_D:
            return
        if self.inference >= THETA_DIRECT_F:
            self.threat = ThreatTypeEnum.DIRECT
            self.privacy = DEVICE_LABEL_D[self.device]
        elif self.inference > THETA_IMPLICIT_F:
            self.threat = ThreatTypeEnum.IMPLICIT
            self.privacy = DEVICE_LABEL_D[self.device]


class MultipleInferClass(SingleInferClass):
    def __init__(
        self,
        state_s: str,
    ) -> None:
        super().__init__(state_s, "", [])
        self.product = 1

    def update_inference(self, single_infer_u: SingleInferClass):
        self.device = single_infer_u.device
        # self.inference += single_infer_u.inference
        self.product *= single_infer_u.inference
        self.inference = 1 - self.product
        self.chainlist.append(single_infer_u.chainlist)
        self.tcalist.extend(single_infer_u.tcalist)
        self.appnames.update(single_infer_u.appnames)
        self.update_threat_privacy()

    def update_threat_privacy(self):
        if self.device not in DEVICE_LABEL_D:
            return
        if self.inference > THETA_IMPLICIT_F:
            self.threat = ThreatTypeEnum.MULTIPLE
            self.privacy = DEVICE_LABEL_D[self.device]
