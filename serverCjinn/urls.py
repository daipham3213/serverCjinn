import pathlib

from django import http
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from graphene_file_upload.django import FileUploadGraphQLView
from graphql import GraphQLCoreBackend

from apps.base.views import current_info


def graphiql(request):
    """Trivial view to serve the `graphiql.html` file."""
    del request
    graphiql_filepath = pathlib.Path(__file__).absolute().parent.parent / "templates" / "graphiql.html"
    with open(graphiql_filepath) as f:
        return http.response.HttpResponse(f.read())


class GraphQLCustomCoreBackend(GraphQLCoreBackend):
    def __init__(self, executor=None):
        # type: (Optional[Any]) -> None
        super().__init__(executor)
        self.execute_params['allow_subscriptions'] = True


urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(FileUploadGraphQLView.as_view(graphiql=getattr(settings, 'DEBUG', False)))),
    path('', current_info),
    path('django-rq/', include('django_rq.urls')),
    path('i18n/', include('django.conf.urls.i18n'))
]
