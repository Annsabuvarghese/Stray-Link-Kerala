from django.shortcuts import render,redirect,get_object_or_404
from .models import ReportSubmit,ReportImage,Condition
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import os
from django.conf import settings
from io import BytesIO
from django.core.mail import EmailMessage

def Report(request):
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

        # try:
        # --- 4. Generate PDF and Send Email ---
        pdf_content = generate_pdf_in_memory(report)#function:generate_pdf_in_memory
        if pdf_content:
                recipient_list = [
                    'straylinkgov@gmail.com',   # The NGO/Gov email
                    'annsabu1111@gmail.com'  # Your monitoring email
                ]  
                email = EmailMessage(
                    subject=f"URGENT: Official Stray Animal Report #{report.id}",
                    body=(
                        f"Hello, \n\n"
                        f"A new stray animal incident has been reported.\n"
                        f"Type: {report.animal_type}\n"
                        f"Location: {report.manual_location}\n\n"
                        f"Latitude: {report.auto_latitude}\n\n"
                        f"Longitude: {report.auto_longitude}\n\n"
                        f"Please see the attached PDF for full details, coordinates, and photos."
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    to=recipient_list,
                )
                # Attach the PDF bytes
                email.attach(f'Report_{report.id}.pdf', pdf_content, 'application/pdf')
                # Send it!
                email.send()
        # except Exception as e:
        #     # We print the error so it shows in your terminal for debugging
        #     print(f"Failed to send email: {e}")

        # redirect to success page
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