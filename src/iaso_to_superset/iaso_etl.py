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


def get_meta_data(token, form_id):
    headers = {"Authorization": "Bearer %s" % token}
    meta_response = requests.get(
        f"https://iaso.bluesquare.org/api/formversions/?form_id={form_id}&fields=descriptor",
        headers=headers,
    )
    metadata = meta_response.json()
    md = metadata["form_versions"][-1]["descriptor"]["children"]
    print("Meta data loaded")
    return md


def save_form_data_as_csv(token, form_id, name):
    headers = {"Authorization": "Bearer %s" % token}
    data_url = f"https://iaso.bluesquare.org/api/instances?form_id={form_id}&csv=true"
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


def export_form(token, form_id, name):
    print(f"Processing {name}")
    md = get_meta_data(token, form_id)
    save_form_data_as_csv(token, form_id, name)
    df = enrich_and_save(name, md)
    return df


def add_one(number):
    return number + 1
