from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Pedido, Plato, Orden
from .forms import ClienteRegistroForm, OrdenForm, PlatoForm
from datetime import date, timedelta
from django.http import HttpResponse

def menu(request):
    items = Plato.objects.all()
    return render(request, 'inicio.html', {'menu_items': items})

@login_required
def orden_actual(request, plato_id):
    plato = get_object_or_404(Plato, id=plato_id)
    today = date.today().isoformat()

    # Siempre se crea un nuevo pedido sin buscar uno existente
    orden = None

    if request.method == 'POST':
        form = OrdenForm(request.POST)
        if form.is_valid():
            orden = form.save(commit=False)
            orden.cliente = request.user
            orden.plato = plato
            orden.precio_total = plato.precio * orden.cantidad
            orden.confirmado = False  # No confirmado al añadir al carrito
            orden.estado = 'pendiente'

            # Verificar si es para guardar en el carrito o confirmar
            if 'guardar_carrito' in request.POST:
                messages.success(request, "Pedido guardado en el carrito.")
                orden.save()
                return redirect('carrito')
            elif 'confirmar_pedido' in request.POST:
                orden.confirmado = True
                messages.success(request, "Pedido confirmado.")
                orden.save()
                return redirect('perfil_cliente')
    else:
        form = OrdenForm()

    return render(request, 'orden_actual.html', {'form': form, 'plato': plato, 'today': today})

@login_required
def carrito_view(request):
    pedidos = Orden.objects.filter(cliente=request.user, confirmado=False)
    
    total = sum(pedido.precio_total for pedido in pedidos)
    
    return render(request, 'carrito.html', {
        'pedidos': pedidos,
        'total': total
    })

def confirmar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    if request.method == 'POST':
        pedido.confirmado = True
        pedido.estado = 'pendiente'
        pedido.save()
        return redirect('perfil_cliente')
    return redirect('orden_actual')

@login_required
def guardar_pedido(request, plato_id):
    plato = get_object_or_404(Plato, id=plato_id)
    
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 1))
        fecha_retiro = request.POST.get('fecha_retiro')
        hora_retiro = request.POST.get('hora_retiro')
        
        pedido = Orden.objects.create(
            cliente=request.user,
            plato=plato,
            cantidad=cantidad,
            fecha_retiro=fecha_retiro,
            hora_retiro=hora_retiro,
            precio_total=plato.precio * cantidad,
            confirmado=False
        )
        pedido.save()
        return redirect('carrito')

@login_required
def eliminar_pedido(request, pedido_id):
    pedido = get_object_or_404(Orden, id=pedido_id)
    pedido.delete()
    return redirect('carrito')

def editar_pedido(request, pedido_id):
    pedido = get_object_or_404(Orden, id=pedido_id)

    if request.method == 'POST':
        form = OrdenForm(request.POST, instance=pedido)
        if form.is_valid():
            pedido = form.save(commit=False)
            pedido.precio_total = pedido.cantidad * pedido.plato.precio
            pedido.save()
            return redirect('carrito')
    else:
        form = OrdenForm(instance=pedido)

    return render(request, 'orden_actual.html', {'form': form, 'plato': pedido.plato, 'pedido': pedido})

@login_required
def finalizar_pedido(request, pedido_id):
    pedido = get_object_or_404(Orden, id=pedido_id, cliente=request.user)
    pedido.confirmado = True
    pedido.estado = 'pendiente'
    pedido.save()
    return redirect('perfil_cliente')

def admin_required(login_url='login_admin'):
    return user_passes_test(lambda u: u.is_staff, login_url=login_url)

def mostrar_inicio(request):
    menu_items = Plato.objects.all() 
    return render(request, 'inicio.html', {'menu_items': menu_items})

