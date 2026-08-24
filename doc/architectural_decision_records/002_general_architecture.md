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

Additionally, the queue will be a two-level priority queue, so that events that need to be acted on quickly can get "bumped" up the queue. As an example, a user beginning a run should take precedence over a routine operation such as updating the readbacks from the hardware or list of blocks. In this case the run beginning is of high priority and the other tasks are of low priority.

## Consequences

- We will need to use thread-safe communication methods to the streaming control boards.
- A refactor will be needed, but it should de-tangle logic and make it easier to add features to `kdaectrl` in the future.
- We will be able to act on some types of actions quicker than others, but care needs to be taken to ensure that all actions aren't just treated as high priority. As well as this we need to ensure that low priority items being acted on less quickly won't cause any undesired behaviour.
