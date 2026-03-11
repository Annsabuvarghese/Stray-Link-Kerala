# from email.mime import application
# from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings
from urllib3 import request
from .models import ReportSubmit, ReportImage, Condition, Profile,Animal,AdoptionApplication,Organization
from django.db.models import Q

from xhtml2pdf import pisa
from io import BytesIO



def Home(request):
    cases = ReportSubmit.objects.all().order_by('-created_at')[:4]
    animals = Animal.objects.filter(in_adoption=True).exclude(status='Adopted').order_by('-id')[:4]

    context = {
        'cases': cases,
        'animals': animals
    }

    if request.user.is_authenticated:
        # 1. Check for Superuser first
        if request.user.is_superuser:
            return redirect('AdminHome')  # Replace with your actual admin URL name

        # 2. Check for Volunteer status
        try:
            if request.user.profile.is_volunteer:
                return redirect('VolunteerHome')
        except Profile.DoesNotExist:
            pass
 
    return render(request, 'Home.html', context)

# def AdminHome(request):

#     cases = ReportSubmit.objects.all().order_by('-id')[:10]
#     animals = Animal.objects.filter(
#         in_adoption=True
#     ).exclude(status='Adopted').order_by('-id')[:10]
    
#     return render(request, 'AdminHome.html', {
#         'cases': cases,
#         'animals': animals
#     })

@login_required
def Report(request):

        # Default conditions list
    # default_conditions = [
    #     "Injured",
    #     "Sick",
    #     "Pregnant",
    #     "Aggressive",
    #     "Abandoned"
    # ]

    # # Default conditions should be created via migration or management command, not here.
    # for condition in default_conditions:
    #     Condition.objects.get_or_create(name=condition)

    conditions = Condition.objects.all()

    if request.method == "POST":

        # Checkbox values → list
        conditions_list = request.POST.getlist('conditions')
        auto_lat = request.POST.get('auto_latitude')
        auto_lon = request.POST.get('auto_longitude')

        # Force None if string is empty
        if not auto_lat: auto_lat = None
        if not auto_lon: auto_lon = None

        if auto_lat and auto_lon:
            location_source = "gps"
        else:
            location_source = "manual"

        report = ReportSubmit.objects.create(
            user=request.user,
            animal_type=request.POST.get('animal_type'),
            animal_count=request.POST.get('animal_count'),
            manual_location=request.POST.get('manual_location'),
            auto_latitude=auto_lat or None,
            auto_longitude=auto_lon or None,
            location_source=location_source,
        )

        for i in range(1, 5):
            photo = request.FILES.get(f'pic{i}')
            if photo:
                ReportImage.objects.create(report=report, image=photo)

        report.conditions.set(conditions_list)

        try:
        # --- 4. Generate PDF and Send Email ---
            pdf_content = generate_pdf_in_memory(report)
            if pdf_content:
                recipient_list = [
                    'straylinkgov@gmail.com',   
                ]  
                email = EmailMessage(
                    subject=f"URGENT: Official Stray Animal Report #{report.id}",
                    body = f"""
To,
The Concerned Authority,

Subject: URGENT – Official Complaint Regarding Stray Animal Incident (Ref No: STRAY/{report.id})

Respected Sir/Madam,

This is to formally inform you that a stray animal incident has been reported through the StrayLink reporting system.

Incident Details:
-----------------------------------------
Reference Number : STRAY/{report.id}
Date & Time      : {report.created_at.strftime('%d %B %Y, %H:%M')}
Animal Type      : {report.animal_type.title()}
Number Observed  : {report.animal_count}
Location         : {report.manual_location}
Latitude         : {report.auto_latitude}
Longitude        : {report.auto_longitude}
-----------------------------------------

The animal has been reported in the following condition(s):
{", ".join([c.name.title() for c in report.conditions.all()]) if report.conditions.exists() else "Not specified"}

This matter may require immediate attention under applicable animal welfare and public safety regulations.

Please find the attached official complaint document (PDF) containing full details and photographic evidence for your review and necessary action.

Kindly acknowledge receipt of this complaint and initiate appropriate intervention at the earliest.

Thanking you.

Sincerely,
StrayLink Incident Reporting System
(Automated Official Notification)
"""
,             
                from_email=settings.EMAIL_HOST_USER,
                    to=recipient_list,
                )
                # Attach the PDF bytes
                email.attach(f'Report_{report.id}.pdf', pdf_content, 'application/pdf')
                # MIME type stands for Multipurpose Internet Mail Extensions type.
                # It is a standard that tells the browser or email client what type of file is being sent.
                # Send it!
                email.send()
        except Exception as e:
            # We print the error so it shows in your terminal for debugging
            print(f"Failed to send email: {e}")

        
        return redirect('ReportSuccess', report_id=report.id)

    return render(request, 'Report.html',
    {'conditions': conditions,}
    )




