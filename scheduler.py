#! /usr/bin/env python3

import LP
import checker

'''
@Function:
  Provide optimal sender and router solution given flow statistics
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
  None
'''
def optimal_scheduling(n, m, dests, port_num, router_choices, flow_num, packet_num, source_timing):
    path_solutions = [[]]
    for comb in packet_num.keys():
        s, d, f = comb
        path_solutions = [path_solution + [(s, d, f, rc)] for path_solution in path_solutions
                          for rc in router_choices[(s, d)]]

    # Find best scheduling solution by solving LP problem
    # best_FCT, best_router_timings, best_router_path, best_egress_port, best_sender_timings = 10E8, None, None, None, None

    print("Total %d path allocations" % len(path_solutions))

    for path_solution in path_solutions[:1]:
        router_path = dict()
        egress_port = dict()
        for s, d, f, rc in path_solution:
            router_path[(s, d, f)] = []
            for router_id, egress_port_id in rc:
                router_path[(s, d, f)].append(router_id)
                egress_port[(s, d, f, router_id)] = egress_port_id

        display_path_solution(n, dests, flow_num, router_path, egress_port)

        '''
        total_FCT, router_timing, sender_timing = LP.solve_LP_by_pulp(n, m, dests, flow_num, packet_num, router_path,
                                                                        egress_port,
                                                                        source_timing)
        
        print("--------------- Global optimized solution by pulp---------------------")
        checker.check_linear_constraint(n, m, dests, flow_num, packet_num, router_path, egress_port, source_timing, router_timing, sender_timing)
        display_optimal_scheduling(total_FCT, n, m, dests, port_num, flow_num, packet_num, router_path, egress_port,
                                   source_timing,
                                   router_timing, sender_timing)
        '''

        total_FCT, router_timing, sender_timing = checker.distributed_policy_with_total_size(n, m, dests, port_num, flow_num, packet_num,
                                                                             router_path, egress_port, source_timing, "Y")

        print("--------------- Distributed optimized solution based on total_size with uniform action ---------------------")
        checker.check_linear_constraint(n, m, dests, flow_num, packet_num, router_path, egress_port, source_timing, router_timing, sender_timing)
        display_optimal_scheduling(total_FCT, n, m, dests, port_num, flow_num, packet_num, router_path, egress_port,
                                   source_timing, router_timing, sender_timing)

        total_FCT, router_timing, sender_timing = checker.distributed_policy_with_total_size(n, m, dests, port_num, flow_num, packet_num, router_path, egress_port, source_timing, "N")

        print("--------------- Distributed optimized solution based on total_size with conflict action ---------------------")
        checker.check_linear_constraint(n, m, dests, flow_num, packet_num, router_path, egress_port, source_timing, router_timing, sender_timing)
        display_optimal_scheduling(total_FCT, n, m, dests, port_num, flow_num, packet_num, router_path, egress_port,
                                   source_timing, router_timing, sender_timing)

        total_FCT, router_timing, sender_timing = LP.solve_LP_by_gurobi(n, m, dests, flow_num, packet_num, router_path,
                                                                        egress_port,
                                                                        source_timing)

        print("--------------- Global optimized solution by gurobi---------------------")
        checker.check_linear_constraint(n, m, dests, flow_num, packet_num, router_path, egress_port, source_timing,
                                        router_timing, sender_timing)
        display_optimal_scheduling(total_FCT, n, m, dests, port_num, flow_num, packet_num, router_path, egress_port,
                                   source_timing,
                                   router_timing, sender_timing)

def display_path_solution(n, dests, flow_num, router_path, egress_port):
    print("Exploring the following path allocation...")
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                path = [(r, egress_port[(s, d, f, r)]) for r in router_path[(s, d, f)]]
                print("host %d to host %d, flow %d, path %s" % (s, d, f, ','.join(map(str, path))))


def display_optimal_scheduling(total_FCT, n, m, dests, port_num, flow_num, packet_num, router_path, egress_port, source_timing, router_timing, sender_timing):
    print("Find optimal solution as follows...")

    if total_FCT is None:
        print("No feasible solution under this path allocation.")
        return

    print("total_FCT is %d" % total_FCT)

    sender_prefer = dict()
    for s in range(n):
        sender_prefer[s] = []
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for p in range(packet_num[(s, d, f)]):
                    sender_prefer[s].append(((s, d, f, p), int(sender_timing[(s, d, f, p)])))
        sender_prefer[s].sort(key=lambda tu: tu[-1])
        print("As for host %d, send in the following order" % s)
        print('->'.join(map(str, sender_prefer[s])))

    router_prefer = dict()
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                for r in router_path[(s, d, f)]:
                    egress_port_id = egress_port[(s, d, f, r)]
                    if (r, egress_port_id) not in router_prefer:
                        router_prefer[(r, egress_port_id)] = []
                    for p in range(packet_num[(s, d, f)]):
                        router_prefer[(r, egress_port_id)].append(
                            ((s, d, f, p), int(router_timing[(s, d, f, p, r, egress_port_id)])))
    for r in range(m):
        for e in range(port_num[r]):
            if (r, e) in router_prefer:
                router_prefer[(r, e)].sort(key=lambda tu: tu[-1])
                print("As for router %d egress port %d, dequeue in the following order:" % (r, e))
                print('->'.join(map(str, router_prefer[(r, e)])))

    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                end_packet = packet_num[(s, d, f)] - 1
                start_t = int(source_timing[(s, d, f, 0)])
                end_router = router_path[(s, d, f)][-1]
                end_egress = egress_port[(s, d, f, end_router)]
                end_t = int(router_timing[(s, d, f, end_packet, end_router, end_egress)])
                print("As for flow (%d, %d, %d), first packet buffered at time slot %d, last packet reached receiver at \
                      time slot %d, fct is %d" % (s, d, f, start_t, end_t + 1, end_t + 1 - start_t))
