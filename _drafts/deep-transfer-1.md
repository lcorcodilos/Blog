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
## Things I said I would never do
--------------------------

Several years ago, I was considering different faster analysis tools for CMS data analysis.
There were (and still *are* really) two competing options:

- RDataFrame which takes its namesake from
the pandas DataFrame albeit with all of the positive and negative attributes of ROOT dragged with it
(positive being that it's designed for particle physics workflows and negative being that the designers
were particle physicists who want to make everything from "first principles").

- Uproot + coffea which "uproots" itself from the dependencies on ROOT so that it can use
open source tools written by software engineers (yay - no remaking the wheel!) but often wrapped in software that is still
designed by particle physicists (...no not like that!).

I went with RDataFrame for the simple reason that it was ROOT native and I wanted others to use the tool
I was working on ([TIMBER](https://lcorcodilos.github.io/TIMBER/)) and the number one way to 
get your code into other people's code is to make the transition both advantageous *and* seamless.

The *seamless* part is where I had a hard time with uproot and coffea. The "Getting Started" sections
of the respective packages are... hard to follow. And that was an opinion I heard echoed from others - specifically
by people in leadership positions that could encourage/discourage the adoption of such tools.
I don't think I spent more than 5 minutes on each "Getting Started" page before I realized RDataFrame was the obvious choice - 
"better the devil you know" in some aspect.

From then on out, I basically swore I would never touch either uproot or coffea - I had no need and realized I
probably wouldn't be around long enough for a need to develop. That is until I decided on this DeepTransfer project...

The issue is that I want to build a neural network with Keras which means I'm going to need
to export the data in ROOT files (CMS NanoAOD format) to numpy arrays (with a detour through pandas
for some manipulation tasks)... which is exactly what uproot does.

It took me FOUR HOURS to figure out how to open a simple file as a pandas DataFrame.
- the `uproot.open` method would hang on my computer (slowly consuming more and more RAM as time progresses)
- the `uproot.iterate` method doesn't work for me since it streams chunks and I need the full set of events in one table,
- the `filter_name` argument is redundant with `expression` (both meant to select specific TBranches to include) but that isn't explained anywhere,
- a simple regex of multiple object collections for `filter_name` would give me back a tuple of DataFrames instead of one big one (WHAT - WHY)

I tried multithreading (apparently doesn't matter unless you're bottlenecked by decompression). I tried `uproot.lazy`. I read
GitHub issues. I read GitHub discussions. Nothing that could just tell me how to open a ROOT file with one of today's most
popular open source data libraries!

![](https://media4.giphy.com/media/l1J9u3TZfpmeDLkD6/200w.gif)

Here's what finally worked:

```python
COLUMNS = [...]
df = uproot.concatenate(filepath+':Events', COLUMNS, library='pd', how='outer')
```

That's it... that's all they had to put in the "Getting Started". 

*Seamless...Seamless...Seamless...*

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
