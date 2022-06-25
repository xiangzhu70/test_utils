#!/usr/bin/env python3

import subprocess
import shlex
import re
import datetime
import argparse
import configparser


def run_test(cmd, parse_patterns=None):

    test_result = None
    test_output = []
    parsed_results = []
    process = subprocess.Popen(shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)

    while process.stdout.readable():
        line = process.stdout.readline()

        if not line:
            break

        line = line.decode().strip()
        test_output.append(line)

        if parse_patterns:
            for (key_name, parse_pattern) in parse_patterns:
                m = re.search(parse_pattern, line)
                if not m:
                    continue
                val = m.group(key_name)
                parsed_results.append((key_name, val))
 
        m = re.search(result_pattern, line)
        if not m:
            continue

        m = re.search(ok_pattern, line)
        if m:
            test_result = "OK"
        else:
            test_result = "FAIL"

    return test_result, test_output, parsed_results


def repeat_test(cmd, n_times, n_failures=1, fail_log_file=None, parse_patterns=None):
    n_failures_found = 0
    for i in range(n_times):
        test_result, test_output, parsed_results = run_test(cmd, parse_patterns=parse_patterns)
        output_line = f"== {i}: {test_result}"
        for (key, val) in parsed_results:
            output_line += f", {key}={val}"
        print(output_line)
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

    parse_patterns = []
    if "parse" in config:
        for key in config["parse"]:
            m = re.search(r"<(?P<key_name>\w+)>", config["parse"][key])
            if not m:
                print(f"key name not found from the parse pattern key {key}")
                continue
            key_name = m.group("key_name")
            parse_patterns.append((key_name, config["parse"][key]))

    print("[Test configurations]")
    print(f"cmd: {cmd}")
    print(f"result_pattern: {result_pattern}")
    print(f"ok_pattern: {ok_pattern}")
    print(f"n_times: {n_times}")
    print(f"fail_log_file: {fail_log_file}")
    print(f"n_failures: {n_failures}")

    if parse_patterns:
        print("\n[Parse patterns]")
        for (key, pattern) in parse_patterns:
            print(f"  {key}")
        print("\n")

    repeat_test(cmd, n_times,
        n_failures=n_failures, fail_log_file=fail_log_file,
        parse_patterns = parse_patterns)

