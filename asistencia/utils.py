from datetime import timedelta
from math import radians, sin, cos, sqrt, atan2


def calcular_horas_netas(hora_entrada, hora_salida, inicio_almuerzo=None, fin_almuerzo=None):
    if not hora_entrada or not hora_salida:
        return None
    total = hora_salida - hora_entrada
    if total < timedelta(0):
        return None
    return total


def obtener_ip_cliente(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def calcular_distancia_gps(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia entre dos coordenadas GPS usando la fórmula de Haversine.
    
    Args:
        lat1, lon1: Latitud y longitud del primer punto (del usuario)
        lat2, lon2: Latitud y longitud del segundo punto (de la oficina)
    
    Returns:
        Distancia en metros
    """
    # Radio de la Tierra en metros
    R = 6371000
    
    # Convertir a radianes
    lat1_rad = radians(float(lat1))
    lon1_rad = radians(float(lon1))
    lat2_rad = radians(float(lat2))
    lon2_rad = radians(float(lon2))
    
    # Diferencias
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula de Haversine
    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distancia = R * c
    return distancia


def validar_ubicacion_gps(latitud_usuario, longitud_usuario, latitud_oficina, 
                          longitud_oficina, radio_permitido_metros=500):
    """
    Valida si el usuario está dentro del radio permitido de la oficina.
    
    Args:
        latitud_usuario, longitud_usuario: Coordenadas del usuario
        latitud_oficina, longitud_oficina: Coordenadas de la oficina
        radio_permitido_metros: Radio permitido en metros (default: 500m)
    
    Returns:
        dict con:
            - 'valido': bool - Si está dentro del radio
            - 'distancia': float - Distancia en metros
            - 'mensaje': str - Mensaje descriptivo
    """
    try:
        distancia = calcular_distancia_gps(latitud_usuario, longitud_usuario, 
                                          latitud_oficina, longitud_oficina)
        
        valido = distancia <= radio_permitido_metros
        
        return {
            'valido': valido,
            'distancia': round(distancia, 2),
            'mensaje': f"Distancia: {round(distancia, 2)}m - {'Ubicación válida' if valido else 'Fuera del rango permitido'}"
        }
    except Exception as e:
        return {
            'valido': False,
            'distancia': None,
            'mensaje': f'Error al validar GPS: {str(e)}'
        }
