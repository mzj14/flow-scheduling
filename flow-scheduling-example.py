#! /usr/bin/env python3

import topology
import flows
import scheduler
import case_debugger


if __name__ == '__main__':
    # '''
    nh_per_rack, nr_l, nr_s = 2, 2, 1
    n, m, port_num, router_choices = topology.leaf_spine_net(nh_per_rack, nr_l, nr_s)
    min_dest_num, max_dest_num, min_flow_num, max_flow_num, alpha, min_packet_num = 1, n - 1, 1, 3, 1.2, 5
    dests, flow_num, packet_num = flows.generate(n, min_dest_num, max_dest_num, min_flow_num, max_flow_num,
                                                 alpha, min_packet_num)
    
    min_start_time, max_start_time, min_interval, max_interval = 0, 2, 1, 2
    source_timing = flows.timing(flow_num, packet_num, min_start_time, max_start_time, min_interval, max_interval)
    # '''

    '''
    flow_data_file = "backup/debug-case-2.txt"
    n, m, nh_per_rack, nr_l, nr_s, dests, port_num, router_choices, flow_num, packet_num, source_timing = case_debugger.readFromFile(flow_data_file)
    '''

    topology.display(n, m, nh_per_rack, nr_l, nr_s, port_num, router_choices)
    flows.display(n, dests, flow_num, packet_num, source_timing)

    scheduler.optimal_scheduling(n, m, dests, port_num, router_choices, flow_num, packet_num, source_timing)


