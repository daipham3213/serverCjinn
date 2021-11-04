import pathlib

from django import http
from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

from apps.base.views import current_info


def graphiql(request):
    """Trivial view to serve the `graphiql.html` file."""
    del request
    graphiql_filepath = pathlib.Path(__file__).absolute().parent.parent / "templates" / "graphiql.html"
    with open(graphiql_filepath) as f:
        return http.response.HttpResponse(f.read())


urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=getattr(settings, 'DEBUG', False)))),
    path('', current_info),
    # path('graphql/', graphiql)
]
