import json
import random
import time

import numpy as np

from Python.utils.application import ApplicationClass
from Python.utils.constant import FILES_DATASETS_PATH_S, PRIVACY_INDEX_D, TEST_FAT_APP_S
from Python.utils.enum import (
    ThreatTypeEnum,
)
from Python.utils.miscellaneous import print_seconds_to_readable, print_memory_usage
from Python.utils.result import MultipleAppChainsClass, TwoAppChainsClass
from Python.utils.simulation import (
    convert_sensitive_devices_based_on_frequency,
    get_application_by_name,
    get_count_of_privacy_types,
    get_device_related_appinfos,
    get_top_ratio_results,
    plot_count_length,
    plot_grouped_and_stacked_bar,
    read_appinfos,
    update_sensitive_devices_of_privacy_label,
)

script_start_time_f = time.perf_counter()

# load_start_time_f = time.perf_counter()
(
    applications_l,
    fat_applications_l,
    total_apps_d,
    fat_apps_d,
    empty_apps_d,
    clean_apps_d,
    used_apps_d,
    clean_apps_i,
    used_apps_i,
) = read_appinfos(FILES_DATASETS_PATH_S)
print(f"Number of Fat Apps for Each Type: ")
print(fat_apps_d)
print()
print(f"Number of Clean Apps (without Fat Apps, without Empty Apps) for Each Type: ")
print(clean_apps_d)
print(f"Number of Clean Apps (without Fat Apps, without Empty Apps): {clean_apps_i}")
print()
print(f"Number of Used Apps (with Fat Apps, without Empty Apps) for Each Type: ")
print(used_apps_d)
print(f"Number of Used Apps (with Fat Apps, without Empty Apps): {used_apps_i}")
print()
# load_end_time_f = time.perf_counter()
# print_seconds_to_readable(round(load_end_time_f - load_start_time_f))


## Section 6.2 Two-App Chains
# two_start_time_f = time.perf_counter()
two_app_chains_u: TwoAppChainsClass = TwoAppChainsClass(
    applications_l, fat_include_b=False, empty_include_b=False
)
print(f"Number of Actuactor Rules: {len(two_app_chains_u.actuators_rules)}")
print(f"Number of Sink Rules: {len(two_app_chains_u.sinks_rules)}")
print(
    f"Number of All Rules: {len(two_app_chains_u.actuators_rules) +len(two_app_chains_u.sinks_rules)}"
)
print()
print(f"Connections:{two_app_chains_u.num_conns}")
print(f"Sinks:{two_app_chains_u.num_sinks/two_app_chains_u.num_conns}")
print(f"Sinks Leak:{two_app_chains_u.num_sinks_leak/two_app_chains_u.num_conns}")
print(f"Activate:{two_app_chains_u.num_activate/two_app_chains_u.num_conns}")
print(f"Enable:{two_app_chains_u.num_enable/two_app_chains_u.num_conns}")
print(f"Match:{two_app_chains_u.num_match/two_app_chains_u.num_conns}")
print(f"Influence:{two_app_chains_u.num_influence/two_app_chains_u.num_conns}")
print()
stat_match_l = sorted(two_app_chains_u.stat_match.items(), key=lambda x: (-x[1], x[0]))
stat_influence_l = sorted(
    two_app_chains_u.stat_influence.items(), key=lambda x: (-x[1], x[0])
)
print(f"Match Device Pairs: {stat_match_l}")
print(f"Influence Physical Channels: {stat_influence_l}")
two_app_chains_u.clear_connections()

# two_end_time_f = time.perf_counter()
# print_seconds_to_readable(round(two_end_time_f - two_start_time_f))

## Section 6.2 Multi-App Chains
# multiple_start_time_f = time.perf_counter()
device_application_d: dict = get_device_related_appinfos(
    applications_l, fat_include_b=False, empty_include_b=False
)

num_dev_l: list = list(range(5, 35, 5))
# num_dev_l: list = list(range(5, 10, 5))
len_num_dev_i = len(num_dev_l)
len_num_priv_i = len(PRIVACY_INDEX_D)
num_iter_i: int = 5000

fat_application_u: ApplicationClass = get_application_by_name(
    fat_applications_l, TEST_FAT_APP_S
)

# fat_application_u = random.choice(fat_applications_l)
# print(fat_application_u.appname)

# 0 2: include chain=1 or not
# 1 2: wo/w fat apps
# 2 5: count, count_risky_direct, count_risky_implicit, count_risky_both, avg_len, max_len
# 3 len_num_dev_i: number of devices
# 4 num_iter_i: iteration
rand_count_length_l = np.zeros((2, 2, 6, len_num_dev_i, num_iter_i))

