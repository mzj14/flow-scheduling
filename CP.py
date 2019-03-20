#! /usr/bin/env python3


from constraint import *

def solve_CP(n, m, dests, port_num, flow_num, packet_num, router_path, egress_port, source_timing, sender_upper_bound, router_upper_bound, FCT_upper_bound):

    CP = Problem()

    sender_timing_vs = []
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    sender_timing_vs.append("sender_timing[(%d, %d, %d, %d)]" % (s, d, f, p))
    CP.addVariables(sender_timing_vs, range(sender_upper_bound))

    router_timing_vs = []
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    for r in router_path[(s, d, f)]:
                        e = egress_port[(s, d, f, r)]
                        router_timing_vs.append("router_timing[(%d, %d, %d, %d, %d, %d)]" % (s, d, f, p, r, e))
    CP.addVariables(router_timing_vs, range(router_upper_bound))

    fct_vs = []
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                fct_vs.append("fct[(%d, %d, %d)]" % (s, d, f))
    CP.addVariables(fct_vs, range(router_upper_bound))

    # Constraint I: each packet must be send out of the source after entering the source buffer

    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    v1 = "sender_timing[(%d, %d, %d, %d)]" % (s, d, f, p)
                    CP.addConstraint(lambda x1: source_timing[(s, d, f, p)] <= x1, (v1,))

    # Constraint I: the time of a host sends out a former packet of a flow must be earlier than sending out a latter packet of this flow

    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)] - 1):
                    v1 = "sender_timing[(%d, %d, %d, %d)]" % (s, d, f, p)
                    v2 = "sender_timing[(%d, %d, %d, %d)]" % (s, d, f, p + 1)
                    CP.addConstraint(lambda x1, x2: x1 + 1 <= x2, (v1, v2))

    # Constraint II: no two packets from the same host should be send out at the same time

    for s in range(n):
        combs = ["sender_timing[(%d, %d, %d, %d)]" % (s, d, f, p) for d in dests[s] for f in range(flow_num[(s, d)]) for p in range(packet_num[(s, d, f)])]
        CP.addConstraint(AllDifferentConstraint(), combs)

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
        for e in range(port_num[r]):
            items = list()
            for comb in combs:
                s, d, f = comb
                if (s, d, f, r) in egress_port and egress_port[(s, d, f, r)] == e:
                    for p in range(packet_num[(s, d, f)]):
                        items.append("router_timing[(%d, %d, %d, %d, %d, %d)]" % (s, d, f, p, r, e))
            CP.addConstraint(AllDifferentConstraint(), items)

    # set total_FCT upper bound
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                end_router = router_path[(s, d, f)][-1]
                end_port = egress_port[(s, d, f, end_router)]
                end_packet = packet_num[(s, d, f)] - 1
                v1 = "router_timing[(%d, %d, %d, %d, %d, %d)]" % (s, d, f, end_packet, end_router, end_port)
                v2 = "fct[(%d, %d, %d)]" % (s, d, f)
                CP.addConstraint(lambda x1, x2: x2 == x1 - source_timing[(s, d, f, 0)] + 1, (v1, v2))

    CP.addConstraint(MaxSumConstraint(FCT_upper_bound), ["fct[(%d, %d, %d)]" % (s, d, f) for s, d, f in combs])

    # set optimization problem as minimizing FCT

    print("Start getting solution...")
    solution = CP.getSolution()
    print("Find solution!")

    total_FCT = 0
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                v3 = "fct[(%d, %d, %d)]" % (s, d, f)
                total_FCT += solution[v3]

    router_timing, sender_timing = format_solution(solution, n, dests, flow_num, packet_num, router_path, egress_port)

    return total_FCT, router_timing, sender_timing


def format_solution(solution, n, dests, flow_num, packet_num, router_path, egress_port):
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
