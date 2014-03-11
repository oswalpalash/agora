from django import forms
from django.contrib.admin import widgets
from django.contrib.comments.forms import CommentForm
from apps.treecomments.models import TreeComments

class TreeCommentsForm(CommentForm):
	parent = forms.ModelChoiceField(queryset=TreeComments.objects.all(), required=False, widget=forms.HiddenInput)
	def get_comment_model(self):
		return TreeComments
	def get_comment_create_data(self):
		data = super(TreeCommentsForm,self).get_comment_create_data()
		data['parent'] = self.cleaned_data['parent']
		return data