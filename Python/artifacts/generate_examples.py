import os
import time

from Python.utils.constant import (
    EXAMPLES_IFTTT_PATH_S,
    EXAMPLES_OPENHAB_PATH_S,
    EXAMPLES_SMARTTHINGS_PATH_S,
    FILES_EXAMPLES_PATH_S,
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

script_start_time_f = time.perf_counter()

make_dir(FILES_EXAMPLES_PATH_S)
make_dir(FILES_TEMPORARY_PATH_S)

# Extract SmartThings TCA Rules
os.system(
    "groovyc Groovy/org/codehaus/groovy/ast/expr/NotExpression.java Groovy/SmartThingsHelper.groovy Groovy/SmartThingsMain.groovy"
)
os.system("groovy Groovy/SmartThingsMain.groovy Examples")
os.system("rm -rf *.class")
os.system("rm -rf org")

# Extract IFTTT TCA Rules
ifttt_d: dict = get_ifttt_json_from_csv(f"{EXAMPLES_IFTTT_PATH_S}/examples.csv")
write_json(f"{FILES_EXAMPLES_PATH_S}/IFTTT.json", ifttt_d)

# Extract OpenHAB TCA Rules
openhab_raw_d = get_openhab_raw_json(EXAMPLES_OPENHAB_PATH_S)
write_json(f"{FILES_TEMPORARY_PATH_S}/OpenHAB.json", openhab_raw_d)

os.system(
    "groovyc Groovy/org/codehaus/groovy/ast/expr/NotExpression.java Groovy/OpenHabHelper.groovy Groovy/OpenHabMain.groovy"
)
os.system("groovy Groovy/OpenHabMain.groovy Examples")
os.system("rm -rf *.class")
os.system("rm -rf org")

script_end_time_f = time.perf_counter()
print()
print_seconds_to_readable(round(script_end_time_f - script_start_time_f))

print_memory_usage()
