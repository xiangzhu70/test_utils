#!/usr/bin/env python3

import re
import argparse
from pdb import set_trace as stop

def args_parse(args_line):
    words = args_line.split() # split by space
    args = []
    key = None
    for word in words:
        #print(f"word: {word}")
        m = re.match(r"-(?P<double>-)?(?P<key>\S+)", word)
        if m:
            # end of last key-values
            if key:
                args.append((key, values))
                #print(f"adding: key {key}, values {values}")
            key = m.group("key")
            values = []
        else:
            values.append(word)
    if key:
        args.append((key, values))
        #print(f"adding: key {key}, values {values}")

    return args

def args_from_file(args_file):
    with open(args_file, "r") as f:
        args_line = f.read()

    args_lines = args_line.splitlines()

    if not len(args_lines) == 1:
        raise Exception("Wrong file")

    args_line = args_lines[0]

    args = args_parse(args_line)

    args.sort(key = lambda e: e[0])

    return args

def vals_cmp(values1, values2):
    if len(values1) != len(values2):
        return False

    for idx in range(len(values1)):
        if values1[idx] != values2[idx]:
            return False

    return True

def args_diff(args1, args2):
    p1 = 0
    p2 = 0
    len1 = len(args1)
    len2 = len(args2)

    while p1 < len1 or p2 < len2:
        if p1 < len1 and p2 < len2:
            if args1[p1][0] == args2[p2][0]:
                if vals_cmp(args1[p1][1], args2[p2][1]):
                    vals_line = " ".join(args1[p1][1])
                    print(f"| S |{p1:3}|{p2:3}| {args1[p1][0]}: {vals_line}")
                else:
                    vals_line = " ".join(args1[p1][1])
                    print(f"| D |{p1:3}|   | {args1[p1][0]}: {vals_line}")
                    vals_line = " ".join(args2[p2][1])
                    print(f"|   |   |{p2:3}| {args2[p2][0]}: {vals_line}")
                p1 += 1
                p2 += 1
                continue
            elif args1[p1][0] < args2[p2][0]:
                vals_line = " ".join(args1[p1][1])
                print(f"|   |{p1:3}|   | {args1[p1][0]}: {vals_line}")
                p1 += 1
                continue
            else:
                vals_line = " ".join(args2[p2][1])
                print(f"|   |   |{p2:3}| {args2[p2][0]}: {vals_line}")
                p2 += 1
                continue

        elif p1 < len1:
            vals_line = " ".join(args1[p1][1])
            print(f"|   |{p1:3}|   | {args1[p1][0]}: {vals_line}")
            p1 += 1
            continue
        else:
            vals_line = " ".join(args2[p2][1])
            print(f"|   |   |{p2:3}| {args2[p2][0]}: {vals_line}")
            p2 += 1
            continue
        
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Diff arguments")
    parser.add_argument("args1")
    parser.add_argument("args2")

    args = parser.parse_args()

    args1 = args_from_file(args.args1)
    args2 = args_from_file(args.args2)

    print(f"args1: {args.args1}, args2: {args.args2}")
    args_diff(args1, args2)



