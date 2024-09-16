from Python.utils.component import (
    ChainClass,
    ChainListClass,
    MultipleInferClass,
    RuleMergeClass,
)
from Python.utils.constant import (
    THETA_IMPLICIT_F,
)
from Python.utils.enum import (
    ChainEnum,
    ConnEnum,
)


class TwoAppChainsClass:
    def __init__(
        self,
        application_l: list,
        fat_include_b: bool = True,
        empty_include_b: bool = False,
    ):
        self.orig_appinfos = application_l
        self.fat_include = fat_include_b
        self.empty_include = empty_include_b
        self.appinfos = self.filter_apps()

        (
            self.orig_appnames,
            self.orig_num_apps,
            self.orig_num_fats,
            self.orig_num_empties,
        ) = self.get_basic_information(self.orig_appinfos)
        self.appnames, self.num_apps, self.num_fats, self.num_empties = (
            self.get_basic_information(self.appinfos)
        )

        self.actuators_rules, self.sinks_rules = self.get_all_rules()
        self.update_connections()

        # Section 6.2
        (
            self.num_conns,
            self.num_sinks,
            self.num_acts,
            self.num_sinks_leak,
            self.num_activate,
            self.num_enable,
            self.num_match,
            self.num_influence,
            self.stat_match,
            self.stat_influence,
        ) = self.get_stats_information()

    def filter_apps(self):
        application_l = []
        for application_u in self.orig_appinfos:
            if application_u.isfat and (not self.fat_include):
                continue
            if application_u.isempty and (not self.empty_include):
                continue
            application_l.append(application_u)
        return application_l

    def get_basic_information(self, applications_l):
        appnames_l = []
        num_apps_i, num_fats_i, num_empty_i = 0, 0, 0

        for application_u in applications_l:
            if application_u.isfat:
                num_fats_i += 1
            if application_u.isempty:
                num_empty_i += 1
            num_apps_i += 1
            appnames_l.append(application_u.appname)
        return appnames_l, num_apps_i, num_fats_i, num_empty_i

    def get_all_rules(self):
        all_actuators_rules_l, all_sinks_rules_l = [], []
        for application_u in self.appinfos:
            actuators_rules_l, sinks_rules_l = (
                application_u.actuators_rules,
                application_u.sinks_rules,
            )
            all_actuators_rules_l.extend(actuators_rules_l)
            all_sinks_rules_l.extend(sinks_rules_l)
        return all_actuators_rules_l, all_sinks_rules_l

    def update_connections(self):
        total_l = self.actuators_rules[:]
        total_l.extend(self.sinks_rules[:])

        for latter_u in total_l:
            for prior_u in self.actuators_rules:
                latter_u.update_connections(prior_u)

    def clear_connections(self):
        total_l = self.actuators_rules[:]
        total_l.extend(self.sinks_rules[:])

        for rule_u in total_l:
            rule_u.clear_connections()

    def get_stats_information(self):
        num_conns_i = 0
        num_sinks_i, num_acts_i = 0, 0
        num_sinks_leak_i = 0
        num_activate_i, num_enable_i = 0, 0
        num_match_i, num_influence_i = 0, 0
        stat_match_d, stat_influence_d = {}, {}

        for rules_l in [self.sinks_rules, self.actuators_rules]:
            for rule_merge_u in rules_l:
                connections_d: dict = rule_merge_u.connections
                for other_merge_u, connections_l in connections_d.items():
                    len_connections_i = len(connections_l)

                    num_conns_i += len_connections_i
                    if rules_l == self.sinks_rules:
                        num_sinks_i += len_connections_i
                        # tca_nodes_l = [other_merge_u.action]
                        tca_nodes_l = []
                        tca_nodes_l.extend(other_merge_u.conditions)
                        tca_nodes_l.extend(other_merge_u.triggers)
                        for tca_node_u in tca_nodes_l:
                            if tca_node_u.threat is not None:
                                num_sinks_leak_i += len_connections_i
                                break
                    else:
                        num_acts_i += len_connections_i

                    for connection_u in connections_l:
                        devices_t: tuple = (
                            connection_u.prev.device,
                            connection_u.next.device,
                        )

                        if connection_u.conn == ConnEnum.MATCH:
                            num_match_i += 1
                            stat_match_d[devices_t] = stat_match_d.get(devices_t, 0) + 1

                        elif connection_u.conn == ConnEnum.INFLUENCE:
                            num_influence_i += 1
                            stat_influence_d[devices_t] = (
                                stat_influence_d.get(devices_t, 0) + 1
                            )

                        if connection_u.chain == ChainEnum.ACTIVATE:
                            num_activate_i += 1
                        elif connection_u.chain == ChainEnum.ENABLE:
                            num_enable_i += 1
        return (
            num_conns_i,
            num_sinks_i,
            num_acts_i,
            num_sinks_leak_i,
            num_activate_i,
            num_enable_i,
            num_match_i,
            num_influence_i,
            stat_match_d,
            stat_influence_d,
        )


