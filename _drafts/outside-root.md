---
layout: post
title: "ROOT dominates High Energy Physics for a reason"
comments: false
description: "Maybe ROOT isn't so bad after all."
keywords: "python, ROOT, CERN, HEP, SQL, relational, database"
---

I've taken two very different positions on ROOT - high energy physics' (HEP) dominant 
computing software. In the later half of grad school, I was an advocate for keeping computing in the ROOT
ecosystem. In contrast, after graduating, I couldn't wait to start exploring everything *not* ROOT
available with Python. Plotly, seaborn, numpy, pandas, Dask, SQL, Parquet - all made
me say, "Wow, what have I been missing?" I even started drafting a post about
all of the nonsensical design decisions in HEP software, ROOT included.

I'll release that eventually but a recent foray into decoupling data from ROOT
formats and tools has me learning that, despite it's... *idiosyncrasies*...
ROOT sits on the throne of HEP software for a reason.

---------

## ROOT's obvious advantage

Most physicists are aware that HEP *used*
to have the biggest data sets in the world but the field is now beaten by orders of magnitude by the likes of Google, Amazon, and others
who have put a lot of money into building out tools for efficiency in processing data. So it's only obvious for physicists
to start looking around at what everyone else is doing!

There are efforts in the community (IRIS-HEP being the most obvious) to start introducing these tools into
HEP workflows through custom layers. But introducing a tool *without* ROOT has a very obvious downside that
I feel is largely ignored by these efforts: **HEP technical knowledge is concentrated almost entirely in ROOT**.

Building a new tool is easy. Convincing people to use your new tool is really hard.

My whole design philosophy with TIMBER was centered around this and I did whatever possible to
make it easy and obvious for physicists to start using it - and that meant
tying it to ROOT which 

1. wouldn't disrupt the pipelines that come before and after TIMBER, and
2. would make the back-end an already familiar ecosystem for those looking to do more.

I even used the default Doxygen theme so TIMBER docs would *look* like the ROOT documentation pages
so a TIMBER user would feel at home when inevitably searching for help.

I believe this is a primary reason why ROOT has failed to be unseated. Most physicists are
not interested in their software tools - they just want something to work (I have opinions about
why this is dumb but for another time...). That means most post-docs, faculty, and staff "grew up"
with ROOT and thus, teach new students ROOT. New students build their analysis environments with ROOT
and, with no one to encourage them otherwise, don't feel the need to look elsewhere. Then they become the post-docs
and the cycle repeats.

At least, *on average.* There are plenty of folks who look for new tools to use but even the majority of
those people get stuck trying to port their non-ROOT results *back* to ROOT for making plots, running fits, using
existing code, etc.

The only real change to the cycle started 5-10 years ago with the introduction of pyROOT (ROOT in Python).
There was less overhead to teach students Python instead of C++ (ROOT's native language) and so 
pyROOT became the defacto ROOT of choice for most people.

----------------

## The greener grass

On the flip side, ROOT has many disadvantageous, all (apparently) small compared to the advantage just discussed.
In order of relevance:

- ROOT's back-end is C++ and pyROOT is just a set of Python bindings.
    - ROOT's and Python's memory managers don't talk to each other so Python can (and will) toss
    variables owned by ROOT causing random and incomprehensible segmentation faults under the right circumstances.
    - ROOT operations are fast but the Python interface encourages using slow `for` loops
    over data entries. In other words, data access is fast but the outer layer of Python doing the work is not. With no
    way to implement more efficient paradigms that have become popular outside of HEP, there's no fix unless
    you learn some C++; an endeavor antithetical to the "get results first, everything else later" mentality.
- There's very little history of ROOT interfacing directly with HEPs primary batch/cloud processing services,
HTCondor and CRAB. One instead manually splits data sets into jobs, an error prone endeavor which is outclassed by something like Dask.
- The TBrowser is the only GUI for doing exploratory data analysis and is visually and practically dated when compared against
something like a simple Dash app.

There's more to list but I think these points cover the most pressing items. However, even if someone wanted to,
abandoning ROOT is a trickier endeavor than it may seem.

------------------

## Data like no other...

Switching to non-ROOT technologies is difficult - not because of an advantage of ROOT, but because
most data technologies outside HEP are not prepared to handle HEP data. HEP data is unique 
because the fundamental unit/row is the "event" - the set of measurements taken by detectors surrounding
a single collision of particles (protons for the LHC). The raw data could conceivably be stored in a table -
events as rows and the readings of every detector component as columns. However, physicists are interested
in reconstructing what happened during or just after the particle collision and for that, they need 
to look at the actual "physics objects" - electrons, muons, sprays of particles (called jets), etc - each
with its own properties - momentum, position, classification scores, etc.

Because of this, the raw detector data is processed through several steps, eventually outputting
the attributes of these objects as the meaningful interpretation of the event (along with
"event-level" variables that characterize the event as a whole - say, total missing energy).
Each event can have a varying number of each object meaning one needs to either,

1. Store an unknown number of columns, one for each object's properties; or
2. Store each event as a row and *groups* of values for each column with one value for each physics object of a given type in the event.

As an example of the second case, imagine having columns for the momentum and three spacial coordinates for all electrons. Then
for an event with two electrons, one would have an array of length two for each of these columns, ensuring 
the arrays are ordered the same between columns.

As is pointed out in this study [[^1]]
on query languages for HEP, database stalwarts like MySQL aren't able to deal with either of these
options. In fact, HEP hasn't used this architecture much either, instead opting for hierarchical data structures instead.
The tabular structure was only really reserved to be used at the level of each analysis with filters
and manipulations already applied.

------------------

## ...with design to match

The study in [[^1]] shows a very interesting result - even with database technologies that could
accommodate HEP data structures, ROOT's RDataFrame had the best performance across the board (on top of being
far less clunky to code - at least, in my opinion).

