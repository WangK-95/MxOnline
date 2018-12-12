from django.db.models import Q
from django.shortcuts import render

# Create your views here.
from django.views.generic import View
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse

from courses.models import Course
from operation.models import UserFavorite
from organization.forms import UserAskForm
from organization.models import CourseOrg, CityDict, Teacher


class OrgView(View):
    def get(self, request):
        all_orgs = CourseOrg.objects.all()
        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            all_orgs = all_orgs.filter(Q(name__icontains=search_keywords) | Q(desc__icontains=search_keywords))
        hot_orgs = all_orgs.order_by('-click_nums')[:3]
        all_citys = CityDict.objects.all()
        city_id = request.GET.get('city', '')
        if city_id:
            all_orgs = all_orgs.filter(city_id=int(city_id))
        category = request.GET.get('ct', '')
        if category:
            all_orgs = all_orgs.filter(category=category)
        sort = request.GET.get('sort', '')
        if sort:
            all_orgs = all_orgs.order_by('-'+sort)
        org_nums = all_orgs.count()

        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(all_orgs, 5, request=request)
        orgs = p.page(page)

        return render(request, 'org-list.html',
                      {'all_orgs': orgs,
                       'all_citys': all_citys,
                       'org_nums': org_nums,
                       'city_id': city_id,
                       'category': category,
                       'hot_orgs': hot_orgs,
                       'sort': sort})


class AddUserAskView(View):
    def post(self, request):
        userask_form = UserAskForm(request.POST)
        if userask_form.is_valid():
            user_ask = userask_form.save(commit=True)
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse('{"status":"fail", "msg":"添加出错"}', content_type='application/json')


class OrgHomeView(View):
    def get(self, request, org_id):
        current_page = 'home'
        course_org = CourseOrg.objects.get(id=int(org_id))
        course_org.click_nums += 1
        course_org.save()
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_type=course_org.id, fav_id=2).exists():
                has_fav = True
        all_courses = course_org.course_set.all()[:4]
        all_teachers = course_org.teacher_set.all()[:3]
        return render(request, 'org-detail-homepage.html',
                      {'all_courses': all_courses,
                       'all_teachers': all_teachers,
                       'course_org': course_org,
                       'current_page': current_page,
                       'has_fav': has_fav})


class OrgCourseView(View):
    def get(self, request, org_id):
        current_page = 'course'
        course_org = CourseOrg.objects.get(id=int(org_id))
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_type=course_org.id, fav_id=2).exists():
                has_fav = True
        all_courses = course_org.course_set.all()
        return render(request, 'org-detail-course.html',
                      {'all_courses': all_courses,
                       'course_org': course_org,
                       'current_page': current_page,
                       'has_fav': has_fav})


class OrgDescView(View):
    def get(self, request, org_id):
        current_page = 'desc'
        course_org = CourseOrg.objects.get(id=int(org_id))
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_type=course_org.id, fav_id=2).exists():
                has_fav = True
        return render(request, 'org-detail-desc.html',
                      {'course_org': course_org,
                       'current_page': current_page,
                       'has_fav': has_fav})


class OrgTeacherView(View):
    def get(self, request, org_id):
        current_page = 'teacher'
        course_org = CourseOrg.objects.get(id=int(org_id))
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2).exists():
                has_fav = True
        all_teachers = course_org.teacher_set.all()
        return render(request, 'org-detail-teachers.html',
                      {'course_org': course_org,
                       'all_teachers': all_teachers,
                       'current_page': current_page,
                       'has_fav': has_fav})


class AddFavView(View):
    def post(self, request):
        fav_id = request.POST.get('fav_id', 0)
        fav_type = request.POST.get('fav_type', 0)
        if not request.user.is_authenticated():
            return HttpResponse('{"status":"fail", "msg":"用户未登录"}', content_type='application/json')
        exist_records = UserFavorite.objects.filter(user=request.user, fav_type=int(fav_type), fav_id=int(fav_id))
        if exist_records.exists():
            exist_records.delete()
            if int(fav_type) == 1:
                course = Course.objects.get(id=int(fav_id))
                course.fav_nums -= 1
                if course.fav_nums < 0:
                    course.fav_nums = 0
                course.save()
            elif int(fav_type) == 2:
                course_org = CourseOrg.objects.get(id=int(fav_id))
                course_org.fav_nums -= 1
                if course_org.fav_nums < 0:
                    course_org.fav_nums = 0
                course_org.save()
            elif int(fav_type) == 3:
                teacher = Teacher.objects.get(id=int(fav_id))
                teacher.fav_nums -= 1
                if teacher.fav_nums < 0:
                    teacher.fav_nums = 0
                teacher.save()
            return HttpResponse('{"status":"success", "msg":"收藏"}', content_type='application/json')
        else:
            user_fav = UserFavorite()
            if int(fav_id) > 0 and int(fav_type) > 0:
                user_fav.user = request.user
                user_fav.fav_type = int(fav_type)
                user_fav.fav_id = int(fav_id)
                user_fav.save()
                if int(fav_type) == 1:
                    course = Course.objects.get(id=int(fav_id))
                    course.fav_nums += 1
                    course.save()
                elif int(fav_type) == 2:
                    course_org = CourseOrg.objects.get(id=int(fav_id))
                    course_org.fav_nums += 1
                    course_org.save()
                elif int(fav_type) == 3:
                    teacher = Teacher.objects.get(id=int(fav_id))
                    teacher.fav_nums += 1
                    teacher.save()
                return HttpResponse('{"status":"success", "msg":"已收藏"}', content_type='application/json')
            else:
                return HttpResponse('{"status":"fail", "msg":"收藏出错"}', content_type='application/json')


class TeacherListView(View):
    def get(self, request):
        all_teachers = Teacher.objects.all()
        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            all_teachers = all_teachers.filter(Q(name__icontains=search_keywords) | Q(work_company__icontains=search_keywords) | Q(work_position__icontains=search_keywords))
        hot_teachers = all_teachers.order_by('-click_nums')[:3]
        sort = request.GET.get('sort', '')
        if sort:
            all_teachers = all_teachers.order_by('-' + sort)
        teacher_nums = all_teachers.count()
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(all_teachers, 5, request=request)
        teachers = p.page(page)
        return render(request, 'teachers-list.html',
                      {'all_teachers': teachers,
                       'teacher_nums': teacher_nums,
                       'hot_teachers': hot_teachers,
                       'sort': sort})


class TeacherDetailView(View):
    def get(self, request, teacher_id):
        teacher = Teacher.objects.get(id=int(teacher_id))
        teacher.click_nums += 1
        teacher.save()
        has_teacher_faved = False
        has_org_faved = False
        if UserFavorite.objects.filter(user=request.user, fav_type=3, fav_id=teacher.id):
            has_teacher_faved = True
        if UserFavorite.objects.filter(user=request.user, fav_type=2, fav_id=teacher.org.id):
            has_org_faved = True
        hot_teachers = Teacher.objects.all().order_by('-click_nums')[:3]
        all_courses = Course.objects.filter(teacher=teacher)
        return render(request, 'teacher-detail.html',
                      {'teacher': teacher,
                       'has_teacher_faved': has_teacher_faved,
                       'has_org_faved': has_org_faved,
                       'hot_teachers': hot_teachers,
                       'all_courses': all_courses})
