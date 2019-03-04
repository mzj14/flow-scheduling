'''
Assume:
1. All links are 10Gps Ethernet
2. All packets are in same size, i.e. 1MTU = 1500 bytes
3. A time slot is 1500 * 8 / 10G = 12us
4. Load balancing will not happen within a flow. Each packet of the same flow takes the same routing path.
5. Each egress port only has 1 queue, whose capacity is infinite.
6. Every end host has to be synchronized with the controller in respect of the time

Input (Remote controller collects this statistics in a period of T):
1. n: number of hosts in the network. Host ids begin from 0.
2. m: number of routers in the network. Router ids begin from 0.
3. dests[s]: list of destination ids related to source s.
4. port_num[r]: number of egress ports on router r.
4. flow_num[s][d]: number of flows from source s to destination d. Flow ids begins from 0.
5. packet_num[s][d][f]: number of packets of flow f from source s to destination d. Packet ids begins from 0.
6. router_choices[s][d][f]: list of list of (router id, egress port id) possibly traversed by flow f from s to d.
7. source_timing[s][d][f][p]: time slot id when packet p in flow f from s to d appeared in the source sending buffer.

Goal: minimize avg flow completion time
# Here, the flow completion time is the duration between the time when the first packet sent out to the network and the time
# when the last packet enter the host buffer

Output:
router_prefer[r][e]: a list of (s, d, f, p) indicating the processing order of each egress port e at router r
send_timing[s][d][f][p]: time slot id when packet p in flow f from s to d is sent out from the source.

Intermediate variables:
1. router_path[s][d][f]: list of router ids that actually traversed by flow f from s to d
2. egress_port[s][d][f][r]: the egress port id of flow f from sender s to destination d at router r. Egress port ids start from 0.
3. router_timing[s][d][f][p][r][e]: time slot when the egress port e of router r dequeue packet p in flow f from sender s to destination d.

Function:
def solve_LP(n, m, dests, flow_num, packet_num, router_path, egress_port, source_timing):

    LP = set() # a set of inequality in linear programming

    # each packet must be send out of the source after entering the source buffer

    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[s][d]):
                LP += source_timing[s][d][f][p] <= send_timing[s][d][f][p]

    # the time of a packet dequeued from a former router egress port must be earlier than from a latter router egress port

    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[s][d]):
                for p in range(packet_num[s][d][f]):
                    router_id_2 = router_path[s][d][f][0]
                    egress_port_id_2 = egress_port[s][d][f][0]
                    LP += send_timing[s][d][f][p] + 1 <= router_timing[s][d][f][p][router_id_2][egress_port_id_2]
                    for r in range(len(router_path[s][d][f]) - 1):
                        router_id_1 = router_path[s][d][f][r]
                        router_id_2 = router_path[s][d][f][r + 1]
                        egress_port_id_1 = egress_port[s][d][f][router_id_1]
                        egress_port_id_2 = egress_port[s][d][f][router_id_2]
                        LP += router_timing[s][d][f][p][router_id_1][egress_port_id_1] + 1 <= router_timing[s][d][f][p][router_id_2][egress_port_id_2]


    # the time of a router dequeues a former packet of a flow must be earlier than dequeuing a latter packet of this flow

    for s in range(n):
        for d in dests[n]:
            for f in range(flow_num[s][d]):
                for r in router_path[s][d][f]:
                    egress_port_id = egress_port[s][d][f][r]
                    for p in range(len(packet_num[s][d][f]) - 1):
                        LP += router_timing[s][d][f][p][r][egress_port_id] + 1 <= router_timing[s][d][f][p + 1][r][egress_port_id]

    # no two packets from different flows sharing the same egress port of a router should have the same egress timing

    combs = [[s] + [d] for s in range(n) for d in dests[s] for f in range(flow_num[s][d])]

    for r in range(m)：
        for comb1 in combs:
            for comb2 in combs:
                s1, d1, f1 = comb1
                s2, d2, f2 = comb2
                if (comb1 != comb2 and egress_port[s1][d1][f1][r] == egress_port[s2][d2][f2][r])
                    e = egress_port[s1][d1][f1][r]
                    for p1 in packet_num[s1][d1][f1]:
                        for p2 in packet_num[s2][d2][f2]:
                            LP += router_timing[s1][d1][f1][p1][r][e] != router_timing[s2][d2][f2][p2][r][e]

    # set optimization problem as minimizing FCT

    total_FCT = 0
    for s in range(n):
        for d in range(n):
           for f in range(flow_num[s][d]):
               end_router = router_path[s][d][f][-1]
               e = egress_port[s][d][f][end_router]
               end_packet = len(packet_num[s][d][f]) - 1
               total_FCT += router_timing[s][d][f][end_packet][end_router][e] + 1 # 1 stands for 1 time slot for last hop to destination

    target = min(total_FCT)

    solve_linear_programming(LP, target)

    return min_total_FCT, router_timing, send_timing

Algorithm:

combs = [[s] + [d] + [f] for s in range(n) for d in dests[s] for f in range(flow_num[s][d])]

path_solutions = [[]]
for comb in combs:
    s, d, f = comb
    path_solutions = [path_solution + [(s, d, f, rc)] for path_solution in path_solutions for rc in router_choices[s][d][f]]

best_FCT, best_router_timing, best_router_path, best_egress_port, best_send_timing = +infinity, None, None, None, None

for path_solution in path_solutions:
    for s, d, f, rc in path_solution:
        for router_id, egress_port_id in rc:
            router_path[s][d][f] += [router_id]
            egress_port[s][d][f][router_id] = egress_port_id
    total_FCT, router_timing, send_timing = solve_LP(n, m, dests, flow_num, packet_num, router_path, egress_port, source_timing)
    if total_FCT < best_FCT:
        best_router_timing, best_router_path, best_egress_port, best_send_timing = router_timing, router_path, egress_port, best_send_timing

# resolve the router_prefer from best_router_path

for s in range(n):
    for d in dests[n]:
        for f in range(flow_num[s][d]):
            for r in router_path[s][d][f]:
                egress_port_id = best_egress_port[s][d][f][r]
                for p in range(packet_num[s][d][f]):
                router_prefer[r][egress_port_id].append(((s, d, f, p), best_router_timing[s][d][f][p][r][egress_port_id]))

for r in range(m):
    for e in port_num[r]:
        router_prefer[r][e].sort(key = lambada tu: tu[-1])
        router_prefer = [rp[0][:-1] for rp in router_prefer[r][e]]


# inform each router r with router_prefer[r][port_num[r]]
# inform each source s with send_timing[s]
'''
