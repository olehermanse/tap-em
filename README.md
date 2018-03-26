# tap-em
Parse TAP to produce appropriate exit code and emojified summary.

## Example

```
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
```
