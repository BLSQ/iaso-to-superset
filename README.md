# IASO to Superset

If you don't work at Bluesquare, there is a good chance that nothing here is very interesting. If so, all good !

Small python package with utility methods to make it easy to get any form data from [Iaso](iaso.org) to a [SuperSet](https://superset.apache.org/) instance.

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

# Repeat for each form. It will create a table with the name "supervision" with all data from the form with id 858
df_v3 = export_form(TOKEN, 858, "supervision_v3")
````

### In Superset

- Add a connection to a new database - find the relevant connection info in OpenHexa "database" panel
- Start adding DataSet & Charts with your nice data!

## Missing features

- [] Does not work "as is" for the Cameroon (as it's translated). Totally fixable with a bit more logic about "is this label translated or not"
- [] Merge method: allow to merge N forms as one date, with an optional mapping dict as parameters:

    mapping = {
        "region": ["region1", "region"] # a field named "region" will exist in the resulting table, with data from either the "region1" or "region2" field
        ...
    }