def login_cliente(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        usuario = authenticate(request, username=username, password=password)
        if usuario is not None:
            login(request, usuario)
            return redirect('pagina_principal')
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos')
    return render(request, 'login_cliente.html')

def login_admin(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('ordenes')
    return render(request, 'login_admin.html')

def registro_cliente(request):
    if request.method == 'POST':
        form = ClienteRegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Te has registrado exitosamente.")
            return redirect('pagina_principal')
        else:
            messages.error(request, "Por favor corrige los errores.")
    else:
        form = ClienteRegistroForm()
    return render(request, 'registro_cliente.html', {'form': form})

def cerrar_sesion(request):
    logout(request)
    return redirect('pagina_principal')

@login_required
def perfil_cliente(request):
    pedidos = Orden.objects.filter(cliente=request.user)
    return render(request, 'perfil_cliente.html', {'pedidos': pedidos})

@login_required
@admin_required()
def menu_admin(request, plato_id=None):
    platos = Plato.objects.all()
    plato = None

    if plato_id:
        plato = get_object_or_404(Plato, id=plato_id)

    if request.method == "POST":
        if plato:
            form = PlatoForm(request.POST, request.FILES, instance=plato)
        else:
            form = PlatoForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect('menu_admin')
    else:
        form = PlatoForm(instance=plato)

    return render(request, 'menu_admin.html', {'platos': platos, 'form': form, 'plato': plato})

@admin_required()
def todas_ordenes(request):
    pedidos_pendientes = Orden.objects.filter(estado='pendiente', confirmado=True)
    pedidos_aceptados = Orden.objects.filter(estado='aceptado')
    pedidos_pagados = Orden.objects.filter(estado='pagado')
    pedidos_cancelados = Orden.objects.filter(estado='cancelado')

    context = {
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_aceptados': pedidos_aceptados,
        'pedidos_pagados': pedidos_pagados,
        'pedidos_cancelados': pedidos_cancelados,
    }
    return render(request, 'ordenes.html', context)

@admin_required()
def aceptar_pedido(request, pedido_id):
    pedido = get_object_or_404(Orden, id=pedido_id)
    if request.method == 'POST':
        pedido.estado = 'aceptado'
        pedido.confirmado = True
        if not pedido.codigo_autenticacion:
            pedido.generar_codigo() 
        pedido.save()
        messages.success(request, f"Pedido aceptado. Código de autenticación: {pedido.codigo_autenticacion}")
    return redirect('ordenes')

@login_required
@admin_required()
def editar_plato(request, plato_id):
    plato = get_object_or_404(Plato, id=plato_id)
    if request.method == "POST":
        plato.nombre = request.POST.get('nombre')
        plato.precio = request.POST.get('precio')
        plato.save()
        return redirect('ordenes')
    return render(request, 'menu_admin.html', {'plato': plato})

@login_required
@admin_required()
def eliminar_plato(request, plato_id):
    plato = get_object_or_404(Plato, id=plato_id)
    plato.delete()
    return redirect('menu_admin')

@admin_required()
def pagado_pedido(request, pedido_id):
    pedido = get_object_or_404(Orden, id=pedido_id)
    if request.method == 'POST':
        # Verificar si ya tiene un código, si no, generar uno
        if not pedido.codigo_autenticacion:
            pedido.generar_codigo()

        pedido.estado = 'pagado'
        pedido.save()

        messages.success(request, f"Pedido marcado como pagado. Código de autenticación: {pedido.codigo_autenticacion}")
    return redirect('ordenes')


@admin_required()
def cancelar_pedido(request, pedido_id):
    pedido = get_object_or_404(Orden, id=pedido_id)
    if request.method == 'POST':
        motivo = request.POST.get('motivo_rechazo')
        if motivo:
            pedido.estado = 'cancelado'
            pedido.motivo_rechazo = motivo
            pedido.save()
            messages.error(request, "Pedido cancelado.")
    return redirect('ordenes')

@admin_required()
def registro_pedidos(request):
    dia_anterior = date.today() - timedelta(days=1)
    
    # Pedidos del día anterior
    pedidos_anteriores = Orden.objects.filter(fecha_retiro=dia_anterior)
    
    # Pedidos con estado pagado y cancelado
    pedidos_pagados = Orden.objects.filter(estado='pagado')
    pedidos_cancelados = Orden.objects.filter(estado='cancelado')

    # Generar archivo TXT si se solicita
    if request.GET.get('descargar') == 'txt':
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="registro_pedidos.txt"'
        
        lines = []
        for pedido in pedidos_anteriores | pedidos_pagados | pedidos_cancelados:
            lines.append(f"Cliente: {pedido.cliente.username}\n")
            lines.append(f"Plato: {pedido.plato.nombre}\n")
            lines.append(f"Cantidad: {pedido.cantidad}\n")
            lines.append(f"Fecha de Retiro: {pedido.fecha_retiro}\n")
            lines.append(f"Hora de Retiro: {pedido.hora_retiro}\n")
            lines.append(f"Precio Total: ${pedido.precio_total}\n")
            lines.append(f"Estado: {pedido.estado}\n")
            if pedido.estado == 'cancelado' and pedido.motivo_rechazo:
                lines.append(f"Motivo de Cancelación: {pedido.motivo_rechazo}\n")
            lines.append(f"Código de Autenticación: {pedido.codigo_autenticacion}\n")
            lines.append("-" * 40 + "\n")
        
        response.writelines(lines)
        return response

    context = {
        'pedidos_anteriores': pedidos_anteriores,
        'pedidos_pagados': pedidos_pagados,
        'pedidos_cancelados': pedidos_cancelados,
        'dia_anterior': dia_anterior
    }
    return render(request, 'registro_pedidos.html', context)

def descargar_registro(request):
    dia_anterior = date.today() - timedelta(days=1)
    pedidos = Orden.objects.filter(fecha_retiro=dia_anterior)
    
    contenido = ""
    for pedido in pedidos:
        contenido += f"Cliente: {pedido.cliente.username}\n"
        contenido += f"Plato: {pedido.plato.nombre}\n"
        contenido += f"Cantidad: {pedido.cantidad}\n"
        contenido += f"Precio Total: ${pedido.precio_total}\n"
        contenido += f"Estado: {pedido.estado}\n"
        contenido += "-"*30 + "\n"

    response = HttpResponse(contenido, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="registro_pedidos.txt"'
    return response
