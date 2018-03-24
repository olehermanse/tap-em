#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse TAP to produce appropriate exit code and emojified summary.

Test Anything Protocol (testanything.org) is an output format for tests.

Todo:
    * Support test skipping
    * Test counter (make test number optional)
    * Use official regex for line detection
    * Allow test plan in end, but not middle

Example:
    $ cat tap_examples/basic.txt
    1..4
    ok 1 - Input file opened
    not ok 2 - First line of the input valid
    ok 3 - Read the rest of the file
    not ok 4 - Summarized correctly # TODO Not written yet
    $ cat tap_examples/basic.txt | python3 tapem.py
    1 4
    1..4
    ok 1 - Input file opened
    not ok 2 - First line of the input valid
    ok 3 - Read the rest of the file
    not ok 4 - Summarized correctly # TODO Not written yet

    🚰  | TAP Test results:
    ✅  | ok 1 - Input file opened
    ❌  | not ok 2 - First line of the input valid
    ✅  | ok 3 - Read the rest of the file
    ❌  | not ok 4 - Summarized correctly # TODO Not written yet

    ⚠️  | Test failures:
    ❌  | not ok 2 - First line of the input valid
    ❌  | not ok 4 - Summarized correctly # TODO Not written yet

    Summary: 2 ok  |  2 not ok  |  0 tap errors
    🔥  | Some tests failed - 2 ✅  |  2 ❌  |  0 🚱
    $ echo $?
    2