Another study [[^2]] in data formats showed that, even when the data is "flat", non-ROOT
formats like HDF5 and Parquet have comparable file sizes to ROOT but get smoked in I/O speeds.

[A thread](https://root-forum.cern.ch/t/re-scalability-of-rdataframes-on-16-cores/46458/5) on the ROOT forums by one of the authors
also revealed that they didn't account for the fact that the number of histograms being written could be in the 1000s - something
RDataFrame is tuned for.

Simply put, this is an very impressive feat that I was not expecting. The technology outside HEP
seemed like it had too much behind it to not be the best solution and that's simply not the case.

The disadvantages of ROOT I listed two sections ago are incredibly frustrating but
the proof is in the pudding - how can one justify changing their whole data analysis pipeline for new tech
if that new tech is worse? In my mind, the performance gap justifies the ROOT teams efforts
to develop new tools like RDataFrame and shows that the HEP community has more computing acumen than
I was willing to credit.

-----------------

## But what about those relational databases?

I still kept thinking about the study in [[^1]] though and realized there's an important missing piece.
I'm not sure if the authors missed it or didn't feel it was appropriate to cover but, to use relational database
technologies like MySQL, why not reinterpret the data as separate tables with the event number 
serving as a joining column?

In other words, put all jets, muons, electrons, etc into their own tables with each individual physics object
being its own row. Include in each of these tables a column storing the event index of that physics object.
Then to do the traditional looping over events, just do a `group by`. And to do any filtering or manipulation
across object types, use a `join`.

This does *not* come with the standard relational database advantage of reducing redundant information.
In fact, it redundantly stores the events index values. However, on the scale of all objects, this is a small cost
and I found that if you take a ROOT TTree with this information, restructure it into per-object tables 
(plus a table with all event-level attributes), and save them as Parquet files,
you get an output the same size as the input ROOT file - awesome!

There are two caveats:
1. This process can be slow - for a 22 MB file, the conversion is about one minute. For a 188 MB file, the conversion is...
it's still running on my laptop and according to `htop`, it's been 30 minutes and the process is currently consuming 2 GB of RAM. So there's
a lot of room for optimization... 
2. The output files have the obvious disadvantage of being... well, there's multiple of them. The input *file* has
now grown to 20-30 files (depending on what lives in the file input file, of course). A quick `tar -czf` fixes this but it's not exactly
an elegant solution.

How about benchmarks? I borrowed the ones performed in [[^1]] which I've actually implemented before for TIMBER and thus, RDataFrame.
I'll adopt the convention in [[^1]] and refer to them as "Q1", "Q2", etc.
On the 22 MB file, Q1-4 are all very simple and runs in a few seconds. Q5 is a bit slower (about 1 minute)
and Q6 is closer to 5 minutes. For a 22 MB input, that's not acceptable. So what's going on?

Q5 and Q6 both require considering combinations of objects of a group. For example, Q5 wants "opposite sign muon pairs"
(opposite sign just means they have opposite electric charge - think of these like electrons and positrons).
That means forming all combinations of muons in the event and finding just those pairs with opposite charge.
A similar scenario exists for Q6 but this time it wants us to find a set of three jets satisfying certain criteria.
It's not rare for their to be more than ten jets in an event so there are a lot of potential combinations!

And this is the wall we hit. Consider the code implementation below for Q5 (I include some helper functions for clarity):

```python
def LVector(*pargs):
    if len(pargs) == 0:
        return vector.obj(pt=0, eta=0, phi=0, m=0)
    elif len(pargs) == 1:
        p = pargs[0]
        return vector.obj(pt=p.pt, eta=p.eta, phi=p.phi, m=p.mass)
    else:
        return reduce(lambda x,y: x+y, [LVector(p) for p in pargs])

def InvariantMass(*plist):
    return LVector(*plist).mass

def extract_rows(df, *idxs):
    return [df.loc[idx,:] for idx in idxs]

def run_bench5(filename):
    '''Plot the MET of events that have an opposite-charge muon pair with an invariant mass between 60 GeV and 120 GeV.'''   
    def opposite_muons(muons):
        muon_combos = []
        for im1, im2 in itertools.combinations(muons.index, 2):
            m1, m2 = extract_rows(muons, im1, im2)
            if m1.charge != m2.charge:
                M = InvariantMass(m1,m2)
                if M > 60 and M < 120:
                    muon_combos.append((m1,m2))

        return len(muon_combos) > 0

    # Reads tarball and extracts event level attributes and Muon collections
    dfs = read_tgz(filename, collections=['event','Muon'])
    muons = dfs['Events']['Muon']
    opposite_muon_events = muons.groupby('event').filter(opposite_muons).event.unique()
    events = dfs['Events']['event']
    events = events[events.event.isin(opposite_muon_events)]

    fig = px.histogram(events, 'MET_sumEt')
    fig.write_image("test_images/fig5.pdf")

```
What costs us is `.filter(opposite_muons)` - the function being called is implemented
as a simple Python `for` loop which is slow (and brings us right back to one of the reasons pyROOT without RDataFrame is slow).
There may be a better implementation in a declarative format
but the fact is that this is the intuitive "first try" implementation if one wants to perform the task at hand.
This is the function a newcomer writes and so it's the one that needs to work well.

In TIMBER, the exact same logical implementation exists - it's just that you *have* to write it in C++
because of ROOT and so it's much faster:

```cpp
RVec<float> InvMassOppMuMu (RVec<float> Muon_pt, RVec<float> Muon_eta, RVec<float> Muon_phi, RVec<float> Muon_mass, RVec<float> Muon_charge) {
    int nMuon = Muon_pt.size();
    int mu0idx, mu1idx;
    ROOT::Math::PtEtaPhiMVector mu0LV;
    ROOT::Math::PtEtaPhiMVector mu1LV; 
    RVec<RVec<int>> comboIdxs = Combinations(Muon_pt,2);
    RVec<float> invMass;

    for (int i = 0; i < comboIdxs[0].size(); i++) {
        mu0idx = comboIdxs[0][i];
        mu1idx = comboIdxs[1][i];

        if (Muon_charge[mu0idx] != Muon_charge[mu1idx]) {
            mu0LV.SetCoordinates(Muon_pt[mu0idx], Muon_eta[mu0idx], Muon_phi[mu0idx], Muon_mass[mu0idx]);
            mu1LV.SetCoordinates(Muon_pt[mu1idx], Muon_eta[mu1idx], Muon_phi[mu1idx], Muon_mass[mu1idx]);
            invMass.push_back((mu0LV+mu1LV).M());
        }
    }
    
    return invMass;
}
```

TIMBER's time on Q5? 9 seconds. Yes - you have to write C++. But it's just a matter of learning the language -
the logic is exactly the same and there's no magic. I'm obviously wagering though that people are more
willing to learn new syntax over how to think declaratively.

----------------

## Summary

The real issue in the discussion surrounding non-HEP tooling in HEP is that few in either party knows how to talk to
the other. There are unique challenges fundamental to HEP data that non-HEP tools are inefficient at solving - or at
least, it's been shown they aren't the best solution. Most people outside HEP don't know this.

Additionally, people inside HEP have shielded themselves from change so long that when something like RDataFrame is
released, the declarative nature feels foreign and unintuitive and asking one to write simple C++ turns into an
unreasonable ask.

Meanwhile, people in big data but outside HEP don't believe in this sort of work. I quote a member of the Data Science Discord channel who said,
"No one believes academic software development translates to industry."
There's a sentiment that "academic" tools like ROOT are old tools with old interfaces that only solve old problems.
To a certain extent that's true and, as I noted, there are fundamental pieces about ROOT that make it really 
frustrating to use. 

However, ROOT developers are the ones bridging the gap. They are clearly paying attention to the advances 
in other domains and adapting them to the standard expectations in HEP; the proof being that RDataFrame has turned out to be the best one for HEP applications.

I'm left wondering a new question though - why can't it beat out these tools in other fields? If it can beat Parquet and pandas
and flavors of SQL in the domain of HEP, can it do the same elsewhere? Maybe everyone should be using ROOT.

------
Sources:

[^1]: 1: https://arxiv.org/pdf/2104.12615.pdf
[^2]: 2: https://iopscience.iop.org/article/10.1088/1742-6596/1085/3/032020/pdf