def ReportSuccess(request, report_id):
    report = get_object_or_404(ReportSubmit, id=report_id)
    return render(request, 'ReportSuccess.html', {'report': report})

#pip instatall weasyprint,pip install xhtml2pdf




def DownloadReportPDF(request, report_id):
    report = get_object_or_404(ReportSubmit, id=report_id)
    
    # 1. Prepare response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Stray_Report_{report_id}.pdf"'

    # 2. Render Template
    template = get_template('ReportPDF.html')
    html = template.render({'report': report})

    # 3. Generate PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
       return HttpResponse('Error generating PDF', status=500)
    return response



def generate_pdf_in_memory(report):
    #Helper function to create PDF content without saving to disk."""
    template = get_template('ReportPDF.html')
    html = template.render({'report': report})
    result = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)
    
    if pisa_status.err:
        return None
    return result.getvalue()




@login_required
def ReportList(request):
    cases = ReportSubmit.objects.exclude(status='rescued').order_by('-id')


    for case in cases:#extra code is used to add additional information inside each case before sending it to the template.
        try:
            animal = Animal.objects.get(id=case.id)  
            case.animal_obj = animal  
            case.is_in_adoption = AdoptionApplication.objects.filter(
                animal=animal,
                status='Waiting'
            ).exists()
        except Animal.DoesNotExist:
            case.animal_obj = None
            case.is_in_adoption = False

    return render(request, 'ReportList.html', {'cases': cases})




def UserRegister(request):
    if request.method == "POST":
        # User auth fields
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # Profile fields
        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        district = request.POST.get("district")
        city = request.POST.get("city")  
        local_body = request.POST.get("local_body")  # From our new select tag
        ward_no = request.POST.get("ward_no")        # From our new select tag
        house_no = request.POST.get("house_no")
        dob = request.POST.get("dob")

        # Validation logic
        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("UserRegister")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("UserRegister")

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        # Create profile using the edited model fields
        Profile.objects.create(
            user=user,
            full_name=full_name,
            phone=phone,
            address=address,
            district=district,
            local_body=local_body,
            ward_no=ward_no,
            house_no=house_no,
            dob=dob
        )

        login(request, user)
        return redirect("Home") 

    return render(request, "UserRegister.html")


def UserLogin(request):
    if request.method == "POST":
        username_or_email = request.POST.get("username")
        password = request.POST.get("password")

        # Check if input is email
        if User.objects.filter(email=username_or_email).exists():
            user_obj = User.objects.get(email=username_or_email)
            username = user_obj.username
        else:
            username = username_or_email

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("Home")
        else:
            messages.error(request, "Invalid credentials")
            return redirect("UserLogin")
            

    return render(request, "UserLogin.html")



def UserLogout(request):
    logout(request)
    return redirect("Home")

