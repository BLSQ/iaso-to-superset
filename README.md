# IASO to Superset

If you don't work at Bluesquare, there is a good chance that nothing here is very interesting. If so, all good !

Small python package with utility methods to make it easy to get any form data from [Iaso](iaso.org) to a [SuperSet](https://superset.apache.org/) instance via OpenHexa.

## How to use

### Setup

Assuming you have a Iaso access

- Note the ids of the forms you want to import
- Get a token in iaso (https://iaso.bluesquare.org/api/apitoken/)
- Get a Open Hexa workspace
- Create a notebook

### Code

````python
!pip install git+https://github.com/BLSQ/iaso-to-superset.git#egg=iaso_to_superset
from iaso_to_superset.iaso_etl import export_form 

import requests
TOKEN = "MY_IASO_TOKEN"
IASO_URL = "https://mfl.minsante.bf" # if not standard

# Repeat for each form. It will create a table with the name "supervision" with all data from the form with id 858
df_v3 = export_form(TOKEN, 858, "supervision_v3", iaso_url=IASO_URL)
````

### In Superset

- Add a connection to a new database - find the relevant connection info in OpenHexa "database" panel
- Start adding DataSet & Charts with your nice data!


## Missing features

- [x] Work with local iaso instances (ie don't assume Iaso is on iaso.bluesquare.org)
- [] Does not work "as is" for the Cameroon (as it's translated). Totally fixable with a bit more logic about "is this label translated or not"
- [] Merge method: allow to merge N forms as one date, with an optional mapping dict as parameters:

    mapping = {
        "region": ["region1", "region"] # a field named "region" will exist in the resulting table, with data from either the "region1" or "region2" field
        ...
    }
- [] Configuration of the org unit retrieval method (status but maybe others)

## Configuration

The while configuration for a given project could be imagined as something like this:

````json
{
    "iaso_url": "https://iaso.bluesquare.org",
    "iaso_token": "secrettoken",
    "forms": [{"id": 46, "name": "healthcenters"}, {"id": 20, "name": "hospitals"}],
    "org_units": {
        "merge_with_forms": true,
        "types": [5],
        "status": "Approved",
        "filter": "&type=blabla",
        "levels": [1,2,3,4,5,6]
        ...
    }

}
````

ie:

- Iaso info: token & server (default to iaso.bluesquare.org)
- forms info - ids & name (for the table/file)
- org unit info: level to match, filters
  - Could be a "iaso filter", is just params to add to the url
  - merge with forms to know if/how we need to merge the org unit info with the form info (could be "inner" or "last" as options too)