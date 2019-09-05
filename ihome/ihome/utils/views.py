from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect

def get_html_file(request,file_name):
    if file_name != "favicon.ico":
        file_name = "/static/html/" + file_name

    params = request.GET
    if params:
        result = urlencode(params)
        return redirect(file_name + '?{}'.format(result))

    return redirect(file_name)


def index(request):
    return redirect('/static/html/index.html')



class LoginRequiredMixin(object):
    """验证用户是否登录的工具类"""

    # 重写as_view()函数
    @classmethod
    def as_view(cls,**initkwargs):
        # 调用父类的as_view()方法
        view = super().as_view()
        # 添加装饰行为
        return login_required(view)