# Ella animalsineyum list cheyyan
def AnimalList(request):
    animals = Animal.objects.all().order_by('-id')
    return render(request, 'AnimalAdoptList.html', 
                  {'animals': animals}
                 )

# Oru animalinte detail page
def AnimalAdoptDetail(request, pk):
    animal = get_object_or_404(Animal, pk=pk)
    return render(request, 'AnimalAdoptDetail.html',
                 {'animal': animal})



@login_required
def ClaimCase(request, id):
    case = get_object_or_404(ReportSubmit, id=id)

    if case.status != 'pending':
        messages.error(request, "This case is no longer open for claiming.")
        return redirect('ReportDetail', report_id=case.id)

    if case.claimed_by:
        messages.warning(request, "Someone else has already claimed this hero mission!")
        return redirect('ReportDetail', report_id=case.id)

    case.claimed_by = request.user
    case.claimed_at = timezone.now()
    case.status = 'in_progress'
    case.save()

    messages.success(request, "You have successfully claimed this case!")
    return redirect('ReportDetail', report_id=case.id)


@login_required
def UnclaimCase(request, id):
    report = get_object_or_404(ReportSubmit, id=id)
    
    if report.claimed_by == request.user:
        report.claimed_by = None
        report.status = 'pending'   
        report.claimed_at = None
        report.save()
        messages.info(request, "Case unclaimed. It is now open for other volunteers.")
    else:
        messages.error(request, "You can only unclaim cases that belong to you.")
    return redirect('ReportDetail', report_id=report.id)




def RescueDetails(request):
    rescued_cases = ReportSubmit.objects.filter(status='rescued')
    return render(request, 'RescueDetails.html', {
        'rescued_cases': rescued_cases
    })

@login_required
def MarkRescued(request, id):

    case = get_object_or_404(ReportSubmit, id=id)

    if case.claimed_by == request.user:
        case.status = 'rescued'
        case.save()

    return redirect('ReportList')

@login_required
def AddToAdoption(request, id):
    report = get_object_or_404(ReportSubmit, id=id)
    

  
    if report.claimed_by != request.user:
        messages.error(request, "You are not authorized to list this animal. Only the rescuer can do this.")
        return redirect('ReportList')


    if report.status != 'rescued':
        messages.warning(request, "Please mark the animal as 'Rescued' before adding it to adoption.")
        return redirect('ReportList')
    
    animal, created = Animal.objects.get_or_create(report=report)
    

    if animal.in_adoption:
        messages.warning(request, "This animal is already in adoption.")
        return redirect('AnimalAdoptDetail', pk=animal.id)
    
    if request.method == 'POST':

        animal.name = request.POST.get('name')
        animal.age = request.POST.get('age')
        animal.breed = request.POST.get('breed')
        animal.gender = request.POST.get('gender')
        
        medical_selected = request.POST.getlist('medical')
        animal.health_status = ", ".join(medical_selected) 
        
        image = request.FILES.get('image')
        if image:
            animal.image = image

        animal.center_type = request.POST.get('center_type')
        animal.center_name = request.POST.get('center_name')
        animal.center_email = request.POST.get('center_email')
        animal.center_phone = request.POST.get('center_phone')
        animal.center_address = request.POST.get('center_address')

        animal.in_adoption = True
        animal.status = "Available"
        animal.save()

        messages.success(request, f"{animal.name} has been listed for adoption!")
        return redirect('AnimalAdoptDetail', pk=animal.id)

    return render(request, 'AddAdopt.html', {'animal': animal})


