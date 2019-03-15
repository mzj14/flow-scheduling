#! /usr/bin/env python3

import heapq
from queue import Queue


def priority_field(s, d, f, p, flag, packet_num):
    if flag == 'total_size':
        return packet_num[(s, d, f)]
    elif flag == 'remain_size':
        return -p, packet_num[(s, d, f)] - p
    else:
        raise Exception("Unknown priority flag!")

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

def distributed_policy_with_total_size(n, m, dests, port_num, flow_num, packet_num, router_path, egress_port,
                       source_timing, uniform_flag):
    time_slot = 0
    sender_buffer = list()
    total_FCT = 0

    total_count, finish_count = 0, 0
    for value in packet_num.values():
        total_count += value

    for s in range(n):
        sender_buffer.append(list())
        if uniform_flag == 'Y':
            heapq.heapify(sender_buffer[s])

    router_buffer = list()
    for r in range(m):
        router_buffer.append(list())
        for e in range(port_num[r]):
            router_buffer[r].append(list())
            heapq.heapify(router_buffer[r][e])

    sender_timing_ans = dict()
    router_timing_ans = dict()
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
                if p == packet_num[(s, d, f)] - 1:
                    total_FCT += time_slot - source_timing[(s, d, f, p)]

        fly_packets = dict()

        for s in range(n):
            # check if there are new packets from the application layer need to enter buffer
            for d in dests[s]:
                for f in range(flow_num[(s, d)]):
                    for p in range(packet_num[s, d, f]):
                        if source_timing[(s, d, f, p)] == time_slot:
                            packet = (packet_num[(s, d, f)], s, d, f, p, 0)
                            if uniform_flag == 'Y':
                                heapq.heappush(sender_buffer[s], packet)
                            else:
                                sender_buffer[s].append(packet)
            # send packet to network every time slot
            if len(sender_buffer[s]) > 0:
                if uniform_flag == 'Y':
                    fly_packet = heapq.heappop(sender_buffer[s])
                else:
                    fly_packet = sender_buffer[s].pop(0)
                re_size, s, d, f, p, x = fly_packet
                sender_timing_ans[(s, d, f, p)] = time_slot
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
                    router_timing_ans[(s, d, f, p, r, e)] = time_slot
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

    return total_FCT, router_timing_ans, sender_timing_ans


def check_linear_constraint(n, m, dests, flow_num, packet_num, router_path, egress_port,
                            source_timing, router_timing, sender_timing):

    check_result = _check_linear_constraint(n, m, dests, flow_num, packet_num, router_path, egress_port,
                            source_timing, router_timing, sender_timing)

    if check_result:
        print("The following distributed solution satisfies the constraint...")
        print("The following distributed solution has total FCT %d" % check_result)
    else:
        print("The following distributed solution does not satisfy the constraint...")


def _check_linear_constraint(n, m, dests, flow_num, packet_num, router_path, egress_port,
                            source_timing, router_timing, sender_timing):

    # Check if constraint I holds
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    if sender_timing[(s, d, f, p)] < source_timing[(s, d, f, p)]:
                        print("Constraint I fails")
                        return False
                    if p < packet_num[(s, d, f)] - 1 and sender_timing[(s, d, f, p)] + 1 > sender_timing[(s, d, f, p + 1)]:
                        print("Constraint I fails")
                        return False

    # Check if constraint III holds
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    router_id_2 = router_path[(s, d, f)][0]
                    egress_port_id_2 = egress_port[(s, d, f, router_id_2)]
                    if sender_timing[(s, d, f, p)] + 1 > router_timing[(s, d, f, p, router_id_2, egress_port_id_2)]:
                        print("Constraint III fails")
                        return False
                    for r in range(len(router_path[(s, d, f)]) - 1):
                        router_id_1 = router_path[(s, d, f)][r]
                        router_id_2 = router_path[(s, d, f)][r + 1]
                        egress_port_id_1 = egress_port[(s, d, f, router_id_1)]
                        egress_port_id_2 = egress_port[(s, d, f, router_id_2)]
                        if router_timing[(s, d, f, p, router_id_1, egress_port_id_1)] + 1 > router_timing[(s, d, f, p, router_id_2, egress_port_id_2)]:
                            print("Constraint III fails")
                            return False

    # Check if constraint IV holds
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for r in router_path[(s, d, f)]:
                    egress_port_id = egress_port[(s, d, f, r)]
                    for p in range(packet_num[(s, d, f)] - 1):
                        if router_timing[(s, d, f, p, r, egress_port_id)] + 1 > router_timing[(s, d, f, p + 1, r, egress_port_id)]:
                            print("Constraint IV fails")
                            return False

    # Check if constraint V holds
    combs = [(s, d, f) for s in range(n) for d in dests[s] for f in range(flow_num[(s, d)])]
    for r in range(m):
        for i in range(len(combs)):
            for j in range(i + 1, len(combs)):
                s1, d1, f1 = combs[i]
                s2, d2, f2 = combs[j]
                if (s1, d1, f1, r) in egress_port and (s2, d2, f2, r) in egress_port and egress_port[(s1, d1, f1, r)] == egress_port[(s2, d2, f2, r)]:
                    e = egress_port[(s1, d1, f1, r)]
                    for p1 in range(packet_num[(s1, d1, f1)]):
                        for p2 in range(packet_num[(s2, d2, f2)]):
                            if router_timing[(s1, d1, f1, p1, r, e)] == router_timing[(s2, d2, f2, p2, r, e)]:
                                print("Constraint V fails")
                                return False

    # Check if constraint II holds
    for s in range(n):
        combs = [(d, f, p) for d in dests[s] for f in range(flow_num[(s, d)]) for p in range(packet_num[(s, d, f)])]
        for i in range(len(combs)):
            for j in range(i + 1, len(combs)):
                d1, f1, p1 = combs[i]
                d2, f2, p2 = combs[j]
                if sender_timing[(s, d1, f1, p1)] == sender_timing[(s, d2, f2, p2)]:
                    print("Constraint II fails")
                    return False

    # re-calculate the total FCT
    total_FCT = 0
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                end_router = router_path[(s, d, f)][-1]
                end_port = egress_port[(s, d, f, end_router)]
                # end_packet = packet_num[(s, d, f)] - 1
                end_t = max([router_timing[(s, d, f, end_packet, end_router, end_port)] for end_packet in range(packet_num[(s, d, f)])])
                total_FCT += end_t - source_timing[(s, d, f, 0)] + 1

    return total_FCT
