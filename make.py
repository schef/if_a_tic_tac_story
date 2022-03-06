#!/usr/bin/env python3

import os
import pty
import select
import sys
from datetime import date
from subprocess import Popen
from time import sleep

import typer

app = typer.Typer()


class Base:
    # Foreground:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    # Formatting
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    # End colored text
    END = '\033[0m'
    NC = '\x1b[0m'  # No Color


def run_bash_cmd(cmd, echo=True, interaction={}, return_lines=True, return_code=False, cr_as_newline=False):
    if echo: print("CMD:", cmd)
    master_fd, slave_fd = pty.openpty()
    line = ""
    lines = []
    with Popen(cmd, shell=True, preexec_fn=os.setsid, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd, universal_newlines=True) as p:
        while p.poll() is None:
            r, w, e = select.select([sys.stdin, master_fd], [], [], 0.01)
            if master_fd in r:
                o = os.read(master_fd, 10240).decode("UTF-8")
                if o:
                    for c in o:
                        if cr_as_newline and c == "\r":
                            c = "\n"
                        if c == "\n":
                            if line and line not in interaction.values():
                                clean = line.strip().split('\r')[-1]
                                lines.append(clean)
                                if echo: print("STD:", line)
                            line = ""
                        else:
                            line += c
            if line:  # pass password to prompt
                for key in interaction:
                    if key in line:
                        if echo: print("PMT:", line)
                        sleep(1)
                        os.write(master_fd, ("%s" % (interaction[key])).encode())
                        os.write(master_fd, "\r\n".encode())
                        line = ""
        if line:
            clean = line.strip().split('\r')[-1]
            lines.append(clean)

    os.close(master_fd)
    os.close(slave_fd)

    if return_lines and return_code:
        return lines, p.returncode
    elif return_code:
        return p.returncode
    else:
        return lines


def get_timestamp():
    today = date.today()
    return today.strftime("%Y%m%d")


@app.command()
def compile_inform():
    cmd = "cc -DLINUX -O2 -o ./bin/inform ./Inform6/*.c"
    run_bash_cmd(cmd)


@app.command()
def compile(revision=None):
    revision_string = ["dev", f"r{revision}"][revision != None]
    timestamp = get_timestamp()
    cmd = f"./bin/inform -v3 +./PunyInform/lib src/a_tic_tac_story.inf releases/a_tic_tac_story_{revision_string}_{timestamp}.z3"
    run_bash_cmd(cmd)


if __name__ == "__main__":
    app()
