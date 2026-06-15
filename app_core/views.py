from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Request, History
from .forms import RequestForm, CommentForm


def is_mod(user):
    return user.is_superuser or user.groups.filter(name='Модератор').exists()


@login_required
def request_create(request):
    if request.method == 'POST':
        form = RequestForm(request.POST, request.FILES)
        if form.is_valid():
            req = form.save(commit=False)
            req.owner = request.user
            req.save()
            return redirect('request_detail', pk=req.pk)
    else:
        form = RequestForm()

    context = {
        'form': form,
        'title': 'Создать заявку'
    }

    return render(request, 'app_core/request_form.html', context)


@login_required
def request_edit(request, pk):
    req = get_object_or_404(Request, pk=pk)
    if not (is_mod(request.user) or req.owner == request.user):
        return redirect('request_list')
    
    if request.method == 'POST':
        form = RequestForm(request.POST, request.FILES, instance=req)
        if form.is_valid():
            form.save()
            return redirect('request_detail', pk=req.pk)
    else:
        form = RequestForm(instance=req)
    
    context = {
        'form': form,
        'title': "Редактировать заявку"
    }

    return render(request, 'app_core/request_form.html', context)


@login_required
def request_list(request):
    status_filter = request.GET.get('status', '')
    queryset = Request.objects.select_related('owner').order_by('-created_at')


    # Обычный пользователь видит только свои заявки. Модератор - все
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    if not is_mod(request.user):
        queryset = queryset.filter(owner=request.user)
    
    
    return render(request, 'app_core/request_list.html', {'requests': queryset})


@login_required
def request_detail(request, pk):
    req = get_object_or_404(Request, pk=pk)
    if not is_mod(request.user) and req.owner != request.user:
        return redirect('request_list')
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.request = req
            comment.author = request.user
            comment.save()
            return redirect('request_detail', pk=pk)
    else:
        form = CommentForm()
    
    context = {'request': req, 'form': form}

    return render(request, 'app_core/request_detail.html', context)


@login_required
@user_passes_test(is_mod)
def change_status(request, pk):
    req = get_object_or_404(Request, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        old_status = req.status
        
        # Валидация статуса
        valid_statuses = [choice[0] for choice in Request.STATUS_CHOICES]
        if new_status in valid_statuses and new_status != old_status:

            # Блок получения старого и нового статусов на русском языке
            old_status_display = req.get_status_display()
            req.status = new_status
            req.save()
            new_status_display = req.get_status_display()
            
            
            # Запись в историю изменений
            History.objects.create(
                request=req,
                user=request.user,
                action='STATUS_CHANGE',
                details={
                    'old_status': old_status,
                    'new_status': new_status,
                    'message': f'Статус заявки с "{old_status_display}" был изменён на "{new_status_display}"'
                }
            )
            messages.success(request, f'Статус заявки #{req.id} изменён на "{req.get_status_display()}"')
        else:
            messages.error(request, 'Недопустимый статус или статус не изменился')
    
    # Возврат пользователя на панель модератора
    return redirect('mod_panel')


@login_required
@user_passes_test(is_mod)
def mod_panel(request):
    status_filter = request.GET.get('status', '')

    queryset = Request.objects.select_related('owner').order_by('-updated_at')

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # Филлерные статы для карточек
    statuses_amount = {
        'total': Request.objects.count(),
        'new': Request.objects.filter(status='NEW').count(),
        'in_progress': Request.objects.filter(status='IN_PROGRESS').count(),
        'finished': Request.objects.filter(status='FINISHED').count(),
        'closed': Request.objects.filter(status='CLOSED').count()
    }

    context = {
        'requests': queryset,
        'stats': statuses_amount,
        'current_filter': status_filter
    }

    return render(request, 'app_core/mod_panel.html', context)