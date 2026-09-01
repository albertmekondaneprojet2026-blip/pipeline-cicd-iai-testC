from django.shortcuts import render

# Create your views here.
#from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def project_list(request):
    """Ecran 'Projets' : version minimale, enrichie au Jour 5."""
    return render(request, 'projects/project_list.html', {'projects': []})