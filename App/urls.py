from django.urls import path
from .import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',views.Report,name='Report'),
    path('report/success/<int:report_id>/', views.ReportSuccess, name='ReportSuccess'),
    path('report/pdf/<int:report_id>/', views.DownloadReportPDF, name='DownloadReportPDF'),
] + static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