@login_required
def ApplyAdoption(request, animal_id):
    animal = get_object_or_404(Animal, id=animal_id)

    if animal.status == "Adopted":
        messages.error(request, "Sorry, this animal has already been adopted!")
        return redirect('AnimalAdoptList')


    already_applied = AdoptionApplication.objects.filter(
        animal=animal, 
        applicant_email=request.user.email
    ).exists()
    
    if already_applied:
        messages.warning(request, "You have already submitted an application for this animal.")
        return redirect('UserProfile')

    if request.method == 'POST':
    
        app = AdoptionApplication.objects.create(
            animal=animal,
            applicant_name=request.POST.get('name'),
            applicant_email=request.POST.get('email'),
            applicant_phone=request.POST.get('phone'),
            is_18=request.POST.get('is_18'),
            stable_income=request.POST.get('stable_income'),
            residence_type=request.POST.get('residence_type'),
            home_ownership=request.POST.get('home_ownership'),
            landlord_permission=request.POST.get('landlord_permission'),
            has_pet=request.POST.get('has_pet'),
            current_pet_type=request.POST.get('current_pet_type'),
            env_quality=request.POST.get('env_quality'),
            status="Waiting"
        )

  
        center_email = animal.center_email
        if center_email:
            try:
                subject = f"URGENT: Adoption Application for {animal.name} (Ref #{app.id})"
                body = f"""
Dear {animal.center_name} Team,

A new formal application has been submitted through StrayLink for an animal in your care.

=======================================================
1. ANIMAL INFORMATION
=======================================================
Name: {animal.name}
Reference ID: {animal.id}
Breed: {animal.breed if animal.breed else 'Not Specified'}
Age Range: {animal.age}
Medical History: {animal.health_status}

=======================================================
2. APPLICANT CONTACT DETAILS
=======================================================
Full Name: {app.applicant_name}
Email: {app.applicant_email}
Phone: {app.applicant_phone}
Address: {request.user.profile.house_no}, {request.user.profile.address}
Location: {request.user.profile.local_body}, {request.user.profile.district}

=======================================================
3. ELIGIBILITY & HOUSEHOLD PROFILE
=======================================================
Age 18+: {app.is_18.upper()}
Type of Residence: {app.residence_type.title()} ({app.home_ownership.title()})
Landlord Permission: {app.landlord_permission.title()}
Home Environment Quality: {app.env_quality.upper()}

Income Stability: {app.stable_income.upper()}


Current Pet Owner: {app.has_pet.upper()}
Existing Pets: {app.current_pet_type.title()}

=======================================================
4. NEXT STEPS
=======================================================
1. Review the applicant's details above.
2. You can contact the applicant directly at {app.applicant_phone}.
3. Update the status in your StrayLink Dashboard.

Best regards,
StrayLink Automated System
"""
                email = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=settings.EMAIL_HOST_USER,
                    to=[center_email],
                    reply_to=[app.applicant_email],
                )
                email.send()
            except Exception as e:
                print(f"Email Error: {e}")

        return redirect('AdoptionSuccess')

    return render(request, 'AdoptApplication.html', {'animal': animal})


@login_required
def AdminAdoptionDashboard(request):

    applications = AdoptionApplication.objects.all().order_by('-applied_at')
    return render(request, 'AdminAdoptionDashboard.html', 
                  {'applications': applications})

@login_required
def ProcessAdoption(request, app_id, action):
    if not request.user.is_staff:
        return redirect('Home')

    application = get_object_or_404(AdoptionApplication, id=app_id)

    if action == 'accept':
        application.status = 'Accepted'

    elif action == 'reject':
        application.status = 'Rejected'

    application.save()
    return redirect('AdminAdoptionDashboard')

def AdoptionSuccess(request):
    return render(request,'AdoptionSuccess.html')




def UserProfile(request):
    
    profile = request.user.profile

    # Adoption applications
    user_applications = AdoptionApplication.objects.filter(
        applicant_email=request.user.email
    )

    # Reports submitted by user
    my_reports = ReportSubmit.objects.filter(
        user=request.user
    ).order_by("-created_at")

    # Rescues done by volunteer
    my_rescues = ReportSubmit.objects.filter(
        claimed_by=request.user,
        status="rescued"
    ).order_by("-verified_at")


    return render(request, 'UserProfile.html', {
        "profile": profile,
        "user_applications": user_applications,
        "my_reports": my_reports,
        "my_rescues": my_rescues,
    })



