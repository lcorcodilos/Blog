---
layout: post
title: "NASA Gender Diversity Part 1: Getting Data"
comments: false
description: "How I sourced NASA publication data."
keywords: "nasa, diversity, data, project, database, engineering"
---

Since this is the first post for this project, I'd like to start by outlining 
motivations and some starting goals. 

It's no secret that STEM fields have a lack of diversity which spans across 
categories of gender, race, and ethnicity. However, I've recently connected with 
someone interested in gender diversity at NASA. The initial idea was to search
for gender pronouns in public NASA documents and tie them back to the formal
position/title to which the pronouns refer. This would give
a rough breakdown of gender diversity in various NASA leadership positions.

Of course, this ignores entirely the people who do not identify as male or female (or
at least, have a different pronoun preference). I'll address the gender binary issue later
but this was one reason that, as I started investigating data sources, I strayed from
the goal of using pronouns to validate gender representation. There were two more reasons in
addition to this.

First, most public NASA documents are formal research publications and, while I still have to
perform the analysis, I don't expect that these technical papers, presentations, etc. will have many instances
of "he" or "she". In fact, coming from a large physics collaboration, I wouldn't
be surprised if the NASA publication review process explicitly removed these pronouns in favor of "they"
or disallowed them altogether (and I think the same can be said for references to those
in NASA leadership positions - they simply wouldn't be included in a research publication).

Second, among the dozen non-research documents that I scanned by eye (press releases, official policies, etc), I never found
"he" or "she" but instead saw "they" - I assume because these releases discuss goals, projects, etc that don't 
necessarily align with a given leader's tenure and so using a gendered pronoun may imply that the position can only be held
by one gender. 

In other words, NASA is a federal agency - if they picked a policy to use "they" everywhere, to do otherwise
would be a mistake that everyone would point out and they would revise accordingly, making any
counts of "he" or "she" a count of "mistakes made" and unsuited for quantifying leadership diversity.

This doesn't mean the project is DOA though.

---

## A different proposal

If I learned anything from academia, it's that publications are the "currency".
Thus, a good question that is more likely to be answerable is how different genders
are represented in NASA research publications. Does the percent of publications with women in the author list
match the percent of women researchers at NASA? How often do women appear as the first author (assuming NASA
doesn't require alphabetical sorting of authors...)? If women are *over*-represented in publications (relative to the percent
of NASA researchers that are women), is that leading to an increase in leadership positions held? Does it have
any impact on how the next generation views women at NASA? In other words, I can't imagine children are reading these papers
so does it even matter for the sake of increasing diversity? [[^1]]

The first study will try to tackle some of the above. However,
with the exception of the brief mention, I've ignored a really important question to this point
that is going to prove difficult to address - 
is there any way to tell if an author does not identify as male or female and, if not, how can that be accounted for
without implicitly forgetting this important group? After all, increasing diversity means more than just 
"more women, fewer men".

My opinion is that non-binary gender identification is going to be nearly impossible from the data I describe below.
In acknowledging that I'm not an expert on this topic and that I don't have the ability to study it, I will consciously work with
just "male" and "female" for now for the sake of understanding gender representation. [[^2]]

---
[^1]: 1: These last few are beyond the scope of what I'd like to do but there should be some acknowledgment of
         the impact of such results.
         
[^2]: 2: The US Census makes the same assumption in broader analyses such as [this one](https://ncses.nsf.gov/pubs/nsb20212/participation-of-demographic-groups-in-stem).
         I'm not saying this justifies my approach but that I'm not the first to face this issue and it doesn't seem that I'm the only one who doesn't have a good solution yet.

## The search for data

After some searching and clicking around various NASA websites, I came across the
[NASA Scientific and Technical Information (STI) repository](https://www.sti.nasa.gov/).
The STI program maintains an [OpenAPI](https://www.sti.nasa.gov/harvesting-data-from-ntrs/)
(with some [rules](https://www.sti.nasa.gov/docs/STI_Open_API_Documentation_20210426.pdf)).
Part of the rules are a rate limit (500 requests per 15 minutes) and a query cap (10,000 records per query).

NASA also requires that you check weekly for changes to "document availability." In other words,
they may make a document public one day and then retract it another day. It is part of the user's responsibility to
drop a document from their use if it has been retracted. More on the technical details of this later.

Of course, I didn't know what I wanted or what was even available, so I naturally wanted everything...

That's where the [bulk download](https://www.sti.nasa.gov/docs/ntrs-public-metadata.json.gz)
came in handy - a zipped 1.4 GB JSON file with entries describing meta information for every file in the
repository but not the direct content. In fact, some of the actual content is not even available
for download (`"disseminated" == "METADATA_ONLY"`)! The schema (dropping parts I don't care about) looks like the following:

```json
{
    "abstract": "Full abstract",
    "authorAffiliations": [
        {
            "id": "Author id",
            "meta": {
                "author": {
                    "name": "Last, First",
                }
            },
            "sequence": "Zero-indexed index of position in author list",
            "submissionId": "Document ID"
        }
    ],
    "center": {
        "code": "Organization abbreviation",
        "id": "Org. ID",
        "name": "Full org. name"
    },
    "created": "YYYY-MM-DDT00:00:00.0000000+00:00",
    "disseminated": "METADATA_ONLY or DOCUMENT_AND_METADATA",
    "distribution": "PUBLIC",
    "distributionDate": "YYYY-MM-DDT00:00:00.0000000+00:00",
    "id": "Int of outer id again",
    "keywords": [],
    "modified": "YYYY-MM-DDT00:00:00.0000000+00:00",
    "onlyAbstract": "Usually False - haven't seen a case of True",
    "publications": [  
        {
            "id": "publisher ID",
            "publicationDate": "YYYY-MM-DDT00:00:00.0000000+00:00",
            "publisher": "Publisher information",
            "submissionId": "Same as ID again"
        }
    ],
    "sensitiveInformation": 0,
    "status": "CURATED",
    "stiType": "Category like OTHER",
    "stiTypeDetails": "More details on the category like 'Other - Student Report'",
    "title": "Title of publication"
}
```

Mostly flat with the exception of some lists, a good chunk of useful info, some redundant info, etc.
As I noted though, no content beyond the abstract. For that, we need the API.

A request is done pretty simply with:
```bash
url="https://ntrs.nasa.gov/api/citations/{id}/downloads"
curl -X GET $url -H "accept: application/json"
```

And the response looks like
```json
[
  {
    "draft": false,
    "mimetype": "application/pdf",
    "name": "{id}.pdf",
    "type": "STI",
    "links": {
      "original": "/api/citations/{id}/downloads/{id}.pdf",
      "pdf": "/api/citations/{id}/downloads/{id}.pdf",
      "fulltext": "/api/citations/{id}/downloads/{id}.txt"
    }
  }
]
```
where `{id}` is the document ID obtainable from the bulk JSON.

Of course, with all of the meta information in the bulk JSON, I just need the paths to 
the full content which follow a very simple pattern, allowing me to skip the API `curl` call
and just do

```bash
wget https://ntrs.nasa.gov/api/citations/{id}/downloads/{id}.txt
```

Of course, I don't know if I'm even going to use this text content yet. At most I'm going to
do some simple searches for "he" and "she" to validate my assumption that these words
don't appear anywhere but other than that, I may never need the above `wget` - it's just
nice to know it's there!

---

## Terms and Conditions
We need to revisit briefly the statement, "Check the Redistributions endpoint regularly (weekly at minimum) for
changes in the document availability. When a document or record is redistributed and
becomes unavailable, it is expected that any copies be removed and the data be resynced."

To fulfill this requirement, one needs to check redistribution did not happen via an API call like
```
https://ntrs.nasa.gov/api/citations/redistributions?redistributedDate.gt=YYYY-MM-DD&page.size=100
```
which checks for any redistributions after a `YYYY-MM-DD`. The API response looks like
```json
{
  "stats": {
    "took": 160,
    "total": 4868,
    "estimate": false,
    "maxScore": 0
  },
  "results": [
    {
      "disseminated": "NONE",
      "id": 19760007927,
      "distribution": "PUBLIC",
      "redistributedDate": "2021-08-27T00:00:00.0000000"
    }
  ]
}
```
The `["stats"]["total"]` entry may be an enormous number. If it is larger than 100, then there are redistributions missing in
`["results"]` since it is capped at 100 (defaults to 25). If this is the case,
date ranges can be checked with the addition of `&redistributedDate.lt=YYYY-MM-DD` and a new date (difference
being that this is a "less than").

Note that anything not `PUBLIC` is either new and inaccessible or needs to be removed from the dataset for
being no longer `PUBLIC` (in the case that NASA decides they don't want the info public anymore which I
imagine is rare).

In principle, one would do the following:
- Assume that the latest bulk download has the most recent distributions;
- Store the date of the bulk download access;
- Perform updates by looking at redistributions which assumes that new public releases all go through redistribution (ie. we do not miss initial distributions).

However, having all of THE most recent data is not so necessary. A month or two of time will only be a handful
of new (just published or just redistributed) papers. So by the end of the study, I will update again but until then,
one or two changes will not make or break the results.

---

## Next steps

Now I have some data to work with but the structure is less than ideal. What I'd really like to work
with is a flat table with redundant information removed. Specifically, meta information on the authors
and organizations is not necessary to include for every document where one or the other appears.
Instead, I want to flatten the JSON into three databases - one for the documents, one for the authors,
and one for the organizations. The IDs for the authors and organizations are what will be used to tie the author and
organization databases back to the documents. In other words, an entry in the document database will have a column for
lists of author IDs, each one mapping back to the meta information in the author database for when we need it.

In addition to doing this, I'd like to keep a list of some of other "to-do" items:
- Create a setup to easily check for redistributions, only updating the three new databases and not overwriting;
- Design a "look up" to convert author names to genders;
    - This will have immediate consequences if someone uses abbreviations, if their name is not immediately recognizable as male or female, etc. It is obviously tied intricately to the binary genders issue... Databases exist with names mapped to genders but it's also possible to train a classifier to assign a gender to a name. The classification scores seem like a good approach since they
    can help distinguish the boundary case of when a name is not obviously male or female.

---

## Useful links
- [API dictionary](https://www.sti.nasa.gov/docs/OpenAPI-Data-Dictionary-062021.pdf)
- [API Web UI](https://ntrs.nasa.gov/api/openapi/)
- [Main repository page](https://sti.nasa.gov/what-is-the-sti-repository/)

