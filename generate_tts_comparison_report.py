#!/usr/bin/env python3
"""
Script de Comparación Completa de Modelos TTS con Reproducción de Audio
======================================================================
Genera un reporte exhaustivo comparando Azure TTS, F5-TTS, Kokoro TTS y XTTS-v2
Incluye métricas de rendimiento, recursos consumidos y REPRODUCTORES DE AUDIO.

Versión con Audio: 2025-06-25
"""

import os
import sys
import time
import json
import subprocess
import threading
import requests
import psutil
import datetime
import shutil
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional

print("🎯 Script de Comparación TTS iniciando...")

# Verificar dependencias
try:
    import statistics
except ImportError:
    print("📦 Instalando dependencias...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psutil', 'requests'])
    import statistics

class ResourceMonitor:
    """Monitor de recursos del sistema durante las pruebas"""
    
    def __init__(self):
        self.monitoring = False
        self.data = []
        self.gpu_available = self._check_gpu()
        
    def _check_gpu(self) -> bool:
        """Verifica si hay GPU disponible"""
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def _get_gpu_stats(self) -> Dict[str, float]:
        """Obtiene estadísticas de GPU"""
        if not self.gpu_available:
            return {"gpu_util": 0, "gpu_memory": 0, "gpu_temp": 0}
        
        try:
            result = subprocess.run([
                'nvidia-smi', '--query-gpu=utilization.gpu,memory.used,temperature.gpu',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                gpu_util, gpu_memory, gpu_temp = result.stdout.strip().split(', ')
                return {
                    "gpu_util": float(gpu_util),
                    "gpu_memory": float(gpu_memory),
                    "gpu_temp": float(gpu_temp)
                }
        except:
            pass
        
        return {"gpu_util": 0, "gpu_memory": 0, "gpu_temp": 0}
    
    def _monitor_loop(self):
        """Loop principal de monitoreo"""
        while self.monitoring:
            timestamp = time.time()
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            gpu_stats = self._get_gpu_stats()
            
            self.data.append({
                "timestamp": timestamp,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_total_gb": memory.total / (1024**3),
                **gpu_stats
            })
            
            time.sleep(2)
    
    def start_monitoring(self):
        """Inicia el monitoreo"""
        self.monitoring = True
        self.data = []
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.start()
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Detiene el monitoreo y retorna estadísticas"""
        self.monitoring = False
        if hasattr(self, 'thread'):
            self.thread.join()
        
        if not self.data:
            return {}
        
        cpu_values = [d["cpu_percent"] for d in self.data]
        memory_values = [d["memory_percent"] for d in self.data]
        gpu_util_values = [d["gpu_util"] for d in self.data]
        gpu_memory_values = [d["gpu_memory"] for d in self.data]
        
        return {
            "duration": len(self.data) * 2,
            "cpu": {
                "avg": statistics.mean(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory": {
                "avg": statistics.mean(memory_values),
                "max": max(memory_values),
                "min": min(memory_values),
                "peak_gb": max([d["memory_used_gb"] for d in self.data])
            },
            "gpu": {
                "available": self.gpu_available,
                "util_avg": statistics.mean(gpu_util_values) if gpu_util_values else 0,
                "util_max": max(gpu_util_values) if gpu_util_values else 0,
                "memory_avg": statistics.mean(gpu_memory_values) if gpu_memory_values else 0,
                "memory_max": max(gpu_memory_values) if gpu_memory_values else 0
            }
        }

if __name__ == "__main__":
    print("✅ Script base creado correctamente")
    print("🔄 Continuando con la implementación completa...")

class TTSModelTester:
    """Tester para un modelo TTS específico con captura de audio"""
    
    def __init__(self, name: str, port: int, directory: str):
        self.name = name
        self.port = port
        self.directory = directory
        self.base_url = f"http://localhost:{port}"
        self.results = {}
        self.audio_files = []
        
    def start_service(self) -> bool:
        """Levanta el servicio Docker"""
        try:
            print(f"🚀 Iniciando {self.name}...")
            original_dir = os.getcwd()
            os.chdir(self.directory)
            
            result = subprocess.run(
                ['docker', 'compose', 'up', '-d'],
                capture_output=True, text=True
            )
            
            os.chdir(original_dir)
            
            if result.returncode != 0:
                print(f"❌ Error iniciando {self.name}: {result.stderr}")
                return False
            
            # Esperar a que el servicio esté listo
            max_wait = 120
            for attempt in range(max_wait // 5):
                time.sleep(5)
                if self._check_health():
                    print(f"✅ {self.name} iniciado correctamente")
                    return True
                print(f"⏳ Esperando {self.name}... ({(attempt + 1) * 5}s)")
            
            print(f"❌ {self.name} no se inició en el tiempo esperado")
            return False
            
        except Exception as e:
            print(f"❌ Error iniciando {self.name}: {e}")
            return False
    
    def stop_service(self):
        """Detiene el servicio Docker"""
        try:
            print(f"🛑 Deteniendo {self.name}...")
            original_dir = os.getcwd()
            os.chdir(self.directory)
            subprocess.run(['docker', 'compose', 'down'], capture_output=True)
            os.chdir(original_dir)
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ Error deteniendo {self.name}: {e}")
    
    def _check_health(self) -> bool:
        """Verifica si el servicio está saludable"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def _capture_audio_files(self, test_name: str) -> List[str]:
        """Captura archivos de audio generados recientemente"""
        debug_audio_path = os.path.join(self.directory, "debug_audio")
        if not os.path.exists(debug_audio_path):
            return []
        
        # Buscar archivos WAV recientes (últimos 30 segundos)
        current_time = time.time()
        recent_files = []
        
        for file_path in glob.glob(os.path.join(debug_audio_path, "*.wav")):
            file_mtime = os.path.getmtime(file_path)
            if current_time - file_mtime < 30:  # Archivos de los últimos 30 segundos
                recent_files.append(file_path)
        
        # Ordenar por tiempo de modificación (más reciente primero)
        recent_files.sort(key=os.path.getmtime, reverse=True)
        
        return recent_files[:2]  # Máximo 2 archivos más recientes
    
    def run_tests(self) -> Dict[str, Any]:
        """Ejecuta las pruebas del modelo"""
        print(f"🧪 Ejecutando pruebas de {self.name}...")
        
        health_info = self._get_health_info()
        voices_info = self._get_voices_info()
        synthesis_tests = self._run_synthesis_tests()
        test_script_results = self._run_test_script()
        
        return {
            "health": health_info,
            "voices": voices_info,
            "synthesis": synthesis_tests,
            "test_script": test_script_results,
            "audio_files": self.audio_files
        }
    
    def _get_health_info(self) -> Dict[str, Any]:
        """Obtiene información de salud del servicio"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"⚠️ Error obteniendo health de {self.name}: {e}")
        return {}
    
    def _get_voices_info(self) -> Dict[str, Any]:
        """Obtiene información de voces disponibles"""
        try:
            endpoints = ["/voices", "/voices?language=es", "/languages"]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    if response.status_code == 200:
                        return response.json()
                except:
                    continue
        except Exception as e:
            print(f"⚠️ Error obteniendo voces de {self.name}: {e}")
        return {}
    
    def _run_synthesis_tests(self) -> Dict[str, Any]:
        """Ejecuta pruebas de síntesis básicas"""
        tests = [
            {
                "name": "synthesis_basic",
                "text": "Hola, esta es una prueba de síntesis de voz básica.",
                "params": {"language": "es"}
            },
            {
                "name": "synthesis_long",
                "text": "Esta es una prueba más larga para evaluar el rendimiento con textos extensos. La síntesis de texto a voz es una tecnología fascinante.",
                "params": {"language": "es"}
            }
        ]
        
        results = {}
        
        for test in tests:
            try:
                print(f"🎤 Ejecutando síntesis: {test['name']}")
                start_time = time.time()
                
                payload = {
                    "text": test["text"],
                    **test["params"]
                }
                
                response = requests.post(
                    f"{self.base_url}/synthesize_json",
                    json=payload,
                    timeout=60
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                # Capturar archivos de audio generados
                audio_files = self._capture_audio_files(test["name"])
                
                if response.status_code == 200:
                    result_data = response.json()
                    results[test["name"]] = {
                        "success": True,
                        "response_time": response_time,
                        "data": result_data,
                        "audio_files": audio_files,
                        "text": test["text"],
                        "description": test["name"]
                    }
                    
                    # Guardar referencia a los archivos de audio
                    for audio_file in audio_files:
                        self.audio_files.append({
                            "test": test["name"],
                            "file": audio_file,
                            "text": test["text"],
                            "description": test["name"]
                        })
                else:
                    results[test["name"]] = {
                        "success": False,
                        "response_time": response_time,
                        "error": f"HTTP {response.status_code}",
                        "text": test["text"],
                        "description": test["name"]
                    }
                    
            except Exception as e:
                results[test["name"]] = {
                    "success": False,
                    "error": str(e),
                    "text": test["text"],
                    "description": test["name"]
                }
        
        return results
    
    def _run_test_script(self) -> Dict[str, Any]:
        """Ejecuta el script de prueba del modelo si existe"""
        test_script = os.path.join(self.directory, "test_service.py")
        
        if not os.path.exists(test_script):
            return {"available": False}
        
        try:
            print(f"📋 Ejecutando script de prueba de {self.name}...")
            start_time = time.time()
            
            original_dir = os.getcwd()
            os.chdir(self.directory)
            
            result = subprocess.run(
                [sys.executable, 'test_service.py'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            os.chdir(original_dir)
            end_time = time.time()
            
            return {
                "available": True,
                "success": result.returncode == 0,
                "duration": end_time - start_time,
                "stdout": result.stdout[-2000:] if result.stdout else "",
                "stderr": result.stderr[-1000:] if result.stderr else ""
            }
            
        except subprocess.TimeoutExpired:
            return {
                "available": True,
                "success": False,
                "error": "Timeout - script tardó más de 5 minutos"
            }
        except Exception as e:
            return {
                "available": True,
                "success": False,
                "error": str(e)
            }

class ReportGenerator:
    """Generador de reportes HTML con reproductores de audio"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.audio_dir = self.output_dir / "audio"
        self.audio_dir.mkdir(exist_ok=True)
        
    def generate_report(self, comparison_data: Dict[str, Any]):
        """Genera el reporte HTML completo con audio"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"tts_comparison_report_{timestamp}.html"
        
        # Copiar archivos de audio al directorio de reportes
        self._copy_audio_files(comparison_data)
        
        html_content = self._generate_html(comparison_data)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # También generar JSON con datos raw
        json_file = self.output_dir / f"tts_comparison_data_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(comparison_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Reporte con audio generado: {report_file}")
        print(f"📊 Datos JSON: {json_file}")
        print(f"🎵 Archivos de audio en: {self.audio_dir}")
        
        return str(report_file)
    
    def _copy_audio_files(self, comparison_data: Dict[str, Any]):
        """Copia archivos de audio al directorio de reportes"""
        audio_counter = 0
        
        for model_name, model_data in comparison_data.get('models', {}).items():
            if model_data.get('status') != 'completed':
                continue
                
            audio_files = model_data.get('test_results', {}).get('audio_files', [])
            
            for audio_info in audio_files:
                source_file = audio_info.get('file')
                if source_file and os.path.exists(source_file):
                    audio_counter += 1
                    
                    # Crear nombre descriptivo
                    model_safe = model_name.replace(' ', '_').replace('-', '_').lower()
                    test_name = audio_info.get('test', 'unknown')
                    
                    dest_filename = f"{audio_counter:02d}_{model_safe}_{test_name}.wav"
                    dest_path = self.audio_dir / dest_filename
                    
                    try:
                        shutil.copy2(source_file, dest_path)
                        audio_info['copied_file'] = dest_filename
                        print(f"🎵 Audio copiado: {dest_filename}")
                    except Exception as e:
                        print(f"⚠️ Error copiando audio {source_file}: {e}")
    
    def _generate_html(self, data: Dict[str, Any]) -> str:
        """Genera el contenido HTML del reporte"""
        timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Generar tabla de resumen
        summary_table = self._generate_summary_table(data)
        
        # Generar análisis detallado
        detailed_analysis = self._generate_detailed_analysis(data)
        
        # Generar análisis de recursos
        resource_analysis = self._generate_resource_table(data)
        
        # Generar sección de audio
        audio_section = self._generate_audio_section(data)
        
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Comparación TTS con Audio</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ font-size: 1.2em; opacity: 0.9; }}
        .section {{ background: white; padding: 25px; margin-bottom: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #2c3e50; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 3px solid #3498db; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .model-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db; }}
        .model-card h3 {{ color: #2c3e50; margin-bottom: 15px; }}
        .metric {{ margin: 10px 0; }}
        .metric-label {{ font-weight: bold; color: #34495e; }}
        .metric-value {{ color: #27ae60; font-weight: bold; }}
        .status-ok {{ color: #27ae60; }}
        .status-error {{ color: #e74c3c; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 0.9em; font-weight: bold; }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-error {{ background: #f8d7da; color: #721c24; }}
        .code {{ font-family: monospace; background: #f4f4f4; padding: 10px; border-radius: 4px; white-space: pre-wrap; max-height: 200px; overflow-y: auto; }}
        .audio-player {{ margin: 10px 0; padding: 15px; background: #f1f3f4; border-radius: 8px; border: 1px solid #e0e0e0; }}
        .audio-player h4 {{ color: #2c3e50; margin-bottom: 8px; font-size: 1em; }}
        .audio-player p {{ color: #666; font-size: 0.9em; margin-bottom: 10px; }}
        .audio-player audio {{ width: 100%; margin-top: 5px; }}
        .audio-section {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }}
        .audio-model {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #e74c3c; }}
        .text-sample {{ background: #fff; padding: 10px; border-radius: 4px; border: 1px solid #ddd; margin: 5px 0; font-style: italic; color: #555; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎤 Reporte de Comparación TTS con Audio</h1>
            <p>Análisis Completo de Modelos de Text-to-Speech</p>
            <p>¡Ahora con Reproductores de Audio! 🔊</p>
            <p>Generado el {timestamp}</p>
        </div>
        
        <div class="section">
            <h2>📊 Resumen Ejecutivo</h2>
            {summary_table}
        </div>
        
        <div class="section">
            <h2>🎵 Muestras de Audio por Modelo</h2>
            {audio_section}
        </div>
        
        <div class="section">
            <h2>🔍 Análisis Detallado por Modelo</h2>
            {detailed_analysis}
        </div>
        
        <div class="section">
            <h2>💻 Análisis de Recursos</h2>
            {resource_analysis}
        </div>
        
        <div class="section">
            <h2>🎯 Recomendaciones</h2>
            <div class="grid">
                <div class="model-card">
                    <h3>🏆 Para Producción Comercial</h3>
                    <p><strong>Azure TTS</strong> - Ideal para aplicaciones que requieren velocidad, confiabilidad y múltiples dialectos</p>
                </div>
                <div class="model-card">
                    <h3>⚡ Para Alto Volumen</h3>
                    <p><strong>Kokoro TTS</strong> - Mejor balance rendimiento/recursos para sistemas auto-hospedados</p>
                </div>
                <div class="model-card">
                    <h3>🎤 Para Clonación de Voz</h3>
                    <p><strong>XTTS-v2</strong> - Cuando necesites clonar voces específicas o máximo control</p>
                </div>
                <div class="model-card">
                    <h3>🇪🇸 Para Acento Español Perfecto</h3>
                    <p><strong>F5-TTS</strong> - Cuando la calidad del acento español sea más importante que la velocidad</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    def _generate_audio_section(self, data: Dict[str, Any]) -> str:
        """Genera la sección de muestras de audio"""
        models = data.get('models', {})
        
        audio_cards = ""
        for model_name, model_data in models.items():
            if model_data.get('status') != 'completed':
                continue
                
            audio_files = model_data.get('test_results', {}).get('audio_files', [])
            
            if not audio_files:
                audio_cards += f"""
                <div class="audio-model">
                    <h3>{model_name}</h3>
                    <p>⚠️ No se capturaron archivos de audio para este modelo</p>
                </div>
                """
                continue
            
            audio_players = ""
            for audio_info in audio_files:
                copied_file = audio_info.get('copied_file')
                if copied_file:
                    description = audio_info.get('description', 'Muestra de audio')
                    text = audio_info.get('text', '')
                    
                    audio_players += f"""
                    <div class="audio-player">
                        <h4>🎵 {description}</h4>
                        <div class="text-sample">"{text}"</div>
                        <audio controls preload="metadata">
                            <source src="audio/{copied_file}" type="audio/wav">
                            Tu navegador no soporta el elemento de audio.
                        </audio>
                    </div>
                    """
            
            audio_cards += f"""
            <div class="audio-model">
                <h3>{model_name}</h3>
                {audio_players}
            </div>
            """
        
        return f'<div class="audio-section">{audio_cards}</div>'
    
    def _generate_summary_table(self, data: Dict[str, Any]) -> str:
        """Genera la tabla de resumen"""
        models = data.get('models', {})
        
        summary_rows = ""
        for model_name, model_data in models.items():
            if model_data.get('status') != 'completed':
                summary_rows += f"""
                <tr>
                    <td><strong>{model_name}</strong></td>
                    <td><span class="badge badge-error">FALLÓ</span></td>
                    <td>N/A</td>
                    <td>N/A</td>
                    <td>N/A</td>
                    <td>N/A</td>
                    <td>N/A</td>
                </tr>
                """
                continue
                
            resources = model_data.get('resources', {})
            test_script = model_data.get('test_results', {}).get('test_script', {})
            synthesis = model_data.get('test_results', {}).get('synthesis', {})
            audio_files = model_data.get('test_results', {}).get('audio_files', [])
            
            cpu_avg = resources.get('cpu', {}).get('avg', 0)
            gpu_max = resources.get('gpu', {}).get('util_max', 0)
            duration = test_script.get('duration', 0)
            success = test_script.get('success', False)
            audio_count = len(audio_files)
            
            # Calcular tiempo de respuesta promedio
            response_times = []
            for test_name, test_data in synthesis.items():
                if test_data.get('success', False):
                    response_times.append(test_data.get('response_time', 0))
            avg_response = statistics.mean(response_times) if response_times else 0
            
            status_badge = 'badge-success' if success else 'badge-error'
            status_text = 'ÉXITO' if success else 'FALLO'
            
            summary_rows += f"""
            <tr>
                <td><strong>{model_name}</strong></td>
                <td><span class="badge {status_badge}">{status_text}</span></td>
                <td>{duration:.1f}s</td>
                <td>{avg_response:.2f}s</td>
                <td>{cpu_avg:.1f}%</td>
                <td>{gpu_max:.1f}%</td>
                <td>🎵 {audio_count}</td>
            </tr>
            """
        
        return f"""
        <table>
            <thead>
                <tr>
                    <th>Modelo</th>
                    <th>Estado</th>
                    <th>Tiempo Pruebas</th>
                    <th>Resp. Promedio</th>
                    <th>CPU Promedio</th>
                    <th>GPU Máxima</th>
                    <th>Muestras Audio</th>
                </tr>
            </thead>
            <tbody>
                {summary_rows}
            </tbody>
        </table>
        """
    
    def _generate_detailed_analysis(self, data: Dict[str, Any]) -> str:
        """Genera el análisis detallado"""
        models = data.get('models', {})
        
        model_cards = ""
        for model_name, model_data in models.items():
            if model_data.get('status') != 'completed':
                model_cards += f"""
                <div class="model-card">
                    <h3>{model_name}</h3>
                    <div class="metric">
                        <span class="metric-label">Estado:</span>
                        <span class="status-error">Error: {model_data.get('error', 'No disponible')}</span>
                    </div>
                </div>
                """
                continue
                
            health = model_data.get('test_results', {}).get('health', {})
            synthesis = model_data.get('test_results', {}).get('synthesis', {})
            resources = model_data.get('resources', {})
            test_script = model_data.get('test_results', {}).get('test_script', {})
            audio_files = model_data.get('test_results', {}).get('audio_files', [])
            
            # Calcular métricas de síntesis
            basic_test = synthesis.get('synthesis_basic', {})
            response_time = basic_test.get('response_time', 0)
            success_count = sum(1 for test in synthesis.values() if test.get('success', False))
            total_tests = len(synthesis)
            
            # Resultado del script de prueba
            script_duration = test_script.get('duration', 0)
            script_success = test_script.get('success', False)
            script_stdout = test_script.get('stdout', '')[-500:] if test_script.get('stdout') else 'N/A'
            
            model_cards += f"""
            <div class="model-card">
                <h3>{model_name}</h3>
                <div class="metric">
                    <span class="metric-label">Estado del Servicio:</span>
                    <span class="metric-value status-ok">{health.get('status', 'unknown')}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Modelo:</span>
                    <span class="metric-value">{health.get('model', 'N/A')}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Tiempo de Respuesta:</span>
                    <span class="metric-value">{response_time:.2f}s</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Pruebas Síntesis:</span>
                    <span class="metric-value">{success_count}/{total_tests}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Muestras de Audio:</span>
                    <span class="metric-value">🎵 {len(audio_files)} archivos capturados</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Script de Prueba:</span>
                    <span class="metric-value {'status-ok' if script_success else 'status-error'}">{script_duration:.1f}s - {'ÉXITO' if script_success else 'FALLO'}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">CPU Promedio:</span>
                    <span class="metric-value">{resources.get('cpu', {}).get('avg', 0):.1f}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">GPU Máxima:</span>
                    <span class="metric-value">{resources.get('gpu', {}).get('util_max', 0):.1f}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Salida Script (últimas líneas):</span>
                    <div class="code">{script_stdout}</div>
                </div>
            </div>
            """
        
        return f'<div class="grid">{model_cards}</div>'
    
    def _generate_resource_table(self, data: Dict[str, Any]) -> str:
        """Genera la tabla de recursos"""
        models = data.get('models', {})
        
        resource_rows = ""
        for model_name, model_data in models.items():
            if model_data.get('status') != 'completed':
                continue
                
            resources = model_data.get('resources', {})
            cpu = resources.get('cpu', {})
            memory = resources.get('memory', {})
            gpu = resources.get('gpu', {})
            
            resource_rows += f"""
            <tr>
                <td><strong>{model_name}</strong></td>
                <td>{cpu.get('avg', 0):.1f}%</td>
                <td>{cpu.get('max', 0):.1f}%</td>
                <td>{memory.get('avg', 0):.1f}%</td>
                <td>{memory.get('peak_gb', 0):.1f} GB</td>
                <td>{gpu.get('util_avg', 0):.1f}%</td>
                <td>{gpu.get('util_max', 0):.1f}%</td>
                <td>{gpu.get('memory_max', 0):.0f} MB</td>
            </tr>
            """
        
        return f"""
        <table>
            <thead>
                <tr>
                    <th>Modelo</th>
                    <th>CPU Promedio</th>
                    <th>CPU Máximo</th>
                    <th>RAM Promedio</th>
                    <th>RAM Pico</th>
                    <th>GPU Promedio</th>
                    <th>GPU Máximo</th>
                    <th>VRAM Máximo</th>
                </tr>
            </thead>
            <tbody>
                {resource_rows}
            </tbody>
        </table>
        """

class TTSComparison:
    """Clase principal para ejecutar la comparación completa con audio"""
    
    def __init__(self):
        self.models = {
            "Azure TTS": TTSModelTester("Azure TTS", 5004, "azure-tts-ms"),
            "F5-TTS": TTSModelTester("F5-TTS", 5005, "f5-tts-ms"),
            "Kokoro TTS": TTSModelTester("Kokoro TTS", 5002, "kokoro-tts-ms"),
            "XTTS-v2": TTSModelTester("XTTS-v2", 5001, "xtts-v2-tts-ms")
        }
        
        self.output_dir = "tts_comparison_reports"
        Path(self.output_dir).mkdir(exist_ok=True)
        
    def run_comparison(self) -> str:
        """Ejecuta la comparación completa con captura de audio"""
        print("🚀 INICIANDO COMPARACIÓN COMPLETA DE MODELOS TTS CON AUDIO")
        print("=" * 70)
        
        comparison_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "models": {},
            "summary": {}
        }
        
        original_dir = os.getcwd()
        
        try:
            for model_name, tester in self.models.items():
                print(f"\n🎯 PROCESANDO: {model_name}")
                print("-" * 40)
                
                # Cambiar al directorio del proyecto
                os.chdir(original_dir)
                
                # Inicializar monitor de recursos
                monitor = ResourceMonitor()
                
                # Iniciar servicio
                if not tester.start_service():
                    comparison_data["models"][model_name] = {
                        "status": "failed_to_start",
                        "error": "No se pudo iniciar el servicio"
                    }
                    continue
                
                # Iniciar monitoreo de recursos
                monitor.start_monitoring()
                
                # Ejecutar pruebas
                test_results = tester.run_tests()
                
                # Detener monitoreo
                resource_stats = monitor.stop_monitoring()
                
                # Detener servicio
                tester.stop_service()
                
                # Guardar resultados
                comparison_data["models"][model_name] = {
                    "status": "completed",
                    "test_results": test_results,
                    "resources": resource_stats
                }
                
                print(f"✅ {model_name} completado")
        
        finally:
            os.chdir(original_dir)
        
        # Generar reporte con audio
        print("\n📄 GENERANDO REPORTE CON AUDIO...")
        report_generator = ReportGenerator(self.output_dir)
        report_file = report_generator.generate_report(comparison_data)
        
        print(f"\n🎉 COMPARACIÓN CON AUDIO COMPLETADA")
        print(f"📄 Reporte disponible en: {report_file}")
        
        return report_file

def main():
    """Función principal"""
    try:
        print("🎯 Verificando sistema...")
        
        # Verificar Docker
        try:
            subprocess.run(['docker', '--version'], capture_output=True, check=True)
            print("✅ Docker disponible")
        except:
            print("❌ Docker no está disponible")
            sys.exit(1)
        
        # Verificar nvidia-smi si hay GPU
        try:
            subprocess.run(['nvidia-smi'], capture_output=True, check=True)
            print("✅ GPU NVIDIA disponible")
        except:
            print("⚠️ GPU NVIDIA no disponible, usando CPU")
        
        # Ejecutar comparación
        comparison = TTSComparison()
        report_file = comparison.run_comparison()
        
        print(f"\n🔗 Para ver el reporte, abre: {report_file}")
        
        # Intentar abrir el reporte automáticamente
        try:
            if sys.platform.startswith('linux'):
                subprocess.run(['xdg-open', report_file])
            elif sys.platform.startswith('darwin'):
                subprocess.run(['open', report_file])
            elif sys.platform.startswith('win'):
                subprocess.run(['start', report_file], shell=True)
        except:
            print("ℹ️ No se pudo abrir el reporte automáticamente")
            
        print(f"✅ Proceso completado exitosamente")
        print(f"📁 Archivos generados en: tts_comparison_reports/")
        print(f"🎵 ¡Ahora puedes escuchar las muestras de audio en el reporte!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Comparación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error durante la comparación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Eliminar la línea anterior que se ejecutaba inmediatamente
if __name__ == "__main__":
    main()
