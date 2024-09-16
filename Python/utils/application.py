from itertools import product

from Python.utils.component import (
    InputClass,
    MethodCallClass,
    RuleClass,
    RuleMergeClass,
    TcaClass,
)
from Python.utils.constant import (
    SCHEDULE_SM_METHOD_L,
    SMARTTHINGS_REFERENCE_D,
    SUBSCRIBE_SM_METHOD_L,
    RUNONCE_SM_METHOD_L,
    RUNEVERY_SM_METHOD_L,
    SINK_SM_MSG_L,
    SINK_SM_HTTP_L,
    SINK_IF_MSG_L,
    SINK_IF_HTTP_L,
    SINK_IF_API_L,
    SINK_OP_MSG_L,
    SINK_OP_HTTP_L,
    SINK_OP_API_L,
    CAPA_FIX_DEVICE_D,
    CAPA_DEFAULT_DEVICE_D,
    IFTTT_FIX_DEVICE_D,
    IFTTT_DEFAULT_DEVICE_D,
    OPENHAB_FIX_DEVICE_D,
    OPENHAB_ITEM_FIX_DEVICE_D,
    EVENT_OP_METHOD_L,
    NOUN_DEVICE_D,
    VERB_STATE_D,
    VERB_ANTONYMY_D,
    LOGICAL_D,
    OPERATION_D,
    NUM_FAT_DEVICES,
)
from Python.utils.enum import AppTypeEnum, MethodTypeEnum, TcaEnum
from Python.utils.miscellaneous import flatten, split_camel_case
from Python.utils.process import (
    infer_device_state_from_ifttt,
    infer_device_type,
    infer_device_type_from_openhab,
    split_op_binding,
)


