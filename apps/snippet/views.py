import difflib

from django.shortcuts import render_to_response, \
     get_object_or_404, get_list_or_404, render, redirect
from django.template.context \
     import RequestContext
from django.http \
     import HttpResponseRedirect, HttpResponseBadRequest, \
     HttpResponse, HttpResponseForbidden
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.utils import simplejson

from apps.snippet.forms import SnippetForm, UserSettingsForm
from apps.snippet.models import Snippet
from apps.snippet.highlight import pygmentize, guess_code_lexer, \
     LEXER_LIST
from apps.pygments_style.models import PygmentsStyle


def explore(request):
    context = {
        'recent_snippets': Snippet.objects.public()[:20]
    }

    return render(request, 'snippet/explore.html', context)


def snippet_new(request):
    if request.method == "POST":
        snippet = Snippet()

        if request.user.is_authenticated():
            snippet.author = request.user


        snippet_form = SnippetForm(request.POST,
                                   request.FILES,
                                   request=request,
                                   instance=snippet)

        if snippet_form.is_valid():
            request, new_snippet = snippet_form.save()
            return redirect(new_snippet)
    else:
        snippet_form = SnippetForm(request=request)

    recent = Snippet.objects.public()[:10]

    context = {
        'snippet_form': snippet_form,
        'recent_snippets' : recent,
        'show': True, # always true b/c guest posting is allowed
    }

    return render(request, 'snippet/snippet_new.djhtml', context)


def snippet_details(request, snippet_id,template_name='snippet/snippet_details.djhtml', is_raw=False):
    
    snippet = get_object_or_404(Snippet, secret_id=snippet_id)
    snippet.num_views += 1
    snippet.save()


    if request.user.is_authenticated() and hasattr(snippet,'author'):
        show = True
    elif ( request.user.is_anonymous() ) and (hasattr(snippet,'author') ):
        if snippet.author == None:
            show = True
        else:
            show = False
    else:
        show = False

    tree = snippet.get_root()
    tree = tree.get_descendants(include_self=True)

    if snippet.title.startswith('Re: '):
        reply_title = snippet.title
    else:
        reply_title = 'Re: %s' % snippet.title

    new_snippet_initial = {
        'content': snippet.content,
        'lexer': snippet.lexer,
        'title': reply_title,
        
    }

    if request.method == "POST":
        snippet_form = SnippetForm(request.POST,
                                   request.FILES,
                                   request=request,
                                   initial=new_snippet_initial)
        if snippet_form.is_valid():
            request, new_snippet = snippet_form.save(parent=snippet)
            return redirect(new_snippet)
    else:
        snippet_form = SnippetForm(initial=new_snippet_initial,
                                   request=request)

    if request.user.is_authenticated():
        default_pygments_style = request.user.get_profile().pygments_style
    else:
        default_pygments_style = PygmentsStyle.objects.get(pk=1)


    r = snippet.rating.votes
    if snippet.rating.votes == 0:
        r = 1

    score = snippet.rating.score/(r)

    context = {
        'snippet_form': snippet_form,
        'snippet': snippet,
        'lines': range(snippet.get_linecount()),
        'tree': tree,
        'language': dict(LEXER_LIST)[snippet.lexer],
        'pygments_styles': PygmentsStyle.objects.all(),
        'default_style': default_pygments_style,
        'no_descendants': len(tree) == 1,
        'show': show,
        'score' : score,
    }

    response = render(request, template_name, context)

    if is_raw:
        response['Content-Type'] = 'text/plain'
        return response
    else:
        return response

def snippet_delete(request, snippet_id):
    snippet = get_object_or_404(Snippet, secret_id=snippet_id)
    try:
        snippet_list = request.session['snippet_list']
    except KeyError:
        return HttpResponseForbidden('You have no recent snippet list, '\
                                     'cookie error?')
    if not snippet.pk in snippet_list:
        return HttpResponseForbidden('That\'s not your snippet, sucka!')
    snippet.delete()
    return HttpResponseRedirect(reverse('snippet_new'))

def snippet_userlist(request, template_name='snippet/snippet_list.djhtml'):

    try:
        snippet_list = get_list_or_404(Snippet,
                                        pk__in=request.session.get(
                                           'snippet_list',
                                           None)
                                       )
    except ValueError:
        snippet_list = None

    template_context = {
        'snippets_max': getattr(settings, 'MAX_SNIPPETS_PER_USER', 10),
        'snippet_list': snippet_list,
    }

    return render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )


def userprefs(request, template_name='snippet/userprefs.djhtml'):

    if request.method == 'POST':
        settings_form = \
                      UserSettingsForm(request.POST,
                                       initial=\
                                       request.session.get('userprefs', None))
        if settings_form.is_valid():
            request.session['userprefs'] = settings_form.cleaned_data
            settings_saved = True
    else:
        settings_form = UserSettingsForm(initial=\
                                         request.session.get('userprefs', None))
        settings_saved = False

    template_context = {
        'settings_form': settings_form,
        'settings_saved': settings_saved,
    }

    return render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )

def snippet_diff(request, template_name='snippet/snippet_diff.djhtml'):

    if request.GET.get('a').isdigit() and request.GET.get('b').isdigit():
        try:
            fileA = Snippet.objects.get(pk=int(request.GET.get('a')))
            fileB = Snippet.objects.get(pk=int(request.GET.get('b')))
        except ObjectDoesNotExist:
            return HttpResponseBadRequest(u'Selected file(s) does not exist.')
    else:
        return HttpResponseBadRequest(u'You must select two snippets.')

    if fileA.content != fileB.content:
        d = difflib.unified_diff(
            fileA.content.splitlines(),
            fileB.content.splitlines(),
            'Original',
            'Current',
            lineterm=''
        )
        difftext = '\n'.join(d)
        difftext = pygmentize(difftext, 'diff')
    else:
        difftext = _(u'No changes were made between this two files.')

    template_context = {
        'difftext': difftext,
        'fileA': fileA,
        'fileB': fileB,
    }

    return render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )

def guess_lexer(request):
    code_string = request.GET.get('codestring', False)
    response = simplejson.dumps({'lexer': guess_code_lexer(code_string)})
    return HttpResponse(response)



#Rating Processing
def processrating(request,snippet_id):
    from djangoratings.views import AddRatingView
    import django.db.models
    from django.contrib.contenttypes.models import ContentType


    content_type = ContentType.objects.get(model='snippet').id
    if request.method == 'POST':
        params = {
            'content_type_id': content_type,
            'object_id': get_object_or_404(Snippet,secret_id=snippet_id).id,
            'field_name': 'rating', # Must be the same as the name declared in the model of snippet
            'score': int( request.POST['Rate']) , # the score value sent
            }
        response = AddRatingView()(request, **params)
        if response.status_code == 200:
            return redirect( request.POST['next'] )