@login_required
def FinalizeRescue(request, id):
    report = get_object_or_404(ReportSubmit, id=id)

    # Security: Only the person who claimed it can finalize it
    if report.claimed_by != request.user:
        messages.error(request, "Access Denied.")
        return redirect('ReportList')

    if request.method == 'POST':
        # 1. Capture the 'Live' proof
        proof_pic = request.FILES.get('rescue_image')
        notes = request.POST.get('rescue_notes')

        if not proof_pic:
            messages.error(request, "You must provide a live photo of the animal at the center/safe-zone.")
            return render(request, 'FinalizeRescue.html', {'report': report})

        # 2. Save the data
        report.rescue_image = proof_pic
        report.rescue_notes = notes
        report.status = 'awaiting_verification' # 
        report.is_verified_rescue = False  # This will be set to True by admin after verification
        report.save()

        messages.success(request, "Proof submitted! Waiting for Admin to verify and mark as Rescued.")
        return redirect('ReportList')

    return render(request, 'FinalizeRescue.html', {'report': report})



@login_required
def ReportDetail(request, report_id):
    report = get_object_or_404(ReportSubmit, id=report_id)
    images = report.images.all()
    
    # Logic to check adoption status (similar to your ReportList logic)
    is_in_adoption = False
    animal_obj = None
    try:
        from .models import Animal
        animal_obj = Animal.objects.get(report=report)
        is_in_adoption = animal_obj.in_adoption
    except:
        pass

    return render(request, 'ReportDetail.html', {
        'report': report,
        'images': images,
        'is_in_adoption': is_in_adoption,
        'animal_obj': animal_obj
    })

def About(request):
    return render(request,'About.html')


@login_required
def VolunteerIns(request):
    if request.method == "POST":
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        profile.is_volunteer_pending = True
        profile.is_volunteer = False
        profile.save()
        
        messages.success(request, "Welcome to the team! You are now a StrayLink Volunteer. 🧡")
        return redirect('UserProfile')
    
    return render(request, 'VolunteerIns.html')

@login_required
def VolunteerWelcome(request):
    return render(request, 'VolunteerWelcome.html')


@login_required
def RescueExp(request,id):
    report = get_object_or_404(ReportSubmit, id=id)
    return render(request, 'RescueExp.html', {'report': report})


@login_required
def VolunteerIns(request):
    if request.method == "POST":
        # related_name='profile' upayogichu profile edukunnu
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        profile.is_volunteer_pending = True
        profile.is_volunteer = False # Admin approve cheythaal mathram True aakum
        profile.save()
        
        messages.success(request, "Ningalude application ayachittundu. Admin approval-nu shesham update labhikku.")
        return redirect('UserProfile')
    
    return render(request, 'VolunteerIns.html')

@login_required
def AdminVolunteerDashboard(request):
    if not request.user.is_staff:
        messages.error(request, "Access Denied. Admins only.")
        return redirect('Home')
    
    # Request ayacha pakshe approve aakaathavar
    pending_profiles = Profile.objects.filter(is_volunteer_pending=True, is_volunteer=False)
    
    return render(request, 'AdminVolDashboard.html', {
        'pending_profiles': pending_profiles
    })

@login_required
def ApproveVolunteer(request, profile_id):
    if not request.user.is_staff:
        return redirect('Home')
    
    profile = get_object_or_404(Profile, id=profile_id)
    profile.is_volunteer = True
    profile.is_volunteer_pending = False # Process poorthiyaayi
    profile.save()
    
    messages.success(request, f"{profile.full_name} ippol official volunteer aanu!")
    return redirect('AdminVolunteerDashboard')

