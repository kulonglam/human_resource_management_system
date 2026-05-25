from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Asset, AssetAssignment
from .forms import AssetForm, AssetAssignmentForm, AssetReturnForm

@login_required
def asset_list(request):
    assets = Asset.objects.all()
    return render(request, 'assets/list.html', {'assets': assets})

@login_required
def asset_detail(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    assignments = asset.assignments.all()
    return render(request, 'assets/detail.html', {'asset': asset, 'assignments': assignments})

@login_required
def asset_create(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asset created successfully')
            return redirect('asset_list')
    else:
        form = AssetForm()
    return render(request, 'assets/form.html', {'form': form, 'title': 'Create Asset'})

@login_required
def asset_update(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asset updated successfully')
            return redirect('asset_detail', pk=asset.pk)
    else:
        form = AssetForm(instance=asset)
    return render(request, 'assets/form.html', {'form': form, 'asset': asset, 'title': 'Update Asset'})

@login_required
def asset_assign(request):
    if request.method == 'POST':
        form = AssetAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            asset = assignment.asset
            asset.current_status = 'assigned'
            asset.save()
            messages.success(request, 'Asset assigned successfully')
            return redirect('asset_list')
    else:
        form = AssetAssignmentForm()
    return render(request, 'assets/assign.html', {'form': form})

@login_required
def asset_return(request, pk):
    assignment = get_object_or_404(AssetAssignment, pk=pk, status='assigned')
    if request.method == 'POST':
        form = AssetReturnForm(request.POST, instance=assignment)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.status = 'returned'
            assignment.save()
            asset = assignment.asset
            asset.current_status = 'available'
            asset.save()
            messages.success(request, 'Asset returned successfully')
            return redirect('asset_list')
    else:
        form = AssetReturnForm(instance=assignment)
    return render(request, 'assets/return.html', {'form': form, 'assignment': assignment})

@login_required
def assignment_list(request):
    assignments = AssetAssignment.objects.all()
    return render(request, 'assets/assignments.html', {'assignments': assignments})
