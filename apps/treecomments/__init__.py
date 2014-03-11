from apps.treecomments.models import TreeComments
from apps.treecomments.forms import TreeCommentsForm

def get_model():
	return TreeComments

def get_form():
	return TreeCommentsForm
	