#! /usr/bin/env python3

import LP
import checker
import or_tool

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

        total_FCT_d_t_c, router_timing_d_t_c, max_router_timing_d_t_c, sender_timing_d_t_c, max_sender_timing_d_t_c = checker.distributed_policy_with_total_size(n, m, dests, port_num, flow_num, packet_num, router_path, egress_port, source_timing, "N")
        total_FCT_d_t_u, router_timing_d_t_u, max_router_timing_d_t_u, sender_timing_d_t_u, max_sender_timing_d_t_u = checker.distributed_policy_with_total_size(n, m, dests, port_num, flow_num, packet_num, router_path, egress_port, source_timing, "Y")
        total_FCT_d_r_c, router_timing_d_r_c, max_router_timing_d_r_c, sender_timing_d_r_c, max_sender_timing_d_r_c = checker.distributed_policy_with_remain_size(n, m, dests, port_num, flow_num, packet_num, router_path, egress_port, source_timing, "N")
        sender_upper_bound = max(max_sender_timing_d_t_c, max_sender_timing_d_t_u, max_sender_timing_d_r_c) * 2
        router_upper_bound = max(max_router_timing_d_t_c, max_router_timing_d_t_u, max_router_timing_d_r_c) * 2
        total_FCT_upper_bound = max(total_FCT_d_t_c, total_FCT_d_t_u, total_FCT_d_r_c)
        total_FCT_g, router_timing_g, sender_timing_g = or_tool.solve_CP(n, m, dests, port_num, flow_num, packet_num, router_path, egress_port, source_timing, sender_upper_bound, router_upper_bound, total_FCT_upper_bound)

        if total_FCT_g < min(total_FCT_d_t_c, total_FCT_d_t_u, total_FCT_d_r_c):
            print("--------------- Distributed optimized solution based on total_size with conflict action ---------------------")
            checker.check_linear_constraint(n, m, dests, flow_num, packet_num, router_path, egress_port, source_timing, router_timing_d_t_c, sender_timing_d_t_c)
            # display_optimal_scheduling(total_FCT_d_t_c, n, m, dests, port_num, flow_num, packet_num, router_path, egress_port, source_timing, router_timing_d_t_c, sender_timing_d_t_c)
            display_optimal_scheduling_by_queue_stats(total_FCT_d_t_c, n, m, dests, port_num, flow_num, packet_num, router_path, egress_port, source_timing, router_timing_d_t_c, sender_timing_d_t_c)
            print("--------------- Distributed optimized solution based on total_size with uniform action ---------------------")
            checker.check_linear_constraint(n, m, dests, flow_num, packet_num, router_path, egress_port, source_timing, router_timing_d_t_u, sender_timing_d_t_u)
            display_optimal_scheduling_by_queue_stats(total_FCT_d_t_u, n, m, dests, port_num, flow_num, packet_num, router_path, egress_port, source_timing, router_timing_d_t_u, sender_timing_d_t_u)
            print("--------------- Distributed optimized solution based on remain_size ---------------------")
            checker.check_linear_constraint(n, m, dests, flow_num, packet_num, router_path, egress_port, source_timing, router_timing_d_r_c, sender_timing_d_r_c)
            display_optimal_scheduling_by_queue_stats(total_FCT_d_r_c, n, m, dests, port_num, flow_num, packet_num, router_path, egress_port, source_timing, router_timing_d_r_c, sender_timing_d_r_c)
            print("--------------- Global optimized solution by constraint programming---------------------")
            checker.check_linear_constraint(n, m, dests, flow_num, packet_num, router_path, egress_port, source_timing, router_timing_g, sender_timing_g)
            display_optimal_scheduling_by_queue_stats(total_FCT_g, n, m, dests, port_num, flow_num, packet_num, router_path, egress_port, source_timing, router_timing_g, sender_timing_g)


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
                    if int(sender_timing[(s, d, f, p)]) != sender_timing[(s, d, f, p)]:
                        print("sender_timing[(%d, %d, %d, %d)] is fractional!!!" % (s, d, f, p))
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
                        if int(router_timing[(s, d, f, p, r, egress_port_id)]) != router_timing[(s, d, f, p, r, egress_port_id)]:
                            print("sender_timing[(%d, %d, %d, %d, %d, %d)] is fractional!!!" % (s, d, f, p, r, egress_port_id))
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
                end_t = router_timing[(s, d, f, end_packet, end_router, end_egress)]
                print("As for flow (%d, %d, %d), first packet buffered at time slot %d, last packet reached receiver at \
                      time slot %d, fct is %d" % (s, d, f, start_t, end_t + 1, end_t + 1 - start_t))


def display_optimal_scheduling_by_queue_stats(total_FCT, n, m, dests, port_num, flow_num, packet_num, router_path, egress_port, source_timing, router_timing, sender_timing):
    schedule_duration = max(router_timing.values()) + 1

    # initialize queue stats
    queue_stats = dict()
    dequeue_items = dict()
    for s in range(n):
        queue_stats[s] = list()
        dequeue_items[s] = None
    for r in range(m):
        for e in range(port_num[r]):
            queue_stats[(r, e)] = list()
            dequeue_items[(r, e)] = None

    # update queue stats every time slot
    for time_slot_id in range(schedule_duration):
        print("################### time_slot %d ###################" % time_slot_id)
        # dequeue packet from host
        for h in range(n):
            if dequeue_items[h] is not None:
                queue_stats[h].remove(dequeue_items[h])
                s, d, f, p = dequeue_items[h]
                r = router_path[(s, d, f)][0]
                e = egress_port[(s, d, f, r)]
                queue_stats[(r, e)].append((s, d, f, p))
                dequeue_items[h] = None

        # add new packet to host queue and decide dequeue item
        for s in range(n):
            for d in dests[s]:
                for f in range(flow_num[(s, d)]):
                    for p in range(packet_num[(s, d, f)]):
                        if source_timing[(s, d, f, p)] == time_slot_id:
                            queue_stats[s].append((s, d, f, p))
                        if sender_timing[(s, d, f, p)] == time_slot_id:
                            dequeue_items[s] = (s, d, f, p)

        # dequeue packet from router
        for r in range(m):
            for e in range(port_num[r]):
                if dequeue_items[(r, e)] is not None:
                    queue_stats[(r, e)].remove(dequeue_items[(r, e)])
                    s, d, f, p = dequeue_items[(r, e)]
                    r_index = router_path[(s, d, f)].index(r)
                    if r_index < len(router_path[(s, d, f)]) - 1:
                        r_next = router_path[(s, d, f)][r_index + 1]
                        e_next = egress_port[(s, d, f, r_next)]
                        queue_stats[(r_next, e_next)].append((s, d, f, p))
                    dequeue_items[(r, e)] = None

        # decide dequeue item of router queue
        for r in range(m):
            for e in range(port_num[r]):
                for s, d, f, p in queue_stats[(r, e)]:
                    if router_timing[(s, d, f, p, r, e)] == time_slot_id:
                        dequeue_items[(r, e)] = (s, d, f, p)

        # display queue stats in current time slot
        for s in range(n):
            print("As for host %d, packets in queue are: %s" % (s, ' '.join(map(str, sorted(queue_stats[s])))))
            print("decide to dequeue", dequeue_items[s])

        for r in range(m):
            for e in range(port_num[r]):
                print("As for router %d, egress port %d, packets in queue are: %s" % (r, e, ' '.join(map(str, sorted(queue_stats[(r, e)])))))
                print("decide to dequeue", dequeue_items[(r, e)])