@login_required
def RejectVolunteer(request, profile_id):
    if not request.user.is_staff:
        return redirect('Home')
    
    profile = get_object_or_404(Profile, id=profile_id)
    profile.is_volunteer_pending = False # Reset the pending status
    profile.save()
    
    messages.warning(request, f"{profile.full_name}'s volunteer request has been removed.")
    return redirect('AdminVolunteerDashboard')


def VolunteerHome(request):
    # Get the latest 10 rescue reports
    cases = ReportSubmit.objects.all().order_by('-id')[:4]
    
    # FIX: Show all animals marked for adoption except those already Adopted
    animals = Animal.objects.filter(
        in_adoption=True
    ).exclude(status='Adopted').order_by('-id')[:4]
    
    return render(request, 'VolunteerHome.html', {
        'cases': cases,
        'animals': animals
    })
@login_required
def FinalizeRescue(request,id):
    # Fetch the specific report
    report = get_object_or_404(ReportSubmit, id=id)

    # Logic: Only the person who 'claimed' the report (or an admin) should be able to finalize it
    if report.claimed_by != request.user and not request.user.is_staff:
        messages.error(request, "You are not authorized to finalize this rescue.")
        return redirect('Home')

    if request.method == 'POST':
        rescue_img = request.FILES.get('rescue_image')
        notes = request.POST.get('rescue_notes')

        if rescue_img:
            # Update report details
            report.rescue_image = rescue_img
            report.rescue_notes = notes
            report.status = 'awaiting_verification' # Moves it to admin review
            report.save()

            messages.success(request, "Rescue proof submitted! Once an admin verifies it, the case will be closed. Great job!")
            return redirect('Home')
        else:
            messages.error(request, "Please upload a photo as proof of rescue.")

    return render(request, 'FinalizeRescue.html', {'report': report})


@login_required
def VerifyRescue(request):  # Removed 'id' from here because this is the LIST view
    # 1. Permission Check
    is_volunteer = getattr(request.user.profile, 'is_volunteer', False)
    if not (request.user.is_staff or is_volunteer):
        messages.error(request, "Access denied. Only volunteers can verify rescues.")
        return redirect('Home')

    # 2. Fetch all reports that have proof but aren't verified
    pending_verifications = ReportSubmit.objects.filter(
        status='awaiting_verification', 
        is_verified_rescue=False
    ).exclude(rescue_image='').order_by('-created_at')

    return render(request, 'VerifyRescue.html', {
        'pending_verifications': pending_verifications
    })

@login_required
def VerifyRescueDetail(request, id):
    # This function handles the specific Approval/Rejection
    report = get_object_or_404(ReportSubmit, id=id)
    is_volunteer = getattr(request.user.profile, 'is_volunteer', False)

    # Permission check
    if not (request.user.is_staff or is_volunteer):
        messages.error(request, "Access Denied.")
        return redirect('Home')

    # Prevent self-verification
    if report.claimed_by == request.user and not request.user.is_staff:
        messages.warning(request, "You cannot verify your own mission. Please wait for another volunteer.")
        return redirect('VerifyRescue')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            report.status = 'rescued'
            report.is_verified_rescue = True
            report.verified_at = timezone.now()
            report.save()
            messages.success(request, f"Mission #{report.id} Approved! Animal marked as safe. 🐾")
        
        elif action == 'reject':
            report.rescue_image = None
            report.rescue_notes = ""
            report.status = 'in_progress'
            report.save()
            messages.warning(request, f"Proof for Mission #{report.id} was rejected and sent back.")

        # After action, go back to the QUEUE to see other cases
        return redirect('VerifyRescue')

    return render(request, 'VerifyRescueDetail.html', {'report': report})

@login_required
def VerifyAdoption(request):
    is_volunteer = getattr(request.user.profile, 'is_volunteer', False)

    if not (request.user.is_staff or is_volunteer):
        messages.error(request, "Access denied.")
        return redirect('Home')

    pending_proofs = AdoptionApplication.objects.filter(
        is_submitted_for_final_verify=True,
        status='Proof_Submitted' 
    ).order_by('-applied_at')

    return render(request, 'VerifyAdoption.html', {
        'pending_adoptions': pending_proofs
    })