"""

# MIT License
#
# Copyright (c) 2018 Ole Herman Schumacher Elgesem
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# SOFTWARE.

__author__ = "Ole Herman Schumacher Elgesem"
__copyright__ = "Copyright 2018, Ole Herman Schumacher Elgesem"
__license__ = "MIT"

__version__ = "0.1.0"

import sys
import os

import argparse


def prefixed(string, emoji):
    return "{}  | {}".format(emoji, string)


class Tapper:
    def __init__(self):
        self.errors = []  # ok test results
        self.successes = []  # not ok test results
        self.results = []  # ok / not ok test results
        self.numbers = []  # unique test numbers encountered
        self.range = []  # Tests which should run
        self.tap_errors = []  # Errors in the TAP test output
        self.error_count = -1

        self.emoji = {
            "success": "✅",
            "failure": "❌",
            "tap": "🚰",
            "tap_error": "🚱",
            "great_success": "❤️",
            "disaster": "🔥",
            "catastrophe": "💥",
            "attention": "⚠️"
        }

        self.ascii = {
            "success": ":-)",
            "failure": ":-(",
            "tap": "^.^",
            "tap_error": "o.O",
            "great_success": "<3 ",
            "disaster": ">.<",
            "catastrophe": "v.v",
            "attention": "!! "
        }

    def set_ascii(self):
        self.emoji = self.ascii

    def found_number(self, num):
        try:
            num = int(num)
        except (ValueError, TypeError):
            self.tap_errors.append("Invalid test number: '{}'".format(num))
        if len(self.range) == 0:
            self.tap_errors.append(
                "No test range defined before result no. {}".format(num))
        elif num not in self.range:
            self.tap_errors.append(
                "Test result {} doesn't fit into any previous range".format(
                    num))
        if num in self.numbers:
            self.tap_errors.append(
                "Multiple results for test no. {}".format(num))
        else:
            self.numbers.append(num)

    def maybe_range(self, word):
        processed = word.replace("..", " ")
        print(processed)
        if "." in processed:
            return
        parts = processed.split()
        if len(parts) != 2:
            return
        a, b = int(parts[0]), int(parts[1])
        if a > b:
            self.tap_errors.append("Invalid range: {}".format(word))
            return
        new_range = range(a, b + 1)
        for num in new_range:
            if num not in self.range:
                self.range.append(num)
            else:
                self.tap_errors.append("Overlapping range '{}' at '{}'".format(
                    word, num))

    def process_line(self, line):
        emoji = self.emoji
        stripped = line.strip()
        number = None
        result = None
        if stripped.startswith("ok"):
            number = stripped.split()[1]
            result = prefixed(stripped, emoji["success"])
            self.successes.append(result)
        elif stripped.startswith("not ok"):
            number = stripped.split()[2]
            result = prefixed(stripped, emoji["failure"])
            self.errors.append(result)

        if result is not None:
            self.results.append(result)
        if number is not None:
            self.found_number(number)

        seq = stripped.split()
        if len(seq) > 0 and ".." in seq[0]:
            self.maybe_range(seq[0])

        print(line, end="")

    def drain(self, file=None, line_list=None):
        assert not (file and line_list)
        if line_list:
            for line in line_list:
                self.process_line(line)
            return
        if not file:
            for line in sys.stdin:
                self.process_line(line)
            return
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                self.process_line(line)

    def finalize(self):
        errors, results = len(self.errors), len(self.results)
        numbers = len(self.numbers)
        results = len(self.results)
        test_range = len(self.range)
        tap_errors = self.tap_errors

        if test_range <= 0:
            tap_errors.append("No test range found")
        if results <= 0:
            tap_errors.append("No test results found")
        if (numbers > test_range) or (results > test_range):
            tap_errors.append(
                "More test results than possible for test range: {}/{}".format(
                    max(numbers, results), test_range))
        self.error_count = errors + len(tap_errors)

    def summarize(self):
        emoji = self.emoji
        self.tap_errors = [
            prefixed(x, emoji["disaster"]) for x in self.tap_errors
        ]
        assert self.error_count >= 0
        if self.results:
            yield ""
            yield prefixed("TAP Test results:", emoji["tap"])
            for result in self.results:
                yield result
        if self.errors:
            yield ""
            yield prefixed("Test failures: ", emoji["attention"])
            for error in self.errors:
                yield error
        if self.tap_errors:
            yield prefixed("Protocol error(s) were found:", emoji["attention"])
            for error in self.tap_errors:
                yield error

        yield ""
        summary = "{} ok  |  {} not ok  |  {} tap errors".format(
            len(self.successes), len(self.errors), len(self.tap_errors))
        emoji_summary = summary.replace("not ok", emoji["failure"]).replace(
            "ok", emoji["success"]).replace("tap errors", emoji["tap_error"])
        yield "Summary: " + summary
        if self.error_count == 0:
            success_message = "All tests successful - " + emoji_summary
            yield prefixed(success_message, emoji["great_success"])
        else:
            all_failed = not self.successes and len(self.results) == len(
                self.range)
            some_all = "All" if all_failed else "Some"
            failure_message = some_all + " tests failed - " + emoji_summary
            fail_emoji = emoji["disaster"]
            if self.tap_errors or not self.successes:
                fail_emoji = emoji["catastrophe"]
            yield prefixed(failure_message, fail_emoji)

    def exit_code(self):
        assert self.error_count >= 0
        return min(self.error_count, 100)


def get_args():
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument(
        '--file', '-f', help='File input (default stdin)', type=str)
    argparser.add_argument(
        '--ascii',
        '-a',
        help='ASCII compatible emoticons',
        action="store_true")
    argparser.add_argument(
        '--install',
        '-i',
        help='Install to /usr/local/bin (may need sudo)',
        action="store_true")
    args = argparser.parse_args()
    return args


def installer():
    os.system("cp {} /usr/local/bin/tap-em".format(__file__))
    os.system("chmod ugo+x /usr/local/bin/tap-em")
    sys.exit(0)

if __name__ == "__main__":
    args = get_args()
    if args.install:
        installer()
    t = Tapper()
    if args.ascii:
        t.set_ascii()
    t.drain(args.file)
    t.finalize()
    for line in t.summarize():
        print(line)
    sys.exit(t.exit_code())
