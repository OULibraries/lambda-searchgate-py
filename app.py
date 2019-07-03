from chalicelib import searchapi
from chalice import Chalice

app = Chalice(app_name="searchgate")


@app.route("/search")
def search():

    try:

        my_api = app.current_request.query_params.get("t")
        my_limit = app.current_request.query_params.get("q")
        my_needle = app.current_request.query_params.get("n")

        my_search = searchapi.LibGuidesSilo()
        result = my_search.get_result(my_needle, my_limit)

        return result.get_data()

    except Exception as error:
        return repr(error)


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
