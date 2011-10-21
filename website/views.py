from django.conf import settings
from django.utils import simplejson
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseNotAllowed, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, TemplateView

from website.models import Member, News, Page, Project, BlogPost, Tag
from website.forms import MemberForm, ProjectForm, BlogForm

class JSONResponseMixin(object):
	def get_json_response(self, json, **kwargs):
		return HttpResponse(json, content_type='application/json', **kwargs)

	def convert_to_json(self, context):
		return simplejson.dumps(context)

	def render_to_response(self, context):
		return self.get_json_response(self.convert_to_json(context))

class HomepageView(TemplateView):
    template_name = 'website/home.html'

class ProfileView(DetailView):
    model = Member
    template_name = 'accounts/profile.html'
    context_object_name = 'member'

class EditProfileView(UpdateView):
	model = Member
	form_class = MemberForm
	template_name = 'accounts/edit_profile.html'

	def render_to_response(self, context):
		if(self.request.user != context['member'].user):
			return HttpResponseForbidden()
		else:
			return UpdateView.render_to_response(self, context)
  
class MembersView(ListView):
	model = Member
	template_name = 'accounts/members.html'
	context_object_name = 'members'

class NewsView(ListView):
	model = News
	template_name = 'website/news/news.html'
	context_object_name = 'news_list'

class NewsDetailView(DetailView):
	model = News
	template_name = 'website/news/article.html'
	context_object_name = 'news'

class PageDetailView(DetailView):
	model = Page
	template_name = 'website/pages/page.html'
	context_object_name = 'page'

class ProjectView(ListView):
	model = Project
	template_name = 'website/projects/projects.html'
	context_object_name = 'projects'

class EditProjectView(UpdateView):
	model = Project
	form_class = ProjectForm
	template_name = 'website/projects/edit_project.html'

	def render_to_response(self, context):
		print context
		return UpdateView.render_to_response(self, context)

class BlogView(ListView):
	template_name = 'website/blogs/blogs.html'

	def get_queryset(self):
		return BlogPost.objects.filter(author__pk=self.kwargs.get('pk', None))

	def get_context_data(self, **kwargs):
		context = super(BlogView, self).get_context_data(**kwargs)
		context['blog_posts'] = self.get_queryset()
		context['member'] = Member.objects.get(pk=self.kwargs.get('pk', None))

		return context
	
	def render_to_response(self, context):
		return ListView.render_to_response(self, context)

class BlogPostView(DetailView):
	model = BlogPost
	template_name = 'website/blogs/blog_post.html'

	def get_context_data(self, **kwargs):
		context = super(BlogPostView, self).get_context_data(**kwargs)
		context['member'] = Member.objects.get(pk=self.kwargs.get('pk', None))
		context['blog'] = BlogPost.objects.get(pk=self.kwargs.get('blog_pk', None), author__pk=context['member'].pk)

		return context

class AddBlogView(CreateView):
	model = BlogPost
	form_class = BlogForm
	template_name = 'website/blogs/add_blog.html'
	object = None
	
	def post(self, request, *args, **kwargs):
		pk = self.kwargs.get('pk', None)
		if pk is not None:
			member = Member.objects.get(pk=pk)
		else:
			return Http404('Could not locate specified user')
		
		form = BlogForm(request.POST)
		
		if form.is_valid():
			self.object = form.save(commit=False)
			self.object.author = member
			self.object.save()
			form.save_m2m()
			return HttpResponseRedirect(self.object.get_absolute_url())
		else:
			return self.render_to_response(self.get_context_data(form=form))

class EditBlogView(UpdateView):
	model = BlogPost
	form_class = BlogForm
	template_name = 'website/blogs/edit_blog.html'

	def get_object(self, **kwargs):
		pk = self.kwargs.get('blog_pk', None)
		return BlogPost.objects.get(pk=self.kwargs.get('blog_pk', None), author__pk=self.kwargs.get('pk', None))

	def get_context_data(self, **kwargs):
		context = super(EditBlogView, self).get_context_data(**kwargs)
		context['member'] = Member.objects.get(pk=self.kwargs.get('pk', None))
		context['blog'] = BlogPost.objects.get(pk=self.kwargs.get('blog_pk', None), author__pk=context['member'].pk)
		return context
	
	def render_to_response(self, context):
		if self.request.user.get_profile() == context['member']:
			return UpdateView.render_to_response(self, context)
		else:
			return HttpResponseForbidden('You do not have permission to edit this blog post')

class TagCloudView(JSONResponseMixin, View):
    def post(self, request, *args, **kwargs):
        tag_name = request.POST['tag']
        blog_post = BlogPost.objects.get(pk=request.POST['blog_id'], author__pk=request.POST['member_id'])
        tag = Tag.objects.get_or_create(name=tag_name)
        
        return HttpResponse()
    
	def get(self, request, *args, **kwargs):
		tags = Tag.objects.all()
		response = {}

		for tag in tags:
			response[tag.name] = BlogPost.objects.filter(tags__name=tag.name).count()
		
		return JSONResponseMixin.render_to_response(self, response)




