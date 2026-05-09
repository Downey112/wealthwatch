import azure.functions as func
import json

app = func.FunctionApp()

@app.route(route="test", auth_level=func.AuthLevel.ANONYMOUS)
def test(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"message": "API Bridge is Active!"}),
        mimetype="application/json",
        status_code=200
    )