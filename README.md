# Exercises for Distributed Systems
This repository contains a small framework written in python for emulating *asynchronous* and *synchronous* distributed systems.

## General
Exercises will be described later in this document.

In general avoid changing any of the files in the `emulators` subdirectory.
Instead, restrict your implementation to extending `emulators.Device` and `emulators.MessageStub`.

Your implementation/solution for, for instance, exersice 1 should go into the `exercises/exercise1.py` document.
I will provide new templates as the course progresses.

You should be able to execute your solution to exercise 1 using the following lines:
```bash
python3.9 exercise_runner.py --lecture 1 --algorithm Gossip --type sync --devices 3
python3.9 exercise_runner.py --lecture 1 --algorithm Gossip --type async --devices 3
```

The first line will execute your implementation of the `Gossip` algorithm in a synchronous setting with three devices, 
while the second line will execute in an asynchronous setting.

For usage of the framework, see `exercises/demo.py` for a lightweight example.
The example can be run with:
```bash
python3.9 exercise_runner.py --lecture 0 --algorithm PingPong --type async --devices 3
```

## Pull Requests
If you have any extensions or improvements you are welcome to create a pull request.

However, pull requests should provide some *significant* improvement, changes in style, renaming of variables etc. 
is strongly discouraged: such changes would likely break the solutions of your fellow students.

# Exercise 1
Implement the following gossiping problem in `exercises/exercise1.py`.

A number of persons initially know one distinct secret each.

In each message, a person discloses all their secrets to the recipient.

These individuals can communicate only in pairs (no conference calls) but it is possible that different pairs of people talk concurrently. For all the tasks below you should consider the following two scenarios:

 - Scenario 1: a person may call any other person, thus the network is a total graph,
 - Scenario 2: the persons are organized in a bi-directional circle, where the each person can only pass messages to the left and the right (use the modulo operator).

In both scenarios you should use the `async` network, details of the differences between `sync` and `async` will be given in the third lecture.

Your tasks are as follows:

 - implement the above behaviour - however, with the freedom to pick which person to talk to, when to send a message, etc. 
 - Try to minimize the number of messages.
 - How few messages are enough?
 - Is your solution optimal? And in what sense?

### NOTICE:
You can have several copies of the `Gossip` class, just give the class another name in the `exercise1.py` document, for instance `ImprovedGossip`.
You should then be able to call the framework with your new class via:
```bash
python3.9 exercise_runner.py --lecture 1 --algorithm ImprovedGossip --type async --devices 3
```

# Exercise 2
1. Implement the RIP protocol (fill in missing code in merge_tables), described in \[DS, fifth edition\] Page 115-118.
2. In the `__init__` of `RipCommunication`, create a ring topology (that is, set up who are the neighbors of each device). Consider a ring size of 10 devices.
   1. How many messages are sent in total before the routing_tables of all nodes are synchronized?
   2. How can you "know" that the routing tables are complete and you can start using the network to route packets? Consider the general case of internet, and the specific case of our toy ring network. 
   3. For the ring network, consider an approach similar to
      1. ```python
         def routing_table_complete(self):
           if len(self.routing_table) < self.number_of_devices()-1:
               return False
           return True
         ```
         Does it work? Each routing table should believe it is completed just one. How many times the routing tables appear to be completed?
   4. Try this other approach, which works better:
      1. ```python
         def routing_table_complete(self):
           if len(self.routing_table) < self.number_of_devices()-1:
               return False
           for row in self.routing_table:
               (next_hop, distance) = self.routing_table[row]
               if distance > (self.number_of_devices()/2):
                   return False
              return True
         ```
    Is it realistic for a real network?
3. Send a `RoutableMessage` after the routing tables are ready. Consider the termination problem. Can a node quit right after receiving the `RoutingMessage` for itself? What happens to the rest of the nodes?
4. What happens, if a link has a negative cost? How many messages are sent before the `routing_tables` converge?

# Exercise 3
Please consult the moodle page, this exercise is not via this framework.

# Exercise 4
Look at `exercises/exercise4.py`, here you should find the `SuzukiKasami` class 
implementing Suzuki-Kasami’s Mutex Algorithm.

For all exercises today, you can use the `sync` network type - but most algorithms should work for `async` also.

1. Examine the algorithm 
    1. Make a doodle on the blackboard/paper showing a few processes, their state, and messages exchanged. Use e.g. a sequence diagram.
    2. Define the purpose of the vectors `_rn` and `_ln`.
2. Discuss the following situations
   1. Is it possible that a node receives a token request message after the corresponding request has been granted? Sketch a scenario.
   2. How can a node know which nodes have ungranted requests?
   3. How does the queue grow?

3. Characterize the algorithms performance and correctness:
   1. Is the algorithm correct? (ME1, ME2, ME3)
   2. How does it perform ? (bandwidth, enter/exit delay,throughput)
   3. How does it cope with failures? / How can it be made fault tolerant?

4. Bonus exercise, modifying the `TokenRing` class of `exercises/exercise4.py`:
   1. Implement heartbeats in the token-ring algorithm for failure detection,
   2. Make it robust against node-failiures, and
   3. Make it possible for new processes to join the ring.

5. Extracurricular exercise/challenge (only if you have nothing better to do over the weekend)
   1. Extend the mutex algorithm implementations s.t. the `do_work()` call starts an asynchronous process (e.g. a future) which later calls a `release()` method on the mutex classes.
   2. Check that the algorithms still work, and modify where needed.
   3. Submit a pull-request!