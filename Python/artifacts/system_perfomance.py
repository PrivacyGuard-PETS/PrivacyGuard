import os
import random
import time

import numpy as np

from Python.utils.application import ApplicationClass
from Python.utils.constant import (
    DATASETS_IFTTT_PATH_S,
    DATASETS_OPENHAB_PATH_S,
    FILES_DATASETS_PATH_S,
    FILES_TEMPORARY_PATH_S,
)
from Python.utils.enum import AppTypeEnum
from Python.utils.miscellaneous import (
    make_dir,
    read_json,
    write_json,
    print_seconds_to_readable,
    print_memory_usage,
)
from Python.utils.process import (
    get_ifttt_json_from_csv,
    get_openhab_raw_json,
)
from Python.utils.result import MultipleAppChainsClass
from Python.utils.simulation import get_device_related_appinfos

script_start_time_f = time.perf_counter()

make_dir(FILES_DATASETS_PATH_S)
make_dir(FILES_TEMPORARY_PATH_S)

applications_l = []

# Processing Time
print(f"Processing Time (milliseconds):")

# Extract SmartThings TCA Rules
sm_start_time_f = time.perf_counter()
os.system(
    "groovyc Groovy/org/codehaus/groovy/ast/expr/NotExpression.java Groovy/SmartThingsHelper.groovy Groovy/SmartThingsMain.groovy"
)
os.system("groovy Groovy/SmartThingsMain.groovy Datasets")
os.system("rm -rf *.class")
os.system("rm -rf org")

smartthings_d: dict = read_json(f"{FILES_DATASETS_PATH_S}/SmartThings.json")

for fname_s, detail_d in smartthings_d.items():
    application_u: ApplicationClass = ApplicationClass(
        fname_s, detail_d, AppTypeEnum.SMARTTHINGS
    )
    applications_l.append(application_u)

n_sm_i = len(smartthings_d)

sm_end_time_f = time.perf_counter()

sm_time_f = (sm_end_time_f - sm_start_time_f) * 1000 / n_sm_i
print(f"SmartThings: {sm_time_f} ms")

# Extract IFTTT TCA Rules
if_start_time_f = time.perf_counter()

ifttt_d: dict = get_ifttt_json_from_csv(f"{DATASETS_IFTTT_PATH_S}/Step3_IoT_Rules.csv")
write_json(f"{FILES_DATASETS_PATH_S}/IFTTT.json", ifttt_d)

for fname_s, detail_d in ifttt_d.items():
    application_u: ApplicationClass = ApplicationClass(
        fname_s, detail_d, AppTypeEnum.IFTTT
    )
    applications_l.append(application_u)

n_if_i = len(ifttt_d)

if_end_time_f = time.perf_counter()

if_time_f = (if_end_time_f - if_start_time_f) * 1000 / n_if_i
print(f"IFTTT: {if_time_f} ms")

# Extract OpenHAB TCA Rules
op_start_time_f = time.perf_counter()

openhab_raw_d = get_openhab_raw_json(DATASETS_OPENHAB_PATH_S)
write_json(f"{FILES_TEMPORARY_PATH_S}/OpenHAB.json", openhab_raw_d)

os.system(
    "groovyc Groovy/org/codehaus/groovy/ast/expr/NotExpression.java Groovy/OpenHabHelper.groovy Groovy/OpenHabMain.groovy"
)
os.system("groovy Groovy/OpenHabMain.groovy Datasets")
os.system("rm -rf *.class")
os.system("rm -rf org")

openhab_d: dict = read_json(f"{FILES_DATASETS_PATH_S}/OpenHAB.json")

for fname_s, detail_d in openhab_d.items():
    application_u: ApplicationClass = ApplicationClass(
        fname_s, detail_d, AppTypeEnum.OPENHAB
    )
    applications_l.append(application_u)

n_op_i = len(ifttt_d)

op_end_time_f = time.perf_counter()

op_time_f = (op_end_time_f - op_start_time_f) * 1000 / n_op_i
print(f"OpenHAB: {op_time_f} ms")

# Calculation Time
num_dev_l: list = list(range(5, 35, 5))
len_num_dev_i = len(num_dev_l)
num_iter_i: int = 5000

device_application_d: dict = get_device_related_appinfos(
    applications_l, fat_include_b=True, empty_include_b=True
)

time_l = np.zeros((len_num_dev_i, num_iter_i))

for idx_dev_i in range(len_num_dev_i):
    num_dev_i = num_dev_l[idx_dev_i]
    # print(f"Iteration of {num_dev_i} Apps.")

    for idx_iter_i in range(num_iter_i):

        rand_dev_e: set = random.sample(list(device_application_d.keys()), num_dev_i)

        rand_applications_l: list = list(
            {random.choice(device_application_d[dev_s]) for dev_s in rand_dev_e}
        )

        rand_start_time_f = time.perf_counter()
        rand_u = MultipleAppChainsClass(
            rand_applications_l, fat_include_b=True, empty_include_b=False
        )

        rand_u.clear_connections()
        rand_end_time_f = time.perf_counter()
        time_l[idx_dev_i, idx_iter_i] = (rand_end_time_f - rand_start_time_f) * 1000

print()
print(f"Calculation Time (milliseconds):")
print(f"From {num_dev_l[0]} to {num_dev_l[-1]}:")
print(np.mean(time_l, 1))

script_end_time_f = time.perf_counter()
print()
print_seconds_to_readable(round(script_end_time_f - script_start_time_f))

print_memory_usage()
