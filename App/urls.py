from django.urls import path
from .import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    
    path('', views.Home, name='Home'),

    path('report/',views.Report,name='Report'),
    path('report/detail/<int:report_id>/', views.ReportDetail, name='ReportDetail'),
    path('reportlist/', views.ReportList, name='ReportList'),
    path('report/success/<int:report_id>/', views.ReportSuccess, name='ReportSuccess'),
    path('report/pdf/<int:report_id>/', views.DownloadReportPDF, name='DownloadReportPDF'),
    path('claim/<int:id>/', views.ClaimCase, name='ClaimCase'),
    path('unclaim/<int:id>/', views.UnclaimCase, name='UnclaimCase'),
    path('rescue-details/', views.RescueDetails, name='RescueDetails'),
    path('mark-rescued/<int:id>/', views.MarkRescued, name='MarkRescued'),
    path('finalize-rescue/<int:id>/', views.FinalizeRescue, name='FinalizeRescue'),
    path('RescueExp/<int:id>/', views.RescueExp, name='RescueExp'),
    path('verify-queue/', views.VerifyRescue, name='VerifyRescue'),
    path('VerifyRescueDetail/<int:id>/', views.VerifyRescueDetail, name='VerifyRescueDetail'),


    path('UserRegister', views.UserRegister, name="UserRegister"),
    path('profile/', views.UserProfile, name='UserProfile'),
    path('userlogin/', views.UserLogin, name="UserLogin"),
    path('userlogout/', views.UserLogout, name="UserLogout"),
    path("edit-profile/", views.EditProfile, name="EditProfile"),


    path('animals/', views.AnimalList, name='AnimalAdoptList'),
    path('animals/<int:pk>/', views.AnimalAdoptDetail, name='AnimalAdoptDetail'),
    path('apply-adoption/<int:animal_id>/', views.ApplyAdoption, name='ApplyAdoption'),
    path('add-to-adoption/<int:id>/', views.AddToAdoption, name='AddToAdoption'),
    path('admin/adoptions/process/<int:app_id>/<str:action>/', views.ProcessAdoption, name='ProcessAdoption'),
    path('adoptionsuccess/', views.AdoptionSuccess, name='AdoptionSuccess'),
    path('VerifyAdoption/', views.VerifyAdoption, name='VerifyAdoption'),
    path('VerifyAdoptionDetail/<int:id>/', views.VerifyAdoptionDetail, name='VerifyAdoptionDetail'),
    path('SubmitAdoptionProof/<int:app_id>/', views.SubmitAdoptionProof, name='SubmitAdoptionProof'),
    path('rescued-list/', views.RescuedList, name='RescuedList'),
    path('adopted-list/', views.AdoptedList, name='AdoptedList'),


    path('AdminHome', views.AdminHome, name='AdminHome'),
    path('admin-adoption-dashboard/', views.AdminAdoptionDashboard, name='AdminAdoptionDashboard'),

    path('VolunteerHome/', views.VolunteerHome, name='VolunteerHome'),
    path('VolunteerIns/', views.VolunteerIns, name='VolunteerIns'),
    path('VolunteerWelcome/', views.VolunteerWelcome, name='VolunteerWelcome'),
    path('admin-panel/volunteers/', views.AdminVolunteerDashboard, name='AdminVolunteerDashboard'),
    path('admin-panel/volunteers/approve/<int:profile_id>/', views.ApproveVolunteer, name='ApproveVolunteer'),
    path('admin-panel/volunteers/reject/<int:profile_id>/', views.RejectVolunteer, name='RejectVolunteer'),


    path('about/', views.About, name='About'),

] + static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)