class ApplicationClass:
    """
    Store all the information from raw information into the class
    """

    def __init__(self, name_s: str, detail_d: dict, filetype_u: AppTypeEnum):
        """
        Initialize the information from the app name and corresponding values


        Args:
            name_s (str): app name
            detail_d (dict): detail of the app from the raw data

        """
        self.appname: str = name_s
        self.filetype: AppTypeEnum = filetype_u
        self.devsets: set = set()

        self.actuators_rules, self.sinks_rules = [], []
        if self.filetype == AppTypeEnum.SMARTTHINGS:
            self.actuators_rules, self.sinks_rules = self.smartapp_process(detail_d)
        elif self.filetype == AppTypeEnum.IFTTT:
            self.actuators_rules, self.sinks_rules = self.ifttt_process(detail_d)
        elif self.filetype == AppTypeEnum.OPENHAB:
            self.actuators_rules, self.sinks_rules = self.openhab_process(detail_d)

        self.isfat: bool = len(self.devsets) > NUM_FAT_DEVICES
        self.isempty: bool = len(self.devsets) == 0

    def ifttt_process(self, detail_d):
        var4_s: str = detail_d["description"]
        var5_s: str = detail_d["name"]
        triggers_l, actions_l = self.get_if_triggers_actions(detail_d, var4_s, var5_s)
        actuators_rules_l, sinks_rules_l = self.get_if_tca_rules(triggers_l, actions_l)
        return actuators_rules_l, sinks_rules_l

    def get_if_triggers_actions(self, detail_d, var4_s, var5_s):
        triggers_l, actions_l = [], []
        for comp_s in ["triggers", "actions"]:
            for item_d in detail_d[comp_s]:
                if_id_s = item_d["id"]
                var3_s = " ".join(split_camel_case(if_id_s))
                var1_s: str = item_d["name"]
                var2_s: str = item_d["description"]
                capa_slug_s: str = item_d["service_slug"]

                device_s: str = infer_device_type(
                    None,
                    NOUN_DEVICE_D,
                    IFTTT_FIX_DEVICE_D,
                    IFTTT_DEFAULT_DEVICE_D,
                    capa_slug_s,
                    var1_s,
                    var2_s,
                    var3_s,
                    var4_s,
                    var5_s,
                )

                state_s = infer_device_state_from_ifttt(None, VERB_STATE_D, var3_s)
                if state_s == "":
                    state_s = if_id_s

                attribute_s = ""
                operator_s = "=="
                arguments_l = []
                type_s = TcaEnum.TRIGGER

                if comp_s == "triggers":
                    tca_u = TcaClass(
                        device_s,
                        attribute_s,
                        operator_s,
                        state_s,
                        arguments_l,
                        type_s,
                        self.appname,
                    )
                    triggers_l.append(tca_u)
                    self.devsets.add(tca_u.device)
                elif comp_s == "actions":
                    if capa_slug_s in SINK_IF_MSG_L:
                        type_s = TcaEnum.SINK_MSG
                    elif capa_slug_s in SINK_IF_HTTP_L:
                        type_s = TcaEnum.SINK_HTTP
                    elif capa_slug_s in SINK_IF_API_L:
                        type_s = TcaEnum.SINK_API
                    else:
                        type_s = TcaEnum.ACTUATOR
                    tca_u = TcaClass(
                        device_s,
                        attribute_s,
                        operator_s,
                        state_s,
                        arguments_l,
                        type_s,
                        self.appname,
                    )
                    actions_l.append(tca_u)
                    self.devsets.add(tca_u.device)
        return triggers_l, actions_l

    def get_if_tca_rules(self, triggers_l, actions_l):
        actuators_l, sinks_l = [], []
        for action_tca_u in actions_l:
            len_i: int = len(triggers_l)
            if len_i == 0:
                continue
            tca_rules_l: list = []
            for trigger_tca_u in triggers_l:
                rule_u = RuleClass(trigger_tca_u, [], action_tca_u, self.appname)
                tca_rules_l.append(rule_u)
            rule_merge_u: RuleMergeClass = RuleMergeClass(action_tca_u, tca_rules_l)
            rule_merge_u.set_execution(action_tca_u, 1 / len_i)
            if action_tca_u.type == TcaEnum.ACTUATOR:
                actuators_l.append(rule_merge_u)
            else:
                sinks_l.append(rule_merge_u)
        return actuators_l, sinks_l

    def smartapp_process(self, detail_d):
        var4_s: str = detail_d["descriptionStr"]
        var5_s: str = detail_d["filenameStr"]
        inputs_d: dict = self.get_sm_inputs(detail_d["inputMap"], var4_s, var5_s)

        method_call_param_d: dict = detail_d["methodCallParamMap"]
        method_call_ud: dict = self.get_method_call_param(method_call_param_d, inputs_d)

        method_params_d: dict = detail_d["methodParamMap"]
        method_call_method_node_d: dict = detail_d["methodCallMethodNodeMap"]

        adjacent_matrix_d: dict = self.get_method_node_method_calls_adjacent_matrix(
            method_call_method_node_d, method_call_ud
        )

        declare_d: dict = detail_d["declarationMap"]
        binary_d: dict = detail_d["binaryMap"]

        raw_tca_rules_d, conditions_e, actions_e = self.get_all_raw_tca_rules(
            method_call_method_node_d, adjacent_matrix_d, method_call_ud
        )

        # print(conditions_e)

        actions_d = self.convert_all_raw_actions_to_tca_class(actions_e, method_call_ud)

        conditions_d: dict = {}
        conditions_ld: dict = self.convert_all_raw_conditions_to_tca_class(
            conditions_d, conditions_e, inputs_d, declare_d, binary_d
        )

        triggers_d = {}
        actuators_rules_l, sinks_rules_l = self.get_sm_tca_rules(
            raw_tca_rules_d, triggers_d, conditions_ld, actions_d, method_call_ud
        )

        # print(actions_d)
        # print(conditions_d)
        # print(triggers_d)

        # print("Actuators:")
        # print(actuators_rules_l)
        # print("\nSinks:")
        # print(sinks_rules_l)
        return actuators_rules_l, sinks_rules_l

    def get_sm_inputs(self, input_d: dict, var4_s: str, var5_s: str) -> dict:
        """
        Get the raw input into input classes, infer the devices here

        Args:
            input_d (dict):

        Returns:


        """
        inputs_d: dict = {}

        for varname_s, texts_l in input_d.items():
            var3_s: str = varname_s
            if any(
                [
                    texts_l[0].lower().startswith(prefix_s)
                    for prefix_s in ["capability.", "device."]
                ]
            ):
                capa_slug_s: str = texts_l[0]
                var1_s: str = texts_l[1]
                var2_s: str = texts_l[2]
                device_s: str = infer_device_type(
                    None,
                    NOUN_DEVICE_D,
                    CAPA_FIX_DEVICE_D,
                    CAPA_DEFAULT_DEVICE_D,
                    capa_slug_s,
                    var1_s,
                    var2_s,
                    var3_s,
                    var4_s,
                    var5_s,
                )

                inputs_d[varname_s] = InputClass(varname_s, capa_slug_s, device_s)
        return inputs_d

    def get_method_call_param(
        self, method_call_param_raw_d: dict, inputs_d: dict
    ) -> dict:
        """
        Get the raw method call param into method call classes

        Args:
            method_call_param_raw_d (dict):

        Returns:


        """
        method_call_params_d: dict = {}
        for text_s, details_l in method_call_param_raw_d.items():
            device_s = ""
            receiver_s: str = details_l[0]
            name_s: str = details_l[1]
            arguments_l: list = details_l[2]

            type_u: MethodTypeEnum = MethodTypeEnum.OTHERS
            if receiver_s == "this":
                if name_s in SUBSCRIBE_SM_METHOD_L:
                    if len(arguments_l) == 0:
                        continue
                    device_s = arguments_l[0]
                    if device_s not in ["app", "location"]:
                        input_u = inputs_d.get(device_s, None)
                        if input_u is not None:
                            device_s = input_u.device + "|" + arguments_l[1]
                    type_u = MethodTypeEnum.SUBSCRIBE
                elif name_s in SCHEDULE_SM_METHOD_L:
                    device_s = "time"
                    type_u = MethodTypeEnum.SCHEDULE
                elif any(
                    [
                        (name_s in methods_l)
                        for methods_l in [RUNONCE_SM_METHOD_L, RUNEVERY_SM_METHOD_L]
                    ]
                ):
                    device_s = "time"
                    type_u = MethodTypeEnum.RUN
                elif name_s in SINK_SM_MSG_L:
                    device_s = "sink"
                    type_u = MethodTypeEnum.SINK_MSG
                elif name_s in SINK_SM_HTTP_L:
                    device_s = "sink"
                    type_u = MethodTypeEnum.SINK_HTTP
            elif receiver_s in inputs_d:
                capa_detail_d: dict = SMARTTHINGS_REFERENCE_D.get(
                    inputs_d[receiver_s].type, None
                )
                if (capa_detail_d is None) or (name_s in capa_detail_d["commands"]):
                    device_s = inputs_d[receiver_s].device
                    type_u = MethodTypeEnum.ACTUATOR
            elif receiver_s in ["location"]:
                device_s = "location"
                type_u = MethodTypeEnum.ACTUATOR

            method_call_params_d[text_s] = MethodCallClass(
                text_s, device_s, receiver_s, name_s, arguments_l, type_u
            )
        return method_call_params_d

    def get_method_node_method_calls_adjacent_matrix(
        self, method_call_method_node_d: dict, method_call_ud: dict
    ):
        adjacent_matrix_d: dict = {}
        method_call_used_l, method_node_used_l = (
            self.get_method_calls_method_nodes_used(method_call_method_node_d)
        )
        for method_node_s in method_node_used_l:
            method_calls_e: set = self.get_method_calls_invoke_method_node(
                method_call_ud, method_node_s
            )
            # adjacent_matrix_d[method_node_s] = method_calls_e

            for method_call_s in method_call_method_node_d:
                method_call_u = method_call_ud.get(method_call_s, None)
                if method_call_u is None:
                    continue
                if (
                    method_call_u.receiver == "this"
                    and method_call_u.name == method_node_s
                ):
                    # adjacent_matrix_d[method_node_s].append(method_call_s)
                    method_calls_e.add(method_call_s)

            adjacent_matrix_d[method_node_s] = sorted(method_calls_e)

            # tmp_l = []
            # for tmp_s in method_calls_e:
            #     if method_node_s in method_call_method_node_d.get(tmp_s, {}):
            #         continue
            #     tmp_l.append(tmp_s)
            # adjacent_matrix_d[method_node_s] = tmp_l

        return adjacent_matrix_d

    def get_method_calls_method_nodes_used(self, method_call_method_node_d: dict):
        method_call_used_l: list = list(set(method_call_method_node_d.keys()))
        method_node_used_e: set = set()
        for method_call_s, method_node_d in method_call_method_node_d.items():
            method_node_used_e.update(method_node_d.keys())
        method_node_used_l = list(method_node_used_e)
        return method_call_used_l, method_node_used_l

    def get_method_calls_invoke_method_node(
        self, method_call_ud: dict, method_node_s: str
    ) -> list:
        """
        Get all method calls which invoke the specific method nodes g. this.{method_s} or this.runIn(arg, method_s)

        Args:
            method_s (str):

        Returns:


        """
        method_calls_e: set = set()

        for text_s, method_call_u in method_call_ud.items():
            arguments_l: list = flatten(method_call_u.arguments)
            if method_node_s in arguments_l:
                if method_call_u.name == "unschedule":
                    continue
                method_calls_e.add(text_s)
        return method_calls_e

    def get_all_raw_tca_rules(
        self,
        method_call_method_node_d: dict,
        adjacent_matrix_d: dict,
        method_call_ud: dict,
    ):
        all_raw_tca_rules_d = {}
        all_raw_conditions_e, all_raw_actions_e = set(), set()
        for method_call_text_s, method_call_u in method_call_ud.items():
            if method_call_u.type in [
                MethodTypeEnum.ACTUATOR,
                MethodTypeEnum.SINK_MSG,
                MethodTypeEnum.SINK_HTTP,
                MethodTypeEnum.SINK_API,
            ]:
                # print(method_call_text_s)
                raw_tca_rules_l = self.get_each_method_call_paths(
                    method_call_text_s,
                    method_call_method_node_d,
                    adjacent_matrix_d,
                    method_call_ud,
                )
                raw_rules_l, conditions_t, actions_t = self.handle_raw_tca_rules(
                    raw_tca_rules_l, method_call_method_node_d
                )
                all_raw_tca_rules_d[method_call_text_s] = raw_rules_l
                all_raw_conditions_e.update(conditions_t)
                all_raw_actions_e.update(actions_t)
        return all_raw_tca_rules_d, all_raw_conditions_e, all_raw_actions_e

    def get_each_method_call_paths(
        self,
        method_call_text_s: str,
        method_call_method_node_d: dict,
        adjacent_matrix_d: dict,
        method_call_ud: dict,
    ):
        raw_tca_rules_l, tree_nodes_l, paths_nodes_l = [], [], []
        visited_l = []

        tree_nodes_l.append(method_call_text_s)
        paths_nodes_l.append([method_call_text_s])

        while len(tree_nodes_l) > 0:
            tree_node_s: str = tree_nodes_l.pop()
            path_node_l: list = paths_nodes_l.pop()

            if tree_node_s in visited_l:
                continue
            visited_l.append(tree_node_s)

            method_call_u: MethodCallClass = method_call_ud[tree_node_s]
            if method_call_u.type in [
                MethodTypeEnum.SUBSCRIBE,
                MethodTypeEnum.SCHEDULE,
            ]:
                raw_tca_rules_l.append(path_node_l[:])

                # print(path_node_l)
                continue

            method_node_d = method_call_method_node_d.get(tree_node_s, {})
            for method_node_s in method_node_d:
                adjacent_method_calls_l: list = adjacent_matrix_d[method_node_s]
                for adjacent_method_call_s in adjacent_method_calls_l:
                    # tmp_nodes_l = [method_node_s, adjacent_method_call_s]
                    tmp_nodes_l = [adjacent_method_call_s]
                    if any([(node_s in path_node_l) for node_s in tmp_nodes_l]):
                        continue
                    tmp_path_l = path_node_l[:]
                    tmp_path_l.extend([method_node_s, adjacent_method_call_s])
                    paths_nodes_l.append(tmp_path_l[:])
                    tree_nodes_l.append(adjacent_method_call_s)

        return raw_tca_rules_l

    def handle_raw_tca_rules(
        self, raw_tca_rules_l: list, method_call_method_node_d: dict
    ):
        # same action, different triggers
        conditions_e, actions_e = set(), set()
        raw_rules_l: list = []

        for each_tca_rule_l in raw_tca_rules_l:
            action_s, trigger_s = each_tca_rule_l[0], each_tca_rule_l[-1]
            raw_conditions_l: list = []
            len_rule_i: int = len(each_tca_rule_l)
            for i in range(0, len_rule_i - 1, 2):
                method_call_s, method_node_s = (
                    each_tca_rule_l[i],
                    each_tca_rule_l[i + 1],
                )
                tmp_conditions_l = method_call_method_node_d[method_call_s][
                    method_node_s
                ]
                raw_conditions_l.insert(0, tmp_conditions_l)
            raw_conditions_l = list(product(*raw_conditions_l))
            conditions_l = [flatten(item_t) for item_t in raw_conditions_l]

            for condition_l in conditions_l:
                conditions_e.update(condition_l)
                actions_e.add(action_s)
                raw_rules_l.append([trigger_s, condition_l, action_s])

        return raw_rules_l, conditions_e, actions_e

    def convert_all_raw_actions_to_tca_class(
        self, all_raw_actions_e: set, method_call_ud: dict
    ):
        all_raw_actions_d: dict = {}
        for raw_action_s in all_raw_actions_e:
            action_u: TcaClass = self.convert_each_raw_action_to_tca_class(
                raw_action_s, method_call_ud
            )
            all_raw_actions_d[raw_action_s] = action_u
        return all_raw_actions_d

    def convert_each_raw_action_to_tca_class(
        self, method_call_text_s: str, method_call_ud: dict
    ):
        method_call_u = method_call_ud[method_call_text_s]
        method_type_s = method_call_u.type

        device_s = method_call_u.device
        attribute_s = ""
        operator_s = "=="
        value_s = VERB_STATE_D.get(method_call_u.name, method_call_u.name)
        arguments_l = method_call_u.arguments
        type_s = TcaEnum.ACTUATOR

        if method_type_s == MethodTypeEnum.SINK_HTTP:
            type_s = TcaEnum.SINK_HTTP
        elif method_type_s == MethodTypeEnum.SINK_MSG:
            type_s = TcaEnum.SINK_MSG
        elif method_type_s == MethodTypeEnum.SINK_API:
            type_s = TcaEnum.SINK_API
        return TcaClass(
            device_s,
            attribute_s,
            operator_s,
            value_s,
            arguments_l,
            type_s,
            self.appname,
        )

    def convert_all_raw_conditions_to_tca_class(
        self,
        conditions_d: dict,
        all_raw_condition_e: set,
        inputs_d: dict,
        declare_d: dict,
        binary_d: dict,
    ):
        all_conditions_d: dict = {}
        for raw_condition_s in all_raw_condition_e:
            # print(raw_condition_s)
            conditions_tca_l: list = self.convert_each_raw_condition_to_tca_class(
                conditions_d, raw_condition_s, inputs_d, declare_d, binary_d
            )
            if len(conditions_tca_l) > 0:
                all_conditions_d[raw_condition_s] = conditions_tca_l
        return all_conditions_d

    def convert_each_raw_condition_to_tca_class(
        self,
        conditions_d: dict,
        raw_condition_s: str,
        inputs_d: dict,
        declare_d: dict,
        binary_d: dict,
    ):
        binaries_l = []
        stack_l = [raw_condition_s]
        visited_l = []
        while len(stack_l) > 0:

            expression_s = stack_l.pop()

            if (len(expression_s) == 0) or (expression_s in visited_l):
                continue
            visited_l.append(expression_s)

            reverse_s = ""
            if expression_s[0] in ["#", "!"]:
                reverse_s = "!"
                expression_s = expression_s[1:]

            if any([(sym_s in expression_s) for sym_s in LOGICAL_D]):
                if expression_s in binary_d:
                    split_l = binary_d[expression_s]

                    stack_l.append(
                        self.convert_boolean_expressions(reverse_s, split_l[0])
                    )
                    stack_l.append(
                        self.convert_boolean_expressions(reverse_s, split_l[2])
                    )
            elif any([(sym_s in expression_s) for sym_s in OPERATION_D]):
                if any([(varname_s in expression_s) for varname_s in inputs_d]):
                    binaries_l.append(
                        self.convert_boolean_expressions(reverse_s, expression_s)
                    )
                if any(
                    [(varname_s in expression_s) for varname_s in ["location", "evt"]]
                ):
                    binaries_l.append(
                        self.convert_boolean_expressions(reverse_s, expression_s)
                    )
            elif expression_s in declare_d:
                stack_l.append(
                    self.convert_boolean_expressions(reverse_s, declare_d[expression_s])
                )
            elif (
                (len(expression_s) > 0)
                and ("!" == expression_s[0])
                and (expression_s[1:] in declare_d)
            ):
                stack_l.append(
                    self.convert_boolean_expressions(
                        reverse_s, expression_s[0] + declare_d[expression_s[1:]]
                    )
                )

        conditions_tca_e: set = set()
        for binary_s in binaries_l:
            tmp_tca_u: TcaClass = self.convert_binary_expression_to_tca_class(
                conditions_d, binary_s, inputs_d, binary_d
            )
            if (tmp_tca_u is not None) and (tmp_tca_u.device != ""):
                conditions_tca_e.add(tmp_tca_u)
        return list(conditions_tca_e)

    def convert_boolean_expressions(self, reverse_s: str, expression_s: str):
        if len(expression_s) > 0 and reverse_s == expression_s[0]:
            expression_s = expression_s[1:]
        else:
            expression_s = reverse_s + expression_s
        return expression_s

    def convert_binary_expression_to_tca_class(
        self, conditions_d: dict, binary_s: str, inputs_d: dict, binary_d: dict
    ):
        reverse_b = False
        if binary_s[0] == "!":
            reverse_b = True
            binary_s = binary_s[1:]

        if binary_s not in binary_d:
            return None

        binary_l: list = binary_d[binary_s][:]
        if reverse_b:
            if binary_l[1] in ["==", "=~"]:
                binary_l[1] = "=="
                binary_l[2] = VERB_ANTONYMY_D.get(binary_l[2], binary_l[2])
            elif binary_l[1] in OPERATION_D:
                binary_l[1] = OPERATION_D.get(binary_l[1], binary_l[1])
        else:
            if binary_l[1] == "!=":
                binary_l[1] = "=="
                binary_l[2] = VERB_ANTONYMY_D.get(binary_l[2], binary_l[2])

        left_s, operator_s, value_s = binary_l
        value_s = VERB_STATE_D.get(value_s, value_s)
        arguments_l = []

        varname_s = ""
        if "." in left_s:
            varname_s = left_s[: left_s.index(".")]

        device_s = varname_s
        if varname_s in inputs_d:
            device_s = inputs_d[device_s].device

        condition_t: tuple = (
            device_s,
            "",
            operator_s,
            value_s,
        )
        condition_u = conditions_d.get(condition_t, None)
        if condition_u is None:
            condition_u = TcaClass(
                *condition_t, arguments_l, TcaEnum.CONDITION, self.appname
            )
            conditions_d[condition_t] = condition_u
        return condition_u

    def get_sm_tca_rules(
        self,
        raw_tca_rules_d: dict,
        triggers_d: dict,
        conditions_ld: dict,
        actions_d: dict,
        method_call_ud: dict,
    ):
        all_tmp_actuator_rules_d, all_tmp_sink_rules_d = {}, {}
        for method_call_text_s, raw_tca_rules_l in raw_tca_rules_d.items():
            for raw_rule_l in raw_tca_rules_l:
                rule_u: RuleClass = self.convert_each_raw_rule_to_tca_class(
                    raw_rule_l, triggers_d, conditions_ld, actions_d, method_call_ud
                )

                if rule_u.action.type == TcaEnum.ACTUATOR:
                    all_tmp_actuator_rules_d[rule_u.action] = (
                        all_tmp_actuator_rules_d.get(rule_u.action, [])
                    )
                    all_tmp_actuator_rules_d[rule_u.action].append(rule_u)
                elif rule_u.action.type in [
                    TcaEnum.SINK_MSG,
                    TcaEnum.SINK_HTTP,
                    TcaEnum.SINK_API,
                ]:
                    all_tmp_sink_rules_d[rule_u.action] = all_tmp_sink_rules_d.get(
                        rule_u.action, []
                    )
                    all_tmp_sink_rules_d[rule_u.action].append(rule_u)
        all_actuator_rules_l = self.remove_duplicate_rules(all_tmp_actuator_rules_d)
        all_sink_rules_l = self.remove_duplicate_rules(all_tmp_sink_rules_d)
        all_sink_rules_l = self.split_closure_sink_rules(all_sink_rules_l)

        return all_actuator_rules_l, all_sink_rules_l

    def split_closure_sink_rules(self, all_sink_rules_l: list):
        rules_merge_l = []
        for rule_merge_u in all_sink_rules_l:
            action_u = rule_merge_u.action
            rules_l = rule_merge_u.rules
            if "$" in action_u.arguments:
                for rule_u in rules_l:
                    tmp_trigger_u = rule_u.trigger
                    tmp_conditions_l = rule_u.conditions
                    tmp_action_u = rule_u.action

                    device_s = tmp_action_u.device
                    attribute_s = tmp_action_u.attribute
                    operator_s = tmp_action_u.operator
                    value_s = tmp_action_u.value
                    arguments_l = tmp_action_u.arguments.split(", ")
                    arguments_l.append(tmp_trigger_u.device)
                    arguments_l.append(tmp_trigger_u.attribute)
                    type_u = tmp_action_u.type
                    appname_s = tmp_action_u.appname

                    new_action_u = TcaClass(
                        device_s,
                        attribute_s,
                        operator_s,
                        value_s,
                        arguments_l,
                        type_u,
                        appname_s,
                    )
                    new_rule_u = RuleClass(
                        tmp_trigger_u, tmp_conditions_l, new_action_u, appname_s
                    )
                    new_rule_u.set_execution(new_action_u, 1)
                    new_rule_merge_u = RuleMergeClass(new_action_u, [new_rule_u])
                    rules_merge_l.append(new_rule_merge_u)
            else:
                rules_merge_l.append(rule_merge_u)

        return rules_merge_l

    def remove_duplicate_rules(self, all_tmp_tca_rules_d: dict):

        clean_tca_rules_l = []
        actions_l: list = sorted(all_tmp_tca_rules_d.keys())
        for action_u in actions_l:
            tmp_tca_rules_l = all_tmp_tca_rules_d[action_u]
            tca_rules_l = self.remove_duplicate_from_each_group_rules(
                action_u, tmp_tca_rules_l
            )
            rule_merge_u: RuleMergeClass = RuleMergeClass(action_u, tca_rules_l)
            if rule_merge_u not in clean_tca_rules_l:
                clean_tca_rules_l.append(rule_merge_u)

        return clean_tca_rules_l

    def remove_duplicate_from_each_group_rules(
        self, action_u: TcaClass, raw_tca_rules_l: list
    ):
        weight_f: float = 1 / len(raw_tca_rules_l)

        tca_rules_l: list = []
        for raw_tca_rule_u in raw_tca_rules_l:
            if raw_tca_rule_u not in tca_rules_l:
                raw_tca_rule_u.set_execution(action_u, weight_f)
                tca_rules_l.append(raw_tca_rule_u)
            else:
                tca_rule_u = tca_rules_l[tca_rules_l.index(raw_tca_rule_u)]
                tca_rule_u.set_execution(action_u, weight_f)
        return tca_rules_l

    def convert_each_raw_rule_to_tca_class(
        self,
        raw_rule_l: list,
        triggers_d: dict,
        conditions_d: dict,
        actions_d: dict,
        method_call_ud: dict,
    ):
        raw_trigger_s, raw_conditions_l, raw_action_s = raw_rule_l

        action_u: TcaClass = actions_d[raw_action_s]
        # action_u.set_execution(action_u, weight_f)

        trigger_method_u: MethodCallClass = method_call_ud[raw_trigger_s]
        trigger_device_s = trigger_method_u.device
        trigger_attribute_s = ""
        trigger_operator_s = "=="
        trigger_value_s = ""
        trigger_arguments_l = []

        if "|" in trigger_device_s:
            trigger_device_l = trigger_device_s.split("|")
            trigger_device_s, trigger_attr_val_s = trigger_device_l
            if "." in trigger_attr_val_s:
                index_i = trigger_attr_val_s.index(".")
                trigger_attribute_s, trigger_value_s = (
                    trigger_attr_val_s[:index_i],
                    trigger_attr_val_s[index_i + 1 :],
                )
            else:
                trigger_attribute_s = trigger_attr_val_s

        conditions_e: set = set()
        for raw_condition_s in raw_conditions_l:
            conditions_tca_l = sorted(conditions_d.get(raw_condition_s, []))
            for condition_tca_u in conditions_tca_l:
                if (
                    condition_tca_u.device == "evt"
                    or condition_tca_u.device == trigger_device_s
                ):
                    trigger_operator_s = condition_tca_u.operator
                    trigger_value_s = condition_tca_u.value
                else:
                    conditions_e.add(condition_tca_u)

        conditions_l = sorted(conditions_e)
        # [condition_u.set_execution(action_u, weight_f) for condition_u in conditions_l]

        trigger_t: tuple = (
            trigger_device_s,
            trigger_attribute_s,
            trigger_operator_s,
            trigger_value_s,
        )

        trigger_u = triggers_d.get(trigger_t, None)
        if trigger_u is None:
            trigger_u = TcaClass(
                *trigger_t, trigger_arguments_l, TcaEnum.TRIGGER, self.appname
            )
            triggers_d[trigger_t] = trigger_u
        # trigger_u.set_execution(action_u, weight_f)

        self.devsets.add(trigger_u.device)
        for condition_u in conditions_l:
            self.devsets.add(condition_u.device)
        self.devsets.add(action_u.device)
        return RuleClass(trigger_u, conditions_l, action_u, self.appname)

    def openhab_process(self, detail_d: dict):
        # fat app
        inputs_d, groups_d = self.get_op_inputs(detail_d["inputMap"])
        # triggers_l: list = detail_d["triggersList"]
        triggers_l: list = self.get_op_raw_triggers(
            detail_d["triggersList"], inputs_d, groups_d
        )

        method_call_param_raw_d: dict = detail_d["methodCallParamMap"]

        method_call_param_d, group_members_method_call_d = self.add_op_method_calls(
            method_call_param_raw_d, groups_d
        )

        method_call_ud: dict = self.get_op_method_call_param(
            method_call_param_d, inputs_d, groups_d
        )

        method_params_d: dict = detail_d["methodParamMap"]
        method_call_method_node_d: dict = detail_d["methodCallMethodNodeMap"]

        adjacent_matrix_d: dict = self.get_method_node_method_calls_adjacent_matrix(
            method_call_method_node_d, method_call_ud
        )

        declare_d: dict = detail_d["declarationMap"]
        binary_d: dict = detail_d["binaryMap"]

        raw_tca_rules_d, conditions_e, actions_e = self.get_op_all_raw_tca_rules(
            method_call_method_node_d,
            adjacent_matrix_d,
            method_call_ud,
            group_members_method_call_d,
        )

        actions_d = self.convert_op_all_raw_actions_to_tca_class(
            actions_e, method_call_ud
        )

        conditions_d: dict = {}
        conditions_ld: dict = self.convert_op_all_raw_conditions_to_tca_class(
            conditions_d, conditions_e, inputs_d, declare_d, binary_d
        )

        triggers_d = {}
        actuators_rules_l, sinks_rules_l = self.get_op_tca_rules(
            raw_tca_rules_d,
            triggers_d,
            conditions_ld,
            actions_d,
            method_call_ud,
            triggers_l,
            inputs_d,
        )
        return actuators_rules_l, sinks_rules_l

    def get_op_inputs(self, input_d: dict) -> dict:
        """
        Get the raw input into input classes, infer the devices here

        Args:
            input_d (dict):

        Returns:


        """
        # itemtype itemname "labeltext [stateformat]" <iconname> (group1, group2, ...) ["tag1", "tag2", ...] {bindingconfig}

        # name_s, [ type_s, label_s, format_s, icon_s, groups_l, tags_l, binding_s, ]

        inputs_d: dict = {}
        group_d: dict = {}

        for varname_s, texts_l in input_d.items():
            type_s, label_s, format_s, icon_s, groups_l, tags_l, binding_s = texts_l

            for group_s in groups_l:
                if group_s not in group_d:
                    group_d[group_s] = set()
                group_d[group_s].add(varname_s)

            item_s = split_op_binding(binding_s)
            device_s: str = infer_device_type_from_openhab(
                None,
                NOUN_DEVICE_D,
                OPENHAB_FIX_DEVICE_D,
                OPENHAB_ITEM_FIX_DEVICE_D,
                icon_s,
                item_s,
                varname_s,
                label_s,
            )
            inputs_d[varname_s] = InputClass(varname_s, icon_s, device_s)
        return inputs_d, group_d

    def get_op_raw_triggers(self, triggers_l, inputs_d, groups_d):
        raw_triggers_l = []
        for tmp_trigger_l in triggers_l:
            trigger_varname_s, trigger_value_s, trigger_type_s = tmp_trigger_l
            if trigger_type_s == "Member":
                trigger_items_l = groups_d[trigger_varname_s]
                for trigger_item_s in trigger_items_l:
                    if trigger_item_s in inputs_d:
                        raw_triggers_l.append([trigger_item_s, trigger_value_s, "Item"])
            # elif trigger_varname_s in inputs_d:
            #     raw_triggers_l.append(tmp_trigger_l)
            else:
                raw_triggers_l.append(tmp_trigger_l)

        return raw_triggers_l

    def add_op_method_calls(self, method_call_param_raw_d: dict, group_d: dict):
        method_call_param_d = {}
        group_members_method_call_d: dict = {}
        for text_s, details_l in method_call_param_raw_d.items():
            receiver_s: str = details_l[0]
            name_s: str = details_l[1]
            arguments_l: list = details_l[2]
            method_call_param_d[text_s] = details_l

            if receiver_s == "this":
                if len(arguments_l) > 0 and (arguments_l[0] in group_d):
                    for item_s in group_d[arguments_l[0]]:
                        new_args_l = arguments_l[:]
                        new_args_l[0] = item_s
                        new_text_s = f"{receiver_s}.{name_s}({', '.join(new_args_l)})"
                        method_call_param_d[new_text_s] = [
                            receiver_s,
                            name_s,
                            new_args_l,
                        ]
                        if text_s not in group_members_method_call_d:
                            group_members_method_call_d[text_s] = []
                        group_members_method_call_d[text_s].append(new_text_s)
            elif receiver_s in group_d:
                for item_s in group_d[receiver_s]:
                    new_text_s = f"{item_s}.{name_s}({', '.join(arguments_l)})"
                    method_call_param_d[new_text_s] = [item_s, name_s, arguments_l]
                    if text_s not in group_members_method_call_d:
                        group_members_method_call_d[text_s] = []
                    group_members_method_call_d[text_s].append(new_text_s)
        return method_call_param_d, group_members_method_call_d

    def get_op_method_call_param(
        self, method_call_param_raw_d: dict, inputs_d: dict, groups_d: dict
    ) -> dict:
        """
        Get the raw method call param into method call classes

        Args:
            method_call_param_raw_d (dict):

        Returns:


        """
        method_call_params_d: dict = {}
        for text_s, details_l in method_call_param_raw_d.items():
            device_s = ""
            receiver_s: str = details_l[0]
            name_s: str = details_l[1]
            arguments_l: list = details_l[2]

            type_u: MethodTypeEnum = MethodTypeEnum.OTHERS

            if name_s in SINK_OP_MSG_L:
                device_s = "sink"
                type_u = MethodTypeEnum.SINK_MSG
            elif name_s in SINK_OP_HTTP_L:
                device_s = "sink"
                type_u = MethodTypeEnum.SINK_HTTP
            elif name_s in SINK_OP_API_L:
                device_s = "sink"
                type_u = MethodTypeEnum.SINK_API
            elif name_s in EVENT_OP_METHOD_L:
                if receiver_s == "this":
                    item_s = arguments_l[0]
                    if item_s in inputs_d:
                        device_s = inputs_d[item_s].device
                        type_u = MethodTypeEnum.ACTUATOR
                elif receiver_s in inputs_d:
                    device_s = inputs_d[receiver_s].device
                    type_u = MethodTypeEnum.ACTUATOR
            method_call_params_d[text_s] = MethodCallClass(
                text_s, device_s, receiver_s, name_s, arguments_l, type_u
            )
        return method_call_params_d

    def get_op_all_raw_tca_rules(
        self,
        method_call_method_node_d: dict,
        adjacent_matrix_d: dict,
        method_call_ud: dict,
        group_members_method_call_d: dict,
    ):
        all_raw_tca_rules_d = {}
        all_raw_conditions_e, all_raw_actions_e = set(), set()
        for method_call_text_s, method_call_u in method_call_ud.items():
            if method_call_u.type in [
                MethodTypeEnum.ACTUATOR,
                MethodTypeEnum.SINK_MSG,
                MethodTypeEnum.SINK_HTTP,
                MethodTypeEnum.SINK_API,
            ]:
                raw_tca_rules_l = self.get_op_each_method_call_paths(
                    method_call_text_s,
                    method_call_method_node_d,
                    adjacent_matrix_d,
                    method_call_ud,
                )
                raw_rules_l, conditions_t, actions_t = self.handle_op_raw_tca_rules(
                    raw_tca_rules_l,
                    method_call_method_node_d,
                    method_call_ud,
                    group_members_method_call_d,
                )
                all_raw_tca_rules_d[method_call_text_s] = raw_rules_l
                all_raw_conditions_e.update(conditions_t)
                all_raw_actions_e.update(actions_t)
        return all_raw_tca_rules_d, all_raw_conditions_e, all_raw_actions_e

    def get_op_each_method_call_paths(
        self,
        method_call_text_s: str,
        method_call_method_node_d: dict,
        adjacent_matrix_d: dict,
        method_call_ud: dict,
    ):
        raw_tca_rules_l, tree_nodes_l, paths_nodes_l = [], [], []
        visited_l = []

        tree_nodes_l.append(method_call_text_s)
        paths_nodes_l.append([method_call_text_s])

        while len(tree_nodes_l) > 0:
            tree_node_s: str = tree_nodes_l.pop()
            path_node_l: list = paths_nodes_l.pop()

            if tree_node_s in visited_l:
                continue
            visited_l.append(tree_node_s)

            method_node_d = method_call_method_node_d.get(tree_node_s, {})
            for method_node_s in method_node_d:
                adjacent_method_calls_l: list = adjacent_matrix_d.get(method_node_s, [])
                if len(adjacent_method_calls_l) == 0:
                    raw_tca_rules_l.append(path_node_l[:])
                for adjacent_method_call_s in adjacent_method_calls_l:
                    tree_nodes_l.append(adjacent_method_call_s)
                    tmp_path_l = path_node_l[:]
                    tmp_path_l.extend([method_node_s, adjacent_method_call_s])
                    paths_nodes_l.append(tmp_path_l[:])

        return raw_tca_rules_l

    def handle_op_raw_tca_rules(
        self,
        raw_tca_rules_l: list,
        method_call_method_node_d: dict,
        method_call_ud: dict,
        group_members_method_call_d: dict,
    ):
        # same action, different triggers
        conditions_e, actions_e = set(), set()
        raw_rules_l: list = []

        for each_tca_rule_l in raw_tca_rules_l:
            action_s = each_tca_rule_l[0]
            raw_conditions_l: list = []
            len_rule_i: int = len(each_tca_rule_l)
            for i in range(0, len_rule_i - 1, 2):
                method_call_s, method_node_s = (
                    each_tca_rule_l[i],
                    each_tca_rule_l[i + 1],
                )
                tmp_conditions_l = method_call_method_node_d[method_call_s][
                    method_node_s
                ]
                raw_conditions_l.insert(0, tmp_conditions_l)
            raw_conditions_l = list(product(*raw_conditions_l))
            conditions_l = [flatten(item_t) for item_t in raw_conditions_l]

            action_l = group_members_method_call_d.get(action_s, [action_s])

            for condition_l in conditions_l:
                for action_s in action_l:
                    conditions_e.update(condition_l)
                    actions_e.add(action_s)
                    raw_rules_l.append([condition_l, action_s])

        return raw_rules_l, conditions_e, actions_e

    def convert_op_all_raw_actions_to_tca_class(
        self, all_raw_actions_e: set, method_call_ud: dict
    ):
        all_raw_actions_d: dict = {}
        for raw_action_s in all_raw_actions_e:
            action_u: TcaClass = self.convert_op_each_raw_action_to_tca_class(
                raw_action_s, method_call_ud
            )
            all_raw_actions_d[raw_action_s] = action_u
        return all_raw_actions_d

    def convert_op_each_raw_action_to_tca_class(
        self, method_call_text_s: str, method_call_ud: dict
    ):
        method_call_u = method_call_ud[method_call_text_s]
        method_type_s = method_call_u.type

        device_s = method_call_u.device
        attribute_s = ""
        operator_s = "=="

        value_s = VERB_STATE_D.get(method_call_u.name, method_call_u.name)

        arguments_l = method_call_u.arguments
        type_s = TcaEnum.ACTUATOR

        if method_type_s == MethodTypeEnum.SINK_HTTP:
            type_s = TcaEnum.SINK_HTTP
        elif method_type_s == MethodTypeEnum.SINK_MSG:
            type_s = TcaEnum.SINK_MSG
        elif method_type_s == MethodTypeEnum.SINK_API:
            type_s = TcaEnum.SINK_API
        elif method_type_s == MethodTypeEnum.ACTUATOR:
            if method_call_u.name in EVENT_OP_METHOD_L:
                if method_call_u.receiver == "this":
                    temp_s = arguments_l[1].strip('"').lower()
                else:
                    temp_s = arguments_l[0].strip('"').lower()
            if temp_s == "0":
                temp_s = "off"
            value_s = VERB_STATE_D.get(temp_s, temp_s)
            type_s = TcaEnum.ACTUATOR

        return TcaClass(
            device_s,
            attribute_s,
            operator_s,
            value_s,
            arguments_l,
            type_s,
            self.appname,
        )

    def convert_op_all_raw_conditions_to_tca_class(
        self,
        conditions_d: dict,
        all_raw_condition_e: set,
        inputs_d: dict,
        declare_d: dict,
        binary_d: dict,
    ):
        all_conditions_d: dict = {}
        for raw_condition_s in all_raw_condition_e:
            conditions_tca_l: list = self.convert_op_each_raw_condition_to_tca_class(
                conditions_d, raw_condition_s, inputs_d, declare_d, binary_d
            )
            if len(conditions_tca_l) > 0:
                all_conditions_d[raw_condition_s] = conditions_tca_l
        return all_conditions_d

    def convert_op_each_raw_condition_to_tca_class(
        self,
        conditions_d: dict,
        raw_condition_s: str,
        inputs_d: dict,
        declare_d: dict,
        binary_d: dict,
    ):
        binaries_l = []
        stack_l = [raw_condition_s]
        visited_l = []

        while len(stack_l) > 0:

            expression_s = stack_l.pop()

            if (len(expression_s) == 0) or (expression_s in visited_l):
                continue
            visited_l.append(expression_s)

            reverse_s = ""
            if expression_s[0] in ["#", "!"]:
                reverse_s = "!"
                expression_s = expression_s[1:]

            if any([(sym_s in expression_s) for sym_s in LOGICAL_D]):
                split_l = binary_d[expression_s]

                stack_l.append(self.convert_boolean_expressions(reverse_s, split_l[0]))
                stack_l.append(self.convert_boolean_expressions(reverse_s, split_l[2]))
            elif any([(sym_s in expression_s) for sym_s in OPERATION_D]):
                if any([(varname_s in expression_s) for varname_s in inputs_d]):
                    binaries_l.append(
                        self.convert_boolean_expressions(reverse_s, expression_s)
                    )
                if any(
                    [(varname_s in expression_s) for varname_s in ["receivedCommand"]]
                ):
                    binaries_l.append(
                        self.convert_boolean_expressions(reverse_s, expression_s)
                    )
            elif expression_s in declare_d:
                stack_l.append(
                    self.convert_boolean_expressions(reverse_s, declare_d[expression_s])
                )
            elif ("!" == expression_s[0]) and (expression_s[1:] in declare_d):
                stack_l.append(
                    self.convert_boolean_expressions(reverse_s, declare_d[expression_s])
                )

        conditions_tca_e: set = set()
        for binary_s in binaries_l:
            tmp_tca_u: TcaClass = self.convert_binary_expression_to_tca_class(
                conditions_d, binary_s, inputs_d, binary_d
            )
            if (tmp_tca_u is not None) and (tmp_tca_u.device != ""):
                conditions_tca_e.add(tmp_tca_u)
        return list(conditions_tca_e)

    def get_op_tca_rules(
        self,
        raw_tca_rules_d: dict,
        triggers_d: dict,
        conditions_ld: dict,
        actions_d: dict,
        method_call_ud: dict,
        triggers_l: list,
        inputs_d: dict,
    ):
        all_tmp_actuator_rules_d, all_tmp_sink_rules_d = {}, {}
        for method_call_text_s, raw_tca_rules_l in raw_tca_rules_d.items():
            for raw_rule_l in raw_tca_rules_l:
                for raw_trigger_l in triggers_l:
                    rule_u: RuleClass = self.convert_op_each_raw_rule_to_tca_class(
                        raw_rule_l,
                        triggers_d,
                        conditions_ld,
                        actions_d,
                        method_call_ud,
                        raw_trigger_l,
                        inputs_d,
                    )

                    if rule_u.action.type == TcaEnum.ACTUATOR:
                        all_tmp_actuator_rules_d[rule_u.action] = (
                            all_tmp_actuator_rules_d.get(rule_u.action, [])
                        )
                        all_tmp_actuator_rules_d[rule_u.action].append(rule_u)
                    elif rule_u.action.type in [
                        TcaEnum.SINK_MSG,
                        TcaEnum.SINK_HTTP,
                        TcaEnum.SINK_API,
                    ]:
                        all_tmp_sink_rules_d[rule_u.action] = all_tmp_sink_rules_d.get(
                            rule_u.action, []
                        )
                        all_tmp_sink_rules_d[rule_u.action].append(rule_u)
        all_actuator_rules_l = self.remove_duplicate_rules(all_tmp_actuator_rules_d)
        all_sink_rules_l = self.remove_duplicate_rules(all_tmp_sink_rules_d)

        return all_actuator_rules_l, all_sink_rules_l

    def remove_duplicate_rules(self, all_tmp_tca_rules_d: dict):

        clean_tca_rules_l = []
        actions_l: list = sorted(all_tmp_tca_rules_d.keys())
        for action_u in actions_l:
            tmp_tca_rules_l = all_tmp_tca_rules_d[action_u]
            tca_rules_l = self.remove_duplicate_from_each_group_rules(
                action_u, tmp_tca_rules_l
            )
            rule_merge_u: RuleMergeClass = RuleMergeClass(action_u, tca_rules_l)
            if rule_merge_u not in clean_tca_rules_l:
                clean_tca_rules_l.append(rule_merge_u)

        return clean_tca_rules_l

    def remove_duplicate_from_each_group_rules(
        self, action_u: TcaClass, raw_tca_rules_l: list
    ):
        weight_f: float = 1 / len(raw_tca_rules_l)

        tca_rules_l: list = []
        for raw_tca_rule_u in raw_tca_rules_l:
            if raw_tca_rule_u not in tca_rules_l:
                raw_tca_rule_u.set_execution(action_u, weight_f)
                tca_rules_l.append(raw_tca_rule_u)
            else:
                tca_rule_u = tca_rules_l[tca_rules_l.index(raw_tca_rule_u)]
                tca_rule_u.set_execution(action_u, weight_f)
        return tca_rules_l

    def convert_op_each_raw_rule_to_tca_class(
        self,
        raw_rule_l: list,
        triggers_d: dict,
        conditions_d: dict,
        actions_d: dict,
        method_call_ud: dict,
        raw_trigger_l: list,
        inputs_d: dict,
    ):
        raw_conditions_l, raw_action_s = raw_rule_l

        action_u: TcaClass = actions_d[raw_action_s]
        # action_u.set_execution(action_u, weight_f)

        trigger_varname_s, trigger_value_s, trigger_type_s = raw_trigger_l

        trigger_device_s = ""
        trigger_attribute_s = ""
        trigger_operator_s = "=="
        trigger_value_s = trigger_value_s.strip('"').lower()
        trigger_arguments_l = []

        if trigger_type_s == "Item":
            if trigger_varname_s in inputs_d:
                trigger_device_s = inputs_d[trigger_varname_s].device
        else:
            trigger_device_s = trigger_type_s.lower()

        conditions_e: set = set()
        for raw_condition_s in raw_conditions_l:
            conditions_tca_l = sorted(conditions_d.get(raw_condition_s, []))
            for condition_tca_u in conditions_tca_l:
                if (
                    condition_tca_u.device == "receivedCommand"
                    or condition_tca_u.device == trigger_device_s
                ):
                    trigger_operator_s = condition_tca_u.operator
                    trigger_value_s = condition_tca_u.value
                else:
                    conditions_e.add(condition_tca_u)

        conditions_l = sorted(conditions_e)
        # [condition_u.set_execution(action_u, weight_f) for condition_u in conditions_l]

        trigger_t: tuple = (
            trigger_device_s,
            trigger_attribute_s,
            trigger_operator_s,
            trigger_value_s,
        )

        trigger_u = triggers_d.get(trigger_t, None)
        if trigger_u is None:
            trigger_u = TcaClass(
                *trigger_t, trigger_arguments_l, TcaEnum.TRIGGER, self.appname
            )
            triggers_d[trigger_t] = trigger_u
        # trigger_u.set_execution(action_u, weight_f)

        self.devsets.add(trigger_u.device)
        for condition_u in conditions_l:
            self.devsets.add(condition_u.device)
        self.devsets.add(action_u.device)
        return RuleClass(trigger_u, conditions_l, action_u, self.appname)

    def set_app_type(self) -> AppTypeEnum:
        """
        Set the type of app, indicate the app have uniq path NONE, ACTUATOR, SINK or BOTH
        Returns:


        """

        len_act_i: int = len(self.actuators_rules)
        len_sink_i: int = len(self.sinks_rules)
        if len_act_i == 0 and len_sink_i == 0:
            return AppTypeEnum.NONE

        if len_act_i > 0 and len_sink_i > 0:
            return AppTypeEnum.BOTH

        if len_act_i > 0:
            return AppTypeEnum.ACTUATOR

        return AppTypeEnum.SINK
