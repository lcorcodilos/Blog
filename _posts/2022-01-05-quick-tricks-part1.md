---
layout: post
title: "Quick Tricks: Part 1"
comments: false
description: "Some python tricks I've learned to improve my code."
keywords: "python"
---

In working on a project involving NASA publication data, I needed a few 
computing solutions that turn out to be generally useful. I'm describing them 
here along with the code that implements the solutions.

---

## Chunky file streaming

Because I wanted to use parallel processing to transform data into the format I wanted,
I needed a way to read chunks of the file for each process without having to open the file
once per process (the file was ~1.4 GB and so I'd need 14 GB of RAM for 10 processes - possible
but inefficient).

In addition, I didn't even want to have 1.4 GB of RAM consumed by the JSON - I just wanted to yield
one line at a time (one JSON-encoded dict), process it, and drop it as the next one is loaded.

The JSON file to stream is a list of entries with each entry being its own line
(and the first line being useless). So to accomplish the first goal, the function below takes in the `start` and `stop` line
numbers to stream (`stop` being exclusive). The function will first skip to the start via `next(f)`
applied `start` times. It will then loop `stop-start` times, progressing to each next line via `next(f)`.

To accomplish the second goal, the function `yield`s the line as a python dictionary for reading by other parts of the code.
Then a simple `for` loop can be built via
```python
for entry in read_bulk_file_chunk(start,stop):
    ...do stuff...
```

Here is the function:

```python
def read_bulk_file_chunk(start=0, stop=NFILES_IN_BULK):
    with open(BULK_FILE_STR, 'r') as f:
        # Move carriage to start
        for _ in range(start):
            next(f)

        for _ in range(stop-start):
            line = next(f)
            if line.strip() in ['{','}']: continue
            bracket_wrapped_line = "{"+line.strip().rstrip(',')+"}"

            try:
                line_dict = json.loads(bracket_wrapped_line)
            except json.decoder.JSONDecodeError:
                print (f'Failed to load {bracket_wrapped_line}')
                continue
            
            yield list(line_dict.items())[0]
```

---

## Per-worker progress bars from scratch with `tqdm`
In addition to splitting over different processes, I wanted to watch the progress of each worker on
a given job (mainly to watch for unexpected slow downs) and how far the total pool of jobs has progressed.

To give a visual idea of the goal, this is the final product:

![](/assets/images/WorkerProgress.gif)

Each worker has it's own progress bar under a "global" progress bar and when a worker is done with a job,
it starts back at 0% with the new job.

This isn't so difficult to accomplish but there are some tricks needed that I had to scrounge from
different sources (with the bulk coming from [this blog](https://leimao.github.io/blog/Python-tqdm-Multiprocessing/)). Here are the main ideas:

1. Maybe the most obvious, you need to wrap the loop with a `tqdm`. However, you don't wrap
the generator like you would normally. Instead, you use `with` to wrap the whole block of code you want to execute
and then manually update the progress bar (ie. increment by 1) once applicable.

2. You need the `position` argument to tell `tqdm` on which line to maintain each progress bar.

3. In addition to wrapping the actual loop doing the evaluations, you need to wrap the calls
to the pool of workers and update a secondary progress bar (the global one) once the result
of each job is ready.

We'll need some imports to start:
```python
from multiprocessing import Pool, RLock, current_process
```

Then here's how to implement the "outer"/global progress bar:

```python
pool = Pool(processes=nproc, initargs=(RLock(),), initializer=tqdm.tqdm.set_lock)
chunk_size = 1000 # some integer - see above section for details on "chunks" in this context
njobs = 10 # some integer

# The outer "global" progress bar that we call "pbar"
with tqdm.tqdm(total=nchunks, desc='Chunks processed ', position=0, dynamic_ncols=True) as pbar:
    results = {} # storage for results so we can check when things finish
    for ijob in range(njobs):
        # Build a package of args to pass to apply_async that includes the job index
        pkg = {
            'pid': ijob,
            'start': ijob*chunk_size,
            'stop': min((ijob+1)*chunk_size, NFILES_IN_BULK)
        }
        # Send job to the pool, store "result" as the key and a "done" flag as the value (False to start since we just submitted)
        results[pool.apply_async(my_func, (pkg,))] = False

    # With all jobs sent, loop over the results that are not ready yet.
    # Once ready, update the "done" flag to True and increment pbar.
    # Exit the outer while when "done" flag is True.
    while len([r for r, done in results.items() if not done]) > 0:
        for result in [r for r, done in results.items() if not done]:
            if result.ready():
                results[result] = True
                pbar.update(1)

    pool.close()
```

This handles the outer progress bar - what about the inner ones inside `my_func`?

```python
def my_func(pkg):
    # Unpack - this is a result of using apply_async
    pid, start, stop = pkg['pid'], pkg['start'], pkg['stop']

    # ID the current process and extract the worker index from that
    pname = current_process().name
    tqdm_text = f"Worker {pname}"
    tqdm_position = int(pname.split('-')[1])+1 # +1 to give that extra line between the "global" progress bar and the workers
    
    # Wrap the progress bar around the for loop and update it manually to support per-process progress bars
    # The "leave" arg says to erase the bar once done (leaving room for the new one to show up)
    with tqdm.tqdm(total=stop-start, desc=tqdm_text, position=tqdm_position, leave=False, dynamic_ncols=True) as pbar:
        for entry_id, entry in read_bulk_file_chunk(start,stop): # see the function in the previous trick
            ...do stuff...                                       # but this iterable could be anything obviously
            pbar.update(1)
```

And that's it! From my understanding, this sort of thing is implemented in tools like Dask
which are probably more appropriate to use but I still found it fun and educational to
set it up "from scratch."

I am wondering if there's a way to do a context manager for this but it would be a context manager
of a context manager so probably a bit contrived and not worth it.