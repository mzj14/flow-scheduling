#! /usr/bin/env python3

'''
@Function:
  Get a leaf spine topology in a fully connected manner
@Parameter:
  nh_per_rack: int, #host per rack
  nr_l: int, #router in the leaf layer
  nr_s: int, #routers in the spine layer
@Return:
  n: #host
  m: #routers
  port_num: map between router id and #port
  router_choices: map between source-destination pair and list of routing path
@Todo:
  Expand to an arbitrary connected manner
  Variable link bandwidth
'''

import math


def leaf_spine_net(nh_per_rack, nr_l, nr_s):
    n = nh_per_rack * nr_l
    m = nr_l + nr_s
    port_num = dict()
    router_choices = dict()

    # set port for leaf router
    for r in range(nr_l):
        port_num[r] = nh_per_rack + nr_s
    # set port for spine router
    for r in range(nr_l, nr_l + nr_s):
        port_num[r] = nr_l

    # set router choices for hosts within rack
    for x in range(n):
        for y in range(x, n):
            router_choices[(x, y)] = []
            router_choices[(y, x)] = []
            x_r = math.floor(x / nh_per_rack)
            y_r = math.floor(y / nh_per_rack)
            x_e = x % nh_per_rack
            y_e = y % nh_per_rack
            if x_r == y_r:
                router_choices[(x, y)].append([(x_r, y_e)])
                router_choices[(y, x)].append([(y_r, x_e)])
            else:
                for r in range(nr_l, nr_l + nr_s):
                    e_1 = nh_per_rack + (r - nr_l)
                    e_2 = y_r
                    router_choices[(x, y)].append([(x_r, e_1), (r, e_2), (y_r, y_e)])
                    e_1 = nh_per_rack + (r - nr_l)
                    e_2 = x_r
                    router_choices[(y, x)].append([(y_r, e_1), (r, e_2), (x_r, x_e)])

    return n, m, port_num, router_choices


def display(n, m, nh_per_rack, nr_l, nr_s, port_num, router_choices):
    print("Create leaf-spine network...")
    print("Totally %d hosts" % n)
    print("%d hosts per rack" % nh_per_rack)
    print("Totally %d routers" % m)
    print("%d routers on leaf layer" % nr_l)
    print("%d routers on spine layer" % nr_s)

    for r in range(m):
        print("router %d uses %s ports" % (r, port_num[r]))
    for s in range(n):
        for d in range(n):
            if s != d:
                print("Available paths from host %d to host %d" % (s, d))
                for path in router_choices[(s, d)]:
                    print(','.join(map(str, path)))
