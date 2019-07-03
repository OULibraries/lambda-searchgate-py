import requests
import http.cookiejar
import boto3
import configparser
import json
import traceback
import pprint


def load_config(ssm_parameter_path):
    client = boto3.client("ssm")

    config = {}
    try:
        param_details = client.get_parameters_by_path(
            Path=ssm_parameter_path, Recursive=False, WithDecryption=True
        )

        if "Parameters" in param_details and len(param_details.get("Parameters")) > 0:
            config = {
                param.get("Name"): param.get("Value")
                for param in param_details.get("Parameters")
            }

    except:
        print("Encountered an error loading config from SSM.")
        traceback.print_exc()
    finally:
        return config


def type_to_icon(content_type):
    # Most content types we just pass through
    if content_type in [
        "article",
        "audio",
        "book",
        "book_chapter",
        "guide",
        "image",
        "journal",
        "microform",
        "Online resource",
        "Online",
        "Online_resource",
        "reference_entry",
        "Research Guides",
        "score",
        "video",
        "sebsite",
    ]:
        return content_type
    else:
        return "other"


class Result:
    def __init__(self):
        self.source = ""
        self.query = ""
        self.full = ""
        self.total = ""
        self.plural = []
        self.topLabel = ""
        self.hits = []  # List of tuples describing search results

    def get_data(self):

        return {
            "source": self.source,
            "query": self.query,
            "full": self.full,
            "total": self.total,  # TODO, come back and format this equivalent to PHP number_Format
            "plural": self.plural,
            "topLabel": self.topLabel,
            "hits": self.hits,
        }

    def add_hit(self, data):

        self.hits.append(
            {
                "link": data.get("my_link"),
                "title": data.get("my_title"),
                "text": data.get("text"),
                "date": data.get("date"),
                "creator": data.get("creator"),
                "image": data.get("image"),
                "type": data.get("type"),
                "context": data.get("context"),
                "icon": type_to_icon(data.get("type")),
            }
        )


class Silo:
    def __init__(self):
        pass

    def get_result(self, query, limit):
        pass

    def is_plural(self, count):
        pass


class LibGuidesSilo(Silo):
    def __init__(self):
        pass

    def get_result(self, query, limit):

        my_result = Result()
        my_result.topLabel = "Research Guides"
        my_result.source = "libguides"
        my_result.query = query
        my_result.full = f"http://guides.ou.edu/srch.php?q={query}&t=0"

        config = load_config("/searchgate/config")

        response = requests.get(
            "http://lgapi.libapps.com/1.1/guides",
            params={
                "key": config["/searchgate/config/libguides_key"],
                "site_id": config["/searchgate/config/libguides_siteid"],
                "sort_by": "relevance",
                "search_terms": query,
            },
        )

        json_response = response.json()

        my_result.total = len(json_response)

        for hit in json_response:

            if hit["status_label"] != "Published":
                continue

            if hit["type_label"] in [
                "Internal Guide",
                "Course Guide",
                "Template Guide",
            ]:
                continue

            return_data = {}
            return_data["my_title"] = hit["name"]
            return_data["my_link"] = hit["url"]
            return_data["text"] = hit["description"]
            return_data["date"] = False
            return_data["creator"] = False
            return_data["type"] = "guide"

            my_result.add_hit(return_data)
            if len(my_result.hits) >= 5:
                break

        return my_result
