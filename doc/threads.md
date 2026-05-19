# Threads in this application

This program comprises multiple threads: 
1) A worker thread blocking if there is something in queue and then processing items on queue - always responsible for updating data object. If further actions need to be taken it may add items to the end of its queue 
2) A hardware polling thread which adds updates to worker queue
3) A `camonitor` thread which monitors block names and adds updates to queue
4) the p4p thread pool on PV puts which add PV updates to queue (and that's all - any logic needs to be done in the worker thread)
5) A thread calling PV posts that read from data class and updating PVs


An example when starting a run: 

1) Someone puts `1` to `BEGINRUNEX`. 
2) The p4p thread pool (4) puts an update on the worker queue. 
3) The worker thread (1) picks this up and then: 
   - Tries to write to the hardware
   - If successful, sends a run start to Kafka
   - If successful, sets dataclass run state to `RUNNING`

Meanwhile, the hardware polling thread (2) is continuously polling the hardware and pushing updates to the queue when it receives data. 

As well as this, the thread calling PV posts (5) updates PVs continuously (in this case the run state). 
Additionally, the thread monitoring blocks (3) adds another item to the queue, which the worker thread can act on (to set the blocks in the data class)

This explicitly requires locking at the UDP layer as there are two threads (the worker thread (1) and the polling thread (2)) that may do UDP communication.

Another example, when someone changes the run title:
1) Someone puts `blah` to `TITLE`
2) The p4p thread pool (4) puts an update on the worker queue. 
3) The worker thread (1) picks this up and then updates the data class and saves to the state file

