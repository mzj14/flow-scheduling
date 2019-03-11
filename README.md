# flow-scheduling
Centralized flow scheduling design

## Modules
* `flow-scheduling-pseudo.py`: pseudo code for mathematical model
* `toplology.py`: generate two-layer leaf-spine network fabric
* `flows.py`: allocate flows to source and destination, as well as timestamps to each packet
* `scheduler.py`: solve LP problem based on different paths
* `LP.py`: solve LP problem
* `flow-scheduling-example.py`: test for centralized flow scheduler

## Run
```
python ./flow-scheduling-example.py
```

## Todo
* Find sending and processing logic for network components to achieve global optimal.
* Test different optimization function 
