import requests
import http.cookiejar
import urllib.parse
import boto3
import json
import traceback
import pprint


def load_config(ssm_parameter_path):
    """Load our config from the AWS SSM Parameter Store."""
    client = boto3.client("ssm")

    config = {}
    try:
        param_details = client.get_parameters_by_path(
            Path=ssm_parameter_path, Recursive=False, WithDecryption=True
        )

        if "Parameters" in param_details and len(param_details.get("Parameters")) > 0:
            # load config dict with keys based on path relative to ssm_parameter_path
            config = {
                param.get("Name")[len(ssm_parameter_path) :]: param.get("Value")
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
    """Defines format for unified search result."""

    def __init__(self):
        self.source = ""
        self.query = ""
        self.full = ""
        self.total = 0
        self.plural = []
        self.topLabel = ""
        self.hits = []  # List of tuples describing search results

    def _plural(self):

        return {
            "end": "" if self.total == 1 else "s",
            "all": "" if self.total == 1 else "All ",
        }

    def get_data(self):

        return {
            "source": self.source,
            "query": self.query,
            "full": self.full,
            "total": f"{self.total:,}",  # use ',' to group digits
            "plural": self._plural(),
            "topLabel": self.topLabel,
            "hits": self.hits,
        }

    def add_hit(self, data):

        self.hits.append(
            {
                "link": data.get("my_link", False),
                "title": data.get("my_title", False),
                "text": data.get("text", False),
                "date": data.get("date", False),
                "creator": data.get("creator", False),
                "image": data.get("image", False),
                "type": data.get("type", False),
                "context": data.get("context", False),
                "icon": type_to_icon(data.get("type")),
            }
        )


class Silo:
    """Base class for various search wrappers. """

    def __init__(self):
        self.config = load_config(
            "/searchgate/config/"
        )  # trailing slash seems required

    def get_result(self, query, limit):
        pass

    def is_plural(self, count):
        pass


class LibGuidesSilo(Silo):
    """Simple wrapper for LibGuides search API."""

    def get_result(self, query, limit):

        my_result = Result()
        my_result.topLabel = "Research Guides"
        my_result.source = "libguides"
        my_result.query = query
        my_result.full = f"http://guides.ou.edu/srch.php?q={query}&t=0"

        lg_params = {
            "key": self.config["libguides_key"],
            "site_id": self.config["libguides_siteid"],
            "sort_by": "relevance",
            "search_terms": query,
        }
        response = requests.get("http://lgapi.libapps.com/1.1/guides", params=lg_params)
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
            return_data["my_title"] = hit.get("name")
            return_data["my_link"] = hit.get("url")
            # description might be empty string, and we want to convert that to false.
            return_data["text"] = hit.get("description", False) or False
            return_data["date"] = False
            return_data["creator"] = False
            return_data["type"] = "guide"

            my_result.add_hit(return_data)
            if len(my_result.hits) >= limit:
                break

        return my_result


class PrimoSilo(Silo):
    """Simple wrapper for Primo search API."""

    def __init__(self, search_variant="articles"):
        super().__init__()
        self.search_variant = search_variant
        # TODO there should probably be better choice for  default primo search

    def get_result(self, query, limit):

        # Wire up credentials
        my_primo_key = self.config["primo_key"]
        my_primo_vid = self.config["primo_vid"]
        my_primo_host = self.config["primo_host"]

        # We do a variety of Primo-based searches
        variant_options = {
            "articles": {
                "label": "Articles & More",
                "source": "articles",
                "q_exclude": "facet_rtype,exact,books",
                "url_facet": "rtype,exclude,books",
            },
            "books": {
                "label": "Book",
                "source": "primobooks",
                "q_include": "facet_rtype,exact,books",
                "url_facet": "rtype,include,books",
            },
            "shareok": {
                "label": "SHAREOK Articles",
                "source": "shareok",
                "api_scope": "ou_dspace",
            },
            # TODO Can I give this a better name, like "primocollection" or whatever
            "collection": {
                "label": "Special Collection",
                "source": "collection",
                "q_include": "facet_local6,exact,special_collections",
                "url_facet": "local6,include,special_collections",
            },
        }
        active_variant = variant_options[self.search_variant]

        # We'll be handing back a result object
        my_result = Result()
        my_result.query = query
        my_result.topLabel = active_variant.get("label")

        # Do primo search
        # See API docs
        # https://developers.exlibrisgroup.com/primo/apis/webservices/rest/pnx
        primo_params = {
            "q": f"any,contains,{query}",
            "qInclude": active_variant.get("q_include", ""),
            "qExclude": active_variant.get("q_exclude", ""),
            "limit": f"{limit}",
            "apikey": f"{my_primo_key}",
            "vid": f"{my_primo_vid}",
            "scope": active_variant.get("api_scope", "default_scope"),
            "addfields": "pnxId",
            "view": "full",
        }
        # response = requests.get(f"{my_primo_host}/primo/v1/pnxs", params=primo_params)
        # json_response = response.json()

        primo_request_url = urllib.parse.urlunsplit(
            (
                "",
                "",
                f"{my_primo_host}/primo/v1/pnxs",
                urllib.parse.urlencode(primo_params),
                "",
            )
        )
        json_response = None
        with urllib.request.urlopen(primo_request_url) as response:
            json_response = json.loads(response.read().decode("utf-8"))

        my_result.source = active_variant.get("source", "")

        full_url = "//ou-primo.hosted.exlibrisgroup.com/primo-explore/search"
        full_url_params = {
            "query": f"any,contains,{query}",
            "facet": active_variant.get("url_facet", ""),
            "search_scope": active_variant.get("api_scope", "default_scope"),
            "vid": my_primo_vid,
            "sortby": "rank",
        }
        my_result.full = urllib.parse.urlunsplit(
            ("", "", full_url, urllib.parse.urlencode(full_url_params), "")
        )

        my_result.total = json_response["info"]["total"]

        for hit in json_response.get("docs"):

            return_data = {}

            return_data["my_title"] = hit.get(
                "title", "No title information available."
            )

            hit_url = "//ou-primo.hosted.exlibrisgroup.com/primo-explore/fulldisplay"
            hit_url_params = {
                "docid": hit.get("pnxId"),
                "vid": my_primo_vid,
                "context": hit.get("context"),
            }
            return_data["my_link"] = urllib.parse.urlunsplit(
                ("", "", hit_url, urllib.parse.urlencode(hit_url_params), "")
            )

            return_data["date"] = hit.get(
                "date", "No published date information available."
            )
            return_data["text"] = False

            return_data["creator"] = (
                hit.get("creator", "No creator inforation available.")
                if isinstance(hit.get("creator", ""), str)
                else "; ".join(hit.get("creator"))
            )

            return_data["type"] = hit.get("type")

            return_data["context"] = hit.get("context")

            my_result.add_hit(return_data)

            # We only want the top several results
            if len(my_result.hits) >= limit:
                break

        return my_result
