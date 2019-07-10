from chalicelib import searchapi
from chalice import Chalice

app = Chalice(app_name="searchgate")


@app.route("/")
def search():
    """Run a simple search against one of several target APIs"""

    try:
        # TODO sanitize input
        search_target = app.current_request.query_params.get("t")
        number_desired = int(app.current_request.query_params.get("n"))
        needle = app.current_request.query_params.get("q")

        # Which kind of search are we doing?
        target_dispatch = {
            "libguides": searchapi.LibGuidesSilo(),
            "primo": searchapi.PrimoSilo("articles"),
            "primobooks": searchapi.PrimoSilo("books"),
            "primoshareok": searchapi.PrimoSilo("shareok"),
            "collection": searchapi.PrimoSilo("collection"),
            "eresource": None,
            "site": None,
            "people": None,
        }
        my_api = target_dispatch.get(search_target, None)

        # Do a search
        result = my_api.get_result(needle, number_desired)
        return {"data": result.get_data()}

    except Exception as error:
        return {"error": repr(error)}


@app.route("/test")
def test():
    return app.current_request.query_params


@app.route("/introspect")
def introspect():
    return app.current_request.to_dict()


# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:
#
# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.
#