rand_sensitive_devices_d: dict = {
    ThreatTypeEnum.DIRECT: {priv_label_s: {} for priv_label_s in PRIVACY_INDEX_D},
    ThreatTypeEnum.IMPLICIT: {priv_label_s: {} for priv_label_s in PRIVACY_INDEX_D},
}

# 0 2: include chain=1 or not
# 1 2: wo/w fat apps
# 2 3: direct, implicit, multiple
# 3 len_num_priv_i: number of privacy types
# 4 len_num_dev_i: number of devices
# 5 num_iter_i: iteration
rand_privacy_types_l = np.zeros((2, 2, 3, len_num_priv_i, len_num_dev_i, num_iter_i))


for idx_dev_i in range(len_num_dev_i):
    num_dev_i = num_dev_l[idx_dev_i]
    # print(f"Iteration of {num_dev_i} Apps.")

    for idx_iter_i in range(num_iter_i):
        # print(f"{num_dev_i} - {idx_iter_i + 1}")

        rand_dev_e: set = random.sample(list(device_application_d.keys()), num_dev_i)

        # Without FAT apps
        rand_applications_l: list = list(
            {random.choice(device_application_d[dev_s]) for dev_s in rand_dev_e}
        )

        rand_wo_fat_u = MultipleAppChainsClass(
            rand_applications_l, fat_include_b=False, empty_include_b=False
        )

        # wo fat apps
        # include chain length = 0
        rand_count_length_l[0, 0, :, idx_dev_i, idx_iter_i] = (
            rand_wo_fat_u.count[0],
            rand_wo_fat_u.count_risky_direct[0],
            rand_wo_fat_u.count_risky_implicit[0],
            rand_wo_fat_u.count_risky_both[0],
            rand_wo_fat_u.avg_len[0],
            rand_wo_fat_u.max_len[0],
        )
        # not include chain length = 0
        rand_count_length_l[1, 0, :, idx_dev_i, idx_iter_i] = (
            rand_wo_fat_u.count[1],
            rand_wo_fat_u.count_risky_direct[1],
            rand_wo_fat_u.count_risky_implicit[1],
            rand_wo_fat_u.count_risky_both[1],
            rand_wo_fat_u.avg_len[1],
            rand_wo_fat_u.max_len[1],
        )

        direct_exposure_wo_fat_w_sink_d = rand_wo_fat_u.single_inference[0]
        implicit_inference_wo_fat_w_sink_d = rand_wo_fat_u.implicit_inference[0]
        multiple_inference_wo_fat_w_sink_d = rand_wo_fat_u.multiple_inference[0]

        direct_exposure_wo_fat_d = rand_wo_fat_u.single_inference[1]
        implicit_inference_wo_fat_d = rand_wo_fat_u.implicit_inference[1]
        multiple_inference_wo_fat_d = rand_wo_fat_u.multiple_inference[1]

        update_sensitive_devices_of_privacy_label(
            rand_sensitive_devices_d, direct_exposure_wo_fat_d, ThreatTypeEnum.DIRECT
        )
        update_sensitive_devices_of_privacy_label(
            rand_sensitive_devices_d,
            implicit_inference_wo_fat_d,
            ThreatTypeEnum.IMPLICIT,
        )
        # update_sensitive_devices_of_privacy_label(
        #     rand_sensitive_devices_d,
        #     multiple_inference_wo_fat_d,
        #     ThreatTypeEnum.IMPLICIT,
        # )

        rand_privacy_types_l[0, 0, 0, :, idx_dev_i, idx_iter_i] = (
            get_count_of_privacy_types(direct_exposure_wo_fat_w_sink_d)
        )
        rand_privacy_types_l[0, 0, 1, :, idx_dev_i, idx_iter_i] = (
            get_count_of_privacy_types(implicit_inference_wo_fat_w_sink_d)
        )
        rand_privacy_types_l[0, 0, 2, :, idx_dev_i, idx_iter_i] = (
            get_count_of_privacy_types(multiple_inference_wo_fat_w_sink_d)
        )
        rand_privacy_types_l[1, 0, 0, :, idx_dev_i, idx_iter_i] = (
            get_count_of_privacy_types(direct_exposure_wo_fat_d)
        )
        rand_privacy_types_l[1, 0, 1, :, idx_dev_i, idx_iter_i] = (
            get_count_of_privacy_types(implicit_inference_wo_fat_d)
        )
        rand_privacy_types_l[1, 0, 2, :, idx_dev_i, idx_iter_i] = (
            get_count_of_privacy_types(multiple_inference_wo_fat_d)
        )

        rand_wo_fat_u.clear_connections()

        # With FAT apps
        rand_fat_applications_l: list = rand_applications_l[:]

        rand_fat_applications_l.append(fat_application_u)

        rand_w_fat_u = MultipleAppChainsClass(
            rand_fat_applications_l, fat_include_b=True, empty_include_b=False
        )

        # with fat apps
        # include chain length = 0
        rand_count_length_l[0, 1, :, idx_dev_i, idx_iter_i] = (
            rand_w_fat_u.count[0],
            rand_w_fat_u.count_risky_direct[0],
            rand_w_fat_u.count_risky_implicit[0],
            rand_w_fat_u.count_risky_both[0],
            rand_w_fat_u.avg_len[0],
            rand_w_fat_u.max_len[0],
        )
        # not include chain length = 0
        rand_count_length_l[1, 1, :, idx_dev_i, idx_iter_i] = (
            rand_w_fat_u.count[1],
            rand_w_fat_u.count_risky_direct[1],
            rand_w_fat_u.count_risky_implicit[1],
            rand_w_fat_u.count_risky_both[1],
            rand_w_fat_u.avg_len[1],
            rand_w_fat_u.max_len[1],
        )

        direct_exposure_w_fat_w_sink_d = rand_w_fat_u.single_inference[0]
        implicit_inference_w_fat_w_sink_d = rand_w_fat_u.implicit_inference[0]
        multiple_inference_w_fat_w_sink_d = rand_w_fat_u.multiple_inference[0]

        direct_exposure_w_fat_d = rand_w_fat_u.single_inference[1]
        implicit_inference_w_fat_d = rand_w_fat_u.implicit_inference[1]
        multiple_inference_w_fat_d = rand_w_fat_u.multiple_inference[1]

        rand_privacy_types_l[0, 1, 0, :, idx_dev_i, idx_iter_i] = (
            get_count_of_privacy_types(direct_exposure_w_fat_w_sink_d)
        )
        rand_privacy_types_l[0, 1, 1, :, idx_dev_i, idx_iter_i] = (
            get_count_of_privacy_types(implicit_inference_w_fat_w_sink_d)
        )
        rand_privacy_types_l[0, 1, 2, :, idx_dev_i, idx_iter_i] = (
            get_count_of_privacy_types(multiple_inference_w_fat_w_sink_d)
        )
        rand_privacy_types_l[1, 1, 0, :, idx_dev_i, idx_iter_i] = (
            get_count_of_privacy_types(direct_exposure_w_fat_d)
        )
        rand_privacy_types_l[1, 1, 1, :, idx_dev_i, idx_iter_i] = (
            get_count_of_privacy_types(implicit_inference_w_fat_d)
        )
        rand_privacy_types_l[1, 1, 2, :, idx_dev_i, idx_iter_i] = (
            get_count_of_privacy_types(multiple_inference_w_fat_d)
        )

        rand_w_fat_u.clear_connections()

