from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        'message': 'CashBook API',
        'version': '1.0',
        'endpoints': {
            'admin': '/admin/',
            'auth': '/api/auth/',
            'api': '/api/v1/',
            'docs': {
                'register': '/api/auth/register/',
                'login': '/api/auth/login/',
                'cashbooks': '/api/v1/cashbooks/',
                'transactions': '/api/v1/transactions/',
                'categories': '/api/v1/categories/',
                'summary': '/api/v1/summary/<cashbook_id>/',
            }
        }
    })

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/v1/', include('books.urls')),
]