@login_required
def VerifyAdoptionDetail(request, id):

    is_volunteer = getattr(request.user.profile, 'is_volunteer', False)
    if not (request.user.is_staff or is_volunteer):
        messages.error(request, "Access denied.")
        return redirect('Home')

    application = get_object_or_404(AdoptionApplication, id=id)
    animal = application.animal

    if application.applicant_email == request.user.email and not request.user.is_staff:
        messages.warning(request, "You cannot verify your own adoption proof.")
        return redirect('VerifyAdoption')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            # Proof ഓക്കെയാണ്, ഇനി പട്ടി ഒഫീഷ്യൽ ആയി Adopted ആണ്
            animal.status = 'Adopted'
            animal.save()
            application.status = 'Verified' # ഫൈനൽ സ്റ്റാറ്റസ്
            application.save()
            messages.success(request, f"Proof Approved! {animal.name} status updated to Adopted.")

        elif action == 'reject':
            # Proof ശരിയല്ല, മൃഗം വീണ്ടും ലഭ്യമാണ്
            animal.status = 'Available'
            animal.save()
            application.status = 'Rejected'
            application.is_submitted_for_final_verify = False
            application.save()
            messages.warning(request, "Proof Rejected. Animal is now back to Available status.")

        return redirect('VerifyAdoption')

    return render(request, 'VerifyAdoptionDetail.html', {'application': application})

@login_required
def SubmitAdoptionProof(request, app_id):
    # Ensure the person uploading is the person who applied
    application = get_object_or_404(AdoptionApplication, id=app_id, applicant_email=request.user.email)
    
    if request.method == "POST":
        img1 = request.FILES.get('proof1')
        img2 = request.FILES.get('proof2')
        notes = request.POST.get('notes')
        
        if img1:
            # 1. Update Application Proof
            application.proof_image_1 = img1
            application.proof_image_2 = img2
            application.user_notes = notes
            application.is_submitted_for_final_verify = True
            application.status = 'Proof_Submitted' # Automatically mark as accepted since they have the pet
            application.save()

            messages.success(request, "Proof submitted! Waiting for volunteer verification.")
            return redirect('UserProfile')
        else:
            messages.error(request, "Please provide a photo to finalize the record.")

    return render(request, 'FinalizeAdoption.html', {'application': application})

@login_required
def RescuedList(request):

    rescued_cases = ReportSubmit.objects.filter(
        status='rescued',
        is_verified_rescue=True
    ).order_by('-verified_at')

    return render(request, 'RescuedList.html', {
        'rescued_cases': rescued_cases
    })

@login_required
def AdoptedList(request):

    adopted_animals = Animal.objects.filter(status='Adopted')
    return render(request, 'AdoptedList.html', {
        'adopted_animals': adopted_animals,
    })




@login_required
def EditProfile(request):

    profile = request.user.profile

    if request.method == "POST":

        dob = request.POST.get("dob")
        profile.dob = dob if dob else None

        profile.image = request.FILES.get("image") or profile.image  # Keep existing image if no new one uploaded
        profile.full_name = request.POST.get("full_name")
        profile.phone = request.POST.get("phone")
        profile.district = request.POST.get("district")
        profile.city = request.POST.get("city")
        profile.address = request.POST.get("address")
        profile.local_body = request.POST.get("local_body")
        profile.ward_no = request.POST.get("ward_no")
        profile.house_no = request.POST.get("house_no")
        profile.address = request.POST.get("address")

        profile.save()

        return redirect("UserProfile")

    return render(request, "EditProfile.html", {"profile": profile})





# Normal User Registration
def UserRegister(request):
    return handle_registration(request, is_volunteer=False)

