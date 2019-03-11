#! /usr/bin/env python3

import heapq
from queue import Queue

'''
@Function:
  Provide sender and router solution given flow statistics based on greedy choices
@Parameters:
  n: #hosts in the network.
  m: #routers in the network.
  dests: map between source and destinations
  port_num: map between router and #port
  flow_num: map between pairs and #flows
  packet_num: map between flows and #packets
  router_choices: maps between pairs and paths
  source_timing: maps between packets and timestamps
@Return:
  total_FCT: sum of all flow completion time
'''

def distributed_policy(n, m, dests, port_num, flow_num, packet_num, router_path, egress_port, source_timing):
    time_slot = 0
    sender_buffer = list()
    total_FCT = 0

    total_count, finish_count = 0, 0
    for value in packet_num.values():
        total_count += value

    for s in range(n):
        sender_buffer.append(Queue())

    router_buffer = list()
    for r in range(m):
        router_buffer.append(list())
        for e in range(port_num[r]):
            router_buffer[r].append(list())
            heapq.heapify(router_buffer[r][e])

    fly_packets = dict()

    while finish_count < total_count:
        # routers insert items for next time slot
        for r in range(m):
            for e in range(port_num[r]):
                if (r, e) in fly_packets:
                    for fly_packet in fly_packets[(r, e)]:
                        heapq.heappush(router_buffer[r][e], fly_packet)
                    fly_packets.pop((r, e))

        # fly packets arrived end hosts
        for key, values in fly_packets.items():
            finish_count += len(values)
            for v in values:
                re_size, s, d, f, p, _ = v
                total_FCT += time_slot - source_timing[(s, d, f, p)]

        fly_packets = dict()

        for s in range(n):
            # check if there are new packets from the application layer need to enter buffer
            for d in dests[s]:
                for f in range(flow_num[(s, d)]):
                    for p in range(packet_num[s, d, f]):
                        if source_timing[(s, d, f, p)] == time_slot:
                            sender_buffer[s].put((packet_num[s, d, f], s, d, f, p, 0))
            # send packet to network every time slot
            # TODO: we current send packets to the network in a FIFO way. May be it is not optimal.
            if not sender_buffer[s].empty():
                fly_packet = sender_buffer[s].get()
                re_size, s, d, f, p, x = fly_packet
                if x < len(router_path[(s, d, f)]):
                    router_next = router_path[(s, d, f)][x]
                    egress_port_next = egress_port[(s, d, f, router_next)]
                else:
                    router_next = m + d
                    egress_port_next = 0
                if (router_next, egress_port_next) not in fly_packets:
                    fly_packets[(router_next, egress_port_next)] = list()
                fly_packets[(router_next, egress_port_next)].append((re_size, s, d, f, p, x + 1))

        # routers pop items for current slot
        for r in range(m):
            for e in range(port_num[r]):
                if router_buffer[r][e]:
                    fly_packet = heapq.heappop(router_buffer[r][e])
                    re_size, s, d, f, p, x = fly_packet
                    if x < len(router_path[(s, d, f)]):
                        router_next = router_path[(s, d, f)][x]
                        egress_port_next = egress_port[(s, d, f, router_next)]
                    else:
                        router_next = m + d
                        egress_port_next = 0
                    if (router_next, egress_port_next) not in fly_packets:
                        fly_packets[(router_next, egress_port_next)] = list()
                    fly_packets[(router_next, egress_port_next)].append((re_size, s, d, f, p, x + 1))

        time_slot += 1

    return total_FCT
