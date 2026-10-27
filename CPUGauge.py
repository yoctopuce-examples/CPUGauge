#!/usr/bin/env python
import argparse
from time import sleep

from yoctopuce.yocto_api import *
from yoctopuce.yocto_servo import *

import psutil


def main():
    parser = argparse.ArgumentParser(
        description='Monitor CPU and Disk usage and update gauges using Yoctopuce Yocto-Servo(-C) device',
    )
    parser.add_argument("--hub", help="The address of YoctoHub where the YoctoServo is connected (default is USB)",
                        default="usb")
    parser.add_argument("--delay", help="The frequency of the update in seconds", default=1.0, type=float)
    parser.add_argument("--verbose", help="Display more information", action='store_true')
    parser.add_argument("--cpu", help="The HardwareId or logical name of the YServo output to use for CPU usage",
                        default="")
    parser.add_argument("--disk", help="The HardwareId or logical name of the YServo output to use for disk usage",
                        default="")
    parser.add_argument("--inventory", action='store_true')
    args = parser.parse_args()
    print(args)
    if args.verbose:
        print("Using Yoctopuce Python library v%s" % YAPI.GetAPIVersion())
    # Register Remote Hub or local USB accesss
    errmsg = YRefParam()
    if YAPI.RegisterHub(args.hub, errmsg) != YAPI.SUCCESS:
        sys.exit("Unable to Register hub \"%s\" (%s)" % (args.hub, errmsg.value))

    if args.inventory:
        print("Detected Servo:")
        servo = YServo.FirstServo()
        while servo is not None:
            print(" %s (logical name=\"%s\")" % (servo.get_hardwareId(), servo.get_logicalName()))
            servo = servo.nextServo()

    if args.cpu == '' and args.disk == '':
        sys.exit("You must specify at least --cpu or --disk")

    print("Starting computer monitoring")
    # setup initial disk counter
    max_disk_usage = 1
    disk_info = psutil.disk_io_counters()
    last_disk_io = disk_info.read_bytes + disk_info.write_bytes
    while True:
        if args.cpu != "":
            # update cpu gauge
            cpu_usage = psutil.cpu_percent()
            cpu_pos = cpu_usage * 20 - 1000
            if args.verbose:
                print("CPU usage: %d (-> pos %d)" % (cpu_usage, cpu_pos))
            try:
                servo_cpu = YServo.FindServo(args.cpu)
                servo_cpu.move(cpu_pos, args.delay * 1000)
            except Exception as e:
                print("Unable to update cpu gauge: %s" % e)
        if args.disk != "":
            # update disk gauge
            disk_info = psutil.disk_io_counters()
            disk_io_total = disk_info.read_bytes + disk_info.write_bytes
            disk_io_delta = disk_io_total - last_disk_io
            last_disk_io = disk_io_total
            if disk_io_delta > max_disk_usage:
                max_disk_usage = disk_io_delta
            disk_pos = disk_io_delta * 2000 / max_disk_usage - 1000
            if args.verbose:
                print("disk usage: %d (-> pos %d)" % (disk_io_delta, disk_pos))
            try:
                servo_disk = YServo.FindServo(args.disk)
                servo_disk.move(disk_pos, args.delay * 1000)
            except Exception as e:
                print("Unable to update disk gauge: %s" % e)
        sleep(args.delay)


if __name__ == '__main__':
    main()
