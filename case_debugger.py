#! /usr/bin/env python3

import parse
from topology import leaf_spine_net


def readFromFile(data_file):
    with open(data_file) as f:
        text = f.read()
    nh_per_rack_parser = parse.compile("{nh:d} hosts per rack")
    nr_l_parser = parse.compile("{nr_l:d} routers on leaf layer")
    nr_s_parser = parse.compile("{nr_s:d} routers on spine layer")
    nh_per_rack = nh_per_rack_parser.search(text)['nh']
    nr_l = nr_l_parser.search(text)['nr_l']
    nr_s = nr_s_parser.search(text)['nr_s']

    n, m, port_num, router_choices = leaf_spine_net(nh_per_rack, nr_l, nr_s)

    pair_parser = parse.compile("Assign {fn:d} flows from host {s:d} to host {d:d}")
    pairs = pair_parser.findall(text)
    packet_parser = parse.compile("flow {}, {pn:d} packets, buffered at {st:d} slot")
    packets = packet_parser.findall(text)

    dests = dict()
    flow_num = dict()
    packet_num = dict()
    source_timing = dict()
    for s in range(n):
        dests[s] = list()
    for pair in pairs:
        s, d, fn = pair['s'], pair['d'], pair['fn']
        print(s, d, fn)
        dests[s].append(d)
        flow_num[(s, d)] = fn
        for f in range(fn):
            packet = packets.next()
            pn, st = packet['pn'], packet['st']
            packet_num[(s, d, f)] = pn
            for p in range(pn):
                source_timing[(s, d, f, p)] = st

    return n, m, nh_per_rack, nr_l, nr_s, dests, port_num, router_choices, flow_num, packet_num, source_timing









