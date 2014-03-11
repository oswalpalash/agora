from django.contrib.comments.models import Comment
from mptt.models import MPTTModel, TreeForeignKey



class TreeComments(MPTTModel,Comment):
	parent = TreeForeignKey('self', null =True, blank=True,related_name='children')

	class MPTTMeta:
		order_insertion_by = ['submit_date']

	class Meta:
		ordering = ['tree_id','lft']


