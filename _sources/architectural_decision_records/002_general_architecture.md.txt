# 2. General architecture

## Status

Current

## Context

This program was initially prototyped with an observable-callback pattern dealing with any change in state.
This approach tangled logic slightly as there are several areas where state can be changed - from hardware, from channel access (for example block values), and from PV access (for example a change of `TITLE`)

As an alternative to this there are some options: 
1) A threaded model with an event queue, where threads add "events" to the queue and a main worker thread acts on them
2) An asynchronous model with a queue as above

## Decision

We will develop this program so that it comprises an event queue which is added to by separate threads that poll hardware and respond to EPICS updates.
One worker thread will respond to these events by popping them off the queue, then mutate the state of the program.

An asynchronous approach seemed overkill for this task and added a layer of complexity, so a threaded model was chosen. 

## Consequences

- We will need to use thread-safe communication methods to the streaming control boards.
- A refactor will be needed, but it should de-tangle logic and make it easier to add features to `kdaectrl` in the future.