from django.db.models import Q
from django.http import HttpResponse
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render

# Create your views here.
from django.views.generic import View

from courses.models import Course, CourseResource, Video
from operation.models import UserFavorite, CourseComments, UserCourse
from utils.mixin_utils import LoginRequiredMixin


class CourseListView(View):
    def get(self, request):
        all_courses = Course.objects.all().order_by('-add_time')
        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            all_courses = all_courses.filter(Q(name__icontains=search_keywords) | Q(desc__icontains=search_keywords) | Q(detail__icontains=search_keywords))
        hot_courses = Course.objects.all().order_by('-click_nums')[:3]
        sort = request.GET.get('sort', '')
        if sort:
            all_courses = all_courses.order_by('-' + sort)
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(all_courses, 6, request=request)
        courses = p.page(page)
        return render(request, 'course-list.html',
                      {'all_courses': courses,
                       'sort': sort,
                       'hot_courses': hot_courses})


class CourseDetailView(View):
    def get(self, request, course_id):
        course = Course.objects.get(id=int(course_id))
        course.click_nums += 1
        course.save()
        has_fav_course = False
        has_fav_org = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course.id, fav_type=1).exists():
                has_fav_course = True
            if UserFavorite.objects.filter(user=request.user, fav_id=course.course_org.id, fav_type=2).exists():
                has_fav_org = True
        tag = course.tag
        relate_course = []
        if tag:
            relate_course = Course.objects.exclude(id=int(course_id)).filter(tag=tag)[:5]
        return render(request, 'course-detail.html',
                      {'course': course,
                       'relate_course': relate_course,
                       'has_fav_course': has_fav_course,
                       'has_fav_org': has_fav_org})


class CourseInfoView(LoginRequiredMixin, View):
    def get(self, request, course_id):
        course = Course.objects.get(id=int(course_id))
        user_courses = UserCourse.objects.filter(user=request.user, course=course)
        if not user_courses:
            UserCourse.objects.create(user=request.user, course=course)
        user_ids = UserCourse.objects.filter(course=course).values_list('user_id', flat=True)
        course_ids = UserCourse.objects.filter(user_id__in=user_ids).values_list('course_id', flat=True)
        relate_courses = Course.objects.exclude(id=int(course_id)).filter(pk__in=course_ids).order_by('-click_nums')[:5]
        all_resources = CourseResource.objects.filter(course=course)
        return render(request, 'course-video.html',
                      {'course': course,
                       'relate_courses': relate_courses,
                       'course_resources': all_resources})


class CourseCommentView(LoginRequiredMixin, View):
    def get(self, request, course_id):
        course = Course.objects.get(id=int(course_id))
        user_ids = UserCourse.objects.filter(course=course).values_list('user_id', flat=True)
        course_ids = UserCourse.objects.filter(user_id__in=user_ids).values_list('course_id', flat=True)
        relate_courses = Course.objects.exclude(id=int(course_id)).filter(pk__in=course_ids).order_by('-click_nums')[:5]
        all_resources = CourseResource.objects.filter(course=course)
        all_comments = CourseComments.objects.all()
        return render(request, 'course-comment.html',
                      {'course': course,
                       'relate_courses': relate_courses,
                       'course_resources': all_resources,
                       'all_comments': all_comments})


class AddCommentsView(View):
    def post(self, request):
        if not request.user.is_authenticated():
            return HttpResponse('{"status":"fail", "msg":"用户未登录"}', content_type='application/json')
        course_id = request.POST.get('course_id', 0)
        comments = request.POST.get('comments', '')
        if int(course_id) > 0 and comments:
            course_comments = CourseComments()
            course_comments.course = Course.objects.get(id=int(course_id))
            course_comments.comments = comments
            course_comments.user = request.user
            course_comments.save()
            return HttpResponse('{"status":"success", "msg":"添加成功"}', content_type='application/json')
        else:
            return HttpResponse('{"status":"fail", "msg":"添加失败"}', content_type='application/json')


class VideoPlayView(View):
    def get(self, request, video_id):
        video = Video.objects.get(id=int(video_id))
        course = video.lesson.course
        user_courses = UserCourse.objects.filter(user=request.user, course=course)
        if not user_courses:
            UserCourse.objects.create(user=request.user, course=course)
        user_ids = UserCourse.objects.filter(course=course).values_list('user_id', flat=True)
        course_ids = UserCourse.objects.filter(user_id__in=user_ids).values_list('course_id', flat=True)
        relate_courses = Course.objects.exclude(id=course.id).filter(pk__in=course_ids).order_by('-click_nums')[:5]
        all_resources = CourseResource.objects.filter(course=course)
        return render(request, 'course-play.html',
                      {'course': course,
                       'video': video,
                       'relate_courses': relate_courses,
                       'course_resources': all_resources})
