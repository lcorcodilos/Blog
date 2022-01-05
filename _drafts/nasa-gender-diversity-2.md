---
layout: post
title: "NASA Gender Diversity Part 2: Transforming the data"
comments: false
description: "How I transformed NASA publication data into a useful set of databases."
keywords: "nasa, diversity, data, project, database, engineering"
---

As noted in [part 1]({% post_url 2022-01-04-nasa-gender-diversity-1 %}) of this series,
I wanted to transform the bulk JSON of all NASA publications into three databases - one
for the published documents, one for the authors, and one for the organizations.

Along the way, I also wanted to transform some of the information into pieces I felt would be
most useful for my own uses. Below is the abbreviated python block with the logic.

First, I hard-code the columns I eventually want, some of which are directly entries in the JSON.
```python
AUTHOR_COLUMNS = ['first','last','middle']
ORG_COLUMNS = ['code','name']
DOC_COLUMNS = ['stiType','disseminated','distribution','created','distributionDate', 'downloadLink', 'authorIdsOrdered',
               'modified','onlyAbstract','stiTypeDetails','status','title','orgId','abstract']
```

Next book the pandas DataFrames:
```python
df_authors = pd.DataFrame(columns = AUTHOR_COLUMNS)
df_orgs = pd.DataFrame(columns = ORG_COLUMNS)
df_docs = pd.DataFrame(columns = DOC_COLUMNS)
```

Now loop over one chunk of the bulk JSON, being careful to use a generator here so the whole file isn't read into memory.
```python
for entry_id, entry in read_bulk_file_chunk(start,stop):
    # First track authors athat are currently untracked
    d_authors = authors_from_entry(entry) # helper to extract all author info for this JSON entry which returns a dict
    for author in d_authors:
        if author['id'] not in df_authors.index: # if not tracking already, add it
            # Be careful to parse names with "first, last" vs something else
            if len(author['name'].split(',')) < 2:
                d_author = {
                    'first': author['name'],
                    'middle': None,
                    'last': None
                }
            else:
                d_author = {
                    'first': author['name'].split(',')[1].strip().split(' ')[0],
                    'last': author['name'].split(',')[0].strip(),
                    'middle': ' '.join(author['name'].split(',')[1].strip().split(' ')[1:])
                }
            # Sanity check you are only using columns you intend to use
            if set(d_author.keys()) != set(AUTHOR_COLUMNS):
                raise KeyError(f'The keys of d_author do not match the AUTHOR_COLUMNS.{chr(10)}{set(d_author.keys())} vs{chr(10)}{set(AUTHOR_COLUMNS)}')
            # Add the author
            df_authors = df_authors.append(pd.Series(d_author, name=author['id']))

    # Now do the same with organizations
    d_org = copy.deepcopy(entry['center'])
    if d_org['id'] not in df_orgs.index:
        d_org_id = d_org.pop('id')
        if set(d_org.keys()) != set(ORG_COLUMNS):
            raise KeyError(f'The keys of d_org do not match the ORG_COLUMNS.{chr(10)}{set(d_org.keys())} vs{chr(10)}{set(ORG_COLUMNS)}')
        df_orgs = df_orgs.append(pd.Series(d_org, name=d_org_id))

    # Now track document
    # columns in first layer of entry -> ['id','stiType','dissemination','distributions','created','distributionDate', 'abstract', 'modified','onlyAbstract','stiTypeDetails','status','title',
    # columns that need to be made -> ['downloadLink', 'authorIdsOrdered','orgId']
    d_doc = {}
    for k in DOC_COLUMNS:
        if k in entry:
            d_doc[k] = entry[k]
        else:
            d_doc[k] = None

    d_doc['authorIdsOrdered'] = [t['id'] for t in d_authors]
    d_doc['orgId'] = entry['center']['id']
    if entry['disseminated'] == 'DOCUMENT_AND_METADATA':
        d_doc['downloadLink'] = f'https://ntrs.nasa.gov/api/citations/{entry_id}/downloads/{entry_id}.txt'
    else:
        d_doc['downloadLink'] = None

    if set(d_doc.keys()) != set(DOC_COLUMNS): # Should never be raised because of last for loop
        raise KeyError(f'The keys of d_doc do not match the DOC_COLUMNS. {set(d_doc.keys()) ^ set(DOC_COLUMNS)}')
    
    df_docs = df_docs.append(pd.Series(d_doc, name=entry['id']))
```

Now clean up by setting the index to the ids and saving out to CSV.
```python
df_docs.index.name = 'id'
df_authors.index.name = 'id'
df_orgs.index.name = 'id'

df_docs.to_csv(f'data/temp/documentDB.csv')
df_authors.to_csv(f'data/temp/authorDB.csv')
df_orgs.to_csv(f'data/temp/organizationDB.csv')
```

One other thing I like to do is keep a "meta database" that stores information about when I last
created and updated CSV files. Here's the function I use that gets run at the very end,

```python
def update_meta_db(dbname):
    _columns = ['creation','update']
    # If meta DB doesn't exist, make it
    if not os.path.exists('data/meta.csv'):
        df = pd.DataFrame(columns=_columns)
        df.index.name = 'name'
    else:
        df = pd.read_csv('data/meta.csv', index_col='name')
        
    now = datetime.datetime.now().strftime("%m/%d/%Y")
    # If DB already being tracked, update the line
    if dbname in df.index:
        df.iloc[dbname, 'update'] = now
    else: # If the DB to track isn't in the meta DB, track it.
        df = df.append(pd.Series({'creation':now, 'update':now}, name=dbname))

    df.to_csv('data/meta.csv')
```

I should note that the JSON has to be run over multiple threads to run in a reasonable amount of time
(~45 min on 10 threads). This requires breaking the JSON into chunks, saving out separate CSV files per chunk,
and combining them back together, accounting for duplicates. For fun, I also implemented some
fancy per-worker terminal progress bars with `tqdm` to track progress.
I'll probably do a separate blog post on that as well as some of these other tricks.

However, I just learned what "Dask" is last week and realized I could've just used that! Oh the tech I was missing in physics-land...