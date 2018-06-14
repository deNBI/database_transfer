#!/usr/bin/env python3
"""
This program enters a infinite loop and prints a three comma separated values:
    unix_timestamp,bytes_sent,bytes_received,unique_id_per_machine,machine_type

It measures the network speed of all interfaces by calculating the delta of the total
received/sent values. The machine type simply determines whether this is a server or a
client machine.
"""

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, FileType
from time import time, sleep
from csv import writer
from subprocess import check_output
from typing import Dict

import psutil

units = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4}

csv_header = ("Time", "Bytes Sent", "Bytes Received", "ID", "Type")


def get_host_information() -> Dict[str, str]:
    """
    Wraps all the information provided by `hostnamectl` in a dictionary.
    :return: Content of `hostnamectl`.
    """
    cmd_output = check_output("/usr/bin/hostnamectl", universal_newlines=True)
    host_information = {}  # type: Dict[str, str]
    for line in cmd_output.splitlines():
        key, value = line.strip().split(":")
        host_information.update({key.strip(): value.strip()})
    return host_information


if __name__ == "__main__":
    host_information = get_host_information()
    default_machine_id = "{boot_id}-{hostname}".format(
        boot_id=host_information["Boot ID"],
        hostname=host_information.get(
            "Transient hostname", host_information["Static hostname"]
        ),
    )
    parser = ArgumentParser(
        usage=__doc__, formatter_class=ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-o",
        "--output_file",
        type=FileType("w"),
        help="File to save results to (csv).",
        default="-",
    )

    parser.add_argument(
        "-i",
        "--interval",
        default=1,
        type=int,
        help="""Interval between measurements (>=1). If unequal one all measurements are
        divided by it.
        """,
    )
    parser.add_argument(
        "-u",
        "--unit",
        help="Unit for measurement rounded to two decimal places.",
        choices=list(units),
        default="M",
    )

    parser.add_argument(
        "--id",
        type=str,
        help="""Unique identifier for this machine for later data aggregation. Default is a
        combination of transient hostname (with static hostname as fallback) and bootID""",
        default=default_machine_id,
    )

    parser.add_argument(
        "-t",
        "--type",
        choices=["client", "stratum0", "stratum1"],
        help="The type of this machine",
        default="client",
    )

    args = parser.parse_args()

    csv_writer = writer(args.output_file)

    sleep_interval = args.interval
    divisor = units[args.unit]

    before_sent, before_recv = None, None

    machine_id = args.id

    machine_type = args.type

    try:
        while True:
            net_stats = psutil.net_io_counters()
            if not before_recv or not before_sent:
                before_sent, before_recv = net_stats.bytes_sent, net_stats.bytes_recv
                csv_writer.writerow(csv_header)
                continue
            now_sent, now_recv = net_stats.bytes_sent, net_stats.bytes_recv
            sent = round((now_sent - before_sent) / divisor / sleep_interval, 2)
            recv = round((now_recv - before_recv) / divisor / sleep_interval, 2)
            csv_writer.writerow((round(time()), sent, recv, machine_id, machine_type))
            before_sent, before_recv = now_sent, now_recv
            sleep(sleep_interval)
    except KeyboardInterrupt:
        pass
