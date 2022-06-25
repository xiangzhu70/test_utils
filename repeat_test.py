#!/usr/bin/env python3

import subprocess
import shlex
import re
import datetime
import argparse
import configparser


def run_test(cmd):

    test_result = None
    test_output = []
    process = subprocess.Popen(shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)

    while process.stdout.readable():
        line = process.stdout.readline()

        if not line:
            break

        line = line.decode().strip()
        test_output.append(line)

        m = re.search(result_pattern, line)
        if not m:
            continue

        m = re.search(ok_pattern, line)
        if m:
            test_result = "OK"
        else:
            test_result = "FAIL"

    return test_result, test_output


def repeat_test(cmd, n_times, n_failures=1, fail_log_file=None):
    n_failures_found = 0
    for i in range(n_times):
        test_result, test_output = run_test(cmd)
        print(f"== {i}: {test_result}")
        if test_result != "OK":
            if fail_log_file:
                if n_failures > 1:
                    fail_log = f"{fail_log_file}_{n_failures_found}"
                else:
                    fail_log = fail_log_file
                with open(fail_log, "w") as f:
                    for line in test_output:
                        f.write(f"{line}\n")
                print(f"== fail log in file {fail_log}")
            n_failures_found += 1
            if n_failures_found >= n_failures:
                break

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Repeat run a test")
    parser.add_argument("-c", "--config", help="config ini file")
    parser.add_argument("-n", "--n_times", help="n times to repeat")

    args = parser.parse_args()

    n_times = 1

    if args.n_times:
        n_times = int(args.n_times)

    conf_file = args.config
    if not conf_file:
        conf_file = "repeat_test.ini"

    config = configparser.ConfigParser()
    ret = config.read(conf_file)

    cmd = config["test"]["cmd"]
    result_pattern = config["test"]["result_pattern"]
    ok_pattern = config["test"]["ok_pattern"]
    
    if "fail_log_file" in config["test"]:
        fail_log_file = config["test"]["fail_log_file"]
    else:
        fail_log_file = None

    if "n_failures" in config["test"]:
        n_failures = config["test"]["n_failures"]
    else:
        n_failures = 1

    print(f"cmd: {cmd}")
    print(f"result_pattern: {result_pattern}")
    print(f"ok_pattern: {ok_pattern}")
    print(f"n_times: {n_times}")
    print(f"fail_log_file: {fail_log_file}")
    print(f"n_failures: {n_failures}")

    repeat_test(cmd, n_times, n_failures=n_failures, fail_log_file=fail_log_file)

