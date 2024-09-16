import re
import time

import spacy

from Python.utils.constant import (
    NOUN_DEVICE_D,
    VERB_STATE_D,
    CAPA_FIX_DEVICE_D,
    CAPA_DEFAULT_DEVICE_D,
    IFTTT_FIX_DEVICE_D,
    IFTTT_DEFAULT_DEVICE_D,
    OPENHAB_FIX_DEVICE_D,
    OPENHAB_ITEM_FIX_DEVICE_D,
    FILES_REFERENCE_PATH_S,
)
from Python.utils.miscellaneous import (
    print_memory_usage,
    print_seconds_to_readable,
    read_json,
)
from Python.utils.process import (
    infer_device_state_from_ifttt,
    infer_device_type,
    infer_device_type_from_openhab,
    split_op_binding,
)

script_start_time_f = time.perf_counter()
# SmartThings
smartthing_truth: dict = read_json(f"{FILES_REFERENCE_PATH_S}/SmartThings_Truth.json")

total_dev_sm_i, correct_dev_sm_i = 0, 0

for fname_s, apps_d in smartthing_truth.items():
    var4_s: str = apps_d["descriptionStr"]
    var5_s: str = apps_d["filenameStr"]
    inputs_d: dict = apps_d["inputMap"]
    for varname_s, texts_l in inputs_d.items():
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
            total_dev_sm_i += 1
            if device_s == texts_l[3]:
                correct_dev_sm_i += 1

print(f"SmartThing Device Type Accuracy: {correct_dev_sm_i / total_dev_sm_i}")

# IFTTTS
ifttt_truth: dict = read_json(f"{FILES_REFERENCE_PATH_S}/IFTTT_Truth.json")
total_if_i, correct_sta_if_i, correct_dev_if_i = 0, 0, 0

for fname_s, apps_d in ifttt_truth.items():

    var4_s: str = apps_d["description"]
    var5_s: str = apps_d["name"]

    for comp_s in ["triggers", "actions"]:
        for item_d in apps_d[comp_s]:
            var3_s: str = item_d["id"]
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
            total_if_i += 1
            if device_s == item_d["device"]:
                correct_dev_if_i += 1
            if state_s == item_d["state"]:
                correct_sta_if_i += 1

print(f"IFTTT Device Type Accuracy: {correct_dev_if_i / total_if_i}")
print(f"IFTTT Device State Accuracy: {correct_sta_if_i / total_if_i}")

# OPENHAB
openhab_truth: dict = read_json(f"{FILES_REFERENCE_PATH_S}/OpenHAB_Truth.json")

total_op_i, correct_sta_op_i, correct_dev_op_i = 0, 0, 0

for fname_s, apps_d in openhab_truth.items():
    for varname_s, texts_l in apps_d.items():
        type_s, label_s, format_s, icon_s, groups_l, tags_l, binding_s, expect_s = (
            texts_l
        )

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
        total_op_i += 1
        if device_s == expect_s:
            correct_dev_op_i += 1
    #     # if state_s == "":
    #     #     correct_sta_op_i += 1

print(f"OpenHab Device Type Accuracy: {correct_dev_op_i / total_op_i}")

script_end_time_f = time.perf_counter()
print()
print_seconds_to_readable(round(script_end_time_f - script_start_time_f))

print_memory_usage()
