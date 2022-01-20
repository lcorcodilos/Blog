---
layout: post
title: "DeepTransfer: Part 1 - Data Acquisition"
comments: false
description: "Getting and manipulation data for a new technique to estimate QCD distributions with neural networks."
keywords: "python, neural network, machine learning, pandas, keras, Tensorflow, deep neural network"
---

I should preface this by saying that I still have access to official CMS data and simulation but
I do not know for how long. I hope that I'll be able to come to some conclusions with this project before I lose
access. In fact, I originally intended to just use CMS OpenData but there's nothing in
full NanoAOD format from 13 TeV data taking... It's been three years since the CMS Run 2 shutoff!
Where is the CMS Open Data?!

![](https://c.tenor.com/WnjJsVOwoJQAAAAC/john-travolta-well.gif)

--------------------------
## A brief rant on opening ROOT files in numpy
--------------------------

The issue is that I want to build a neural network with Keras which means I'm going to need
to export the data in ROOT files (CMS NanoAOD format) to numpy arrays (with a detour through pandas
for some manipulation tasks)... which is exactly what a tool called [uproot](https://uproot.readthedocs.io/en/latest/index.html) does.
As I'll detail in a future post on software in particle physics, I've avoided using uproot to this point because I always
had alternatives that seemed easier to use.

This tendency to avoid uproot was validated when it took me **FOUR HOURS** to figure out how to open a simple ROOT
file as a pandas DataFrame as I worked through several issues:
- the `uproot.open` method would hang on my computer (slowly consuming more and more RAM as time progresses)
- the `uproot.iterate` method doesn't work for me since it streams chunks and I need the full set of events in one table,
- the `filter_name` argument is redundant with `expression` (both meant to select specific TBranches to include) but that isn't explained anywhere,
- a simple regex of multiple object collections for `filter_name` would give me back a tuple of DataFrames instead of one big one (WHAT - WHY)

I read the "Getting Started" section of the docs. I tried multithreading to help `uproot.open` (apparently doesn't make a difference unless you're bottle-necked by decompression).
I tried `uproot.lazy` unsuccessfully. I tried `uproot.concatenate` unsuccessfully. I read GitHub issues. I read GitHub discussions. Nothing that could just tell me how to open a ROOT file with one of today's most
popular open source data libraries!

![](https://media4.giphy.com/media/l1J9u3TZfpmeDLkD6/200w.gif)

Here's what finally worked:

```python
COLUMNS = [...]
df = uproot.concatenate(filepath+':Events', COLUMNS, library='pd', how='outer')
```

That's it... that's all they had to put in the "Getting Started". 

I used to make the assumption that software written by particle physicists is of poor quality
(there were some obvious indicators that, again, I'll cover in another post)
but I never used enough software outside of that environment to know if that assumption was true.
I have since compared being a new user of uproot, coffea, CMSSW, and even ROOT to being a new user of open source 
libraries like pandas, Dask, and keras and it's painfully obvious that I was correct.

With that rant out of the way...

--------------------------
## Reformatting NanoAOD
--------------------------

The pandas DataFrame has a very specific format in order to accommodate physics data.
Specifically, the "unit" in physics data is the "event" and each event has inside of
it a certain number of "physics objects" that can be electrons, muons, photons,
or showers of particles called "jets". In one event you might have two electrons
and in the next, zero electrons. So how can one structure the table?

NanoAOD's approach is to 
