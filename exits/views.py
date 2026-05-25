from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ExitProcess, ExitChecklist
from .forms import ExitProcessForm, ExitChecklistForm, ExitChecklistStatusForm

@login_required
def exit_list(request):
    exits = ExitProcess.objects.all()
    return render(request, 'exits/list.html', {'exits': exits})

@login_required
def exit_detail(request, pk):
    exit_process = get_object_or_404(ExitProcess, pk=pk)
    checklist_items = exit_process.checklist_items.all()
    return render(request, 'exits/detail.html', {'exit_process': exit_process, 'checklist_items': checklist_items})

@login_required
def exit_create(request):
    if request.method == 'POST':
        form = ExitProcessForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exit process created successfully')
            return redirect('exits:list')
    else:
        form = ExitProcessForm()
    return render(request, 'exits/form.html', {'form': form, 'title': 'Create Exit Process'})

@login_required
def exit_update(request, pk):
    exit_process = get_object_or_404(ExitProcess, pk=pk)
    if request.method == 'POST':
        form = ExitProcessForm(request.POST, instance=exit_process)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exit process updated successfully')
            return redirect('exits:detail', pk=exit_process.pk)
    else:
        form = ExitProcessForm(instance=exit_process)
    return render(request, 'exits/form.html', {'form': form, 'exit_process': exit_process, 'title': 'Update Exit Process'})

@login_required
def checklist_add(request, exit_id):
    exit_process = get_object_or_404(ExitProcess, pk=exit_id)
    if request.method == 'POST':
        form = ExitChecklistForm(request.POST)
        if form.is_valid():
            checklist_item = form.save(commit=False)
            checklist_item.exit_process = exit_process
            checklist_item.save()
            messages.success(request, 'Checklist item added')
            return redirect('exits:detail', pk=exit_process.pk)
    else:
        form = ExitChecklistForm()
    return render(request, 'exits/checklist_form.html', {'form': form, 'exit_process': exit_process})

@login_required
def checklist_update(request, pk):
    checklist_item = get_object_or_404(ExitChecklist, pk=pk)
    if request.method == 'POST':
        form = ExitChecklistStatusForm(request.POST, instance=checklist_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Checklist item updated')
            return redirect('exits:detail', pk=checklist_item.exit_process.pk)
    else:
        form = ExitChecklistStatusForm(instance=checklist_item)
    return render(request, 'exits/checklist_update.html', {'form': form, 'checklist_item': checklist_item})
