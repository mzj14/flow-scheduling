#! /usr/bin/env python3

from random import sample, randint
import numpy as np

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
  dests: maps between source and destinations
  flow_num: maps between pairs and #flows
  packet_num: maps between flows and #packets
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
            for f in flow_num[(s, d)]:
                packet_num[(s, d, f)] = np.random.pareto(alpha, 1) + min_packet_num

    return dests, flow_num, packet_num