# Direct Volunteer Registration
def VolunteerRegister(request):
    return handle_registration(request, is_volunteer=True)

# Shared logic for both
def handle_registration(request, is_volunteer=False):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        district = request.POST.get("district")
        city = request.POST.get("city")  
        local_body = request.POST.get("local_body")
        ward_no = request.POST.get("ward_no")
        house_no = request.POST.get("house_no")
        dob = request.POST.get("dob")
        image= request.FILES.get("image")  
        

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect(request.path)

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect(request.path)

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        # Create profile
        Profile.objects.create(
            user=user,
            full_name=full_name,
            phone=phone,
            address=address,
            district=district,
            city=city,
            local_body=local_body,
            ward_no=ward_no,
            house_no=house_no,
            dob=dob if dob else None,
            is_volunteer=is_volunteer,
            image=image
        )

        login(request, user)
        return redirect("Home")

    return render(request, "UserRegister.html", {"is_volunteer": is_volunteer})








def OrganizationRegister(request):

    if request.method == "POST":

        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        org_type = request.POST.get("org_type")

        district = request.POST.get("district")
        city = request.POST.get("city")
        local_body = request.POST.get("local_body")

        address = request.POST.get("address")
        reg_no = request.POST.get("registration_number")

        image = request.FILES.get("image")

        Organization.objects.create(
            name=name,
            email=email,
            phone=phone,
            org_type=org_type,
            district=district,
            city=city,
            local_body=local_body,
            address=address,
            registration_number=reg_no,
            image=image
        )

        return redirect("Home")

    return render(request,"OrganizationRegister.html")







def OrganizationDisplay(request):

    org_type = request.GET.get("type")

    if org_type:
        organizations = Organization.objects.filter(org_type=org_type)
    else:
        organizations = Organization.objects.all()

    return render(request, "OrganizationDisplay.html", {
        "organizations": organizations,
        "selected_type": org_type
    })


def OrganizationDetail(request, org_id):

    org = Organization.objects.get(id=org_id)

    return render(request, "OrganizationDetail.html", {
        "org": org
    })











@login_required
def OurVolunteer(request):

    user_profile = request.user.profile

    city_filter = request.GET.get("city")
    local_body_filter = request.GET.get("local_body")

    volunteers = Profile.objects.filter(is_volunteer=True)

    # Apply filters
    if city_filter:
        volunteers = volunteers.filter(city=city_filter)

    if local_body_filter:
        volunteers = volunteers.filter(local_body=local_body_filter)

    # Prioritize nearby volunteers
    volunteers = sorted(
        volunteers,
        key=lambda v: (
            v.city != user_profile.city,
            v.local_body != user_profile.local_body
        )
    )

    # For filter dropdown
    cities = Profile.objects.filter(is_volunteer=True).values_list("city", flat=True).distinct()
    local_bodies = Profile.objects.filter(is_volunteer=True).values_list("local_body", flat=True).distinct()

    return render(request, "OurVolunteer.html", {
        "volunteers": volunteers,
        "cities": cities,
        "local_bodies": local_bodies,
        "selected_city": city_filter,
        "selected_local_body": local_body_filter
    })


def VolunteerDetail(request, volunteer_id):

    volunteer = get_object_or_404(Profile, id=volunteer_id, is_volunteer=True)

    return render(request, "VolunteerDetail.html", {
        "volunteer": volunteer
    })

def Contact(request):
    return render(request, "Contact.html")


def AdminHome(request):
    # Get the latest 10 rescue reports
    cases = ReportSubmit.objects.all().order_by('-id')[:4]
    
    # FIX: Show all animals marked for adoption except those already Adopted
    animals = Animal.objects.filter(
        in_adoption=True
    ).exclude(status='Adopted').order_by('-id')[:4]
    
    return render(request, 'AdminHome.html', {
        'cases': cases,
        'animals': animals
    })