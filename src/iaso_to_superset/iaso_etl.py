## Utilitary functions
import os

import pandas as pd
import requests
from sqlalchemy import create_engine

# Convert a list into a dict name => label


def convert_choices(choices):
    return {c["name"]: c["label"] for c in choices}


# Trying to match the value in the data table with a label
# Some shenanigan to standardise values (everything to string, avoid decimal values, etc)
# If it seems like a multi value thing, split and send it back as a unique, comma separated field (example: services)
def assign_label(value, labels):
    # print("Trying to find label for", value, "in", labels)
    if len(str(value).split(" ")) > 1:
        # print("Mutliple values")
        values = [str(v) for v in str(value).split(" ")]
        return ", ".join([assign_label(v, labels) for v in values])

    if pd.isna(value):
        return value

    if isinstance(value, str):
        if value.isnumeric():
            value = str(int(value))

    if isinstance(value, float):
        value = str(int(value))

    if value in labels:
        return labels[value]
    else:
        return value


# Create the "labels" dict of dict with one key per "select" column (field)
# Assumes all select question are either at first or second level (ie in a group)
# In other words: no groups in groups (or more)
def analyze_data(data, metadata):
    labels = {}

    for m in metadata:
        if "type" in m and "select" in m["type"]:
            values = m["children"]
            labels[m["name"]] = convert_choices(values)
        if "children" in m:
            for c in m["children"]:
                if "type" in c and "select" in c["type"]:
                    values = c["children"]
                    labels[c["name"]] = convert_choices(values)

    return labels


# For each column in the DF, if it's in the meta (ie if it is a select kind of question)
# Replace the names by the associated labeles
def replace_names_with_labels(data, labels_dicts):
    names = data.columns.values
    for n in names:
        if n in labels_dicts:
            labels = labels_dicts[n]
            data[n] = data[n].map(lambda v: assign_label(v, labels))

    return data


# Get the org units from Iaso and save them in CSV & SQL table
# Still a bit specific to Burkina Faso - what about the filter there?
def collect_org_units(
    iaso_url,
    token,
    name="org_units",
):
    url = (
        iaso_url
        + '/api/orgunits/?limit=20&order=id&page=1&searches=[{"validation_status":"VALID","source":5,"orgUnitTypeId":"4"}]&locationLimit=3000&csv=true'
    )

    headers = {"Authorization": "Bearer %s" % token}
    org_response = requests.get(url, headers=headers)

    org_content = org_response.content
    file_path = f"{name}.csv"

    with open(file_path, "wb") as file:
        file.write(org_content)
        print(f"File {file_path} created")

    df = pd.read_csv(file_path)

    engine = create_engine(os.environ["WORKSPACE_DATABASE_URL"])
    df.to_sql(name, con=engine, if_exists="replace")

    return df


# Assuming two df (form & org unit), create a merged one with one line per org unit (taking the last is the form has multiple lines per org unit)
# Assumes the org unit id is named "ID" in the org unit df and "Org unit id" in the form df
def merge_units_to_form(org_units, form):
    f_dedup = form.drop_duplicates(subset=["Org unit id"], keep="last")
    form_with_unit_df = org_units.merge(
        f_dedup, left_on="ID", right_on="Org unit id", suffixes=("_ou", "_form")
    )
    return form_with_unit_df


def get_meta_data(token, form_id, iaso_url):
    headers = {"Authorization": "Bearer %s" % token}
    meta_response = requests.get(
        f"{iaso_url}/api/formversions/?form_id={form_id}&fields=descriptor",
        headers=headers,
    )
    metadata = meta_response.json()
    md = metadata["form_versions"][-1]["descriptor"]["children"]
    print("Meta data loaded")
    return md


def save_form_data_as_csv(token, form_id, name, iaso_url):
    headers = {"Authorization": "Bearer %s" % token}
    data_url = f"{iaso_url}/api/instances?form_id={form_id}&csv=true"
    data = requests.get(data_url, headers=headers)
    text_content = data.content

    file_path = f"{name}.csv"

    with open(file_path, "wb") as file:
        file.write(text_content)
    print(f"File {file_path} created")


def enrich_and_save(name, metadata):
    data = pd.read_csv(f"{name}.csv")
    labels_dicts = analyze_data(data, metadata)
    df = replace_names_with_labels(data, labels_dicts)

    print("Names replaced by labels")
    engine = create_engine(os.environ["WORKSPACE_DATABASE_URL"])
    df.to_sql(name, con=engine, if_exists="replace", index_label="id")
    print(f"Data saved in {name} table")
    return df


def export_form(token, form_id, name, iaso_url="https://iaso.bluesquare.org"):
    print(f"Processing {name}")
    md = get_meta_data(token, form_id, iaso_url)
    save_form_data_as_csv(token, form_id, name, iaso_url)
    df = enrich_and_save(name, md)
    return df
