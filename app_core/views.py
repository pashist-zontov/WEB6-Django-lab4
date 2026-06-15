from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Request, Comment
from .forms import RequestForm, CommentForm


def is_mod(user):
    return user.is_superuser or user.groups.filter(name='Модератор').exists()

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
def mod_panel(request):
    requests = Request.objects.filter(status__in=['NEW', 'IN_PROGRESS']).order_by('-created_at')
    return render(request, 'app_core/mod_panel.html', {'requests' : requests})