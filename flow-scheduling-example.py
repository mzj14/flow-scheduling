#! /usr/bin/env python3

import topology
import flows
import scheduler

if __name__ == '__main__':
    nh_per_rack, nr_l, nr_s = 3, 5, 3
    n, m, port_num, router_choices = topology.leaf_spine_net(nh_per_rack, nr_l, nr_s)

    min_dest_num, max_dest_num, min_flow_num, max_flow_num, alpha, min_packet_num = 0, n - 1, 0, 10, 1.2, 25
    dests, flow_num, packet_num = flows.generate(n, min_dest_num, max_dest_num, min_flow_num, max_flow_num,
                                                 alpha, min_packet_num)

    min_start_time, max_start_time, min_interval, max_interval = 0, 5, 2, 10
    source_timing = flows.timing(flow_num, packet_num, min_start_time, max_start_time, min_interval, max_interval)

    scaling_factor = 100
    solution_upper_bound = (max_start_time + max_interval * max_flow_num) * scaling_factor
    router_prefers, sender_prefers = scheduler.optimal_scheduling(n, m, dests, port_num, router_choices,
                                                      flow_num, packet_num, source_timing, solution_upper_bound)
    print(router_prefers, sender_prefers)

