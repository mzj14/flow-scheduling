#! /usr/bin/env python3

from random import sample, randint
import numpy as np
import math

'''
@Function:
  Generate flow statistics for n hosts
@Parameter:
  n: #host
  min_dest_num: #destinations each host has at least
  max_dest_num: #destinations each host has at most
  min_flow_num: #flows each pair has at least
  max_flow_num: #flows each pair has at most
  alpha: shape of the Pareto Distribution
  min_packet_num: #packets each flow has at least
@Return:
  dests: map between source and destinations
  flow_num: map between pairs and #flows
  packet_num: map between flows and #packets
@Todo:
  variable packet length
'''
def generate(n, min_dest_num, max_dest_num, min_flow_num, max_flow_num, alpha, min_packet_num):
    dests = dict()
    flow_num = dict()
    packet_num = dict()

    for s in range(n):
        # determine #destinations
        dest_num = randint(min_dest_num, max_dest_num)
        dests[s] = sorted(sample(list(range(s)) + list(range(s + 1, n)), dest_num))

        # determine #flows
        for d in dests[s]:
            flow_num[(s, d)] = randint(min_flow_num, max_flow_num)
            for f in range(flow_num[(s, d)]):
                packet_num[(s, d, f)] = math.floor(np.random.pareto(alpha, 1) + min_packet_num)

    return dests, flow_num, packet_num


'''
@Function:
  Arrange time slots for all packets generated before
@Parameter:
  flow_num: map between pairs and #flows
  packet_num: map between flows and #packets
  min_start_time: lower bound for first flow start time
  max_start_time: upper bound for first flow start time
  min_interval: lower bound for interval between flows
  max_interval: upper bound for interval between flows
@Return:
  source_timing: map between packets and timestamp buffering 
@Todo:
  Various timing manners 
'''
def timing(flow_num, packet_num, min_start_time, max_start_time, min_interval, max_interval):
    source_timing = dict()
    for host_key, f_num in flow_num.items():
        s, d = host_key
        start_time = randint(min_start_time, max_start_time)
        for f_id in range(f_num):
            for p_id in range(packet_num[(s, d, f_id)]):
                packet_key = (s, d, f_id, p_id)
                source_timing[packet_key] = start_time
            start_time += randint(min_interval, max_interval)
    return source_timing


def display(n, dests, flow_num, packet_num, source_timing):
    print("Assign flows to pairs...")
    for s in range(n):
        for d in dests[s]:
            print("Assign flows from host %d to host %d" % (s, d))
            for f in range(flow_num[(s, d)]):
                print("flow %d, %d packets, buffered at %d slot" % (f, packet_num[(s, d, f)], source_timing[(s, d, f, 0)]))

