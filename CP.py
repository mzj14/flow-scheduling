#! /usr/bin/env python3


from constraint import *

def solve_CP(n, m, dests, flow_num, packet_num, router_path, egress_port, source_timing, solution_upper_bound):

    CP = Problem()

    sender_timing_vs = []
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    sender_timing_vs.append("sender_timing[(%d, %d, %d, %d)]" % (s, d, f, p))
    CP.addVariables(sender_timing_vs, range(solution_upper_bound))

    router_timing_vs = []
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    for r in router_path[(s, d, f)]:
                        e = egress_port[(s, d, f, r)]
                        router_timing_vs.append("router_timing[(%d, %d, %d, %d, %d, %d)]" % (s, d, f, p, r, e))
    CP.addVariables(router_timing_vs, range(solution_upper_bound))

    # Constraint I: each packet must be send out of the source after entering the source buffer

    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    v1 = "sender_timing[(%d, %d, %d, %d)]" % (s, d, f, p)
                    CP.addConstraint(lambda x1: source_timing[(s, d, f, p)] <= x1, (v1,))

    # Constraint II: no two packets from the same host should be send out at the same time

    for s in range(n):
        combs = [(d, f, p) for d in dests[s] for f in range(flow_num[(s, d)]) for p in range(packet_num[(s, d, f)])]
        for comb1 in combs:
            for comb2 in combs:
                if comb1 != comb2:
                    d1, f1, p1 = comb1
                    d2, f2, p2 = comb2
                    v1 = "sender_timing[(%d, %d, %d, %d)]" % (s, d1, f1, p1)
                    v2 = "sender_timing[(%d, %d, %d, %d)]" % (s, d2, f2, p2)
                    CP.addConstraint(lambda x1, x2: x1 != x2, (v1, v2))

    # Constraint III: the time of a packet dequeued from a former router egress port must be earlier than from a latter router egress port

    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    router_id_2 = router_path[(s, d, f)][0]
                    egress_port_id_2 = egress_port[(s, d, f, router_id_2)]
                    v1 = "sender_timing[(%d, %d, %d, %d)]" % (s, d, f, p)
                    v2 = "router_timing[(%d, %d, %d, %d, %d, %d)]" % (s, d, f, p, router_id_2, egress_port_id_2)
                    CP.addConstraint(lambda x1, x2: x1 + 1 <= x2, (v1, v2))
                    for r in range(len(router_path[(s, d, f)]) - 1):
                        router_id_1 = router_path[(s, d, f)][r]
                        router_id_2 = router_path[(s, d, f)][r + 1]
                        egress_port_id_1 = egress_port[(s, d, f, router_id_1)]
                        egress_port_id_2 = egress_port[(s, d, f, router_id_2)]
                        v1 = "router_timing[(%d, %d, %d, %d, %d, %d)]" % (s, d, f, p, router_id_1, egress_port_id_1)
                        v2 = "router_timing[(%d, %d, %d, %d, %d, %d)]" % (s, d, f, p, router_id_2, egress_port_id_2)
                        CP.addConstraint(lambda x1, x2: x1 + 1 <= x2, (v1, v2))

    # Constraint IV: the time of a router dequeues a former packet of a flow must be earlier than dequeuing a latter packet of this flow

    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for r in router_path[(s, d, f)]:
                    egress_port_id = egress_port[(s, d, f, r)]
                    for p in range(packet_num[(s, d, f)] - 1):
                        v1 = "router_timing[(%d, %d, %d, %d, %d, %d)]" % (s, d, f, p, r, egress_port_id)
                        v2 = "router_timing[(%d, %d, %d, %d, %d, %d)]" % (s, d, f, p + 1, r, egress_port_id)
                        CP.addConstraint(lambda x1, x2: x1 + 1 <= x2, (v1, v2))

    # Constraint V: no two packets from different flows sharing the same egress port of a router should have the same egress timing

    combs = [(s, d, f) for s in range(n) for d in dests[s] for f in range(flow_num[(s, d)])]

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
                            v1 = "router_timing[(%d, %d, %d, %d, %d, %d)]" % (s1, d1, f1, p1, r, e)
                            v2 = "router_timing[(%d, %d, %d, %d, %d, %d)]" % (s2, d2, f2, p2, r, e)
                            CP.addConstraint(lambda x1, x2: x1 != x2, (v1, v2))

    # set optimization problem as minimizing FCT

    total_FCT = 0
    print("Start getting solution...")
    solutions = CP.getSolution()
    print("Find solution!")

    for solution in solutions:
        for s in range(n):
            for d in dests[s]:
                for f in range(flow_num[(s, d)]):
                    end_router = router_path[(s, d, f)][-1]
                    end_port = egress_port[(s, d, f, end_router)]
                    end_packet = len(packet_num[(s, d, f)]) - 1
                    v1 = "router_timing[(%d, %d, %d, %d, %d, %d)]" % (s, d, f, end_packet, end_router, end_port)
                    v2 = "source_timing[(%d, %d, %d, %d)]" % (s, d, f, 0)
                    total_FCT += solution[v1] - solution[v2] + 1
        solution['total_FCT'] = total_FCT

    solutions.sort(key=lambda dic: dic['total_FCT'])

    min_total_FCT = solutions[0]['total_FCT']
    router_timings, sender_timings = list(), list
    for solution in solutions:
        if solution['total_FCT'] > min_total_FCT:
            break
        else:
            router_timing, sender_timing = format_solution(solution)
            router_timings.append(router_timing)
            sender_timings.append(sender_timing)

    return min_total_FCT, router_timings, sender_timings


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