class MultipleAppChainsClass(TwoAppChainsClass):
    def __init__(
        self,
        application_l: list,
        fat_include_b: bool = False,
        empty_include_b: bool = False,
    ):
        super().__init__(application_l, fat_include_b, empty_include_b)

        self.chains: dict = self.get_all_chains()

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
        self.single_exists = [{}, {}]
        self.direct_exposure, self.implicit_inference = [{}, {}], [{}, {}]
        self.multiple_inference = [{}, {}]
        self.multiple_exists = [{}, {}]

        for i_i in range(2):
            (
                self.count[i_i],
                self.count_risky_direct[i_i],
                self.count_risky_implicit[i_i],
                self.count_risky_both[i_i],
                self.avg_len[i_i],
                self.max_len[i_i],
            ) = self.get_count_length_stats(i_i)
            self.single_inference[i_i] = self.get_single_inference(i_i)
            self.single_exists[i_i] = self.get_exist_inference(
                self.single_inference[i_i]
            )
            self.direct_exposure[i_i], self.implicit_inference[i_i] = (
                self.get_threat_types(i_i)
            )
            self.multiple_inference[i_i] = self.get_multisink_inference(i_i)
            self.multiple_exists[i_i] = self.get_exist_inference(
                self.multiple_inference[i_i]
            )

    def get_all_chains(self):
        all_chains_l: list = []
        for sink_rule_u in self.sinks_rules:
            chains_list_u = self.get_chains_of_each_sink(sink_rule_u)
            if chains_list_u is not None:
                all_chains_l.append(chains_list_u)
        return all_chains_l

    def get_chains_of_each_sink(self, sink_rule_u: RuleMergeClass):
        chains_l, tree_nodes_l, paths_nodes_l = [], [], []
        tree_nodes_l.append(sink_rule_u)
        paths_nodes_l.append([sink_rule_u])
        visited_l = []

        while len(tree_nodes_l) > 0:
            tree_node_s: RuleMergeClass = tree_nodes_l.pop()
            path_node_l: list = paths_nodes_l.pop()

            if tree_node_s in visited_l:
                continue
            visited_l.append(tree_node_s)

            adjacent_rules_l: list = sorted(tree_node_s.connections.keys())

            if len(adjacent_rules_l) == 0:
                # print(path_node_l)
                chain_u: ChainClass = ChainClass(path_node_l[:])
                chains_l.append(chain_u)
                continue

            for adjacent_rules_u in adjacent_rules_l:
                tree_nodes_l.append(adjacent_rules_u)
                tmp_path_l = path_node_l[:]
                # tmp_path_l.insert(0, adjacent_rules_u)
                tmp_path_l.append(adjacent_rules_u)
                paths_nodes_l.append(tmp_path_l[:])
        if len(chains_l) > 0:
            return ChainListClass(chains_l)
        return None

    def get_count_length_stats(self, index_i):
        count_i, count_risky_direct_i, count_risky_implicit_i, count_risky_both_i = (
            0,
            0,
            0,
            0,
        )
        max_len_i, avg_len_i = 0, 0
        num_i = len(self.chains)

        for chainlist_u in self.chains:
            count_i += chainlist_u.count[index_i] / num_i
            count_risky_direct_i += chainlist_u.count_risky_direct[index_i] / num_i
            count_risky_implicit_i += chainlist_u.count_risky_implicit[index_i] / num_i
            count_risky_both_i += chainlist_u.count_risky_both[index_i] / num_i
            max_len_i += chainlist_u.max_len[index_i] / num_i
            avg_len_i += chainlist_u.avg_len[index_i] / num_i

        return (
            count_i,
            count_risky_direct_i,
            count_risky_implicit_i,
            count_risky_both_i,
            avg_len_i,
            max_len_i,
        )

    def get_single_inference(self, index_i=0):
        single_inference_d: dict = {}
        for chain_list_u in self.chains:
            single_inference_d[chain_list_u] = chain_list_u.single_inference[index_i]
        return single_inference_d

    def get_exist_inference(self, device_inference_d):
        exist_inference_d = {}
        for chainlist_u, inferences_d in device_inference_d.items():
            tmp_inference_d: dict = {}
            for state_s, inference_u in inferences_d.items():
                if (inference_u.inference > THETA_IMPLICIT_F) and (
                    inference_u.threat is not None
                ):
                    tmp_inference_d[state_s] = inference_u
            if len(tmp_inference_d) > 0:
                exist_inference_d[chainlist_u] = tmp_inference_d
        return exist_inference_d

    def get_threat_types(
        self,
        index_i: int,
    ):
        direct_exposure_d, implicit_inference_d = {}, {}
        for chain_list_u in self.chains:
            direct_exposure_d[chain_list_u], implicit_inference_d[chain_list_u] = (
                chain_list_u.direct_exposure[index_i],
                chain_list_u.implicit_inference[index_i],
            )
        return direct_exposure_d, implicit_inference_d

    def get_multisink_inference(
        self,
        index_i: int,
    ):
        multiple_candidates_d: dict = {}
        for chain_list_u in self.chains:
            candidates_d: dict = chain_list_u.multiple_candidates[index_i]
            if len(candidates_d) > 0:
                for state_s, single_inference_u in candidates_d.items():
                    if state_s not in multiple_candidates_d:
                        multiple_candidates_d[state_s] = MultipleInferClass(state_s)
                    if multiple_candidates_d[state_s].inference <= THETA_IMPLICIT_F:
                        multiple_candidates_d[state_s].update_inference(
                            single_inference_u
                        )
        multiple_d: dict = {}
        for state_s, multiple_infer_u in multiple_candidates_d.items():
            chains_list_t = tuple(multiple_infer_u.chainlist)
            if len(chains_list_t) <= 1:
                continue
            if chains_list_t not in multiple_d:
                multiple_d[chains_list_t] = {}
            multiple_d[chains_list_t][state_s] = multiple_infer_u
        return multiple_d