# Average Number and Length of Cross-App Chains
mean_count_length_l = np.mean(rand_count_length_l, axis=4)
plot_count_length(num_dev_l, mean_count_length_l, 0)

# Probability of Risky Chains
count_wo_fat_w_sink_l = mean_count_length_l[0, 0, 0, :]
count_risky_wo_fat_w_sink_l = mean_count_length_l[0, 0, 2, :]
count_w_fat_w_sink_l = mean_count_length_l[0, 1, 0, :]
count_risky_w_fat_w_sink_l = mean_count_length_l[0, 1, 2, :]

print()
print("Probability of Risky Chains:")
print("Without Fat:")
print(count_risky_wo_fat_w_sink_l / count_wo_fat_w_sink_l)
print("With Fat:")
print(count_risky_w_fat_w_sink_l / count_w_fat_w_sink_l)
print()


# Typical Sensitive Devices
sensitive_devices_d = convert_sensitive_devices_based_on_frequency(
    rand_sensitive_devices_d
)
print(sensitive_devices_d)
print()
print("Top 80% Typical Sensitive Devices:")
top_typical_sensitive_d = {}
for type_m, devices_d in sensitive_devices_d.items():
    type_s = str(type_m)
    top_typical_sensitive_d[type_s] = {}
    for label_s, devices_l in devices_d.items():
        top_typical_sensitive_d[type_s][label_s] = get_top_ratio_results(devices_l)
print(json.dumps(top_typical_sensitive_d, indent=4))

# Average Number of Risky Chains with Different Privacy Threats
mean_privacy_types_l = np.mean(rand_privacy_types_l, axis=5)
plot_grouped_and_stacked_bar(num_dev_l, mean_privacy_types_l)

# multiple_end_time_f = time.perf_counter()
# print_seconds_to_readable(round(multiple_end_time_f - multiple_start_time_f))

script_end_time_f = time.perf_counter()
print()
print_seconds_to_readable(round(script_end_time_f - script_start_time_f))

print_memory_usage()
