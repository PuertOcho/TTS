#!/usr/bin/env python3
"""
Script de verificación rápida para el sistema de comparación TTS
Verifica que todos los componentes estén listos antes de la comparación completa
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_deps():
    """Verifica dependencias de Python"""
    try:
        import requests
        import psutil
        print("✅ Dependencias Python: OK")
        return True
    except ImportError as e:
        print(f"❌ Dependencias Python faltantes: {e}")
        print("   Ejecuta: pip install -r requirements_comparison.txt")
        return False

def check_docker():
    """Verifica Docker"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker: {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker no disponible")
            return False
    except:
        print("❌ Docker no instalado")
        return False

def check_docker_compose():
    """Verifica Docker Compose"""
    try:
        result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker Compose: OK")
            return True
        else:
            print("❌ Docker Compose no disponible")
            return False
    except:
        print("❌ Docker Compose no disponible")
        return False

def check_gpu():
    """Verifica GPU NVIDIA"""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            # Extraer información básica
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Driver Version' in line:
                    print(f"✅ GPU NVIDIA: {line.strip()}")
                    return True
            print("✅ GPU NVIDIA: Disponible")
            return True
        else:
            print("⚠️ GPU NVIDIA: No disponible (usará CPU)")
            return False
    except:
        print("⚠️ GPU NVIDIA: No disponible (usará CPU)")
        return False

def check_directories():
    """Verifica estructura de directorios"""
    required_dirs = [
        "azure-tts-ms",
        "f5-tts-ms", 
        "kokoro-tts-ms",
        "xtts-v2-tts-ms"
    ]
    
    missing = []
    for dir_name in required_dirs:
        if not Path(dir_name).is_dir():
            missing.append(dir_name)
    
    if missing:
        print(f"❌ Directorios faltantes: {', '.join(missing)}")
        return False
    else:
        print("✅ Estructura de directorios: OK")
        return True

def check_ports():
    """Verifica puertos libres"""
    import socket
    
    ports = [5001, 5002, 5004, 5005]
    busy_ports = []
    
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:  # Puerto ocupado
            busy_ports.append(port)
    
    if busy_ports:
        print(f"⚠️ Puertos ocupados: {busy_ports}")
        print("   El script intentará detener servicios automáticamente")
        return True  # No es crítico, se puede manejar
    else:
        print("✅ Puertos libres: OK")
        return True

def check_disk_space():
    """Verifica espacio en disco"""
    import shutil
    
    free_bytes = shutil.disk_usage('.').free
    free_gb = free_bytes / (1024**3)
    
    if free_gb >= 2:
        print(f"✅ Espacio en disco: {free_gb:.1f} GB disponibles")
        return True
    else:
        print(f"⚠️ Espacio en disco bajo: {free_gb:.1f} GB disponibles")
        print("   Se recomienda al menos 2GB libres")
        return free_gb >= 1  # Mínimo 1GB

def main():
    print("🔍 VERIFICACIÓN DEL SISTEMA PARA COMPARACIÓN TTS")
    print("=" * 50)
    
    checks = [
        ("Dependencias Python", check_python_deps),
        ("Docker", check_docker),
        ("Docker Compose", check_docker_compose),
        ("GPU NVIDIA", check_gpu),
        ("Estructura de directorios", check_directories),
        ("Puertos disponibles", check_ports),
        ("Espacio en disco", check_disk_space)
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Error verificando {name}: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    
    critical_checks = results[:5]  # Los primeros 5 son críticos
    optional_checks = results[5:]  # Los últimos son opcionales
    
    if all(critical_checks):
        print("🎉 ¡SISTEMA LISTO PARA COMPARACIÓN!")
        print("   Puedes ejecutar: ./run_tts_comparison.sh")
        
        if not all(optional_checks):
            print("\n⚠️ Advertencias menores detectadas (no críticas)")
        
        return True
    else:
        print("❌ SISTEMA NO ESTÁ LISTO")
        print("   Corrige los errores críticos antes de continuar")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
