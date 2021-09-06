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
