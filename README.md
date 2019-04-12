# flow-scheduling
Centralized flow scheduling design

## Modules
* `flow-scheduling-pseudo.py`: pseudo code for mathematical model
* `toplology.py`: generate two-layer leaf-spine network fabric
* `flows.py`: allocate flows to source and destination, as well as timestamps to each packet
* `scheduler.py`: solve flow scheduling problem based on different allocated paths
* `or_tool.py`: solve constraint programming problem using google or_tool
* `flow-scheduling-example.py`: test code on tiny network scale
* `checker.py`: distributed scheduling decision as comparision to centralized flow scheduling

## Run
```
python ./flow-scheduling-example.py
```

## Results
For example, see `results/study-case-1`:
* `cenario.txt`: statistics about network fabric and scheduled flows
* `queue-stats-tu.txt`: queues in each time slot based on priority flow scheduling with flow size
* `queue-stats-g`: queues in each time slot based on optimal global scheduling

## Todo
* Find sending and processing logic for network components to achieve global optimal.
* Test different optimization function 
