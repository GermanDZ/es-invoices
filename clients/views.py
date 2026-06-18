"""Owner-scoped client CRUD (T-015 Operation 5).

Mirrors the certificates app view shape: every view is ``@login_required`` and
every lookup filters by ``owner=request.user`` (``get_object_or_404`` against the
owner's queryset), so a user can never reach another user's client — a
cross-owner request is a 404, not a 403 leak (requirement 4).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClientForm
from .models import Client


@login_required
def client_list(request):
    clients = Client.objects.filter(owner=request.user)
    return render(request, "clients/list.html", {"clients": clients})


@login_required
def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.owner = request.user
            client.save()
            messages.success(request, "Client saved.")
            return redirect("clients:list")
    else:
        form = ClientForm()
    return render(request, "clients/form.html", {"form": form, "mode": "create"})


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk, owner=request.user)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, "Client updated.")
            return redirect("clients:list")
    else:
        form = ClientForm(instance=client)
    return render(
        request, "clients/form.html", {"form": form, "mode": "edit", "client": client}
    )


@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk, owner=request.user)
    if request.method == "POST":
        client.delete()
        messages.success(request, "Client deleted.")
        return redirect("clients:list")
    return render(request, "clients/confirm_delete.html", {"client": client})
