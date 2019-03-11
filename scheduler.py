#! /usr/bin/env python3

import CP
import LP

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

    for path_solution in path_solutions:
        router_path = dict()
        egress_port = dict()
        for s, d, f, rc in path_solution:
            router_path[(s, d, f)] = []
            for router_id, egress_port_id in rc:
                router_path[(s, d, f)].append(router_id)
                egress_port[(s, d, f, router_id)] = egress_port_id

        display_path_solution(n, dests, flow_num, router_path, egress_port)

        total_FCT, router_timing, sender_timing = LP.solve_LP(n, m, dests, flow_num, packet_num, router_path, egress_port,
                                                           source_timing)

        display_optimal_scheduling(total_FCT, n, m, dests, port_num, flow_num, packet_num, router_path, egress_port,
                                   router_timing, sender_timing)

        # LP.solve_LP(n, m, dests, flow_num, packet_num, router_path, egress_port, source_timing)

        '''
        if total_FCT < best_FCT:
            best_FCT, best_router_timings, best_router_path, best_egress_port, best_sender_timings = total_FCT, router_timing, router_path, egress_port, best_sender_timing
        '''

    # resolve the router_prefer from best_router_timing, best_router_path, best_egress_port
    '''
    router_prefers = list()
    for best_router_timing in best_router_timings:
        router_prefer = dict()
        for s in range(n):
            for d in dests[s]:
                for f in range(flow_num[(s, d)]):
                    for r in best_router_path[(s, d, f)]:
                        egress_port_id = best_egress_port[(s, d, f, r)]
                        if (r, egress_port) not in router_prefer:
                            router_prefer[(r, egress_port_id)] = []
                        for p in range(packet_num[(s, d, f)]):
                            router_prefer[(r, egress_port_id)].append(
                                ((s, d, f, p), best_router_timing[(s, d, f, p, r, egress_port_id)]))
        for r in range(m):
            for e in port_num[r]:
                if (r, e) in router_prefer:
                    router_prefer[(r, e)].sort(key=lambda tu: tu[-1])
        router_prefers.append(router_prefer)


    # resolve the sender_prefer from the best_sender_timing
    sender_prefers = list()
    for best_sender_timing in best_sender_timings:
        sender_prefer = dict()
        for s in range(n):
            sender_prefer[s] = []
            for d in dests[s]:
                for f in range(flow_num[(s, d)]):
                    for p in range(packet_num[(s, d, f)]):
                        sender_prefer[s].append((d, f, p, best_sender_timing[(s, d, f, p)]))
            sender_prefer[s].sort(key=lambda tu: tu[-1])
        sender_prefers.append(sender_prefer)

    return router_prefers, sender_prefers
    '''

def display_path_solution(n, dests, flow_num, router_path, egress_port):
    print("Exploring the following path allocation...")
    for s in range(n):
        for d in dests[s]:
            for f in range(flow_num[(s, d)]):
                path = [(r, egress_port[(s, d, f, r)]) for r in router_path[(s, d, f)]]
                print("host %d to host %d, flow %d, path %s" % (s, d, f, ','.join(map(str, path))))


def display_optimal_scheduling(total_FCT, n, m, dests, port_num, flow_num, packet_num, router_path, egress_port, router_timing, sender_timing):
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
                    sender_prefer[s].append(((d, f, p), sender_timing[(s, d, f, p)]))
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
                            ((s, d, f, p), router_timing[(s, d, f, p, r, egress_port_id)]))
    for r in range(m):
        for e in range(port_num[r]):
            if (r, e) in router_prefer:
                router_prefer[(r, e)].sort(key=lambda tu: tu[-1])
                print("As for router %d egress port %d, dequeue in the following order:" % (r, e))
                print('->'.join(map(str, router_prefer[(r, e)])))
