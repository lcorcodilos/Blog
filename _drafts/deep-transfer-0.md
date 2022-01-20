---
layout: post
title: "DeepTransfer: Part 0"
comments: false
description: "An introduction to the motivations behind a new technique to estimate QCD distributions with neural networks."
keywords: "python, neural network, machine learning, pandas, keras, Tensorflow, deep neural network"
---

Since I finished my PhD, I've spent a lot of time learning - a bit ironic considering
it was the end of my academic career. Not being quite sure what I wanted to do, I started
down several avenues simultaneously: started some projects, completed the majority of Kaggle's
data science courses, began reading half a dozen
technical books across different subjects related to data science, machine learning, and
even quantitative trading, wrote some code for a personal python library
([`CorcLib`](https://github.com/lcorcodilos/CorcLib) if you want to check it out, though
it's a bit sparse at the moment), and participated in some online data science communities
doing some reading and asking.

I now have a much better mental map of the landscape of "data science" and
I think it's now safe to say I've been following the Dunning-Kruger curve. [[^1]]
I can identify exactly when I was at the top of Mt. Stupid and there was a moment
a few days ago when reading *Generative Deep Learning* by David Foster that I realized
I was in the Valley of Despair.

![Dunning-Kruger curve](https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Dunning%E2%80%93Kruger_Effect_01.svg/1231px-Dunning%E2%80%93Kruger_Effect_01.svg.png)

The most useful practice you have in a PhD program though is constantly riding this curve
over and over again for different topics. And that makes the Valley of Despair less hopeless
because I know that if I keep moving forward, the slope will only become positive and stay positive.

To keep moving forward though is going to require a good project and in my opinion, a project
in a domain I am familiar with so that my learning effort can be focused on the new tools
rather than spread over new tools *and* a new subject. So as cool as image generation sounds
(I have a good project for this so I can learn Django but that's for another post),
I'm going back to one of the problems in which I would consider myself an expert - modeling
QCD multijet backgrounds in binned particle physics analyses (this is what I developed [2DAlphabet](https://lucascorcodilos.com/2DAlphabet/) for
and was half of my dissertation).

-------------------------
## Particle physics analyses
-------------------------
### In a haystack

Farmer Fred has a farm with live stock that he feeds with hay that he buys from Farmer Hank.
Hank has recently diversified his business by starting to produce needles for the local
sewing community. In fact, the needles are just very dense pieces of hay that could
harm livestock if consumed but are otherwise the two are very similar to the naked eye.

However, one day, Fred receives a phone call from Hank that there's been a terrible mix up with
the hay and needle production lines and there may or may not be needles in the hay he delivered
to Fred. Fred is concerned the livestock could accidentally eat the needles causing them harm.
Hank asks for Fred's help to determine if there are any needles in the pile. This will inform
Hank about where things went wrong and what other customers need to be informed (not wanting to
cause unnecessary panic if possible).

Fred, being a former particle physicist, agrees to help. He devises a simple plan. Because
the hay and needles are so similar, he can't just inspect them one-by-one. Instead, he
asks Fred for a bale of hay (guaranteed to have no needles) and pile of needles
(guaranteed to have no hay). Using these, Fred calculates the density of the hay (mass per m^2) and needles
(mass per needle).

Multiplying the volume of the suspect bale by just the density of the hay, Fred has a prediction
of the pile's weight for the null hypothesis that there are no needles in the hay. He then proposes
a complete model of the suspect bale's mass with the following equation:

*pile volume \* hay density + num. of needles \* mass per needle*

Or in mathematical notation we can carry around:

$$V_{pile} \cdot \rho_{hay} + N_{needles} \cdot m_{needle}$$

The only term in the equation that Fred doesn't know is the number of needles so by setting
the entire equation equal to the mass of the suspect bale (which he gets by weighing on his big scale),
he can solve for $$N_{needles}$$. If it is at or near 0 (the null hypothesis), then the
hay is safe for the livestock to eat. If not, Fred has found Hank's needles!

A good chunk of particle physics analyses are exactly this scenario except

- "number of events" replaces "mass",
- the hay is the number events predicted by "Standard Model backgrounds" (ie. physics we already know about),
- the needles are the number of events predicted by a theoretical "Beyond Standard Model (BSM) signal" (ie. physics for which we have a theoretical model that we want to discover).

These are often denoted with $$b$$ and $$s$$, respectively and the
complete model is just $$b + r \cdot s$$ where $$r$$ is the "signal strength". The case of $$r=0$$ is the null hypothesis
and any non-zero $$r$$ is sign that there exists new physics processes unaccounted for in the estimate of events produced by Standard Model backgrounds.

### Selections

Fred performs his analysis and observes a value of $$N_{needles}$$ that makes him a bit nervous. It isn't
high but it's not *zero* and he has uncertainty in his measurements of the hay and needle densities and
in the volume of the suspect bale that make the $$N_{needles}$$ result inconclusive.

While trying to work this out, he realizes that some of the pieces in the pile
are very obviously hay - they break with no effort, are discolored, and are very light. With these
discriminators, he realizes he can easily remove half of the hay from the suspect pile without risking picking out
needles. For what remains in the suspect pile, the ratio of true needles to true hay has gone up which
means $$N_{needles}$$ will be more sensitive to deviations in the total pile mass.

The problem he has introduced is that his measurement of the hay density no longer works! Recall
that this was measured on a pile of all hay types but he has removed pieces that are very light and,
thus, raised the average density of the real hay in his suspect pile. To account for this, Fred goes to the
clean pile of hay Hank gave him and removes hay with the same criteria as was applied to the suspect pile - 
break with no effort, discolored, very light. He re-measures the hay density in this pile, plugs it into his equation,
measures the mass of the new suspect pile, and calculates $$N_{needles}$$ again - it's stayed the same but its proportion relative to the total pile
is higher making it more significant! He phones Hank to let him know he found his needles.

In particle physics analyses, this process is called "applying a selection" and it is used to increase
the proportion of $$s$$ to $$b$$. This means looking at a subset of all data that is (as much as possible) enriched
in potential $$s$$ and depleted in $$b$$. In an ideal scenario (but nearly non-existent in high energy colliders), $$b = 0$$, leaving $$r \cdot s = d$$.

### Binning

In Fred's phone call with Hank, Hank expresses more interest in the results, "That's great
about the total number of needles you detected but do you know how much of each size?"

"Each size?"

Unbeknownst to Fred, Hank had started producing needles of different sizes - this is
part of what led to the mix-up - and so to debug his production line, Hank is interested to know 
how much of each size made it into Fred's hay. In fact, these different sizes were
already in the small pile Hank had loaned to Fred for the sake of measuring the mass per
needle. All Fred needed to do was to sort them.

Fred devises a new modification - grab 3 sets of 5 containers from the barn. Each container
in a set would be used to store objects of different mass; light objects would go in the 1st bin,
medium-light objects in the 2nd, medium in the 3rd, medium-heavy in the 4th, heavy in the 5th.
The scheme would be used to separate the three different piles Fred had to that point - 
true hay, true needles, and the suspect pile.

Fred would then use his model equation for each triplet of bins. This would allow him to potentially
isolate the deviation to a particular needle type. If only heavy needles polluted his suspect pile, he would only
find a non-zero $$N_{needles}$$ in the 5th bin!

This strategy is called a "binned analysis" and is used all of the time in modern high energy
particle physics analyses - sometimes in more than one dimension! If the bins are considered
correlated in any way (say Hank's production line sorting failed as a function of needle mass)
then you have a "binned *shape* analysis".

### Building models

There are a two more important analogies between the hay and needle story and actual particle physics
analyses. The first is that, with the clean hay sample provided by Hank, Fred had a "control" to work with
and study. When working with the control, Fred developed a "transfer function" that allowed him to transfer
measurable information into an estimate of the information he wanted. In this case, the hay density measured in
the control allowed him to "transfer" information about the volume to information about the mass.

The second analogy is that the clean hay and needle samples played the role of simulated particle
physics events. Specifically, particle physicists will simulate very specific processes - both for the $$b$$ and $$s$$ -
from the level of fundamental interactions - the protons colliding, the decay products that come flying out from the collision,
the interaction of these particles with the detector material, the digitization of the detector read out, the reconstruction
of physics objects (electrons, muons, sprays of particles, etc). All of this is very complex and very time consuming to
calculate. However, since it replicates as best as possible the actual physics that occurs when collecting data from real collisions
(just like how Hank gave Fred clean needle and hay piles from the same factory), it serves as invaluable building block
for building the model.

There are issues with physics simulation that Fred didn't face with his analogous needle and hay piles. First,
the modeling is good but it's imperfect. Even with such detailed simulation, many assumptions are made and those assumptions create
systematic errors. Additionally, the simulated events sample a subspace of the proton-proton collision probability distribution
but that space is often still larger than the subspace created from a full selection on the data. If the simulation doesn't perform
well in the one corner of phase space you care about, you're out of luck!

This is where "control" samples are reintroduced - one can select a subset of data that is orthogonal to the
selection that enriches $$s$$ and instead enriches $$b$$, study $$b$$, and use that information in the region enriched with $$s$$.
Often, one will develop a transfer function that "transfers" the information in the $$b$$ enriched region to the $$s$$ enriched
region. In many cases (like Fred's), one will pre-measure the transfer function. But if you're clever, you
can build it as part of the model - fitting the model parameters to the $$b$$ enriched and $$s$$ enriched
regions simultaneously!

This is the fundamental building block of 2DAlphabet - put the bins of your control and signal regions
in one likelihood, establish a relationship that maps the control region values to the signal region values,
and fit for the relationship (while simultaneously fitting for $$r$$ and every other parameter of the model
via analytic minimization of the total negative log likelihood)!

-------------------------
## Where I left off: Parametric black boxes
-------------------------
As 2DAlphabet was developed, I came across several issues in the real-world application
of the modeling scheme. Primary among those was that we wanted to use a simple polynomial to transfer information
from the control region to the signal region and it wouldn't work - the necessary function was too complicated and
adding extra terms to the polynomial meant risking creating features in our $$b$$ that looked like $$s$$, thus hurting
our ability to distinguish between hay and needles.

The solution was to use simulation of the background we were trying to model (colloquially called "QCD")
with this technique.

In the 2D binned space with axes $$x$$ and $$y$$, we originally had the relationship

$$N_{signal}(x,y) = N_{control}(x,y) \cdot TF(x,y,\vec{\alpha})$$

where $$TF(x,y,\vec{\alpha})$$ was our polynomial transfer function with a list of coefficients, $$\vec{\alpha}$$. We changed this to

$$N_{signal}(x,y) = N_{control}(x,y) \cdot TF_{MC}(x,y) \cdot TF(x,y,\vec{\alpha})$$

where $$TF_{MC}(x,y)$$ is the transfer function calculated explicitly in the simulation and with no free parameters.

In other words, it was a big constant shape that we factored out. If it was even close to the true $$\frac{N_{signal}(x,y)}{N_{control}(x,y)}$$,
it would factor out complexity, allowing $$TF(x,y,\vec{\alpha})$$ to take a simpler form (which is exactly what happened).

Of course, this raises the question - what makes $$TF_{MC}(x,y)$$ so special? Coming from simulation makes it well motivated but
it's not exactly accurate - $$\vec{\alpha}$$ was still made of 4 free parameters to account for the difference between $$TF_{MC}(x,y)$$ and the true $$\frac{N_{signal}(x,y)}{N_{control}(x,y)}$$.
The fact is that you could plug *anything* into $$TF_{MC}(x,y)$$ and still have something that is technically valid - $$TF(x,y,\vec{\alpha})$$ may 
need to become more complicated (opposite of the goal) but there's no fundamental issue stopping you from sticking a big constant out front
to make life easier/harder.

In this way the part of the expression $$TF_{MC}(x,y) \cdot TF(x,y,\vec{\alpha})$$ is really just a black box. This
could be *anything* provided we still satisfy the fundamental requirement that the resulting $$b$$ is not at risk
of creating features that look like $$s$$.

And this is what brings us to the concept I'll start to explore in the next post - developing
a trained neural network that can provide a fully data-driven parameterization of the transfer function
where the network inputs are *unbinned* events in a control region mapped to a *binned*
distributions in the signal region, the final layer
having a soft-max activation so that the set of neurons is really a binned probability distribution!

----------------
[^1]: 1: I am aware this plot is not an accurate representation of the Dunning-Kruger effect and that this is the internet's popular interpretation of the effect. I still think it holds.
         Or maybe my over-confidence in the plot is a result of the effect itself - we may never know!