import random

from django.http import HttpResponseNotFound
from django.contrib.contenttypes.models import ContentType
from django import template

from secretballot import views

from likes.utils import can_vote
from likes import signals


def can_vote_test(request, content_type, object_id, vote):
    return can_vote(
        content_type.get_object_for_this_type(id=object_id),
        request.user,
        request
    )


def like(request, content_type, id, vote):
    # Crawlers will follow the like link if anonymous liking is enabled. They
    # typically do not have referrer set.
    if 'HTTP_REFERER' not in request.META:
        return HttpResponseNotFound()

    url_friendly_content_type = content_type
    app, modelname = content_type.split('-')
    
    content_type = ContentType.objects.get(app_label=app, model__iexact=modelname)
    if request.is_ajax():
        likes_template = 'likes/inclusion_tags/likes_%s.html' % modelname.lower()
        try:
            template.loader.get_template(likes_template)
        except template.TemplateDoesNotExist:
            likes_template = 'likes/inclusion_tags/likes.html'

        context_pocessor = ContentObjProcessor(content_type.model_class(), id)

        response = views.vote(
            request,
            content_type=content_type,
            object_id=id,
            vote=vote,
            template_name=likes_template,
            can_vote_test=can_vote_test,
            context_processors=[context_pocessor],
            extra_context={
                'likes_enabled': True,
                'can_vote': False,
                'content_type': url_friendly_content_type,
            }
        )
    else:
        # Redirect to referer but append unique number(determined
        # from global vote count) to end of URL to bypass local cache.
        redirect_url = '%s?v=%s' % (request.META['HTTP_REFERER'],
                                    random.randint(0, 10))
        response = views.vote(
            request,
            content_type=content_type,
            object_id=id,
            vote=vote,
            redirect_url=redirect_url,
            can_vote_test=can_vote_test
        )

    signals.object_liked.send(sender=content_type.model_class(),
                              instance=content_type.get_object_for_this_type(id=id),
                              request=request)

    return response


class ContentObjProcessor(object):
    """Bug fix.
       Put into context an object with special manager.
       That enables the inclusion of ``total_upvotes`` and ``total_downvotes``
       as well as some extra functionality.

       """

    def __init__(self, model_class, obj_id):
        self.cls = model_class
        self.obj_id = obj_id

    def __call__(self, request):
        obj = self.cls.objects.from_request(request).get(pk=self.obj_id)
        return {
            'content_obj': obj,
            'user_vote': obj.user_vote,
        }
