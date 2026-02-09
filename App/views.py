from django.shortcuts import render,redirect

# Create your views here.
def Report(request):
    return render(request,"Report.html")
