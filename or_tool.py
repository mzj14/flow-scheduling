#! /usr/bin/env python3


from ortools.sat.python import cp_model


class SolutionPrinterWithLimit(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, limit):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__solution_limit = limit
        self.__solution_count = 0

    def on_solution_callback(self):
        print('Solution %i' % self.__solution_count)
        print('  objective value = %i' % self.ObjectiveValue())
        self.__solution_count += 1
        if self.__solution_limit >= self.ObjectiveValue():
            print("Find a good solution, stop search now!")
            self.StopSearch()

    def solution_count(self):
        return self.__solution_count

def solve_CP(n, m, dests, port_num, flow_num, packet_num, router_path, egress_port, source_timing, sender_upper_bound, router_upper_bound, FCT_upper_bound):

    model = cp_model.CpModel()

    sender_timing_vs = dict()
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    sender_timing_vs[(s, d, f, p)] = model.NewIntVar(source_timing[(s, d, f, p)], sender_upper_bound, "sender_timing[(%d, %d, %d, %d)]" % (s, d, f, p))

    router_timing_vs = dict()
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    for r in router_path[(s, d, f)]:
                        e = egress_port[(s, d, f, r)]
                        router_timing_vs[(s, d, f, p, r, e)] = model.NewIntVar(source_timing[(s, d, f, p)], router_upper_bound, "router_timing[(%d, %d, %d, %d, %d, %d)]" % (s, d, f, p, r, e))

    # Constraint I: the time of a host sends out a former packet of a flow must be earlier than sending out a latter packet of this flow

    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)] - 1):
                    model.Add(sender_timing_vs[(s, d, f, p)] + 1 <= sender_timing_vs[(s, d, f, p + 1)])

    # Constraint II: no two packets from the same host should be send out at the same time

    for s in range(n):
        combs = [sender_timing_vs[(s, d, f, p)] for d in dests[s] for f in range(flow_num[(s, d)]) for p in range(packet_num[(s, d, f)])]
        model.AddAllDifferent(combs)

    # Constraint III: the time of a packet dequeued from a former router egress port must be earlier than from a latter router egress port

    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    router_id_2 = router_path[(s, d, f)][0]
                    egress_port_id_2 = egress_port[(s, d, f, router_id_2)]
                    model.Add(sender_timing_vs[(s, d, f, p)] + 1 <= router_timing_vs[(s, d, f, p, router_id_2, egress_port_id_2)])
                    for r in range(len(router_path[(s, d, f)]) - 1):
                        router_id_1 = router_path[(s, d, f)][r]
                        router_id_2 = router_path[(s, d, f)][r + 1]
                        egress_port_id_1 = egress_port[(s, d, f, router_id_1)]
                        egress_port_id_2 = egress_port[(s, d, f, router_id_2)]
                        model.Add(router_timing_vs[(s, d, f, p, router_id_1, egress_port_id_1)] + 1 <= router_timing_vs[(s, d, f, p, router_id_2, egress_port_id_2)])

    # Constraint IV: the time of a router dequeues a former packet of a flow must be earlier than dequeuing a latter packet of this flow

    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for r in router_path[(s, d, f)]:
                    egress_port_id = egress_port[(s, d, f, r)]
                    for p in range(packet_num[(s, d, f)] - 1):
                        model.Add(router_timing_vs[(s, d, f, p, r, egress_port_id)] + 1 <= router_timing_vs[(s, d, f, p + 1, r, egress_port_id)])

    # Constraint V: no two packets from different flows sharing the same egress port of a router should have the same egress timing

    combs = [(s, d, f) for s in range(n) for d in dests[s] for f in range(flow_num[(s, d)])]
    for r in range(m):
        for e in range(port_num[r]):
            items = list()
            for comb in combs:
                s, d, f = comb
                if (s, d, f, r) in egress_port and egress_port[(s, d, f, r)] == e:
                    for p in range(packet_num[(s, d, f)]):
                        items.append(router_timing_vs[(s, d, f, p, r, e)])
            model.AddAllDifferent(items)

    # set optimization problem as minimizing FCT

    fcts = list()
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                end_router = router_path[(s, d, f)][-1]
                end_port = egress_port[(s, d, f, end_router)]
                end_packet = packet_num[(s, d, f)] - 1
                fcts.append(
                    router_timing_vs[(s, d, f, end_packet, end_router, end_port)] - source_timing[(s, d, f, 0)] + 1)

    model.Minimize(sum(fcts))

    print("Start getting solution...")
    solver = cp_model.CpSolver()
    solution_printer = SolutionPrinterWithLimit(0)
    status = solver.SolveWithSolutionCallback(model, solution_printer)
    print("Find solution!")
    print('Status = %s' % solver.StatusName(status))
    print('Number of solutions found: %i' % solution_printer.solution_count())

    if status == cp_model.OPTIMAL:
        total_FCT = solver.ObjectiveValue()
        router_timing, sender_timing = format_solution(solver, sender_timing_vs, router_timing_vs, n, dests, flow_num, packet_num, router_path, egress_port)
        return total_FCT, router_timing, sender_timing
    else:
        raise Exception("Can not find optimal value")


def format_solution(solver, sender_timing_vs, router_timing_vs, n, dests, flow_num, packet_num, router_path, egress_port):
    sender_timing = dict()
    router_timing = dict()
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    sender_timing[(s, d, f, p)] = solver.Value(sender_timing_vs[(s, d, f, p)])
                    for r in router_path[(s, d, f)]:
                        e = egress_port[(s, d, f, r)]
                        router_timing[(s, d, f, p, r, e)] = solver.Value(router_timing_vs[(s, d, f, p, r, e)])
    return router_timing, sender_timing
