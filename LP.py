#! /usr/bin/env python3


from pulp import *

def solve_LP(n, m, dests, flow_num, packet_num, router_path, egress_port, source_timing, solution_upper_bound):

    LP = LpProblem("Linear Programming Problem", LpMinimize)

    # Constraint I: each packet must be send out of the source after entering the source buffer

    sender_timing = dict()
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    sender_timing[(s, d, f, p)] = LpVariable("sender_timing[(%d, %d, %d, %d)]" % (s, d, f, p),
                                                             source_timing[(s, d, f, p)], None, 'Continuous')

    router_timing = dict()
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    for r in router_path[(s, d, f)]:
                        e = egress_port[(s, d, f, r)]
                        router_timing[(s, d, f, p, r, e)] = LpVariable("router_timing[(%d, %d, %d, %d, %d, %d)]" % (s, d, f, p, r, e),
                                                                       0, None, 'Continuous')

    # Constraint II: no two packets from the same host should be send out at the same time

    sdiff = dict()
    for s in range(n):
        combs = [(d, f, p) for d in dests[s] for f in range(flow_num[(s, d)]) for p in range(packet_num[(s, d, f)])]
        for comb1 in combs:
            for comb2 in combs:
                if comb1 != comb2:
                    d1, f1, p1 = comb1
                    d2, f2, p2 = comb2
                    sdiff[(s, d1, f1, p1, d2, f2, p2)] = LpVariable("sdiff[(%d, %d, %d, %d, %d, %d, %d)]" % (s, d1, f1, p1, d2, f2, p2),
                                                                       0, 1, 'Integer')
                    LP += sender_timing[(s, d1, f1, p1)] - sender_timing[(s, d2, f2, p2)] <= -1 + 10E8 * sdiff[(s, d1, f1, p1, d2, f2, p2)]
                    LP += sender_timing[(s, d1, f1, p1)] - sender_timing[(s, d2, f2, p2)] >= 1 - 10E8 * (1 - sdiff[(s, d1, f1, p1, d2, f2, p2)])

    # Constraint III: the time of a packet dequeued from a former router egress port must be earlier than from a latter router egress port

    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    router_id_2 = router_path[(s, d, f)][0]
                    egress_port_id_2 = egress_port[(s, d, f, router_id_2)]
                    LP += sender_timing[(s, d, f, p)] + 1 <= router_timing[(s, d, f, p, router_id_2, egress_port_id_2)]
                    for r in range(len(router_path[(s, d, f)]) - 1):
                        router_id_1 = router_path[(s, d, f)][r]
                        router_id_2 = router_path[(s, d, f)][r + 1]
                        egress_port_id_1 = egress_port[(s, d, f, router_id_1)]
                        egress_port_id_2 = egress_port[(s, d, f, router_id_2)]
                        LP += router_timing[(s, d, f, p, router_id_1, egress_port_id_1)] + 1 <= router_timing[(s, d, f, p, router_id_2, egress_port_id_2)]

    # Constraint IV: the time of a router dequeues a former packet of a flow must be earlier than dequeuing a latter packet of this flow

    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for r in router_path[(s, d, f)]:
                    egress_port_id = egress_port[(s, d, f, r)]
                    for p in range(packet_num[(s, d, f)] - 1):
                        LP += router_timing[(s, d, f, p, r, egress_port_id)] + 1 <= router_timing[(s, d, f, p + 1, r, egress_port_id)]

    # Constraint V: no two packets from different flows sharing the same egress port of a router should have the same egress timing

    combs = [(s, d, f) for s in range(n) for d in dests[s] for f in range(flow_num[(s, d)])]

    ediff = dict()
    for r in range(m):
        for comb1 in combs:
            for comb2 in combs:
                s1, d1, f1 = comb1
                s2, d2, f2 = comb2
                if comb1 != comb2 and (s1, d1, f1, r) in egress_port and (s2, d2, f2, r) in egress_port and \
                        egress_port[(s1, d1, f1, r)] == egress_port[(s2, d2, f2, r)]:
                    e = egress_port[(s1, d1, f1, r)]
                    for p1 in range(packet_num[(s1, d1, f1)]):
                        for p2 in range(packet_num[(s2, d2, f2)]):
                            ediff[(s1, d1, f1, p1, s2, d2, f2, p2, r, e)] = LpVariable(
                                "ediff[(%d, %d, %d, %d, %d, %d, %d, %d, %d, %d)]" % (s1, d1, f1, p1, s2, d2, f2, p2, r, e), 0, 1, 'Integer')
                            LP += router_timing[(s1, d1, f1, p1, r, e)] - router_timing[(s2, d2, f2, p2, r, e)] <= -1 + 10E8 * ediff[(s1, d1, f1, p1, s2, d2, f2, p2, r, e)]
                            LP += router_timing[(s1, d1, f1, p1, r, e)] - router_timing[(s2, d2, f2, p2, r, e)] >= 1 - 10E8 * (1 - ediff[(s1, d1, f1, p1, s2, d2, f2, p2, r, e)])

    # set optimization problem as minimizing FCT

    fcts = list()
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                end_router = router_path[(s, d, f)][-1]
                end_port = egress_port[(s, d, f, end_router)]
                end_packet = packet_num[(s, d, f)] - 1
                fcts.append(
                    router_timing[(s, d, f, end_packet, end_router, end_port)] - source_timing[(s, d, f, 0)] + 1)

    LP += lpSum(fcts)

    LP.solve()

    print("status is %s" % LpStatus[LP.status])

    print("minimal avg FCT is %f" % value(LP.objective))

    '''
    for v in LP.variables():
        print("%s = %d", (v.name, v.varValue))
    '''

    # return min_total_FCT, router_timings, sender_timings


def format_solution(solution, n, m, dests, flow_num, packet_num, router_path, egress_port):
    sender_timing = dict()
    router_timing = dict()
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    v = "sender_timing[(%d, %d, %d, %d)]" % (s, d, f, p)
                    sender_timing[(s, d, f, p)] = solution[v]
                    for r in router_path[(s, d, f)]:
                        e = egress_port[(s, d, f, r)]
                        v = "router_timing[(%d, %d, %d, %d, %d, %d)]" % (s, d, f, p, r, e)
                        router_timing[(s, d, f, p, r, e)] = solution[v]
    return router_timing, sender_timing
