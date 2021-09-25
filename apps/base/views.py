import datetime
from django.http import HttpResponse


def current_info(request):
    now = datetime.datetime.now()
    html = """
    <html>
        <body>
            <p>Server is up!</p>
            <p>It is now %s.</p>
            <p>Online:  %s.</p>
        </body>
    </html>
    """ % (now.strftime('%d-%m-%y, %H:%M'), len(request.online_now_ids))
    return HttpResponse(html)
